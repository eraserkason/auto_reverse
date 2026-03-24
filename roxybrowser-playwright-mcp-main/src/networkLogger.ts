/**
 * Copyright (c) Microsoft Corporation.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { createRequire } from 'module';
import { v4 as uuidv4 } from 'uuid';
import { logUnhandledError } from './utils/log.js';
import { registerSession, updateSessionMeta, writeNetworkEntry } from './redisWriter.js';

import type { FullConfig } from './config.js';
import type * as playwright from 'playwright';

type FilterOptions = {
  firstPartyHosts: string[];
  keepThirdPartyHosts: string[];
  keepUnknownJs: boolean;
};

type FilterOutcome = {
  keep: boolean;
  reason: string;
};

const require = createRequire(import.meta.url);
const sessionNetworkFilter = require('../../main_project_backend/network/session_network_filter.js') as {
  classifyEntry: (entry: unknown, options: FilterOptions) => FilterOutcome;
  inferFirstPartyHosts: (input: { pageUrl?: string }) => string[];
};

type NetworkLogEntry = {
  id: string;
  timestamp: string;
  request: {
    method: string;
    url: string;
    protocol: string;
    headers: Record<string, string>;
    body?: string;
    bodySize: number;
    bodyTruncated: boolean;
  };
  response: {
    status: number;
    statusText: string;
    protocol: string;
    headers: Record<string, string>;
    body?: string;
    bodySize: number;
    bodyTruncated: boolean;
    mimeType: string;
  };
  timing: {
    startedAt: string;
    finishedAt: string;
    duration: number;
  };
};

const SENSITIVE_HEADERS = [
  'authorization',
  'cookie',
  'set-cookie',
  'x-api-key',
  'x-auth-token',
];

type ExtractedBodyData = {
  body?: string;
  size: number;
  truncated: boolean;
};

type CaptureState = 'inactive' | 'armed' | 'active';

export class NetworkLogger {
  readonly sessionId: string;
  private _config: FullConfig;
  private _armedEntries: NetworkLogEntry[] = [];
  private _pendingEntries: NetworkLogEntry[] = [];
  private _flushTimeout: NodeJS.Timeout | undefined;
  private _activeFlushPromise: Promise<void> | undefined;
  private _captureState: CaptureState;
  private _omitResponseBodyMimeTypes: string[];
  private _sensitiveHeaders: string[];
  private _requestStartTimes: Map<playwright.Request, number> = new Map();
  private _pendingBodyExtractions: Set<Promise<void>> = new Set();
  private _firstPartyHosts: Set<string> = new Set();
  private _pageUrl: string | undefined;

  constructor(sessionId: string, config: FullConfig) {
    this.sessionId = sessionId;
    this._config = config;
    this._captureState = config.network?.logRequestsFromFirstNavigation ? 'inactive' : 'active';
    this._omitResponseBodyMimeTypes = (config.network?.omitResponseBodyMimeTypes || []).map(type => type.trim().toLowerCase()).filter(Boolean);
    this._sensitiveHeaders = config.network?.sensitiveHeaders || SENSITIVE_HEADERS;
  }

  static async create(config: FullConfig, rootPath: string | undefined, sessionId?: string): Promise<NetworkLogger> {
    void rootPath;
    const id = sessionId ?? `session-${Date.now()}`;
    if (!sessionId)
      await registerSession(id, { startTime: new Date().toISOString() }).catch(logUnhandledError);
    await updateSessionMeta(id, {
      networkFilterMode: 'write_filtered',
      networkFilterSource: 'session_network_filter',
      networkIndexVersion: 'v1',
      networkIndexMode: 'structured_write_side_v1',
    }).catch(logUnhandledError);
    // eslint-disable-next-line no-console
    console.error(`Network Log (Redis): session=${id}`);
    if (config.logSessionId && !sessionId) {
      // eslint-disable-next-line no-console
      console.error(`Session ID: ${id}`);
    }
    return new NetworkLogger(id, config);
  }

  isActive(): boolean {
    return this._captureState === 'active';
  }

  armForNavigation() {
    if (this._captureState === 'active')
      return;
    this._captureState = 'armed';
  }

  activateArmedCapture() {
    if (this._captureState === 'active')
      return;
    this._captureState = 'active';
    if (!this._armedEntries.length)
      return;
    this._pendingEntries.push(...this._armedEntries);
    this._armedEntries = [];
    this._scheduleFlush();
  }

  discardArmedCapture() {
    if (this._captureState !== 'armed')
      return;
    this._captureState = 'inactive';
    this._armedEntries = [];
    this._requestStartTimes.clear();
  }

  logRequest(request: playwright.Request, response: playwright.Response) {
    const captureState = this._captureState;
    if (captureState === 'inactive') {
      this._requestStartTimes.delete(request);
      return;
    }
    const startTime = this._requestStartTimes.get(request) || Date.now();
    this._requestStartTimes.delete(request);
    const finishedTime = Date.now();

    const entry: NetworkLogEntry = {
      id: uuidv4(),
      timestamp: new Date().toISOString(),
      request: {
        method: request.method(),
        url: request.url(),
        protocol: this._getProtocol(request),
        headers: this._redactHeaders(request.headers()),
        bodySize: 0,
        bodyTruncated: false,
      },
      response: {
        status: response.status(),
        statusText: response.statusText(),
        protocol: this._getProtocol(response),
        headers: this._redactHeaders(response.headers()),
        bodySize: 0,
        bodyTruncated: false,
        mimeType: response.headers()['content-type'] || 'unknown',
      },
      timing: {
        startedAt: new Date(startTime).toISOString(),
        finishedAt: new Date(finishedTime).toISOString(),
        duration: finishedTime - startTime,
      },
    };
    this._rememberFirstPartyContext(request, entry);

    if (!this._config.network?.omitRequestBody) {
      try {
        const postData = request.postData();
        if (postData) {
          const bodySize = Buffer.byteLength(postData, 'utf8');
          entry.request.body = postData;
          entry.request.bodySize = bodySize;
          entry.request.bodyTruncated = false;
        }
      } catch {
        // Ignore errors when extracting request body
      }
    }

    if (!this._config.network?.omitResponseBody) {
      const bodyExtraction = this._extractResponseBody(response).then(bodyData => {
        if (bodyData) {
          if (bodyData.body !== undefined)
            entry.response.body = bodyData.body;
          entry.response.bodySize = bodyData.size;
          entry.response.bodyTruncated = bodyData.truncated;
        }
        this._appendEntry(entry, captureState);
      }).catch(error => {
        logUnhandledError(error);
        this._appendEntry(entry, captureState);
      }).finally(() => {
        this._pendingBodyExtractions.delete(bodyExtraction);
      });
      this._pendingBodyExtractions.add(bodyExtraction);
    } else {
      this._appendEntry(entry, captureState);
    }
  }

  recordRequestStart(request: playwright.Request) {
    if (this._captureState === 'inactive')
      return;
    this._requestStartTimes.set(request, Date.now());
  }

  private async _extractResponseBody(response: playwright.Response): Promise<ExtractedBodyData | null> {
    try {
      const body = await response.body();
      const size = body.length;
      const isBinary = this._isBinaryContent(response);
      if (this._shouldOmitResponseBody(response)) {
        return {
          size,
          truncated: size > 0,
        };
      }

      return {
        body: isBinary ? body.toString('base64') : body.toString('utf8'),
        size,
        truncated: false,
      };
    } catch {
      return null;
    }
  }

  private _normalizeContentType(contentType: string): string {
    return contentType.split(';', 1)[0]?.trim().toLowerCase() || '';
  }

  private _shouldOmitResponseBody(response: playwright.Response): boolean {
    if (!this._omitResponseBodyMimeTypes.length)
      return false;
    const normalizedContentType = this._normalizeContentType(response.headers()['content-type'] || '');
    return !!normalizedContentType && this._omitResponseBodyMimeTypes.includes(normalizedContentType);
  }

  private _isBinaryContent(response: playwright.Response): boolean {
    const contentType = this._normalizeContentType(response.headers()['content-type'] || '');
    const binaryTypes = [
      'image/',
      'video/',
      'audio/',
      'application/pdf',
      'application/zip',
      'application/octet-stream',
      'font/',
    ];
    return binaryTypes.some(type => contentType.includes(type));
  }

  private _redactHeaders(headers: Record<string, string>): Record<string, string> {
    const redacted = { ...headers };
    for (const key of Object.keys(redacted)) {
      if (this._sensitiveHeaders.includes(key.toLowerCase()))
        redacted[key] = '[REDACTED]';
    }
    return redacted;
  }

  private _getProtocol(requestOrResponse: playwright.Request | playwright.Response): string {
    const url = requestOrResponse.url();
    if (url.startsWith('https://')) return 'HTTPS';
    if (url.startsWith('http://')) return 'HTTP';
    return 'unknown';
  }

  private _appendEntry(entry: NetworkLogEntry, captureState: CaptureState) {
    if (captureState === 'inactive')
      return;
    if (captureState === 'armed') {
      if (this._captureState === 'inactive')
        return;
      if (this._captureState === 'active') {
        this._pendingEntries.push(entry);
        this._scheduleFlush();
        return;
      }
      this._armedEntries.push(entry);
      return;
    }
    this._pendingEntries.push(entry);
    this._scheduleFlush();
  }

  private _scheduleFlush() {
    if (this._flushTimeout)
      clearTimeout(this._flushTimeout);
    this._flushTimeout = setTimeout(() => {
      void this._flushEntries().catch(logUnhandledError);
    }, 1000);
  }

  async flush(): Promise<void> {
    while (true) {
      while (this._pendingBodyExtractions.size)
        await Promise.all([...this._pendingBodyExtractions]);
      if (this._flushTimeout)
        clearTimeout(this._flushTimeout);
      if (this._activeFlushPromise) {
        await this._activeFlushPromise;
        continue;
      }
      if (!this._pendingEntries.length)
        return;
      await this._flushEntries();
    }
  }

  private async _flushEntries() {
    if (this._activeFlushPromise)
      return this._activeFlushPromise;

    clearTimeout(this._flushTimeout);
    this._flushTimeout = undefined;
    const entries = this._pendingEntries;
    this._pendingEntries = [];
    if (!entries.length)
      return;
    const flushEntries = entries.filter(entry => this._shouldWriteEntry(entry));

    this._activeFlushPromise = Promise.all(flushEntries.map(entry => writeNetworkEntry(this.sessionId, {
      id: entry.id,
      timestamp: entry.timestamp,
      request: entry.request as unknown as Record<string, unknown>,
      response: entry.response as unknown as Record<string, unknown>,
      timing: entry.timing as unknown as Record<string, unknown>,
    }))).then(() => {});

    try {
      await this._activeFlushPromise;
    } finally {
      this._activeFlushPromise = undefined;
    }
  }

  private _rememberFirstPartyContext(request: playwright.Request, entry: NetworkLogEntry) {
    const resourceType = request.resourceType();
    if (resourceType === 'document' || entry.response.mimeType.toLowerCase().includes('text/html')) {
      this._pageUrl = entry.request.url;
      for (const host of sessionNetworkFilter.inferFirstPartyHosts({ pageUrl: entry.request.url }))
        this._firstPartyHosts.add(host);
      void updateSessionMeta(this.sessionId, {
        pageUrl: entry.request.url,
        currentUrl: entry.request.url,
      }).catch(logUnhandledError);
    }
  }

  private _shouldWriteEntry(entry: NetworkLogEntry): boolean {
    const result = sessionNetworkFilter.classifyEntry(entry, {
      firstPartyHosts: [...this._firstPartyHosts],
      keepThirdPartyHosts: [],
      keepUnknownJs: true,
    });

    if (result.keep)
      return true;

    if (!this._pageUrl && entry.request.url) {
      for (const host of sessionNetworkFilter.inferFirstPartyHosts({ pageUrl: entry.request.url }))
        this._firstPartyHosts.add(host);
    }
    return false;
  }
}

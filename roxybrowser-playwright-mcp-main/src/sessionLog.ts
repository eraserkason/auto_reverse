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

import { Response } from './response.js';
import { logUnhandledError } from './utils/log.js';
import { registerSession, writeSessionEntry } from './redisWriter.js';

import type { FullConfig } from './config.js';
import type * as actions from './actions.js';
import type { Tab, TabSnapshot } from './tab.js';

type LogEntry = {
  timestamp: number;
  toolCall?: {
    toolName: string;
    toolArgs: Record<string, unknown>;
    result: string;
    isError?: boolean;
  };
  userAction?: actions.Action;
  code: string;
  tabSnapshot?: TabSnapshot;
};

export class SessionLog {
  readonly sessionId: string;
  private _ordinal = 0;
  private _pendingEntries: LogEntry[] = [];
  private _flushEntriesTimeout: NodeJS.Timeout | undefined;
  private _activeFlushPromise: Promise<void> | undefined;

  constructor(sessionId: string) {
    this.sessionId = sessionId;
  }

  static async create(config: FullConfig, rootPath: string | undefined): Promise<SessionLog> {
    void rootPath;
    const sessionId = `session-${Date.now()}`;
    const log = new SessionLog(sessionId);
    await registerSession(sessionId, { startTime: new Date().toISOString() }).catch(logUnhandledError);
    // eslint-disable-next-line no-console
    console.error(`Session (Redis): ${sessionId}`);
    if (config.logSessionId) {
      // eslint-disable-next-line no-console
      console.error(`Session ID: ${sessionId}`);
    }
    return log;
  }

  logResponse(response: Response) {
    const entry: LogEntry = {
      timestamp: performance.now(),
      toolCall: {
        toolName: response.toolName,
        toolArgs: response.toolArgs,
        result: response.result(),
        isError: response.isError(),
      },
      code: response.code(),
      tabSnapshot: response.tabSnapshot(),
    };
    this._appendEntry(entry);
  }

  logUserAction(action: actions.Action, tab: Tab, code: string, isUpdate: boolean) {
    code = code.trim();
    if (isUpdate) {
      const lastEntry = this._pendingEntries[this._pendingEntries.length - 1];
      if (lastEntry.userAction?.name === action.name) {
        lastEntry.userAction = action;
        lastEntry.code = code;
        return;
      }
    }
    if (action.name === 'navigate') {
      const lastEntry = this._pendingEntries[this._pendingEntries.length - 1];
      if (lastEntry?.tabSnapshot?.url === action.url)
        return;
    }
    const entry: LogEntry = {
      timestamp: performance.now(),
      userAction: action,
      code,
      tabSnapshot: {
        url: tab.page.url(),
        title: '',
        ariaSnapshot: action.ariaSnapshot || '',
        modalStates: [],
        consoleMessages: [],
        downloads: [],
      },
    };
    this._appendEntry(entry);
  }

  private _appendEntry(entry: LogEntry) {
    this._pendingEntries.push(entry);
    if (this._flushEntriesTimeout)
      clearTimeout(this._flushEntriesTimeout);
    this._flushEntriesTimeout = setTimeout(() => {
      void this._flushEntries().catch(logUnhandledError);
    }, 1000);
  }

  async flush(): Promise<void> {
    while (true) {
      if (this._flushEntriesTimeout)
        clearTimeout(this._flushEntriesTimeout);
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

    clearTimeout(this._flushEntriesTimeout);
    this._flushEntriesTimeout = undefined;
    const entries = this._pendingEntries;
    this._pendingEntries = [];
    if (!entries.length)
      return;

    this._activeFlushPromise = (async () => {
      await Promise.all(entries.map(async entry => {
        const ordinal = ++this._ordinal;

        const payload = {
          ordinal,
          toolCall: entry.toolCall,
          userAction: entry.userAction as Record<string, unknown> | undefined,
          code: entry.code,
          snapshot: entry.tabSnapshot?.ariaSnapshot,
        };

        await writeSessionEntry(this.sessionId, payload);
      }));
    })();

    try {
      await this._activeFlushPromise;
    } finally {
      this._activeFlushPromise = undefined;
    }
  }
}

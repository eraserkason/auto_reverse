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

import type * as playwright from 'playwright';

export type ToolCapability = 'core' | 'core-tabs' | 'core-install' | 'vision' | 'pdf';

export type Config = {
  /**
   * The browser to use.
   */
  browser?: {
    /**
     * The type of browser to use.
     */
    browserName?: 'chromium' | 'firefox' | 'webkit';

    /**
     * Keep the browser profile in memory, do not save it to disk.
     */
    isolated?: boolean;

    /**
     * Path to a user data directory for browser profile persistence.
     * Temporary directory is created by default.
     */
    userDataDir?: string;

    /**
     * Launch options passed to
     * @see https://playwright.dev/docs/api/class-browsertype#browser-type-launch-persistent-context
     *
     * This is useful for settings options like `channel`, `headless`, `executablePath`, etc.
     */
    launchOptions?: playwright.LaunchOptions;

    /**
     * Context options for the browser context.
     *
     * This is useful for settings options like `viewport`.
     */
    contextOptions?: playwright.BrowserContextOptions;

    /**
     * Chrome DevTools Protocol endpoint to connect to an existing browser instance in case of Chromium family browsers.
     */
    cdpEndpoint?: string;

    /**
     * Remote endpoint to connect to an existing Playwright server.
     */
    remoteEndpoint?: string;
  },

  server?: {
    /**
     * The port to listen on for SSE or MCP transport.
     */
    port?: number;

    /**
     * The host to bind the server to. Default is localhost. Use 0.0.0.0 to bind to all interfaces.
     */
    host?: string;
  },

  /**
   * List of enabled tool capabilities. Possible values:
   *   - 'core': Core browser automation features.
   *   - 'pdf': PDF generation and manipulation.
   *   - 'vision': Coordinate-based interactions.
   */
  capabilities?: ToolCapability[];

  /**
   * Whether to save the Playwright session into the output directory.
   */
  saveSession?: boolean;

  /**
   * Whether to include the browser session id in tool responses and stderr logs.
   */
  logSessionId?: boolean;

  /**
   * Whether to save the Playwright trace of the session into the output directory.
   */
  saveTrace?: boolean;

  /**
   * The directory to save output files.
   */
  outputDir?: string;

  network?: {
    /**
     * List of origins to allow the browser to request. Default is to allow all. Origins matching both `allowedOrigins` and `blockedOrigins` will be blocked.
     */
    allowedOrigins?: string[];

    /**
     * List of origins to block the browser to request. Origins matching both `allowedOrigins` and `blockedOrigins` will be blocked.
     */
    blockedOrigins?: string[];

    /**
     * Enable network request/response logging to disk.
     */
    logRequests?: boolean;

    /**
     * Delay network logging until the first successful `browser_navigate` call.
     * Requests captured before that business navigation window are discarded.
     */
    logRequestsFromFirstNavigation?: boolean;

    /**
     * Custom directory for network logs. Defaults to outputDir/network/
     */
    logDir?: string;

    /**
     * Maximum response body size to log (in bytes). Default is 100KB (102400 bytes).
     * Responses larger than this will be truncated.
     */
    maxBodySize?: number;

    /**
     * List of headers to redact for security. Default includes: authorization, cookie, set-cookie, x-api-key, x-auth-token
     */
    sensitiveHeaders?: string[];

    /**
     * Omit request body from logs. Default is false.
     */
    omitRequestBody?: boolean;

    /**
     * Omit response body from logs. Default is false.
     */
    omitResponseBody?: boolean;

    /**
     * Response MIME types whose body should not be stored. Matching is done against the
     * normalized MIME type without charset parameters, for example `text/javascript`.
     * Metadata such as headers, status, timing, and bodySize are still preserved.
     */
    omitResponseBodyMimeTypes?: string[];
  };

  /**
   * Whether to send image responses to the client. Can be "allow", "omit", or "auto". Defaults to "auto", which sends images if the client can display them.
   */
  imageResponses?: 'allow' | 'omit';

  /**
   * Redis connection URL for session and network log output.
   * Can also be set via the REDIS_URL environment variable.
   * Defaults to redis://localhost:6379.
   */
  redisUrl?: string;

  /**
   * Key prefix for Redis session data.
   * Can also be set via the REDIS_SESSION_PREFIX environment variable.
   * Defaults to "browser".
   */
  redisSessionPrefix?: string;
};

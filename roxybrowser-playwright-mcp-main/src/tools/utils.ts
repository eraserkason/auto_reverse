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

// @ts-ignore
import { asLocator } from 'playwright-core/lib/utils';

import type * as playwright from 'playwright';
import type { Tab } from '../tab.js';

const ACTION_COMPLETION_TIMEOUT_MS = 5000;
const ACTION_POST_COMPLETION_SETTLE_MS = 250;
const STRIPE_PRIVATE_FRAME_SELECTOR_PATTERN = /iframe\[name="__privateStripeFrame\d+"\]/g;
const STRIPE_EXPIRY_TEXTBOX_LOCATOR_PATTERN = /getByRole\('textbox', \{ name: '(?:Expiration date MM \/ YY|Expiration \(MM\/YY\) MM \/ YY)' \}\)/g;
const STRIPE_EXPIRY_TEXTBOX_LOCATOR = `getByRole('textbox', { name: /^Expiration.*MM \\/ YY$/i })`;

// Playwright locators are most resilient when they stay user-facing.
// Stripe rotates secure iframe names and slightly renames the expiry field
// after card entry, so strip the volatile frame suffix and allow the
// official expiry label variants to resolve at action time.
function stabilizeResolvedLocator(locatorCode: string): string {
  let stabilized = locatorCode.replace(STRIPE_PRIVATE_FRAME_SELECTOR_PATTERN, 'iframe[name^="__privateStripeFrame"][title="Secure payment input frame"]');
  if (stabilized.includes('__privateStripeFrame'))
    stabilized = stabilized.replace(STRIPE_EXPIRY_TEXTBOX_LOCATOR_PATTERN, STRIPE_EXPIRY_TEXTBOX_LOCATOR);
  return stabilized;
}

export async function waitForCompletion<R>(tab: Tab, callback: () => Promise<R>): Promise<R> {
  const requests = new Set<playwright.Request>();
  let frameNavigated = false;
  let observedActivity = false;
  let waitCallback: () => void = () => {};
  const waitBarrier = new Promise<void>(f => { waitCallback = f; });

  const requestListener = (request: playwright.Request) => {
    observedActivity = true;
    requests.add(request);
  };
  const requestSettledListener = (request: playwright.Request) => {
    requests.delete(request);
    if (!requests.size)
      waitCallback();
  };

  const frameNavigateListener = (frame: playwright.Frame) => {
    if (frame.parentFrame())
      return;
    observedActivity = true;
    frameNavigated = true;
    dispose();
    clearTimeout(timeout);
    void tab.waitForLoadState('load').then(waitCallback);
  };

  const onTimeout = () => {
    dispose();
    waitCallback();
  };

  tab.page.on('request', requestListener);
  tab.page.on('requestfinished', requestSettledListener);
  tab.page.on('requestfailed', requestSettledListener);
  tab.page.on('framenavigated', frameNavigateListener);
  const timeout = setTimeout(onTimeout, ACTION_COMPLETION_TIMEOUT_MS);

  const dispose = () => {
    tab.page.off('request', requestListener);
    tab.page.off('requestfinished', requestSettledListener);
    tab.page.off('requestfailed', requestSettledListener);
    tab.page.off('framenavigated', frameNavigateListener);
    clearTimeout(timeout);
  };

  try {
    const result = await callback();
    if (!requests.size && !frameNavigated)
      waitCallback();
    await waitBarrier;
    if (observedActivity)
      await tab.waitForTimeout(ACTION_POST_COMPLETION_SETTLE_MS);
    return result;
  } finally {
    dispose();
  }
}

export async function generateLocator(locator: playwright.Locator): Promise<string> {
  try {
    const { resolvedSelector } = await (locator as any)._resolveSelector();
    return stabilizeResolvedLocator(asLocator('javascript', resolvedSelector));
  } catch (e) {
    throw new Error('Ref not found, likely because element was removed. Use browser_snapshot to see what elements are currently on the page.');
  }
}

export function materializeLocator(page: playwright.Page, locatorCode: string): playwright.Locator {
  // `locatorCode` is generated from Playwright's own resolved selector string,
  // so re-evaluating it against `page` gives us a locator that is not tied to
  // the original aria-ref snapshot selector.
  const stabilizedLocatorCode = stabilizeResolvedLocator(locatorCode);
  return new Function('page', `return page.${stabilizedLocatorCode};`)(page) as playwright.Locator;
}

export async function callOnPageNoTrace<T>(page: playwright.Page, callback: (page: playwright.Page) => Promise<T>): Promise<T> {
  return await (page as any)._wrapApiCall(() => callback(page), { internal: true });
}

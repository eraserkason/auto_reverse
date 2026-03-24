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

import { z } from 'zod';

import { defineTabTool } from './tool.js';
import { elementSchemaBase } from './snapshot.js';
import { generateLocator, materializeLocator } from './utils.js';
import * as javascript from '../utils/codegen.js';

import type * as playwright from 'playwright';

const MASKED_INPUT_FALLBACK_DELAY_MS = 85;
const LOCATOR_VISIBILITY_TIMEOUT_MS = 60000;

function normalizeEditableValue(value: string): string {
  return value.replace(/\r\n/g, '\n');
}

function compactEditableValue(value: string): string {
  return normalizeEditableValue(value).replace(/\s+/g, '');
}

function editableValuesMatch(actual: string | undefined, expected: string): boolean {
  if (actual === undefined)
    return false;

  const normalizedActual = normalizeEditableValue(actual);
  const normalizedExpected = normalizeEditableValue(expected);
  return normalizedActual === normalizedExpected || compactEditableValue(normalizedActual) === compactEditableValue(normalizedExpected);
}

type EditableValueProbe = {
  value: string | undefined;
  readOnly: boolean;
};

async function probeEditableValue(locator: playwright.Locator): Promise<EditableValueProbe | undefined> {
  try {
    return await locator.evaluate(element => {
      const candidate = element as Element & {
        value?: unknown,
        inputMode?: unknown,
        placeholder?: unknown,
        autocomplete?: unknown,
        readOnly?: unknown,
      };
      const baseValue = (() => {
        if (element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement || element instanceof HTMLSelectElement)
          return element.value;
        if (element instanceof HTMLElement && element.isContentEditable)
          return element.innerText;
        if (typeof candidate.value === 'string')
          return candidate.value;
        return element.textContent ?? '';
      })();
      return {
        value: typeof baseValue === 'string' ? baseValue : undefined,
        readOnly: Boolean(candidate.readOnly),
      } satisfies EditableValueProbe;
    });
  } catch {
    return undefined;
  }
}

async function readEditableValue(locator: playwright.Locator): Promise<string | undefined> {
  return (await probeEditableValue(locator))?.value;
}

async function prepareEditableLocator(locator: playwright.Locator) {
  await locator.waitFor({ state: 'visible', timeout: LOCATOR_VISIBILITY_TIMEOUT_MS });
  try {
    await locator.scrollIntoViewIfNeeded();
  } catch {
  }
  await locator.focus();
}

async function rewriteThroughKeyboard(locator: playwright.Locator, text: string) {
  await prepareEditableLocator(locator);
  await locator.page().keyboard.press('ControlOrMeta+A');
  await locator.page().keyboard.press('Backspace');
  await locator.page().keyboard.type(text, { delay: MASKED_INPUT_FALLBACK_DELAY_MS });
}

async function typeIntoLocator(locator: playwright.Locator, text: string, options?: {
  slowly?: boolean,
  elementDescription?: string,
}) {
  await prepareEditableLocator(locator);
  if (options?.slowly)
    await locator.pressSequentially(text);
  else
    await locator.fill(text);

  let valueProbe = await probeEditableValue(locator);
  if (editableValuesMatch(valueProbe?.value, text))
    return;

  if (options?.slowly) {
    await rewriteThroughKeyboard(locator, text);
    valueProbe = await probeEditableValue(locator);
    if (editableValuesMatch(valueProbe?.value, text))
      return;
    if (valueProbe?.value === undefined)
      return;
  }

  if (!options?.slowly) {
    try {
      await locator.fill('');
    } catch {
    }
    await prepareEditableLocator(locator);
    await locator.pressSequentially(text);
    valueProbe = await probeEditableValue(locator);
    if (editableValuesMatch(valueProbe?.value, text))
      return;
  }

  const actualValue = valueProbe?.value;
  const target = options?.elementDescription || 'element';
  throw new Error(`Typed value did not settle on ${target}. Expected ${JSON.stringify(text)}, got ${JSON.stringify(actualValue)}.`);
}

async function prepareSelectLocator(locator: playwright.Locator) {
  await locator.waitFor({ state: 'visible', timeout: LOCATOR_VISIBILITY_TIMEOUT_MS });
  try {
    await locator.scrollIntoViewIfNeeded();
  } catch {
  }
}

const pressKey = defineTabTool({
  capability: 'core',

  schema: {
    name: 'browser_press_key',
    title: 'Press a key',
    description: 'Press a key on the keyboard',
    inputSchema: z.object({
      key: z.string().describe('Name of the key to press or a character to generate, such as `ArrowLeft` or `a`'),
    }),
    type: 'destructive',
  },

  handle: async (tab, params, response) => {
    response.setIncludeSnapshot();
    response.addCode(`// Press ${params.key}`);
    response.addCode(`await page.keyboard.press('${params.key}');`);

    await tab.waitForCompletion(async () => {
      await tab.page.keyboard.press(params.key);
    });
  },
});

const typeSchema = elementSchemaBase.extend({
  text: z.string().describe('Text to type into the element'),
  submit: z.boolean().optional().describe('Whether to submit entered text (press Enter after)'),
  slowly: z.boolean().optional().describe('Whether to type one character at a time. Useful for triggering key handlers in the page. By default entire text is filled in at once.'),
}).superRefine((value, ctx: z.RefinementCtx) => {
  if (!value.ref && !value.selector) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: 'Either ref or selector is required',
      path: ['ref'],
    });
  }
});

const fillFormFieldSchema = elementSchemaBase.extend({
  value: z.string().optional().describe('Text value to type into the field'),
  values: z.array(z.string()).min(1).optional().describe('Dropdown option values to select when the target is a select element'),
  slowly: z.boolean().optional().describe('Whether to type text one character at a time for this field'),
}).superRefine((value, ctx: z.RefinementCtx) => {
  if (!value.ref && !value.selector) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: 'Either ref or selector is required',
      path: ['ref'],
    });
  }
  const variantCount = Number(value.value !== undefined) + Number(value.values !== undefined);
  if (variantCount !== 1) {
    ctx.addIssue({
      code: z.ZodIssueCode.custom,
      message: 'Each field must provide exactly one of "value" or "values"',
      path: ['value'],
    });
  }
});

const fillFormSchema = z.object({
  fields: z.array(fillFormFieldSchema).min(1).describe('Form fields to fill or select in sequence'),
});

const type = defineTabTool({
  capability: 'core',
  schema: {
    name: 'browser_type',
    title: 'Type text',
    description: 'Type text into editable element',
    inputSchema: typeSchema,
    type: 'destructive',
  },

  handle: async (tab, params, response) => {
    response.setIncludeSnapshot();
    const locator = await tab.refLocator(params);
    const locatorExpression = await generateLocator(locator);
    const locatorCode = `page.${locatorExpression}`;
    const executionLocator = materializeLocator(tab.page, locatorExpression).describe(params.element);

    if (params.slowly)
      response.addCode(`await ${locatorCode}.pressSequentially(${javascript.quote(params.text)});`);
    else
      response.addCode(`await ${locatorCode}.fill(${javascript.quote(params.text)});`);

    if (params.submit)
      response.addCode(`await ${locatorCode}.press('Enter');`);

    await tab.waitForCompletion(async () => {
      await typeIntoLocator(executionLocator, params.text, {
        slowly: params.slowly,
        elementDescription: params.element,
      });

      if (params.submit)
        await executionLocator.press('Enter');
    });
  },
});

const fillForm = defineTabTool({
  capability: 'core',
  schema: {
    name: 'browser_fill_form',
    title: 'Fill form',
    description: 'Fill multiple form fields',
    inputSchema: fillFormSchema,
    type: 'destructive',
  },

  handle: async (tab, params, response) => {
    response.setIncludeSnapshot();

    const fields = await Promise.all(params.fields.map(async field => {
      const locator = await tab.refLocator(field);
      const locatorExpression = await generateLocator(locator);
      return {
        field,
        locatorCode: `page.${locatorExpression}`,
        executionLocator: materializeLocator(tab.page, locatorExpression).describe(field.element),
      };
    }));

    for (const entry of fields) {
      if (entry.field.values)
        response.addCode(`await ${entry.locatorCode}.selectOption(${javascript.formatObject(entry.field.values)});`);
      else if (entry.field.slowly)
        response.addCode(`await ${entry.locatorCode}.pressSequentially(${javascript.quote(entry.field.value!)});`);
      else
        response.addCode(`await ${entry.locatorCode}.fill(${javascript.quote(entry.field.value!)});`);
    }

    await tab.waitForCompletion(async () => {
      for (const entry of fields) {
        if (entry.field.values) {
          await prepareSelectLocator(entry.executionLocator);
          await entry.executionLocator.selectOption(entry.field.values);
          continue;
        }

        await typeIntoLocator(entry.executionLocator, entry.field.value!, {
          slowly: entry.field.slowly,
          elementDescription: entry.field.element,
        });
      }
    });
  },
});

export default [
  pressKey,
  type,
  fillForm,
];

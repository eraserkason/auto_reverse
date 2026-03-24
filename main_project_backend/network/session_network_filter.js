#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const IMAGE_EXTENSIONS = new Set(['png', 'jpg', 'jpeg', 'gif', 'svg', 'webp', 'ico', 'bmp', 'avif']);
const STYLE_EXTENSIONS = new Set(['css']);
const FONT_EXTENSIONS = new Set(['woff', 'woff2', 'ttf', 'otf', 'eot']);
const MEDIA_EXTENSIONS = new Set(['mp4', 'mp3', 'ts', 'm3u8', 'webm', 'wav', 'ogg', 'mov', 'm4a']);
const JS_EXTENSIONS = new Set(['js', 'mjs', 'cjs']);

const IMAGE_MIME_PREFIXES = ['image/'];
const STYLE_MIME_PREFIXES = ['text/css'];
const FONT_MIME_KEYWORDS = ['font/', 'woff', 'ttf', 'otf', 'eot'];
const MEDIA_MIME_PREFIXES = ['audio/', 'video/'];
const MEDIA_MIME_KEYWORDS = ['mpegurl', 'mp2t'];
const JS_MIME_KEYWORDS = ['javascript', 'ecmascript'];
const COMMON_MULTI_LABEL_PUBLIC_SUFFIXES = new Set([
  'co.uk',
  'org.uk',
  'gov.uk',
  'ac.uk',
  'com.au',
  'net.au',
  'org.au',
  'edu.au',
  'co.jp',
  'or.jp',
  'ne.jp',
  'go.jp',
  'com.cn',
  'net.cn',
  'org.cn',
  'gov.cn',
  'com.hk',
  'net.hk',
  'org.hk',
  'com.sg',
  'net.sg',
  'org.sg',
  'com.my',
  'net.my',
  'org.my',
  'co.nz',
  'org.nz',
  'govt.nz',
  'co.kr',
  'or.kr',
  'go.kr',
]);

const KNOWN_JS_RULES = [
  {
    reason: 'jquery_js',
    test: ctx => (
      ctx.path.includes('/wp-includes/js/jquery/')
      || /(^|[\/._-])jquery([\/._-]|$)/.test(ctx.basename)
      || ctx.basename === 'jquery.min.js'
      || ctx.basename === 'jquery-migrate.min.js'
    ),
  },
  {
    reason: 'wordpress_core_js',
    test: ctx => (
      ctx.path.includes('/wp-includes/js/dist/')
      || ctx.path.includes('/wp-includes/js/tinymce/')
      || ctx.path.includes('/wp-includes/js/mediaelement/')
    ),
  },
  {
    reason: 'analytics_js',
    test: ctx => (
      ctx.host.endsWith('googletagmanager.com')
      || ctx.host.endsWith('google-analytics.com')
      || ctx.lowerUrl.includes('/gtag/js')
    ),
  },
  {
    reason: 'stripe_js',
    test: ctx => (
      ctx.host === 'js.stripe.com'
      || ctx.host.endsWith('.stripe.com')
      || ctx.host.endsWith('.stripe.network')
    ),
  },
  {
    reason: 'plaid_js',
    test: ctx => ctx.host === 'cdn.plaid.com',
  },
  {
    reason: 'quill_js',
    test: ctx => (
      ctx.host === 'cdn.quilljs.com'
      || (ctx.host === 'cdn.jsdelivr.net' && ctx.lowerUrl.includes('quill'))
    ),
  },
  {
    reason: 'accessibility_js',
    test: ctx => (
      ctx.host === 'acsbapp.com'
      || ctx.host.endsWith('.acsbapp.com')
      || ctx.lowerUrl.includes('accessibe')
      || ctx.lowerUrl.includes('acsbapp')
    ),
  },
  {
    reason: 'doublethedonation_js',
    test: ctx => (
      ctx.host.endsWith('doublethedonation.com')
      || ctx.lowerUrl.includes('ddplugin')
    ),
  },
  {
    reason: 'popup_plugin_js',
    test: ctx => (
      ctx.lowerUrl.includes('popup-maker')
      || ctx.path.includes('/pum/')
      || ctx.basename === 'pum-site-scripts.js'
    ),
  },
  {
    reason: 'gdpr_plugin_js',
    test: ctx => (
      ctx.lowerUrl.includes('gdpr-cookie-compliance')
      || ctx.lowerUrl.includes('moove_gdpr')
    ),
  },
  {
    reason: 'lazyload_js',
    test: ctx => ctx.lowerUrl.includes('lazysizes'),
  },
  {
    reason: 'fontawesome_js',
    test: ctx => ctx.lowerUrl.includes('fontawesome'),
  },
  {
    reason: 'chariot_js',
    test: ctx => ctx.lowerUrl.includes('chariot-connect'),
  },
];

function printHelp() {
  const help = [
    '用法:',
    '  node session_network_filter.js <input-file> [--output <path>] [--removed-output <path>]',
    '    [--first-party <host1,host2>] [--keep-third-party-hosts <host1,host2>] [--drop-unknown-js]',
    '',
    '输入支持:',
    '  1. Debug Session Export Markdown',
    '  2. 纯 network entry JSON 数组',
    '',
    '默认行为:',
    '  - 输入 Markdown 时，默认输出过滤后的 network JSON',
    '  - 仅当 --output 指向 .md 时，才渲染缩减版 Markdown',
    '  - 过滤图片 / CSS / 字体 / 媒体资源',
    '  - 过滤明显公共库 / 官方脚本 / 插件脚本',
    '  - 保留第一方业务 JS',
    '  - 拿不准的第三方 JS 默认保留',
    '',
    '示例:',
    '  node session_network_filter.js debug-session.md',
    '  node session_network_filter.js session-network.json --first-party acttochange.org',
    '  node session_network_filter.js debug-session.md --keep-third-party-hosts acttochange.ddock.gives',
  ].join('\n');
  process.stdout.write(`${help}\n`);
}

function parseArgs(argv) {
  const args = {
    inputPath: '',
    outputPath: '',
    removedOutputPath: '',
    firstPartyHosts: [],
    keepThirdPartyHosts: [],
    keepUnknownJs: true,
  };

  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith('--') && !args.inputPath) {
      args.inputPath = token;
      continue;
    }

    switch (token) {
      case '--help':
      case '-h':
        args.help = true;
        break;
      case '--output':
        args.outputPath = argv[++i] || '';
        break;
      case '--removed-output':
        args.removedOutputPath = argv[++i] || '';
        break;
      case '--first-party':
        args.firstPartyHosts = splitCsv(argv[++i] || '');
        break;
      case '--keep-third-party-hosts':
        args.keepThirdPartyHosts = splitCsv(argv[++i] || '');
        break;
      case '--drop-unknown-js':
        args.keepUnknownJs = false;
        break;
      default:
        throw new Error(`未知参数: ${token}`);
    }
  }

  return args;
}

function splitCsv(value) {
  return value
    .split(',')
    .map(item => item.trim().toLowerCase())
    .filter(Boolean);
}

function readInputFile(inputPath) {
  const content = fs.readFileSync(inputPath, 'utf8');
  const sourceType = detectSourceType(inputPath, content);
  if (sourceType === 'markdown')
    return parseMarkdownInput(content);
  return parseJsonInput(content);
}

function detectSourceType(inputPath, content) {
  const ext = path.extname(inputPath).toLowerCase();
  if (ext === '.md')
    return 'markdown';
  if (ext === '.json')
    return 'json';
  if (content.includes('## Session Network'))
    return 'markdown';
  return 'json';
}

function parseMarkdownInput(content) {
  const networkSection = matchMarkdownJsonSection(content, 'Session Network');
  const pageUrl = extractMarkdownBulletValue(content, 'url');
  const sessionId = extractMarkdownBulletValue(content, 'session_id');
  const entries = normalizeEntries(JSON.parse(networkSection));
  return {
    sourceType: 'markdown',
    content,
    entries,
    pageUrl,
    sessionId,
  };
}

function parseJsonInput(content) {
  const parsed = JSON.parse(content);
  return {
    sourceType: 'json',
    content,
    entries: normalizeEntries(parsed),
    pageUrl: '',
    sessionId: '',
  };
}

function matchMarkdownJsonSection(content, title) {
  const pattern = buildMarkdownJsonSectionPattern(title);
  const match = content.match(pattern);
  if (!match)
    throw new Error(`未找到 Markdown 段落: ${title}`);
  return match[1];
}

function buildMarkdownJsonSectionPattern(title) {
  const escapedTitle = title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return new RegExp(`## ${escapedTitle}\\r?\\n\\r?\\n\`\`\`json\\r?\\n([\\s\\S]*?)\\r?\\n\`\`\``, 'm');
}

function extractMarkdownBulletValue(content, key) {
  const escapedKey = key.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const pattern = new RegExp(`^- ${escapedKey}: \`([^\\n\`]*)\`$`, 'm');
  const match = content.match(pattern);
  return match ? match[1].trim() : '';
}

function normalizeEntries(value) {
  if (Array.isArray(value))
    return value;
  if (value && Array.isArray(value.entries))
    return value.entries;
  throw new Error('输入内容不是 network entry 数组');
}

function inferFirstPartyHosts(input) {
  const inferredHosts = [];
  const pageUrl = input.pageUrl || '';
  if (!pageUrl)
    return inferredHosts;
  const parsed = safeParseUrl(pageUrl);
  if (!parsed)
    return inferredHosts;
  const host = parsed.hostname.toLowerCase();
  inferredHosts.push(host);
  const registrableDomain = inferRegistrableDomain(host);
  if (registrableDomain && registrableDomain !== host)
    inferredHosts.push(registrableDomain);
  return Array.from(new Set(inferredHosts));
}

function isIpv4Hostname(host) {
  if (!/^\d{1,3}(?:\.\d{1,3}){3}$/.test(host))
    return false;
  return host.split('.').every(part => {
    const value = Number(part);
    return Number.isInteger(value) && value >= 0 && value <= 255;
  });
}

function isIpv6Hostname(host) {
  return host.includes(':');
}

function inferRegistrableDomain(hostname) {
  const host = String(hostname || '').trim().toLowerCase();
  if (!host)
    return '';
  if (host === 'localhost' || isIpv4Hostname(host) || isIpv6Hostname(host))
    return host;

  const parts = host.split('.').filter(Boolean);
  if (parts.length <= 1)
    return host;

  const lastTwo = parts.slice(-2).join('.');
  if (COMMON_MULTI_LABEL_PUBLIC_SUFFIXES.has(lastTwo) && parts.length >= 3)
    return parts.slice(-3).join('.');
  return lastTwo;
}

function safeParseUrl(rawUrl) {
  try {
    return new URL(rawUrl);
  } catch {
    try {
      return new URL(rawUrl, 'http://local.invalid');
    } catch {
      return null;
    }
  }
}

function buildContext(entry) {
  const requestUrl = String(entry?.request?.url || '').trim();
  const parsedUrl = safeParseUrl(requestUrl);
  const pathname = parsedUrl ? (parsedUrl.pathname || '') : '';
  const basename = pathname ? pathname.split('/').pop() || '' : '';
  const extension = extractExtension(pathname);
  const mimeType = normalizeMimeType(entry?.response?.mimeType || entry?.response?.headers?.['content-type'] || '');

  return {
    entry,
    requestUrl,
    lowerUrl: requestUrl.toLowerCase(),
    host: parsedUrl ? parsedUrl.hostname.toLowerCase() : '',
    path: pathname.toLowerCase(),
    basename: basename.toLowerCase(),
    extension,
    mimeType,
  };
}

function extractExtension(pathname) {
  if (!pathname)
    return '';
  const base = pathname.split('/').pop() || '';
  const dotIndex = base.lastIndexOf('.');
  if (dotIndex === -1)
    return '';
  return base.slice(dotIndex + 1).toLowerCase();
}

function normalizeMimeType(mimeType) {
  return String(mimeType || '')
    .split(';', 1)[0]
    .trim()
    .toLowerCase();
}

function isJsLike(ctx) {
  if (JS_EXTENSIONS.has(ctx.extension))
    return true;
  return JS_MIME_KEYWORDS.some(keyword => ctx.mimeType.includes(keyword));
}

function matchesPrefix(value, prefixes) {
  return prefixes.some(prefix => value.startsWith(prefix));
}

function matchesKeyword(value, keywords) {
  return keywords.some(keyword => value.includes(keyword));
}

function hostMatches(host, candidates) {
  return candidates.some(candidate => host === candidate || host.endsWith(`.${candidate}`));
}

function classifyEntry(entry, options) {
  const ctx = buildContext(entry);

  if (!ctx.requestUrl) {
    return { keep: true, reason: 'missing_url' };
  }

  if (IMAGE_EXTENSIONS.has(ctx.extension) || matchesPrefix(ctx.mimeType, IMAGE_MIME_PREFIXES))
    return { keep: false, reason: 'image' };

  if (STYLE_EXTENSIONS.has(ctx.extension) || matchesPrefix(ctx.mimeType, STYLE_MIME_PREFIXES))
    return { keep: false, reason: 'stylesheet' };

  if (FONT_EXTENSIONS.has(ctx.extension) || matchesKeyword(ctx.mimeType, FONT_MIME_KEYWORDS))
    return { keep: false, reason: 'font' };

  if (
    MEDIA_EXTENSIONS.has(ctx.extension)
    || matchesPrefix(ctx.mimeType, MEDIA_MIME_PREFIXES)
    || matchesKeyword(ctx.mimeType, MEDIA_MIME_KEYWORDS)
  ) {
    return { keep: false, reason: 'media' };
  }

  if (!isJsLike(ctx))
    return { keep: true, reason: 'non_static_or_non_js' };

  if (hostMatches(ctx.host, options.keepThirdPartyHosts))
    return { keep: true, reason: 'explicit_keep_host' };

  for (const rule of KNOWN_JS_RULES) {
    if (rule.test(ctx))
      return { keep: false, reason: rule.reason };
  }

  if (hostMatches(ctx.host, options.firstPartyHosts))
    return { keep: true, reason: 'first_party_js' };

  if (options.keepUnknownJs)
    return { keep: true, reason: 'unknown_third_party_js_kept' };

  return { keep: false, reason: 'unknown_third_party_js' };
}

function filterEntries(entries, rawOptions = {}) {
  const options = {
    firstPartyHosts: Array.from(new Set((rawOptions.firstPartyHosts || []).map(item => item.toLowerCase()))),
    keepThirdPartyHosts: Array.from(new Set((rawOptions.keepThirdPartyHosts || []).map(item => item.toLowerCase()))),
    keepUnknownJs: rawOptions.keepUnknownJs !== false,
  };

  const kept = [];
  const removed = [];
  const removedByReason = {};
  const keptByReason = {};

  for (const entry of entries) {
    const result = classifyEntry(entry, options);
    if (result.keep) {
      kept.push(entry);
      keptByReason[result.reason] = (keptByReason[result.reason] || 0) + 1;
      continue;
    }
    removed.push({ reason: result.reason, entry });
    removedByReason[result.reason] = (removedByReason[result.reason] || 0) + 1;
  }

  return {
    kept,
    removed,
    stats: {
      total: entries.length,
      kept: kept.length,
      removed: removed.length,
      removedByReason,
      keptByReason,
      firstPartyHosts: options.firstPartyHosts,
      keepThirdPartyHosts: options.keepThirdPartyHosts,
      keepUnknownJs: options.keepUnknownJs,
    },
  };
}

function renderFilteredMarkdown(originalContent, keptEntries, stats) {
  const summary = {
    total: stats.total,
    kept: stats.kept,
    removed: stats.removed,
    removedByReason: stats.removedByReason,
    keptByReason: stats.keptByReason,
    firstPartyHosts: stats.firstPartyHosts,
    keepThirdPartyHosts: stats.keepThirdPartyHosts,
    keepUnknownJs: stats.keepUnknownJs,
    filteredAt: new Date().toISOString(),
  };

  let output = originalContent;
  output = output.replace(
    /^- network_count: `[^`\n]*`$/m,
    [
      `- network_count: \`${keptEntries.length}\``,
      `- original_network_count: \`${stats.total}\``,
      `- removed_network_count: \`${stats.removed}\``,
      `- filter_applied_at: \`${summary.filteredAt}\``,
    ].join('\n'),
  );

  const replacementSection = [
    '## Filter Summary',
    '',
    '```json',
    JSON.stringify(summary, null, 2),
    '```',
    '',
    '## Session Network',
    '',
    '```json',
    JSON.stringify(keptEntries, null, 2),
    '```',
    '',
  ].join('\n');

  return output.replace(buildMarkdownJsonSectionPattern('Session Network'), replacementSection.trimEnd());
}

function resolveDefaultOutputPath(inputPath) {
  const dir = path.dirname(inputPath);
  const base = path.basename(inputPath, path.extname(inputPath));
  return path.join(dir, `${base}.filtered.json`);
}

function resolveDefaultRemovedOutputPath(inputPath) {
  const dir = path.dirname(inputPath);
  const base = path.basename(inputPath, path.extname(inputPath));
  return path.join(dir, `${base}.removed.json`);
}

function writeJson(filePath, payload) {
  fs.writeFileSync(filePath, `${JSON.stringify(payload, null, 2)}\n`, 'utf8');
}

function main(argv = process.argv.slice(2)) {
  const args = parseArgs(argv);
  if (args.help || !args.inputPath) {
    printHelp();
    process.exit(args.help ? 0 : 1);
  }

  const input = readInputFile(args.inputPath);
  const inferredFirstPartyHosts = inferFirstPartyHosts(input);
  const firstPartyHosts = Array.from(new Set([...inferredFirstPartyHosts, ...args.firstPartyHosts]));

  const result = filterEntries(input.entries, {
    firstPartyHosts,
    keepThirdPartyHosts: args.keepThirdPartyHosts,
    keepUnknownJs: args.keepUnknownJs,
  });

  const outputPath = args.outputPath || resolveDefaultOutputPath(args.inputPath);
  const removedOutputPath = args.removedOutputPath || resolveDefaultRemovedOutputPath(args.inputPath);

  if (path.extname(outputPath).toLowerCase() === '.md') {
    const filteredMarkdown = renderFilteredMarkdown(input.content, result.kept, result.stats);
    fs.writeFileSync(outputPath, filteredMarkdown, 'utf8');
  } else {
    writeJson(outputPath, result.kept);
  }

  writeJson(removedOutputPath, result.removed);

  const summaryLines = [
    `输入类型: ${input.sourceType}`,
    `输入文件: ${path.resolve(args.inputPath)}`,
    `输出文件: ${path.resolve(outputPath)}`,
    `移除明细: ${path.resolve(removedOutputPath)}`,
    `第一方域名: ${result.stats.firstPartyHosts.join(', ') || '(未推断/未指定)'}`,
    `总条数: ${result.stats.total}`,
    `保留条数: ${result.stats.kept}`,
    `移除条数: ${result.stats.removed}`,
    `保留未知第三方 JS: ${result.stats.keepUnknownJs ? '是' : '否'}`,
    `移除原因统计: ${JSON.stringify(result.stats.removedByReason, null, 2)}`,
  ];
  process.stdout.write(`${summaryLines.join('\n')}\n`);
}

if (require.main === module) {
  try {
    main();
  } catch (error) {
    process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
    process.exit(1);
  }
}

module.exports = {
  classifyEntry,
  filterEntries,
  inferFirstPartyHosts,
  main,
  parseJsonInput,
  parseMarkdownInput,
  printHelp,
  readInputFile,
  renderFilteredMarkdown,
};

#!/usr/bin/env node
'use strict';

const filterModule = require('../network/session_network_filter.js');

if (require.main === module) {
  try {
    filterModule.main();
  } catch (error) {
    process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
    process.exit(1);
  }
}

module.exports = filterModule;

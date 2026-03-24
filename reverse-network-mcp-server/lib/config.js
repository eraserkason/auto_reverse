'use strict';

const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';
const REDIS_SESSION_PREFIX = process.env.REDIS_SESSION_PREFIX || 'browser';

module.exports = {
  REDIS_SESSION_PREFIX,
  REDIS_URL,
};

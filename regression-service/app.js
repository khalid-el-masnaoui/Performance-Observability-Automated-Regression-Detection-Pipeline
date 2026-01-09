const express = require("express");
const axios = require("axios");
const Redis = require("ioredis");

const app = express();
app.use(express.json());

// --------------------
// Config
// --------------------
const REDIS_HOST = process.env.REDIS_HOST || "redis";
const PROM_URL = process.env.PROM_URL || "http://prometheus:9090";
const SLACK_WEBHOOK = process.env.SLACK_WEBHOOK;
const REPORT_URL = (process.env.REPORT_URL || "http://report-service:5000");

const redis = new Redis({ host: REDIS_HOST });

const QUERIES = {
  p95: `
histogram_quantile(
  0.95,
  sum(rate(app_request_duration_seconds_bucket[2m])) by (le, route)
)`,

  p99: `
histogram_quantile(
  0.99,
  sum(rate(app_request_duration_seconds_bucket[2m])) by (le, route)
)`,

  avg: `
sum(rate(app_request_duration_seconds_sum[2m])) by (route)
/
sum(rate(app_request_duration_seconds_count[2m])) by (route)
`,

  error_rate: `
sum(rate(app_requests_total{status=~"5.."}[2m])) by (route)
/
sum(rate(app_requests_total[2m])) by (route)
`,

  throughput: `
sum(rate(app_request_duration_seconds_count[1m])) by (route)
`,

  max_latency: `
max_over_time(app_request_duration_seconds_sum[5m])
`
};

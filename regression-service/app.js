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

// --------------------
// Query Prometheus
// --------------------
async function runQuery(query) {

  try {

    const res = await axios.get(`${PROM_URL}/api/v1/query`, {
      params: { query }
    });

    return res.data?.data?.result || [];

  } catch (e) {

    return [];
  }
}

async function queryPrometheusP95(route) {
  const query = `
    histogram_quantile(0.95,
      sum(rate(app_request_duration_seconds_bucket{route="${route}"}[2m])) by (le)
    )
  `;
    
    const result = await runQuery(query);
    if (!result.length) return 0;

    return parseFloat(result[0].value[1]);
}



async function queryPrometheusMetrics(route) {

  const build = async (query) => {
    const result = await runQuery(query);

    for (const item of result) {

      if (item.metric.route !== route) continue;

      const value = parseFloat(item.value[1]);

      if (isNaN(value)) return 0;

      return Number(value.toFixed(4));
    }

    return 0;
  };

  return {
    p95: await build(QUERIES.p95),
    p99: await build(QUERIES.p99),
    avg: await build(QUERIES.avg),
    rps: await build(QUERIES.rps),
    error_rate: await build(QUERIES.error_rate),
    throughput: await build(QUERIES.throughput),
    max_latency: await build(QUERIES.max_latency),
  };
}

async function queryPrometheusMetricsOptimized() {

  const raw = {};

  for (const [name, query] of Object.entries(QUERIES)) {

    const result = await runQuery(query);

    raw[name] = result;
  }

  const final = {};

  for (const metricName in raw) {

    const series = raw[metricName];

    for (const item of series) {

      const route = item.metric.route;

      if (!route) continue;

      const value = parseFloat(item.value[1]);

      if (!final[route]) {
        final[route] = {};
      }

      final[route][metricName] = isNaN(value)
        ? 0
        : Number(value.toFixed(4));
    }
  }

  return final;
}

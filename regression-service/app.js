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


// --------------------
// Trigger SPX
// --------------------
async function triggerSPX(route) {
  await redis.setex(`spx:${route}`, 60, "1");
}

// --------------------
// Send Slack
// --------------------
async function sendSlack(route, current, baseline, increase, regression) {
  if (!SLACK_WEBHOOK) {
    console.log("No Slack webhook configured");
    return;
  }

  const payload = {
    attachments: [
      {
        color: regression ? "#ff0000" : "#36a64f",
        title: `🚨 Performance Alert: ${route}`,
        fields: [
          { title: "Current p95", value: `${current.toFixed(2)}s`, short: true },
          { title: "Baseline p95", value: `${baseline.toFixed(2)}s`, short: true },
          { title: "Increase", value: `${(increase * 100).toFixed(1)}%`, short: true },
          { title: "Regression", value: String(regression), short: true },
        ],
        footer: "Regression Service",
      },
    ],
  };

  try {
    await axios.post(SLACK_WEBHOOK, payload);
  } catch (err) {
    console.error("Slack error:", err.message);
  }
}

// --------------------
// Generate Baseline PDF report
// --------------------
async function generateBaselineReport(route, payload) {

    try {

        await axios.post(
            REPORT_URL+"/generate-baseline",
            {
                route,
                p95: payload.p95,
                p99: payload.p99,
                avg: payload.avg,
                error_rate: payload.error_rate,
                max_latency: payload.max_latency,
                throughput: payload.throughput
            }
        );

        console.log(`Baseline report generated for ${route}`);

    } catch (err) {

        console.error("Baseline report error:", err.message);
    }
}

// --------------------
// Generate Regression PDF report
// --------------------
async function generateReport(route, data) {
  try {
    await axios.post(REPORT_URL+"/generate", {
      [route]: data,
    });
  } catch (err) {
    console.error("Report error:", err.message);
  }
}

// --------------------
// Store baseline
// --------------------
app.post("/baseline", async (req, res) => {
    const { route, p95, p99, avg, error_rate, max_latency, throughput } = req.body;

    if (!route || !p95) {
        return res.status(400).json({ error: "route and p95 required" });
    }

    const payload = {
        p95,
        p99: p99 || 0,
        avg: avg || 0,
        error_rate: error_rate || 0,
        max_latency: max_latency || 0,
        throughput: throughput || 0,
        updated_at: Date.now(),
    };

    await redis.set(`baseline:${route}`, JSON.stringify(payload));
    
    await generateBaselineReport(route, payload);

    res.json({ status: "stored", route });
});

// --------------------
// Alert handler
// --------------------
app.post("/alert", async (req, res) => {
  //console.log("Received alert:", JSON.stringify(req.body, null, 2));
    
  const alerts = req.body.alerts || [];

  const results = [];

  for (const alert of alerts) {
    const route = alert.labels?.route;
    if (!route) continue;

    const baselineRaw = await redis.get(`baseline:${route}`);
    if (!baselineRaw) {
      console.log(`No baseline for ${route}`);
      continue;
    }

    const baseline = JSON.parse(baselineRaw);

    //const current = await queryPrometheusP95(route);
    //const currentMetrics = await queryPrometheusMetrics(route);
    const currentMetricsAll = await queryPrometheusMetricsOptimized();
      
    //console.log(`Current metrics for ${route}:`, currentMetricsAll);
      
    if (!currentMetricsAll[route]) continue;
      
    currentMetrics = currentMetricsAll[route];
      
    if (!baseline.p95) continue;

    const increase = (currentMetrics.p95 - baseline.p95) / baseline.p95;
    const regression = increase > 0.3;
   
    //console.log(`Route: ${route}, increase: ${increase.toFixed(2)}, Regression: ${regression}`);
    if(regression) {

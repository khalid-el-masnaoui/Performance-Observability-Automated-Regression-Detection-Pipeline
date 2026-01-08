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

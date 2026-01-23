# Performance Observability & Automated Regression Detection Pipeline

A containerized end-to-end (almost :upside_down_face:) **performance observability and automated regression detection system** for PHP applications.

This project integrates:

- ⚡ Nginx + PHP-FPM application layer
- 📊 Prometheus metrics collection
- 📈 Grafana dashboards
- 🔥 SPX PHP profiler with flamegraphs
- 🚨 Alertmanager for alert routing
- 🤖 Custom regression detection service (Node.js)
- 🧪 k6 load testing for automated performance validation
- 📄 PDF report generation for baselines & regressions (Python)

This project is intended as a practical demo of how to wire **PHP request metrics**, **alerting**,  **dynamic profiler activation**,  **automatic regression detection** and **historical trend analysis & tracking** together into a reproducible Docker-based performance observability & automated regression detection pipeline.


## Overview

This project is designed to detect performance regressions automatically by:

1. collecting request latency metrics from PHP routes,
2. comparing current performance against stored baselines,
3. triggering SPX profiling when a route slows down,
4. sending Slack alerts if configured,
5. generating PDF regression reports,

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

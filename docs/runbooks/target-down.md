# Runbook: PrometheusTargetDown
## Severity: Critical
### Diagnosis
1. Open Prometheus Targets: `http://localhost:9090/targets`
2. Inspect ServiceMonitor selector matching the target Service.

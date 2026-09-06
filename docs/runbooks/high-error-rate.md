# Runbook: HighErrorRate
## Severity: Critical
### Diagnosis
1. Check application logs: `kubectl logs -l app=backend -n devops-app --tail=100`
2. Inspect database connectivity and recent deployment status.
### Mitigation
- Rollback if caused by bad release: `kubectl rollout undo deployment/backend -n devops-app`

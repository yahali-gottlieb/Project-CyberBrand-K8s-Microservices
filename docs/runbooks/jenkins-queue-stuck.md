# Runbook: JenkinsQueueStuck
## Severity: Warning
### Diagnosis
1. Check Kubernetes agent provisioning logs in Jenkins controller.
2. Ensure cluster capacity allows dynamic pod creation in `jenkins` namespace.

# Runbook: ReplicasMismatch
## Severity: Warning
### Diagnosis
1. Check pending or crashing pods: `kubectl get pods -n devops-app`
2. Describe failing pod: `kubectl describe pod <pod-name> -n devops-app`

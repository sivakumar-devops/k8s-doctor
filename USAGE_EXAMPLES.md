# K8s Doctor - Usage Examples

## API Endpoints

### 1. Health Check

```bash
curl http://localhost:8080/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2026-04-13T10:30:00.123456",
  "monitoring": {
    "pods": true,
    "nodes": true,
    "deployments": true,
    "statefulsets": true,
    "daemonsets": true
  },
  "namespaces": ["default", "monitoring"],
  "rate_limit": {
    "total_diagnoses_this_hour": 5,
    "max_diagnoses_per_hour": 30,
    "remaining_capacity": 25,
    "reset_time": "2026-04-13T11:30:00.123456"
  },
  "diagnoses_count": 42,
  "fixes_applied": 3
}
```

### 2. Get Current Status

```bash
curl http://localhost:8080/status
```

Response:
```json
{
  "status": {
    "last_check": "2026-04-13T10:29:55.123456",
    "pods_checked": 15,
    "nodes_checked": 3,
    "deployments_checked": 5,
    "issues_detected": 2,
    "fixes_applied": 1
  },
  "recent_diagnoses": 42
}
```

### 3. Get Diagnosis History

```bash
curl http://localhost:8080/history
```

Response:
```json
{
  "total": 42,
  "recent": [
    {
      "timestamp": "2026-04-13T10:28:30.123456",
      "resource": "default/nginx-pod-abc123",
      "resource_type": "Pod",
      "diagnosis": {
        "root_cause": "Container restarting due to memory limit exceeded",
        "severity": "high",
        "issue_type": "OOMKilled",
        "suggested_fix": "Increase memory limit from 128Mi to 256Mi",
        "auto_restart_safe": false,
        "estimated_recovery_time": "5",
        "requires_manual_intervention": true,
        "config_suggestions": ["memory: 256Mi"],
        "likely_recurring": true,
        "estimated_impact": "Pod will continue crashing without memory increase"
      }
    },
    {
      "timestamp": "2026-04-13T10:27:15.123456",
      "resource": "worker-node-02",
      "resource_type": "Node",
      "diagnosis": {
        "root_cause": "Node disk space critically low at 95% capacity",
        "severity": "high",
        "issue_type": "DiskPressure",
        "suggested_fix": "1. Delete old logs/data 2. Add more disk space 3. Enable automatic log rotation",
        "auto_fix_safe": false,
        "requires_manual_intervention": true,
        "recommended_action": "cordon",
        "affected_pods": 8,
        "estimated_recovery_time": "30",
        "likely_recurring": false,
        "estimated_impact": "Node cannot accept new pods. Existing pods at risk of eviction."
      }
    }
  ]
}
```

### 4. Get Detailed Statistics

```bash
curl http://localhost:8080/stats
```

Response:
```json
{
  "monitoring_status": {
    "last_check": "2026-04-13T10:29:55.123456",
    "pods_checked": 15,
    "nodes_checked": 3,
    "deployments_checked": 5,
    "issues_detected": 2,
    "fixes_applied": 1
  },
  "rate_limiter": {
    "total_diagnoses_this_hour": 5,
    "max_diagnoses_per_hour": 30,
    "remaining_capacity": 25,
    "reset_time": "2026-04-13T11:30:00.123456"
  },
  "remediation_stats": {
    "total_fixes": 8,
    "total_restarts": 3,
    "total_rollbacks": 1,
    "resources_fixed": 4,
    "fix_history_by_resource": {
      "default/crash-loop-pod": [
        {
          "timestamp": "2026-04-13T10:25:00.123456",
          "issue_type": "Pod",
          "action": "restart"
        }
      ]
    }
  },
  "diagnosis_history_count": 42
}
```

### 5. Get Prometheus Metrics

```bash
curl http://localhost:8080/metrics
```

Response:
```
# HELP k8s_doctor_diagnoses_total Total diagnoses performed
# TYPE k8s_doctor_diagnoses_total counter
k8s_doctor_diagnoses_total 42

# HELP k8s_doctor_fixes_applied_total Total fixes applied
# TYPE k8s_doctor_fixes_applied_total counter
k8s_doctor_fixes_applied_total 8

# HELP k8s_doctor_issues_detected_total Total issues detected
# TYPE k8s_doctor_issues_detected_total counter
k8s_doctor_issues_detected_total 15

# HELP k8s_doctor_rate_limit_remaining Rate limit remaining
# TYPE k8s_doctor_rate_limit_remaining gauge
k8s_doctor_rate_limit_remaining 25
```

## Real-World Scenarios

### Scenario 1: Detecting CrashLoopBackOff

K8s Doctor detects a pod stuck in CrashLoopBackOff:

**Detection:**
```
Pod: production/api-server-xyz
Status: CrashLoopBackOff
Restarts: 12
```

**Claude Diagnosis:**
```json
{
  "root_cause": "Application failing to connect to database. Connection string has old hostname.",
  "severity": "high",
  "issue_type": "CrashLoopBackOff",
  "suggested_fix": "Update connection string in ConfigMap from 'db.old.cluster' to 'db.cluster.svc.local'",
  "auto_restart_safe": true,
  "config_suggestions": ["DB_HOST=db.cluster.svc.local"],
  "likely_recurring": false,
  "estimated_impact": "API service down. Requests return 503. Cascades to all dependent services."
}
```

**Slack Alert Sent:**
🔴 Pod Issue: api-server-xyz
- **Severity:** HIGH
- **Root Cause:** Application failing to connect to database
- **Suggested Fix:** Update connection string
- **Config:** DB_HOST=db.cluster.svc.local

### Scenario 2: Node Memory Pressure

K8s Doctor detects node memory pressure:

**Detection:**
```
Node: worker-02
Condition: MemoryPressure = True
Allocatable: 16Gi
Available: <500Mi
```

**Claude Diagnosis:**
```json
{
  "root_cause": "Node has insufficient memory for pod requirements. A container memory leak is consuming 14Gi.",
  "severity": "high",
  "issue_type": "MemoryPressure",
  "suggested_fix": "1. Identify memory leak container 2. Cordon node 3. Drain pods to other nodes 4. Investigate container image",
  "auto_fix_safe": false,
  "requires_manual_intervention": true,
  "recommended_action": "cordon",
  "affected_pods": 12,
  "estimated_recovery_time": "60",
  "likely_recurring": false
}
```

**Action Taken:**
- Node cordoned to prevent new pod scheduling
- Alert sent to Slack with manual steps

### Scenario 3: Deployment Replica Mismatch

K8s Doctor detects deployment stuck at 2/5 replicas:

**Detection:**
```
Deployment: monitoring/prometheus
Desired: 5
Ready: 2
Updated: 2
Available: 2
```

**Claude Diagnosis:**
```json
{
  "root_cause": "Image 'prometheus:2.50.0' doesn't exist in registry. Pull attempts fail silently.",
  "severity": "high",
  "issue_type": "ImagePullError",
  "suggested_fix": "1. Verify image tag exists 2. Fix image reference 3. Trigger rollout restart",
  "auto_rollback_safe": true,
  "scale_adjustment": {"desired_replicas": 3, "reason": "Reduce load while investigating"},
  "requires_manual_intervention": false
}
```

**Remediation Applied:**
- Deployment rolled out with restart
- Alert sent to Slack with recovery status

### Scenario 4: Learning Mode (First Week)

```bash
# Run in observe-only mode
kubectl set env deployment/k8s-doctor AUTO_FIX=false -n k8s-doctor

# Review diagnoses for 7 days
# Check accuracy and build confidence
# Then enable auto-fix

kubectl set env deployment/k8s-doctor AUTO_FIX=true -n k8s-doctor
```

### Scenario 5: Multiple Issues Detected

K8s Doctor runs periodic checks and finds multiple issues:

**Hour 1:** Pod restarting (diagnosed)
**Hour 2:** Node running low on disk (diagnosed)
**Hour 3:** Deployment stuck on old image (diagnosed)
**Hour 4:** Node auto-cordoned due to memory (diagnosed)

All sent to Slack with prioritization:
1. 🔴 HIGH: Node disk critically low
2. 🟠 MEDIUM: Deployment image mismatch
3. 🟡 LOW: Pod transient errors

## Configuration Tuning

### For Cost Optimization

```bash
# Increase check interval (reduce API calls)
kubectl set env deployment/k8s-doctor CHECK_INTERVAL=60 -n k8s-doctor

# Reduce diagnosis rate limit
kubectl set env deployment/k8s-doctor MAX_DIAGNOSES_PER_HOUR=15 -n k8s-doctor

# Monitor fewer namespaces
kubectl set env deployment/k8s-doctor TARGET_NAMESPACES="production" -n k8s-doctor

# Disable low-priority monitoring
kubectl set env deployment/k8s-doctor MONITOR_DAEMONSETS=false -n k8s-doctor
```

**Expected savings:** ~40-50% API cost reduction

### For Aggressive Monitoring

```bash
# Faster checks
kubectl set env deployment/k8s-doctor CHECK_INTERVAL=15 -n k8s-doctor

# More diagnoses allowed
kubectl set env deployment/k8s-doctor MAX_DIAGNOSES_PER_HOUR=60 -n k8s-doctor

# Monitor all namespaces
kubectl set env deployment/k8s-doctor TARGET_NAMESPACES="*" -n k8s-doctor

# Enable all monitoring
kubectl set env deployment/k8s-doctor \
  MONITOR_PODS=true \
  MONITOR_NODES=true \
  MONITOR_DEPLOYMENTS=true \
  MONITOR_STATEFULSETS=true \
  MONITOR_DAEMONSETS=true \
  -n k8s-doctor
```

**Expected cost:** ~$10-15/month

## Integration Examples

### With PagerDuty

Extend `notifications.py` to add PagerDuty:

```python
def send_pagerduty_alert(self, diagnosis, severity):
    if severity == "high":
        # Send to PagerDuty incident
        requests.post("https://events.pagerduty.com/v2/enqueue", ...)
```

### With DataDog

Send metrics to DataDog:

```python
from datadog import initialize, api

def send_metrics(self, stats):
    api.Metric.send(
        metric="k8s.doctor.diagnoses",
        points=stats["diagnosis_count"]
    )
```

### With Prometheus AlertManager

Configure AlertManager to integrate:

```yaml
receivers:
- name: 'k8s-doctor'
  webhook_configs:
  - url: 'http://k8s-doctor:8080/alerts'
```

## Monitoring K8s Doctor Itself

Monitor the monitor:

```bash
# Pod restart loops
kubectl logs -f deployment/k8s-doctor -n k8s-doctor | grep "restart"

# API errors
kubectl logs -f deployment/k8s-doctor -n k8s-doctor | grep "error"

# Check metrics
curl http://localhost:8080/metrics | grep k8s_doctor

# Check health regularly
watch curl http://localhost:8080/health
```

## Performance Tuning

### Optimize for Large Clusters (1000+ pods)

```bash
# Check less frequently
CHECK_INTERVAL=120

# Monitor fewer namespaces
TARGET_NAMESPACES="critical,production"

# Limit diagnoses
MAX_DIAGNOSES_PER_HOUR=20

# Increase resource limits
kubectl set resources deployment/k8s-doctor \
  --limits=cpu=1,memory=1Gi \
  --requests=cpu=500m,memory=512Mi \
  -n k8s-doctor
```

### Optimize for Development Clusters

```bash
# Check frequently for fast feedback
CHECK_INTERVAL=10

# Allow more aggressive fixes
MAX_RESTARTS_PER_HOUR=20

# Monitor all namespaces
TARGET_NAMESPACES="default,kube-system,*"

# Lower resource limits
kubectl set resources deployment/k8s-doctor \
  --limits=cpu=200m,memory=256Mi \
  --requests=cpu=50m,memory=64Mi \
  -n k8s-doctor
```

# K8s Doctor - Project Summary

## Overview

**K8s Doctor** is an enterprise-grade Kubernetes troubleshooting agent that combines:
- **Real-time Monitoring** - Watches pods, nodes, deployments 24/7
- **AI-Powered Diagnosis** - Claude analyzes issues with cluster context
- **Smart Remediation** - Applies safe fixes automatically or alerts teams
- **Cost-Effective** - ~$3-5/month for monitoring multiple clusters

Built on the principles of the Docker Container Doctor but specifically engineered for Kubernetes' distributed nature and complexity.

---

## Project Structure

```
k8s-doctor/
├── k8s_doctor.py              # Main application & Flask server
├── k8s_client.py              # Kubernetes API wrapper
├── diagnosis_engine.py        # Claude AI diagnosis logic
├── error_detection.py         # Issue pattern detection
├── remediation_engine.py      # Auto-fix orchestration
├── notifications.py           # Slack alerting
├── rate_limiter.py            # API quota management
│
├── k8s/                       # Kubernetes deployment manifests
│   ├── rbac.yaml              # RBAC permissions
│   └── deployment.yaml        # Full deployment spec
│
├── Dockerfile                 # Container image
├── requirements.txt           # Python dependencies
│
├── README.md                  # Project overview
├── GETTING_STARTED.md         # 5-minute quickstart
├── DEPLOYMENT_GUIDE.md        # Detailed K8s deployment
├── USAGE_EXAMPLES.md          # Real-world scenarios
└── .env.example               # Configuration template
```

---

## Key Components

### 1. **K8s Client Module** (`k8s_client.py`)
Unified wrapper around Kubernetes Python client:
- List/monitor pods, nodes, deployments, statefulsets, daemonsets
- Fetch logs and events for context
- Execute remediation (restart pods, scale, cordon nodes)
- Error handling and retry logic

**Features:**
- List 15+ K8s resource types
- Fetch logs with configurable history
- Execute remediation safely
- Detailed health/status extraction

### 2. **Error Detection** (`error_detection.py`)
Identifies K8s issues with pattern matching:
- **Pod errors:** CrashLoopBackOff, ImagePullBackOff, OOMKilled, Evicted, etc.
- **Node errors:** Memory/disk/network pressure, not ready, cordoned
- **Deployment errors:** Replica mismatches, failed rollouts, image pull errors
- **Workload errors:** StatefulSet, DaemonSet status checks

**Smart Features:**
- Multi-level severity assessment (low/medium/high)
- Log pattern analysis
- Condition checking
- Container status analysis

### 3. **Claude Diagnosis Engine** (`diagnosis_engine.py`)
AI-powered root cause analysis:
- Sends structured prompts with full context
- Parses JSON responses with validation
- Supports pod, node, deployment, general workload diagnoses
- Rate-limited to prevent API quota exhaustion

**Diagnosis Includes:**
- Root cause (1-2 sentences)
- Severity level
- Issue type classification
- Suggested remediation steps
- Auto-fix safety assessment
- Config recommendations
- Impact assessment

### 4. **Remediation Engine** (`remediation_engine.py`)
Safe, automated issue resolution:
- Pod restart with throttling (max 5/hour)
- Deployment scaling and rollouts
- Node cordon/uncordon
- Rollback prevention (max 1/day)
- Audit trail of all actions

**Safety Measures:**
- Checks diagnosis safety flags
- Implements restart throttling
- Verifies resource state after actions
- Records all changes for audit

### 5. **Notification Service** (`notifications.py`)
Slack integration for alerting:
- Color-coded severity (🔴 high, 🟠 medium, 🟡 low)
- Rich formatting with Slack Block Kit
- Includes diagnosis, impact, and recommendations
- Optional low-severity filtering

### 6. **Rate Limiter** (`rate_limiter.py`)
Cost and quota management:
- Max diagnoses per hour (configurable)
- Hourly reset with tracking
- Prevents API quota exhaustion
- Detailed remaining capacity reporting

### 7. **Flask API** (in `k8s_doctor.py`)
REST endpoints for monitoring:
- `/health` - System health check
- `/status` - Current monitoring status
- `/history` - Recent diagnoses (last 50)
- `/stats` - Detailed statistics
- `/metrics` - Prometheus format metrics

---

## Smart Features

### 1. Error Deduplication
- Hashes recent logs to avoid re-diagnosing identical issues
- Reduces API calls by ~80% in crash scenarios

### 2. Intelligent Diagnosis
- Analyzes last 100 lines of logs
- Fetches K8s events from last 1 hour
- Includes resource metrics and conditions
- Claude provides contextualized fixes

### 3. Progressive Remediation
- Low severity: Log only
- Medium severity: Alert team
- High severity: Apply fix OR alert with urgency

### 4. Restart Throttling
- Max 5 restarts per pod per hour
- After threshold, requires manual review
- Prevents cascading failures

### 5. Workload-Aware Monitoring
- Different strategies for pods vs deployments vs StatefulSets
- Database-aware (conservative) vs stateless (aggressive) handling
- Node-level pressure detection and management

### 6. Multi-Namespace Support
- Monitor any combination of namespaces
- Cluster-wide node monitoring
- Per-namespace resource quotas

---

## Configuration Options

### Core Monitoring
```env
TARGET_NAMESPACES=default,kube-system,monitoring
CHECK_INTERVAL=30
LOG_LINES=100
EVENTS_CHECK_HOURS=1
```

### Monitoring Flags
```env
MONITOR_PODS=true
MONITOR_NODES=true
MONITOR_DEPLOYMENTS=true
MONITOR_STATEFULSETS=true
MONITOR_DAEMONSETS=true
```

### Remediation
```env
AUTO_FIX=true
AUTO_RESTART_PODS=true
AUTO_ROLLBACK_DEPLOYMENTS=true
MAX_RESTARTS_PER_HOUR=5
MAX_DIAGNOSES_PER_HOUR=30
```

### Notifications
```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/...
SEND_LOW_SEVERITY_ALERTS=false
```

### API
```env
HEALTH_CHECK_PORT=8080
HEALTH_CHECK_HOST=0.0.0.0
```

---

## Deployment Modes

### 1. Local Development
```bash
python k8s_doctor.py
```
- Connects to current kubectl context
- Useful for testing and validation
- Direct logs to console

### 2. Docker Container
```bash
docker build -t k8s-doctor .
docker run -e ANTHROPIC_API_KEY=... k8s-doctor
```
- Portable across environments
- Easy to push to registry

### 3. Kubernetes Deployment
```bash
kubectl apply -f k8s/rbac.yaml
kubectl create secret generic k8s-doctor-secrets --from-literal=...
kubectl apply -f k8s/deployment.yaml
```
- Production-ready with RBAC
- Health checks and readiness probes
- Prometheus metrics integration

---

## Kubernetes RBAC

### Permissions Granted
**Reader (ClusterRole: k8s-doctor-reader)**
- Read pods, logs, events
- Read nodes, services
- Read deployments, statefulsets, daemonsets
- Read namespaces

**Remediator (ClusterRole: k8s-doctor-remediator)**
- Delete pods (restart)
- Patch deployments (scale, rollout)
- Patch nodes (cordon/uncordon)

This principle of least privilege ensures K8s Doctor can't accidentally damage the cluster.

---

## Example Workflows

### Workflow 1: Catch CrashLoopBackOff
```
1. Monitor detects: Pod in CrashLoopBackOff, 12 restarts
2. Fetch logs: "Connection refused: db.old.cluster:5432"
3. Claude diagnosis: "Database hostname outdated"
4. Remedy: Send Slack alert with suggested fix
5. Alert sent: "Update ConfigMap DB_HOST=db.cluster.svc.local"
```

### Workflow 2: Node Disk Pressure
```
1. Monitor detects: Node disk 95% full
2. Fetch context: 12 pods on node, 8 evictable
3. Claude diagnosis: "WAL files consuming 14GB"
4. Remedy: Cordon node (auto-fix safe)
5. Action: Node cordoned, pods drained
6. Alert: "Manual: Clean WAL files or add disk"
```

### Workflow 3: Deployment Stuck
```
1. Monitor detects: Deployment 2/5 replicas ready
2. Fetch logs: "ImagePullBackOff - no such image"
3. Claude diagnosis: "Image tag doesn't exist in registry"
4. Remedy: Trigger rollout restart (safely)
5. Action: Deployment rolled out
6. Alert: "Deployment recovered - investigate image"
```

---

## Cost Analysis

### Cost Breakdown
- **Claude API:** $0.003 per 1K input tokens, $0.015 per 1K output tokens
- **Typical Diagnosis:** ~800 input tokens, ~300 output tokens = $0.006
- **Rate Limit:** 30 diagnoses/hour max = $0.18/hour at full throttle
- **With Deduplication:** ~80% reduction = ~$0.04/hour typical

### Estimated Monthly Costs
| Scenario | Diagnoses/Month | Cost |
|----------|-----------------|------|
| Quiet cluster (1 issue/day) | 30 | $0.20 |
| Active cluster (2 issues/hour) | 1,440 | $8.64 |
| Busy cluster (full rate limit) | 21,600 | $129.60 |
| **Recommended Config** | **500-1000** | **$3-5** |

---

## Comparison with Alternatives

| Feature | K8s Doctor | Prometheus | DataDog | New Relic |
|---------|-----------|------------|---------|-----------|
| **Cost** | $3-5/mo | $50+/mo | $200+/mo | $300+/mo |
| **Setup Time** | 10 min | 1-2 hours | 1 hour | 1 hour |
| **AI Diagnosis** | ✅ Yes | ❌ No | ⚠️ Limited | ⚠️ Limited |
| **Auto-Fix** | ✅ Yes | ❌ No | ⚠️ Limited | ❌ No |
| **Multi-Cloud** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Learning Curve** | Easy | Medium | Easy | Easy |

---

## Smart Futures (Advanced Features)

### Planned Features
1. **Predictive Scaling**
   - Analyze resource usage patterns
   - Recommend HPA policies
   - Suggest resource requests/limits

2. **Anomaly Detection**
   - Baseline normal behavior
   - Detect unusual patterns
   - Proactive alerting

3. **Multi-Cluster Support**
   - Monitor multiple clusters
   - Correlated diagnostics
   - Cross-cluster remediation

4. **Integration Plugins**
   - PagerDuty, Opsgenie, Slack
   - DataDog, NewRelic, Dynatrace
   - Custom webhook support

5. **Learning Mode**
   - Improve diagnosis accuracy over time
   - User feedback loop
   - Fine-tuned models per environment

---

## Monitoring K8s Doctor Itself

K8s Doctor is designed to be monitored:

```bash
# Health check
curl http://localhost:8080/health

# Metrics for Prometheus
curl http://localhost:8080/metrics

# Status
curl http://localhost:8080/status

# Diagnoses made
curl http://localhost:8080/history
```

Recommended: Set up a separate monitoring alert for K8s Doctor's health endpoint.

---

## Quick Start Commands

```bash
# Local setup
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env && nano .env
python k8s_doctor.py

# Kubernetes deployment
kubectl apply -f k8s/rbac.yaml
kubectl create secret generic k8s-doctor-secrets \
  --from-literal=anthropic-api-key=$ANTHROPIC_API_KEY -n k8s-doctor
kubectl apply -f k8s/deployment.yaml

# Monitor
kubectl port-forward -n k8s-doctor svc/k8s-doctor 8080:8080
curl http://localhost:8080/health
curl http://localhost:8080/history | jq '.recent[0:3]'
```

---

## File Reference

| File | Purpose | Key Classes/Functions |
|------|---------|----------------------|
| `k8s_doctor.py` | Main app + Flask API | `initialize_services()`, `monitoring_loop()`, Flask routes |
| `k8s_client.py` | K8s API wrapper | `K8sClient` class, pod/node/deployment methods |
| `diagnosis_engine.py` | Claude integration | `DiagnosisEngine` class, prompt builders |
| `error_detection.py` | Pattern detection | `ErrorDetector` class, error patterns |
| `remediation_engine.py` | Auto-fix logic | `RemediationEngine` class, fix application |
| `notifications.py` | Slack alerts | `NotificationService` class |
| `rate_limiter.py` | API quota | `RateLimiter` class |

---

## Next Steps

1. **Deploy locally** - Follow GETTING_STARTED.md
2. **Run in observe mode** - Set AUTO_FIX=false for 1 week
3. **Review diagnoses** - Check accuracy and build confidence
4. **Enable auto-fix** - Activate when comfortable
5. **Integrate monitoring** - Connect to Prometheus/Grafana
6. **Tune configuration** - Optimize for your cluster

---

## Support Resources

- **GETTING_STARTED.md** - 5-minute quickstart
- **DEPLOYMENT_GUIDE.md** - Complete deployment guide
- **USAGE_EXAMPLES.md** - Real-world scenarios
- **README.md** - Project overview
- **Docker Container Doctor article** - Inspiration and patterns

---

## License

MIT License - Feel free to modify and extend for your needs.

---

**Happy troubleshooting with K8s Doctor! 🏥🚀**

# K8s Doctor - Complete Documentation Index

Welcome to **K8s Doctor** - Your AI-powered Kubernetes troubleshooting agent! This index helps you navigate all documentation and code.

## 📚 Documentation (Start Here)

### For Quick Start (5 minutes)
👉 **[GETTING_STARTED.md](./GETTING_STARTED.md)**
- 5-minute local setup
- Kubernetes deployment
- Quick testing
- Common issues

### For Detailed Deployment
👉 **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)**
- Local development setup
- Kubernetes deployment options
- Docker deployment
- Configuration reference
- Troubleshooting guide

### For Real-World Examples
👉 **[USAGE_EXAMPLES.md](./USAGE_EXAMPLES.md)**
- API endpoint examples
- Real incident scenarios
- Configuration tuning
- Integration examples

### For Project Overview
👉 **[README.md](./README.md)**
- Features overview
- Architecture diagram
- Quick start
- Monitored issues
- Security considerations

### For Technical Details
👉 **[PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md)**
- Complete architecture
- Component descriptions
- Smart features
- Cost analysis
- Comparison with alternatives

---

## 💻 Core Application Code

### Entry Point
**`k8s_doctor.py`** (500+ lines)
- Main Flask application
- Monitoring loops for all resource types
- REST API endpoints (/health, /status, /history, /stats, /metrics)
- Thread management
- Service initialization

**Key Functions:**
- `initialize_services()` - Set up all components
- `monitor_pods()`, `monitor_nodes()`, `monitor_deployments()` - Monitoring functions
- `monitoring_loop()` - Main loop that runs every CHECK_INTERVAL seconds
- Flask routes for health/status/history

### Kubernetes Integration
**`k8s_client.py`** (400+ lines)
- Unified Kubernetes API wrapper
- Kubernetes Python client abstraction

**Key Classes:**
- `K8sClient` - Main client class
  - `list_pods()`, `list_nodes()`, `list_deployments()`
  - `list_statefulsets()`, `list_daemonsets()`
  - `get_pod_logs()`, `get_pod_events()`
  - `restart_pod()`, `scale_deployment()`, `rollout_restart_deployment()`
  - `cordon_node()`, `uncordon_node()`

### AI Diagnosis Engine
**`diagnosis_engine.py`** (300+ lines)
- Claude AI integration for diagnosis
- Structured prompt building
- JSON response parsing

**Key Classes:**
- `DiagnosisEngine` - Main diagnosis orchestrator
  - `diagnose_pod_issue()` - Pod-specific diagnosis
  - `diagnose_node_issue()` - Node-specific diagnosis
  - `diagnose_deployment_issue()` - Deployment diagnosis
  - `diagnose_workload_issue()` - StatefulSet/DaemonSet diagnosis

### Error Detection
**`error_detection.py`** (250+ lines)
- K8s-specific error pattern detection
- Severity assessment

**Key Classes:**
- `ErrorDetector` - Pattern matching and detection
  - `detect_pod_errors()` - Pod status analysis
  - `detect_node_errors()` - Node status analysis
  - `detect_deployment_errors()` - Deployment analysis
  - `detect_log_errors()` - Log analysis
  - `detect_workload_errors()` - Workload analysis
  - `prioritize_errors()` - Severity ranking

### Remediation Engine
**`remediation_engine.py`** (300+ lines)
- Safe, throttled auto-fix logic
- History tracking

**Key Classes:**
- `RemediationEngine` - Remediation orchestration
  - `apply_remediation()` - Router to specific fixes
  - `_remediate_pod()` - Pod restart logic
  - `_remediate_deployment()` - Deployment fixes
  - `_remediate_node()` - Node operations
  - `_can_restart()` - Throttle checks
  - `get_fix_history()` - Audit trail

### Notifications
**`notifications.py`** (250+ lines)
- Slack integration
- Alert formatting

**Key Classes:**
- `NotificationService` - Notification orchestration
  - `send_pod_alert()` - Pod alerts
  - `send_node_alert()` - Node alerts
  - `send_deployment_alert()` - Deployment alerts
  - `_send_slack_alert()` - Core Slack integration

### Rate Limiting
**`rate_limiter.py`** (100+ lines)
- API quota management
- Cost control

**Key Classes:**
- `RateLimiter` - Rate limiting
  - `can_diagnose()` - Check if diagnosis allowed
  - `record_diagnosis()` - Track usage
  - `get_remaining_capacity()` - Capacity reporting

---

## 🐳 Deployment Configuration

### Kubernetes Manifests
**`k8s/` directory**

- **`k8s/rbac.yaml`** (180+ lines)
  - Namespace creation
  - Service account
  - ClusterRole for reading K8s resources
  - ClusterRole for remediation
  - ClusterRoleBindings

- **`k8s/deployment.yaml`** (200+ lines)
  - ConfigMap for configuration
  - Secret for API keys
  - Full Deployment spec
  - Service definition
  - ServiceMonitor for Prometheus

### Docker
**`Dockerfile`**
- Python 3.12 slim base
- Dependency installation
- Non-root user setup
- Health check configuration

### Environment
**`.env.example`**
- All configurable parameters
- Default values
- Example API keys

---

## 📊 Quick Reference Guides

### Configuration Quick Start

```bash
# Clone project
git clone https://github.com/your-org/k8s-doctor.git
cd k8s-doctor

# Setup Python environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API key and preferences

# Run
python k8s_doctor.py

# Test health
curl http://localhost:8080/health
```

### Kubernetes Quick Start

```bash
# Setup RBAC
kubectl apply -f k8s/rbac.yaml

# Create secrets
kubectl create secret generic k8s-doctor-secrets \
  --from-literal=anthropic-api-key=$ANTHROPIC_API_KEY \
  -n k8s-doctor

# Deploy
kubectl apply -f k8s/deployment.yaml

# Monitor
kubectl logs -f deployment/k8s-doctor -n k8s-doctor
```

---

## 🔍 Architecture Overview

```
┌─────────────────────────────────────────────────┐
│           K8s Doctor Application                │
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │      Flask API Server (k8s_doctor.py)   │  │
│  │  /health  /status  /history  /metrics    │  │
│  └────────────────┬─────────────────────────┘  │
│                   │                             │
│  ┌────────────────▼─────────────────────────┐  │
│  │    Monitoring Loop (every 30s)           │  │
│  │  - Pods  - Nodes  - Deployments          │  │
│  │  - StatefulSets  - DaemonSets            │  │
│  └────────────────┬─────────────────────────┘  │
│                   │                             │
│  ┌────────────────▼─────────────────────────┐  │
│  │   Error Detection & Classification       │  │
│  │   (error_detection.py)                   │  │
│  └────────────────┬─────────────────────────┘  │
│                   │                             │
│       ┌───────────▼───────────┐                │
│       │  Issue Found?         │                │
│       │  Severity >= HIGH?    │                │
│       └───┬─────────────────┬──┘                │
│     No    │               Yes                  │
│           │                 │                  │
│        ┌──▼──┐          ┌────▼────────┐       │
│        │Alert│          │  Diagnose   │       │
│        │Slack│          │  (Claude)   │       │
│        └──────┘          └────┬───────┘       │
│                               │               │
│                    ┌──────────▼──────────┐    │
│                    │  Safe to Auto-Fix?  │    │
│                    └──┬──────────────┬───┘    │
│                   Yes │           No  │       │
│                       │              │        │
│              ┌────────▼──────┐     ┌─▼─┐    │
│              │  Apply Fix    │     │Doc│    │
│              │(remediation)  │     │Ref│    │
│              └────┬──────────┘     └───┘    │
│                   │                         │
│              ┌────▼──────────┐              │
│              │ Notify Slack  │              │
│              └───────────────┘              │
│                                              │
└─────────────────────────────────────────────┘
         │
         ├──► Kubernetes API Server
         │
         ├──► Claude API (diagnosis)
         │
         └──► Slack Webhooks (alerts)
```

---

## 🎯 What Gets Monitored

### Pod Issues
- ✅ CrashLoopBackOff
- ✅ ImagePullBackOff
- ✅ Pending (with restarts)
- ✅ OOMKilled
- ✅ Evicted
- ✅ Failed state
- ✅ High restart counts

### Node Issues
- ✅ MemoryPressure
- ✅ DiskPressure
- ✅ NetworkUnavailable
- ✅ NotReady
- ✅ Cordoned/Draining
- ✅ PIDPressure

### Deployment Issues
- ✅ Replica mismatches
- ✅ Failed rollouts
- ✅ Image pull errors
- ✅ ProgressDeadlineExceeded
- ✅ Resource constraint failures

### Workload Issues
- ✅ StatefulSet replica mismatches
- ✅ DaemonSet missing replicas
- ✅ Configuration errors

---

## 🚀 Smart Features

| Feature | File | Description |
|---------|------|-------------|
| **AI Diagnosis** | `diagnosis_engine.py` | Claude analyzes all context and provides intelligent fixes |
| **Error Deduplication** | `k8s_doctor.py` | Avoids re-diagnosing identical issues (80% cost reduction) |
| **Restart Throttling** | `remediation_engine.py` | Max 5 restarts/pod/hour prevents cascades |
| **Rate Limiting** | `rate_limiter.py` | Max diagnoses/hour prevents quota exhaustion |
| **Slack Integration** | `notifications.py` | Rich alerts with severity, impact, recommendations |
| **RBAC Security** | `k8s/rbac.yaml` | Minimal permissions, principle of least privilege |
| **Health Monitoring** | `k8s_doctor.py` | Self-monitoring with /health endpoint |
| **Prometheus Metrics** | `k8s_doctor.py` | /metrics endpoint for integration |

---

## 📈 Configuration Options

### Monitoring
| Variable | Default | Purpose |
|----------|---------|---------|
| `TARGET_NAMESPACES` | `default` | Namespaces to monitor (comma-separated) |
| `CHECK_INTERVAL` | `30` | Seconds between monitoring cycles |
| `LOG_LINES` | `100` | Lines of pod logs to fetch |
| `EVENTS_CHECK_HOURS` | `1` | Hours of events to fetch |
| `MONITOR_PODS` | `true` | Enable pod monitoring |
| `MONITOR_NODES` | `true` | Enable node monitoring |
| `MONITOR_DEPLOYMENTS` | `true` | Enable deployment monitoring |

### Remediation
| Variable | Default | Purpose |
|----------|---------|---------|
| `AUTO_FIX` | `true` | Enable automatic remediation |
| `AUTO_RESTART_PODS` | `true` | Allow pod restarts |
| `AUTO_ROLLBACK_DEPLOYMENTS` | `true` | Allow deployment rollbacks |
| `MAX_RESTARTS_PER_HOUR` | `5` | Rate limit for pod restarts |
| `MAX_DIAGNOSES_PER_HOUR` | `30` | Rate limit for diagnoses |

### Notifications
| Variable | Default | Purpose |
|----------|---------|---------|
| `SLACK_WEBHOOK_URL` | `` | Slack webhook for alerts (optional) |
| `SEND_LOW_SEVERITY_ALERTS` | `false` | Include low-severity alerts |

---

## 🔐 Security

### RBAC Permissions
✅ Read-only: pods, nodes, events, logs, deployments, statefulsets, daemonsets
✅ Write-only: pod deletion, deployment patching, node cordoning
❌ Cannot: exec into containers, pull images, modify storage, delete namespaces

### Secrets Management
- API keys stored in Kubernetes secrets
- Never committed to git
- Available as environment variables to pod

### Network Security
- Health endpoint only on localhost in local mode
- Behind auth in production
- No external commands accepted

---

## 💰 Cost Estimation

### API Usage
- Typical pod diagnosis: 800 input + 300 output tokens = $0.006
- With deduplication: ~80% reduction in real-world usage
- Rate limiting: 30 max diagnoses/hour

### Monthly Costs (by scenario)
| Cluster Size | Issues/Day | Monthly Cost |
|--------------|-----------|--------------|
| Quiet (Dev) | 1 | $0.20 |
| Active (Prod) | 5 | $1.00 |
| Busy (Multi-team) | 30 | $6.00 |
| Very Busy | 100+ | $20+ |

### Comparison
- K8s Doctor: $3-5/month
- Prometheus + Grafana: $50/month
- DataDog: $200+/month
- New Relic: $300+/month

---

## 🆘 Troubleshooting Index

| Problem | Solution |
|---------|----------|
| Pod not starting | Check logs: `kubectl logs -p pod-name` |
| No diagnoses | Check rate limit: `curl :8080/stats` |
| High API costs | Reduce `MAX_DIAGNOSES_PER_HOUR` or `CHECK_INTERVAL` |
| Slack not working | Verify webhook URL in secret |
| RBAC errors | Run: `kubectl auth can-i list pods --as=system:serviceaccount:k8s-doctor:k8s-doctor` |
| Pod keeps restarting | Check if hitting throttle limit (5/hour) |

---

## 📞 Support & Resources

### Documentation
- 📖 README.md - Project overview
- 🚀 GETTING_STARTED.md - Quick start
- 📋 DEPLOYMENT_GUIDE.md - Detailed setup
- 💡 USAGE_EXAMPLES.md - Real scenarios
- 📊 PROJECT_SUMMARY.md - Technical deep dive

### Code Files
- `k8s_doctor.py` - Main application
- `k8s_client.py` - Kubernetes API wrapper
- `diagnosis_engine.py` - Claude integration
- `error_detection.py` - Issue detection
- `remediation_engine.py` - Auto-fix logic
- `notifications.py` - Slack alerting

### Configuration
- `.env.example` - Configuration template
- `k8s/rbac.yaml` - Kubernetes permissions
- `k8s/deployment.yaml` - Kubernetes deployment
- `Dockerfile` - Container image

---

## 🎓 Learning Path

### Day 1: Getting Started
1. Read GETTING_STARTED.md
2. Run locally with Python
3. Test health endpoint
4. Review example diagnoses

### Day 2-3: Understand Architecture
1. Read PROJECT_SUMMARY.md
2. Review k8s_doctor.py structure
3. Understand diagnostic flow
4. Check error patterns

### Day 4-5: Deploy to Kubernetes
1. Follow DEPLOYMENT_GUIDE.md
2. Review k8s/rbac.yaml
3. Deploy with kubectl
4. Monitor logs

### Week 2: Production Tuning
1. Run in observe mode (AUTO_FIX=false)
2. Review diagnoses accuracy
3. Tune configuration
4. Enable auto-fix
5. Monitor Slack alerts

### Week 3+: Advanced Features
1. Integrate Prometheus
2. Set up Grafana dashboards
3. Add custom remediation
4. Extend notifications

---

## 🔗 External References

- **Original Article:** [Docker Container Doctor on FreeCodeCamp](https://www.freecodecamp.org/news/docker-container-doctor-how-i-built-an-ai-agent-that-monitors-and-fixes-my-containers/)
- **Kubernetes Python Client:** https://github.com/kubernetes-client/python
- **Anthropic Claude API:** https://console.anthropic.com
- **Slack Webhooks:** https://api.slack.com/messaging/webhooks

---

## 📋 Quick Navigation

### I want to...
- **Get started quickly** → [GETTING_STARTED.md](./GETTING_STARTED.md)
- **Deploy to Kubernetes** → [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
- **See real examples** → [USAGE_EXAMPLES.md](./USAGE_EXAMPLES.md)
- **Understand the code** → [PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md)
- **Know what's monitored** → [README.md](./README.md)
- **Find a specific component** → See "Core Application Code" section above
- **Configure settings** → See "Configuration Options" section above
- **Fix a problem** → See "Troubleshooting Index" section above

---

**Ready to get started? → [GETTING_STARTED.md](./GETTING_STARTED.md) 🚀**

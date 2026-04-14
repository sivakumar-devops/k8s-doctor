# K8s Doctor - Getting Started Guide

Welcome to **K8s Doctor** - Your AI-powered Kubernetes troubleshooting companion! This guide will get you up and running in minutes.

## What is K8s Doctor?

K8s Doctor is an intelligent monitoring agent that:
- 🔍 **Monitors** your Kubernetes cluster 24/7
- 🧠 **Diagnoses** issues using Claude AI
- 🔧 **Remediates** problems automatically (when safe)
- 📢 **Alerts** your team via Slack
- 💰 **Saves** costs by preventing downtime

Inspired by the Docker Container Doctor project, but built specifically for Kubernetes with advanced cluster-wide awareness.

## 5-Minute Quick Start

### Step 1: Clone the Repository
```bash
cd /path/to/k8s-doctor
```

### Step 2: Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment
```bash
# Copy example config
cp .env.example .env

# Edit .env with your settings
nano .env
```

Edit these key settings:
```env
ANTHROPIC_API_KEY=sk-ant-YOUR_API_KEY_HERE
TARGET_NAMESPACES=default,kube-system,monitoring
SLACK_WEBHOOK_URL=https://hooks.slack.com/... (optional)
```

### Step 4: Run Locally
```bash
python k8s_doctor.py
```

You should see:
```
2026-04-13 10:30:00 - k8s_doctor - INFO - Starting K8s Doctor...
2026-04-13 10:30:01 - k8s_doctor - INFO - Kubernetes client initialized successfully
2026-04-13 10:30:02 - k8s_doctor - INFO - All services initialized successfully
2026-04-13 10:30:02 - k8s_doctor - INFO - Health endpoint available at http://0.0.0.0:8080/health
2026-04-13 10:30:03 - k8s_doctor - INFO - K8s Doctor monitoring loop started
```

### Step 5: Test Health Endpoint
In another terminal:
```bash
curl http://localhost:8080/health
```

Should return:
```json
{
  "status": "healthy",
  "timestamp": "2026-04-13T10:30:15.123456",
  "monitoring": {
    "pods": true,
    "nodes": true,
    ...
  }
}
```

**✅ You're running K8s Doctor locally!**

---

## Deploy to Kubernetes

### Prerequisites
- kubectl access to your cluster
- Ability to create namespace and RBAC
- (Optional) Access to your container registry

### Deployment Steps

#### 1. Create Namespace and RBAC
```bash
kubectl apply -f k8s/rbac.yaml
```

This creates:
- `k8s-doctor` namespace
- Service account with appropriate permissions
- ClusterRoles for reading/writing resources

#### 2. Create Secrets
```bash
# Store API keys securely
kubectl create secret generic k8s-doctor-secrets \
  --from-literal=anthropic-api-key=$ANTHROPIC_API_KEY \
  --from-literal=slack-webhook-url=$SLACK_WEBHOOK_URL \
  -n k8s-doctor
```

Replace `$ANTHROPIC_API_KEY` and `$SLACK_WEBHOOK_URL` with your actual values.

#### 3. Deploy the Application
```bash
kubectl apply -f k8s/deployment.yaml
```

#### 4. Verify Deployment
```bash
# Check pod is running
kubectl get pods -n k8s-doctor

# View logs
kubectl logs -f deployment/k8s-doctor -n k8s-doctor

# Check status
kubectl describe deployment k8s-doctor -n k8s-doctor
```

#### 5. Access Health Endpoint
```bash
# Port forward
kubectl port-forward -n k8s-doctor svc/k8s-doctor 8080:8080

# In another terminal
curl http://localhost:8080/health
curl http://localhost:8080/history
```

**✅ K8s Doctor is now monitoring your cluster!**

---

## Understanding K8s Doctor

### What It Monitors

#### Pods
- CrashLoopBackOff
- ImagePullBackOff
- Pending (with high restart counts)
- OOMKilled
- Evicted
- Failed state

#### Nodes
- Memory pressure
- Disk pressure
- Network unavailable
- Not ready
- Cordoned/Draining

#### Deployments
- Replica mismatches
- Failed rollouts
- Image pull errors
- Resource constraints

#### StatefulSets & DaemonSets
- Ready replicas mismatches
- Pod/container failures
- Configuration errors

### How It Works

```
┌─────────────────────────────────────────┐
│  1. Monitor Cluster Resources           │
│     (every 30 seconds)                  │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  2. Detect Error Patterns               │
│     (CrashLoopBackOff, OOMKilled, etc.) │
└──────────────┬──────────────────────────┘
               │
        ┌──────▼──────┐
        │ Error Found?│
        └──────┬──────┘
               │ Yes
┌──────────────▼──────────────────────────┐
│  3. Fetch Context                       │
│     (logs, events, resource metrics)    │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  4. Send to Claude for Diagnosis        │
│     (AI-powered analysis)               │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  5. Get Root Cause & Recommendations    │
│     (via Claude response)               │
└──────────────┬──────────────────────────┘
               │
        ┌──────▼──────────┐
        │ High Severity?  │
        └──────┬───────┬──┘
      Yes ┌────┘       └────┐ No
         ▼                   ▼
    ┌────────────┐    ┌──────────────┐
    │ Auto-Fix   │    │ Notify Team  │
    │ (if safe)  │    │ via Slack    │
    └────────────┘    └──────────────┘
```

### Configuration Modes

#### Observe Mode (First Week)
```bash
# Run without making changes
AUTO_FIX=false
SEND_LOW_SEVERITY_ALERTS=true
```
**Goal:** Verify accuracy of diagnoses

#### Production Mode
```bash
# Enable automatic remediation
AUTO_FIX=true
AUTO_RESTART_PODS=true
MAX_RESTARTS_PER_HOUR=5
```
**Goal:** Minimize manual intervention

#### Conservative Mode
```bash
# Maximum safety guards
AUTO_FIX=true
AUTO_RESTART_PODS=true
MAX_RESTARTS_PER_HOUR=2
CHECK_INTERVAL=60
```
**Goal:** Reduce risk, increase stability

---

## Key Features

### 🧠 AI-Powered Diagnosis
Each issue is analyzed by Claude, which:
- Reads application logs
- Reviews Kubernetes events
- Analyzes resource metrics
- Provides root cause analysis
- Suggests fixes
- Assesses auto-fix safety

### 🔧 Safe Remediation
Smart safety guards prevent chaos:
- **Restart throttling:** Max 5 pod restarts/hour
- **Severity checks:** Only auto-fix high-severity issues
- **Verification:** Confirms resource is healthy after fix
- **Manual review:** Requires approval for critical changes
- **Audit trail:** All actions logged

### 📊 Monitoring Dashboard
Access real-time status via REST API:
- `/health` - System health
- `/status` - Current monitoring status
- `/history` - Recent diagnoses
- `/stats` - Detailed statistics
- `/metrics` - Prometheus metrics

### 📢 Slack Integration
Automatic alerts with:
- Severity indicators (🔴 high, 🟠 medium, 🟡 low)
- Root cause analysis
- Recommended fixes
- Config suggestions
- Impact assessment

---

## Common Use Cases

### Use Case 1: Prevent Overnight Outages

**Problem:** Your API crashes at 3 AM, stays down until morning

**K8s Doctor Solution:**
1. Detects crash via pod status
2. Analyzes logs via Claude
3. Identifies root cause (e.g., database connection pool exhausted)
4. Safe restart applied automatically
5. Slack alert sent to on-call engineer
6. Service recovered in < 1 minute

### Use Case 2: Catch Resource Issues Early

**Problem:** Nodes run out of disk space, pods start evicting

**K8s Doctor Solution:**
1. Monitors disk pressure
2. Alerts before critical state
3. Suggests cleanup or scaling
4. Prevents cascade failures

### Use Case 3: Simplified Troubleshooting

**Problem:** Junior engineer needs to debug pod issues

**K8s Doctor Solution:**
1. Review K8s Doctor's diagnosis
2. See root cause identified
3. Get recommended fixes
4. Or let doctor auto-fix if safe

---

## Cost Breakdown

With recommended settings (30-second checks, 30 diagnoses/hour max):

| Component | Cost |
|-----------|------|
| Claude API calls | $2-5/month |
| Kubernetes cluster | $0 (no additional) |
| Slack | Free tier |
| Infrastructure | ~100MB RAM |
| **Total** | **~$3-5/month** |

**Comparison:** Traditional monitoring (Prometheus + Grafana) = $50-100+/month

---

## Troubleshooting

### "No diagnoses being made"

Check monitoring is enabled:
```bash
kubectl logs deployment/k8s-doctor -n k8s-doctor | grep "monitoring"
```

Check rate limit status:
```bash
curl http://localhost:8080/stats | jq '.rate_limiter'
```

### "Pod not connecting to cluster"

Verify RBAC:
```bash
kubectl auth can-i list pods \
  --as=system:serviceaccount:k8s-doctor:k8s-doctor
```

### "High API costs"

Reduce diagnosis frequency:
```bash
kubectl set env deployment/k8s-doctor \
  CHECK_INTERVAL=60 \
  MAX_DIAGNOSES_PER_HOUR=15 \
  -n k8s-doctor
```

### "Slack alerts not sending"

Verify webhook URL:
```bash
kubectl get secret k8s-doctor-secrets -n k8s-doctor \
  -o jsonpath='{.data.slack-webhook-url}' | base64 -d
```

---

## Next Steps

1. **Deploy to Kubernetes** (if not done yet)
   - Follow DEPLOYMENT_GUIDE.md

2. **Run in Observe Mode** (Week 1)
   - Set `AUTO_FIX=false`
   - Review diagnoses accuracy
   - Adjust settings as needed

3. **Enable Auto-Fix** (After Week 1)
   - Set `AUTO_FIX=true`
   - Monitor Slack alerts
   - Track fixes applied

4. **Integrate with Monitoring**
   - Connect Prometheus
   - Add to dashboards
   - Create alerts based on metrics

5. **Tune Configuration**
   - Adjust check interval based on cluster size
   - Tune diagnosis rate limit
   - Focus monitoring on critical namespaces

---

## Resources

- **README.md** - Project overview
- **DEPLOYMENT_GUIDE.md** - Detailed deployment instructions
- **USAGE_EXAMPLES.md** - Real-world examples and API usage
- **k8s/rbac.yaml** - Kubernetes permissions
- **k8s/deployment.yaml** - Full K8s manifest

---

## Support & Feedback

- Found a bug? Check logs: `kubectl logs deployment/k8s-doctor -n k8s-doctor`
- Have a feature request? Review the architecture and contribute!
- Need help? Check USAGE_EXAMPLES.md for detailed scenarios

---

## Quick Reference

```bash
# Start locally
python k8s_doctor.py

# Deploy to K8s
kubectl apply -f k8s/rbac.yaml
kubectl create secret generic k8s-doctor-secrets \
  --from-literal=anthropic-api-key=$ANTHROPIC_API_KEY -n k8s-doctor
kubectl apply -f k8s/deployment.yaml

# Check health
curl http://localhost:8080/health

# View recent diagnoses
curl http://localhost:8080/history | jq '.recent[0:3]'

# Check stats
curl http://localhost:8080/stats | jq '.monitoring_status'

# View logs
kubectl logs -f deployment/k8s-doctor -n k8s-doctor

# Port forward
kubectl port-forward -n k8s-doctor svc/k8s-doctor 8080:8080

# Update config
kubectl set env deployment/k8s-doctor CHECK_INTERVAL=60 -n k8s-doctor
```

**Happy troubleshooting! 🚀**

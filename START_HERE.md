# 🏥 K8s Doctor - START HERE

## Welcome! 👋

You now have a complete, production-ready **Kubernetes troubleshooting agent** powered by Claude AI. This document helps you take the first steps.

---

## ⚡ 5-Minute Quick Start

### Option A: Run Locally (Linux/Mac/WSL)

```bash
cd k8s-doctor

# Setup Python
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env: Add your ANTHROPIC_API_KEY

# Run
python k8s_doctor.py

# Test (in another terminal)
curl http://localhost:8080/health
```

### Option B: Deploy to Kubernetes

```bash
# Setup permissions
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

✅ Done! K8s Doctor is now monitoring your cluster.

---

## 📚 Documentation Map

| Document | Purpose | Read Time |
|----------|---------|-----------|
| **[INDEX.md](./INDEX.md)** | Complete documentation index | 5 min |
| **[GETTING_STARTED.md](./GETTING_STARTED.md)** | Detailed 5-10 minute setup | 10 min |
| **[README.md](./README.md)** | Project features & overview | 15 min |
| **[DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)** | Kubernetes deployment details | 20 min |
| **[USAGE_EXAMPLES.md](./USAGE_EXAMPLES.md)** | Real-world scenarios & API | 20 min |
| **[PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md)** | Technical architecture deep dive | 30 min |

**Recommended reading order:**
1. This file (2 min)
2. [GETTING_STARTED.md](./GETTING_STARTED.md) (5 min)
3. [README.md](./README.md) (15 min)
4. Try it out! (5 min)
5. [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) if deploying to K8s

---

## 🎯 What Does K8s Doctor Do?

### Monitors
- 🔍 **Pods:** CrashLoopBackOff, OOMKilled, ImagePullBackOff, etc.
- 🔍 **Nodes:** Memory pressure, disk pressure, not ready, cordoned
- 🔍 **Deployments:** Replica mismatches, failed rollouts, image errors
- 🔍 **StatefulSets & DaemonSets:** Replica and configuration issues

### Diagnoses
- 🧠 Uses Claude AI to analyze logs and events
- 🧠 Identifies root causes
- 🧠 Suggests specific fixes
- 🧠 Assesses if auto-fix is safe

### Fixes (When Safe)
- 🔧 Restarts failing pods
- 🔧 Triggers deployment rollouts
- 🔧 Cordons problematic nodes
- 🔧 All with safety guards and throttling

### Alerts
- 📢 Sends detailed Slack alerts
- 📢 Includes root cause, impact, and recommendations
- 📢 Color-coded by severity (🔴 high, 🟠 medium, 🟡 low)

### Saves You
- ⏰ Hours of manual debugging
- 💰 $50+ on monitoring tools (costs ~$3-5/month)
- 😴 Sleep (no more 3 AM pages!)

---

## 🔑 Key Features

| Feature | Benefit |
|---------|---------|
| **AI Diagnosis** | Understands your application like a human expert |
| **Safe Auto-Fix** | Fixes issues but never breaks things (with throttling) |
| **Smart Alerts** | Only alerts when really needed |
| **Cost Effective** | ~$3-5/month vs $50-300+ for alternatives |
| **Easy Setup** | Deploy in 5 minutes |
| **Kubernetes Native** | Built for K8s from the ground up |

---

## 🚀 Getting Started

### Step 1: Choose Your Path

**Are you on a Linux/Mac with kubectl access?**
- YES → Skip to Step 2 (Local Setup)
- NO → Skip to Step 3 (Kubernetes Deployment)

### Step 2: Local Setup (Recommended for First Time)

```bash
# 1. Navigate to project
cd k8s-doctor

# 2. Create Python environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure
cp .env.example .env
# Open .env and add:
# ANTHROPIC_API_KEY=sk-ant-YOUR_KEY_HERE

# 5. Run
python k8s_doctor.py

# 6. Test (new terminal)
curl http://localhost:8080/health
```

You should see a JSON response with status "healthy".

### Step 3: Deploy to Kubernetes

Once local testing is successful:

```bash
# 1. Apply permissions
kubectl apply -f k8s/rbac.yaml

# 2. Create secret with API key
kubectl create secret generic k8s-doctor-secrets \
  --from-literal=anthropic-api-key=sk-ant-YOUR_KEY_HERE \
  -n k8s-doctor

# 3. Deploy
kubectl apply -f k8s/deployment.yaml

# 4. Verify
kubectl get pods -n k8s-doctor
kubectl logs -f deployment/k8s-doctor -n k8s-doctor
```

### Step 4: First Week - Observe Mode

```bash
# Disable auto-fix to verify accuracy
kubectl set env deployment/k8s-doctor AUTO_FIX=false -n k8s-doctor

# Review diagnoses for a week
# Check accuracy and build confidence
# Then enable auto-fix
kubectl set env deployment/k8s-doctor AUTO_FIX=true -n k8s-doctor
```

### Step 5: Monitor and Tune

```bash
# Check health
curl http://localhost:8080/health

# View recent diagnoses
curl http://localhost:8080/history

# Get statistics
curl http://localhost:8080/stats
```

---

## 🔍 Testing It Works

### Local Testing

```bash
# 1. While K8s Doctor is running, trigger an issue
# Simulate a pod crash loop
kubectl run test-crash --image=busybox --restart=Never -- sh -c "exit 1"

# 2. Check K8s Doctor logs
kubectl logs -f deployment/k8s-doctor -n k8s-doctor

# 3. Should see diagnosis in 30-60 seconds
# Or check history endpoint
curl http://localhost:8080/history | jq '.recent[0]'
```

### Kubernetes Testing

```bash
# 1. Create test pod
kubectl run test-oom --image=busybox --requests='memory=10Mi' -- \
  sh -c 'python -c "import sys; sys.stdout.write(\"x\"*1000000000)"'

# 2. Watch K8s Doctor logs
kubectl logs -f deployment/k8s-doctor -n k8s-doctor

# 3. Should detect OOMKilled and diagnose within 30-60 seconds
```

---

## 📊 API Endpoints

Once running, access these endpoints:

```bash
# Health check
curl http://localhost:8080/health

# Current status
curl http://localhost:8080/status

# Recent diagnoses (last 50)
curl http://localhost:8080/history

# Detailed statistics
curl http://localhost:8080/stats

# Prometheus metrics
curl http://localhost:8080/metrics
```

---

## ⚙️ Configuration

### Essential Settings
```env
# Required
ANTHROPIC_API_KEY=sk-ant-YOUR_KEY

# Namespaces to monitor
TARGET_NAMESPACES=default,kube-system

# Check frequency (seconds)
CHECK_INTERVAL=30

# Maximum diagnoses per hour (cost control)
MAX_DIAGNOSES_PER_HOUR=30

# Optional: Slack alerts
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Safety Settings
```env
# Enable/disable auto-fix
AUTO_FIX=true

# Maximum pod restarts per hour
MAX_RESTARTS_PER_HOUR=5

# Include low-severity alerts
SEND_LOW_SEVERITY_ALERTS=false
```

See `.env.example` for all options.

---

## 🎓 Next Steps

### Immediate (Today)
- ✅ Follow one of the Quick Start sections above
- ✅ Run K8s Doctor (local or K8s)
- ✅ Test the health endpoint
- ✅ Read [GETTING_STARTED.md](./GETTING_STARTED.md)

### Short Term (This Week)
- ✅ Deploy to your Kubernetes cluster
- ✅ Run in observe mode (AUTO_FIX=false)
- ✅ Review diagnoses for accuracy
- ✅ Review [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)

### Medium Term (This Month)
- ✅ Enable AUTO_FIX=true
- ✅ Configure Slack alerts
- ✅ Integrate with monitoring (Prometheus/Grafana)
- ✅ Tune settings based on your cluster

### Long Term
- ✅ Review cost vs alternatives
- ✅ Extend with custom remediation
- ✅ Integrate with incident management (PagerDuty, etc.)
- ✅ Use predictive features (planned)

---

## ❓ FAQ

**Q: Is it safe to enable AUTO_FIX right away?**
A: Best practice is to run in observe mode for 1 week first. This builds confidence in diagnosis accuracy. Then enable AUTO_FIX.

**Q: How much does it cost?**
A: ~$3-5/month with recommended settings. Way less than Prometheus, DataDog, or New Relic.

**Q: Will it restart critical databases?**
A: No. It carefully checks if auto-fix is safe before restarting. StatefulSets and DaemonSets get manual review by default.

**Q: What if something goes wrong?**
A: All actions are logged and can be audited. Safety throttles (max 5 restarts/hour) prevent cascades. You can disable auto-fix instantly.

**Q: Can it work with multiple clusters?**
A: Currently, one instance per cluster. Multi-cluster support is on the roadmap.

**Q: How do I get support?**
A: Check the troubleshooting sections in DEPLOYMENT_GUIDE.md first. Review logs: `kubectl logs deployment/k8s-doctor -n k8s-doctor`.

---

## 🐛 Troubleshooting

### Pod not connecting to cluster
```bash
# Check RBAC permissions
kubectl auth can-i list pods --as=system:serviceaccount:k8s-doctor:k8s-doctor

# If permission denied, reapply RBAC
kubectl delete -f k8s/rbac.yaml
kubectl apply -f k8s/rbac.yaml
```

### No diagnoses being made
```bash
# Check rate limit
curl http://localhost:8080/stats

# Check logs for errors
kubectl logs deployment/k8s-doctor -n k8s-doctor | grep -i error
```

### High API costs
```bash
# Reduce check frequency
kubectl set env deployment/k8s-doctor CHECK_INTERVAL=60 -n k8s-doctor

# Reduce max diagnoses
kubectl set env deployment/k8s-doctor MAX_DIAGNOSES_PER_HOUR=15 -n k8s-doctor
```

More troubleshooting in [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md#troubleshooting).

---

## 📞 Documentation Quick Links

- **Complete Index:** [INDEX.md](./INDEX.md)
- **Detailed Setup:** [GETTING_STARTED.md](./GETTING_STARTED.md)
- **Project Overview:** [README.md](./README.md)
- **Deployment Guide:** [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
- **Usage Examples:** [USAGE_EXAMPLES.md](./USAGE_EXAMPLES.md)
- **Technical Details:** [PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md)

---

## 💡 Example Diagnoses

### Example 1: Pod Crash
```
Pod: default/api-server-xyz
Status: CrashLoopBackOff, 15 restarts

Claude Diagnosis:
- Root Cause: "Connection refused to database. Connection string outdated."
- Suggested Fix: "Update DB_HOST in ConfigMap from 'db.old.local' to 'db.cluster.svc'"
- Severity: HIGH
- Auto-Fix Safe: true (but requires config change first)

Result: Slack alert sent to team with specific fix steps
```

### Example 2: Node Pressure
```
Node: worker-03
Status: MemoryPressure, Allocatable: 500Mi of 16Gi

Claude Diagnosis:
- Root Cause: "Container memory leak. One pod using 14GB."
- Recommended Action: "cordon node, drain pods, investigate image"
- Severity: HIGH
- Auto-Fix Safe: true (node cordoned automatically)

Result: Node cordoned, team alerted, pods drained
```

---

## ✨ You're All Set!

You now have a complete AI-powered Kubernetes troubleshooting agent. 

**Next step:** Follow one of the Quick Start sections above and get it running!

---

### Need Help?
1. Read the relevant documentation (linked above)
2. Check troubleshooting section in DEPLOYMENT_GUIDE.md
3. Review logs: `kubectl logs -f deployment/k8s-doctor -n k8s-doctor`
4. Check health: `curl http://localhost:8080/health`

### Questions?
- Review [USAGE_EXAMPLES.md](./USAGE_EXAMPLES.md) for real scenarios
- Check [PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md) for technical deep dive
- See [INDEX.md](./INDEX.md) for complete documentation map

**Happy troubleshooting! 🚀**

---

*K8s Doctor - AI-Powered Kubernetes Troubleshooting*
*Inspired by Docker Container Doctor, built for Kubernetes*

# K8s Doctor Deployment Guide

## Quick Start: Local Development

### Prerequisites
- Python 3.10+
- kubectl configured with access to your cluster
- OpenAI/Anthropic API key

### Steps

```bash
# 1. Clone/setup project
cd k8s-doctor

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with:
# - ANTHROPIC_API_KEY=sk-ant-...
# - TARGET_NAMESPACES=default,monitoring
# - SLACK_WEBHOOK_URL=https://hooks.slack.com/... (optional)

# 5. Run locally
python k8s_doctor.py

# 6. In another terminal, check health
curl http://localhost:8080/health
curl http://localhost:8080/history
```

## Kubernetes Deployment

### Option 1: Using kubectl

```bash
# 1. Create namespace and RBAC
kubectl apply -f k8s/rbac.yaml

# 2. Create secret with API key
kubectl create secret generic k8s-doctor-secrets \
  --from-literal=anthropic-api-key=$ANTHROPIC_API_KEY \
  --from-literal=slack-webhook-url=$SLACK_WEBHOOK_URL \
  -n k8s-doctor

# 3. Create ConfigMap with app files
kubectl create configmap k8s-doctor-app \
  --from-file=k8s_client.py \
  --from-file=k8s_doctor.py \
  --from-file=diagnosis_engine.py \
  --from-file=error_detection.py \
  --from-file=remediation_engine.py \
  --from-file=notifications.py \
  --from-file=rate_limiter.py \
  -n k8s-doctor

# 4. Create deployment
kubectl apply -f k8s/deployment.yaml

# 5. Verify
kubectl get pods -n k8s-doctor
kubectl logs -f deployment/k8s-doctor -n k8s-doctor
```

### Option 2: Using Helm (Advanced)

Create a `values.yaml`:

```yaml
replicaCount: 1

image:
  repository: python
  tag: "3.12-slim"

anthropicApiKey: "sk-ant-..."
slackWebhookUrl: ""

config:
  targetNamespaces: "default,kube-system,monitoring"
  checkInterval: 30
  monitorPods: true
  monitorNodes: true
  autoFix: true
  maxDiagnosesPerHour: 30

resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi

serviceMonitor:
  enabled: false
```

### Option 3: Docker Deployment

```bash
# Build Docker image
docker build -t k8s-doctor:latest .

# Tag and push to registry
docker tag k8s-doctor:latest myregistry/k8s-doctor:latest
docker push myregistry/k8s-doctor:latest

# Update deployment.yaml with new image
# Then deploy to K8s
```

## Configuration

### Environment Variables

**Core Configuration:**
- `ANTHROPIC_API_KEY`: Your API key (required)
- `TARGET_NAMESPACES`: Comma-separated list of namespaces to monitor
- `CHECK_INTERVAL`: Seconds between checks (default: 30)

**Monitoring:**
- `MONITOR_PODS`: Enable pod monitoring (default: true)
- `MONITOR_NODES`: Enable node monitoring (default: true)
- `MONITOR_DEPLOYMENTS`: Enable deployment monitoring (default: true)
- `MONITOR_STATEFULSETS`: Enable StatefulSet monitoring (default: true)
- `MONITOR_DAEMONSETS`: Enable DaemonSet monitoring (default: true)

**Remediation:**
- `AUTO_FIX`: Enable automatic fixes (default: true)
- `AUTO_RESTART_PODS`: Allow pod restarts (default: true)
- `MAX_RESTARTS_PER_HOUR`: Rate limit for restarts (default: 5)
- `MAX_DIAGNOSES_PER_HOUR`: Rate limit for diagnoses (default: 30)

**Notifications:**
- `SLACK_WEBHOOK_URL`: Slack incoming webhook for alerts (optional)
- `SEND_LOW_SEVERITY_ALERTS`: Include low-severity alerts (default: false)

**API:**
- `HEALTH_CHECK_PORT`: Port for health endpoint (default: 8080)
- `HEALTH_CHECK_HOST`: Host binding (default: 0.0.0.0)

## Verification

### Check Deployment Status

```bash
# Check pod is running
kubectl get pods -n k8s-doctor
kubectl describe pod <pod-name> -n k8s-doctor

# Check logs
kubectl logs -f deployment/k8s-doctor -n k8s-doctor

# Port forward to access health endpoint
kubectl port-forward -n k8s-doctor svc/k8s-doctor 8080:8080

# In another terminal
curl http://localhost:8080/health
curl http://localhost:8080/status
curl http://localhost:8080/history
```

### Check RBAC Permissions

```bash
# Verify service account permissions
kubectl auth can-i list pods --as=system:serviceaccount:k8s-doctor:k8s-doctor
kubectl auth can-i delete pods --as=system:serviceaccount:k8s-doctor:k8s-doctor
kubectl auth can-i patch nodes --as=system:serviceaccount:k8s-doctor:k8s-doctor
```

## Integration with Monitoring

### Prometheus Integration

If you have Prometheus installed:

```yaml
# ServiceMonitor is included in deployment.yaml
# Prometheus will scrape metrics from:
# http://k8s-doctor:8080/metrics
```

### Slack Integration

1. Create Slack App at https://api.slack.com/apps
2. Enable Incoming Webhooks
3. Create webhook URL for your channel
4. Update secret:

```bash
kubectl patch secret k8s-doctor-secrets -n k8s-doctor \
  -p '{"data":{"slack-webhook-url":"'$(echo -n 'YOUR_WEBHOOK_URL' | base64)'"}}'
```

## Advanced Configurations

### Monitor Specific Namespace Only

```bash
kubectl set env deployment/k8s-doctor \
  TARGET_NAMESPACES="production" \
  -n k8s-doctor
```

### Disable Auto-Fix (Observe Only)

```bash
kubectl set env deployment/k8s-doctor \
  AUTO_FIX=false \
  -n k8s-doctor
```

### Increase Diagnosis Rate Limit

```bash
kubectl set env deployment/k8s-doctor \
  MAX_DIAGNOSES_PER_HOUR=50 \
  -n k8s-doctor
```

## Troubleshooting

### Pod not starting

```bash
# Check events
kubectl describe pod <pod-name> -n k8s-doctor

# Check logs
kubectl logs <pod-name> -n k8s-doctor
```

### Connection refused error

```bash
# Check RBAC permissions
kubectl auth can-i list pods --as=system:serviceaccount:k8s-doctor:k8s-doctor

# Recreate RBAC if needed
kubectl delete -f k8s/rbac.yaml
kubectl apply -f k8s/rbac.yaml
```

### API key not found

```bash
# Check secret exists
kubectl get secret k8s-doctor-secrets -n k8s-doctor

# Check secret has correct key
kubectl get secret k8s-doctor-secrets -n k8s-doctor -o jsonpath='{.data}' | jq .
```

### No diagnoses being made

```bash
# Check logs for rate limiting
kubectl logs deployment/k8s-doctor -n k8s-doctor | grep "rate limit"

# Check monitored namespaces
kubectl logs deployment/k8s-doctor -n k8s-doctor | grep "monitoring"

# Increase MAX_DIAGNOSES_PER_HOUR
kubectl set env deployment/k8s-doctor MAX_DIAGNOSES_PER_HOUR=50 -n k8s-doctor
```

## Uninstalling

```bash
# Delete deployment
kubectl delete -f k8s/deployment.yaml

# Delete RBAC
kubectl delete -f k8s/rbac.yaml

# Delete namespace
kubectl delete namespace k8s-doctor
```

## Next Steps

1. **Monitor Initial Deployments**: Run in observe-only mode for a week
2. **Review Diagnoses**: Check health endpoint regularly
3. **Enable Auto-Fix**: Once comfortable with diagnosis accuracy
4. **Integrate Monitoring**: Connect with Prometheus/Grafana
5. **Set Up Alerts**: Configure Slack/PagerDuty notifications

## Support

For issues or questions:
1. Check logs: `kubectl logs deployment/k8s-doctor -n k8s-doctor`
2. Check health: `curl http://k8s-doctor:8080/health`
3. Review documentation

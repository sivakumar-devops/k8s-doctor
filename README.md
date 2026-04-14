# Kubernetes Doctor 🏥

An AI-powered Kubernetes troubleshooting agent that monitors pods, nodes, and deployments in real-time, diagnoses issues using Claude AI, and automatically applies safe remediation strategies.

## Features

### Monitoring Capabilities
- **Pod Monitoring**: Detects CrashLoopBackOff, ImagePullBackOff, Pending, OOMKilled, Evicted states
- **Node Monitoring**: Identifies resource pressure, disk pressure, memory pressure, network issues
- **Deployment Monitoring**: Tracks replica mismatches, failed rollouts, invalid configurations
- **StatefulSet/DaemonSet Monitoring**: Monitors stateful workload health
- **Event Tracking**: Captures K8s events for context-aware diagnostics

### Smart Features
- **AI Diagnosis**: Uses Claude to analyze logs, events, and metrics for root cause analysis
- **Automatic Remediation**: Safely restarts pods, triggers rollbacks, adjusts resources
- **Rate Limiting**: Prevents API quota exhaustion and costs
- **Error Deduplication**: Avoids duplicate diagnoses of the same issue
- **Predictive Scaling**: Suggests resource adjustments based on patterns
- **Slack Integration**: Real-time alerts with detailed diagnosis
- **Health Monitoring**: Built-in health endpoint for cluster visibility

### Safety Features
- Conservative auto-fix: Only restarts on high-severity issues
- Restart throttling: Prevents restart loops
- Rollback safeguards: Validates deployment state before recovery
- Manual approval options: Can integrate approval flows
- Comprehensive audit logging

## Quick Start

### Prerequisites
- Python 3.10+
- Access to Kubernetes cluster (kubeconfig configured)
- OpenAI/Anthropic API key
- Optional: Slack webhook for notifications

### Installation

```bash
# Clone and setup
cd k8s-doctor
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings:
# - ANTHROPIC_API_KEY
# - TARGET_NAMESPACES
# - SLACK_WEBHOOK_URL (optional)
```

### Local Testing

```bash
# Run the doctor (reads current kubeconfig)
python k8s_doctor.py

# In another terminal, check health
curl http://localhost:8080/health
curl http://localhost:8080/history
curl http://localhost:8080/status
```

### Kubernetes Deployment

```bash
# Create namespace
kubectl create namespace k8s-doctor

# Create secret for API key
kubectl create secret generic k8s-doctor-secrets \
  --from-literal=anthropic-api-key=$ANTHROPIC_API_KEY \
  -n k8s-doctor

# Deploy K8s Doctor
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/deployment.yaml

# Verify deployment
kubectl get pods -n k8s-doctor
kubectl logs -f deployment/k8s-doctor -n k8s-doctor
```

## Configuration

### Environment Variables

```
ANTHROPIC_API_KEY          OpenAI/Anthropic API key (required)
TARGET_NAMESPACES          Comma-separated namespaces to monitor
CHECK_INTERVAL             Seconds between monitoring cycles (default: 30)
AUTO_FIX                   Enable automatic remediation (default: true)
AUTO_RESTART_PODS          Allow pod restarts (default: true)
AUTO_ROLLBACK_DEPLOYMENTS  Allow deployment rollbacks (default: true)
MAX_RESTARTS_PER_HOUR      Rate limit for pod restarts (default: 5)
SLACK_WEBHOOK_URL          Slack incoming webhook URL (optional)
```

## Architecture

```
┌─────────────────────────────────────────────┐
│        Kubernetes Cluster                    │
│                                              │
│  ┌───────────┐  ┌──────────┐  ┌────────┐   │
│  │  Pods     │  │  Nodes   │  │  Events│   │
│  └─────┬─────┘  └────┬─────┘  └────┬───┘   │
│        │             │              │        │
│        └─────────────┼──────────────┘        │
│                      │                        │
│                Kubernetes API                 │
│                      │                        │
│            ┌─────────┴─────────┐             │
│            │  K8s Doctor Agent │             │
│            │  (Python + Flask) │             │
│            └─────────┬─────────┘             │
│                      │                        │
└──────────────────────┼────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         │             │             │
    ┌────▼────┐  ┌────▼─────┐  ┌───▼─────┐
    │Claude AI│  │Slack Hook │  │ Health  │
    │(Diagnosis)│  │(Alerts)   │  │Endpoint │
    └─────────┘  └──────────┘  └─────────┘
```

## Monitored Issue Patterns

### Pod Issues
- `CrashLoopBackOff`: Container keeps restarting
- `ImagePullBackOff`: Cannot pull container image
- `Pending`: Pod stuck waiting for resources
- `OOMKilled`: Out of memory
- `Evicted`: Pod evicted due to node pressure
- `Failed`: Pod execution failed

### Node Issues
- `MemoryPressure`: Node running low on memory
- `DiskPressure`: Node disk space critical
- `NetworkUnavailable`: Node network issues
- `NotReady`: Node not ready to accept pods
- `CordonDrain`: Node cordoned/draining

### Deployment Issues
- Replica mismatches
- Failed rollouts
- Invalid configurations
- Image pull errors at scale
- Resource constraint failures

## API Endpoints

### Health Check
```bash
GET /health
```
Returns monitoring status, connected namespaces, recent diagnoses count.

### History
```bash
GET /history
```
Returns last 50 diagnoses with details.

### Status
```bash
GET /status
```
Returns real-time status: pods monitored, nodes, recent issues, API health.

### Metrics
```bash
GET /metrics
```
Returns Prometheus-style metrics for integration.

## Smart Features Deep Dive

### 1. Automatic Diagnosis
The doctor analyzes:
- Pod/Container logs (last 100 lines)
- Kubernetes events
- Resource metrics
- Historical patterns

Claude provides:
- Root cause analysis
- Severity assessment
- Recommended fixes
- Safety assessment for auto-fix

### 2. Predictive Scaling
Analyzes resource patterns to suggest:
- Memory/CPU limits adjustments
- Replica count recommendations
- HPA policy suggestions

### 3. Error Deduplication
Uses log hash to avoid diagnosing identical errors repeatedly, reducing API costs.

### 4. Rate Limiting
- Max diagnoses per hour (prevents runaway costs)
- Restart throttling (max 5 per pod per hour)
- API call batching

## Troubleshooting

### Doctor Not Connecting to Cluster
```bash
# Verify kubeconfig
kubectl auth can-i list pods --as=system:serviceaccount:k8s-doctor:k8s-doctor

# Check connectivity
python -c "from kubernetes import client, config; config.load_kube_config(); print(client.CoreV1Api().get_api_resources())"
```

### High API Costs
- Increase `CHECK_INTERVAL` (30 → 60 seconds)
- Decrease `MAX_DIAGNOSES_PER_HOUR`
- Disable low-severity alerts
- Use `TARGET_NAMESPACES` to focus monitoring

### Slack Notifications Not Working
- Verify webhook URL in `.env`
- Check webhook still active in Slack app
- Review logs for `SlackError`

## Cost Estimation

With recommended settings:
- **Claude API**: $2-5/month per cluster (with rate limiting)
- **Compute**: Minimal (runs in ~100MB memory)
- **Time saved**: 2-4 hours/month of debugging

## Security Considerations

- **RBAC**: Doctor has read access to pods, events, logs; write access for restarts/updates
- **API Key**: Never commit `.env` file; use K8s secrets in production
- **Network**: Health endpoint behind auth in production
- **Audit**: All actions logged for compliance

## Contributing

Issues and PRs welcome! Areas for contribution:
- Additional monitoring plugins
- Custom remediation strategies
- Integration with other tools (DataDog, New Relic)
- Performance optimizations

## License

MIT

## Support

For issues, questions, or feature requests, open an issue or contact the maintainers.

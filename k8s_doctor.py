"""
Kubernetes Doctor - AI-powered monitoring and troubleshooting agent.
Main application entry point.
"""

import os
import time
import logging
import json
from datetime import datetime
from threading import Thread
from typing import Dict, List, Optional

from flask import Flask, jsonify
from dotenv import load_dotenv

from k8s_client import K8sClient
from diagnosis_engine import DiagnosisEngine
from error_detection import ErrorDetector
from remediation_engine import RemediationEngine
from notifications import NotificationService
from rate_limiter import RateLimiter

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment variables
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
TARGET_NAMESPACES = [ns.strip() for ns in os.getenv("TARGET_NAMESPACES", "default").split(",")]
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", "30"))
MONITOR_PODS = os.getenv("MONITOR_PODS", "true").lower() == "true"
MONITOR_NODES = os.getenv("MONITOR_NODES", "true").lower() == "true"
MONITOR_DEPLOYMENTS = os.getenv("MONITOR_DEPLOYMENTS", "true").lower() == "true"
MONITOR_STATEFULSETS = os.getenv("MONITOR_STATEFULSETS", "true").lower() == "true"
MONITOR_DAEMONSETS = os.getenv("MONITOR_DAEMONSETS", "true").lower() == "true"
LOG_LINES = int(os.getenv("LOG_LINES", "100"))
EVENTS_CHECK_HOURS = int(os.getenv("EVENTS_CHECK_HOURS", "1"))
AUTO_FIX = os.getenv("AUTO_FIX", "true").lower() == "true"
AUTO_RESTART_PODS = os.getenv("AUTO_RESTART_PODS", "true").lower() == "true"
MAX_RESTARTS_PER_HOUR = int(os.getenv("MAX_RESTARTS_PER_HOUR", "5"))
MAX_DIAGNOSES_PER_HOUR = int(os.getenv("MAX_DIAGNOSES_PER_HOUR", "30"))
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
SEND_LOW_SEVERITY_ALERTS = os.getenv("SEND_LOW_SEVERITY_ALERTS", "false").lower() == "true"
HEALTH_CHECK_PORT = int(os.getenv("HEALTH_CHECK_PORT", "8080"))
HEALTH_CHECK_HOST = os.getenv("HEALTH_CHECK_HOST", "0.0.0.0")

# Global state
k8s_client: Optional[K8sClient] = None
diagnosis_engine: Optional[DiagnosisEngine] = None
remediation_engine: Optional[RemediationEngine] = None
notification_service: Optional[NotificationService] = None
rate_limiter: Optional[RateLimiter] = None

diagnosis_history: List[Dict] = []
monitoring_status = {
    "last_check": None,
    "pods_checked": 0,
    "nodes_checked": 0,
    "deployments_checked": 0,
    "issues_detected": 0,
    "fixes_applied": 0,
}

# Flask app
app = Flask(__name__)


def initialize_services():
    """Initialize all services."""
    global k8s_client, diagnosis_engine, remediation_engine, notification_service, rate_limiter

    logger.info("Initializing K8s Doctor services...")

    try:
        k8s_client = K8sClient()
        diagnosis_engine = DiagnosisEngine()
        remediation_engine = RemediationEngine(k8s_client)
        notification_service = NotificationService(SLACK_WEBHOOK_URL)
        rate_limiter = RateLimiter(MAX_DIAGNOSES_PER_HOUR)

        logger.info("All services initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        return False


def monitor_pods():
    """Monitor pods for issues."""
    for namespace in TARGET_NAMESPACES:
        try:
            pods = k8s_client.list_pods(namespace)
            monitoring_status["pods_checked"] = len(pods)

            for pod in pods:
                pod_name = pod["name"]
                resource_key = f"{namespace}/{pod_name}"

                # Detect errors
                errors, severity = ErrorDetector.detect_pod_errors(pod)

                if errors:
                    monitoring_status["issues_detected"] += 1
                    logger.warning(f"Pod {resource_key}: {errors} (severity: {severity})")

                    # Check rate limit
                    if not rate_limiter.can_diagnose(resource_key):
                        logger.warning(f"Skipping diagnosis for {resource_key}: rate limited")
                        continue

                    # Get logs and events
                    logs = k8s_client.get_pod_logs(namespace, pod_name, LOG_LINES)
                    events = k8s_client.get_pod_events(namespace, pod_name, EVENTS_CHECK_HOURS)

                    # Diagnose
                    diagnosis = diagnosis_engine.diagnose_pod_issue(
                        pod_name, namespace, pod, logs, events, errors
                    )

                    if diagnosis:
                        rate_limiter.record_diagnosis(resource_key)
                        diagnosis_history.append({
                            "timestamp": datetime.now().isoformat(),
                            "resource": resource_key,
                            "resource_type": "Pod",
                            "diagnosis": diagnosis,
                        })

                        # Apply remediation
                        remediation_result = None
                        if AUTO_FIX and severity == "high":
                            remediation_result = remediation_engine.apply_remediation(
                                "pod",
                                namespace,
                                pod_name,
                                diagnosis,
                                allow_restart=AUTO_RESTART_PODS,
                                max_restarts_per_hour=MAX_RESTARTS_PER_HOUR,
                            )
                            if remediation_result and remediation_result.get("success"):
                                monitoring_status["fixes_applied"] += 1

                        # Send notification
                        notification_service.send_pod_alert(
                            namespace,
                            pod_name,
                            diagnosis,
                            remediation_result,
                            SEND_LOW_SEVERITY_ALERTS,
                        )

        except Exception as e:
            logger.error(f"Error monitoring pods in {namespace}: {e}")


def monitor_nodes():
    """Monitor nodes for issues."""
    try:
        nodes = k8s_client.list_nodes()
        monitoring_status["nodes_checked"] = len(nodes)

        for node in nodes:
            node_name = node["name"]

            # Detect errors
            errors, severity = ErrorDetector.detect_node_errors(node)

            if errors:
                monitoring_status["issues_detected"] += 1
                logger.warning(f"Node {node_name}: {errors} (severity: {severity})")

                # Check rate limit
                if not rate_limiter.can_diagnose(node_name):
                    logger.warning(f"Skipping diagnosis for node {node_name}: rate limited")
                    continue

                # Diagnose
                diagnosis = diagnosis_engine.diagnose_node_issue(
                    node_name, node, None, errors
                )

                if diagnosis:
                    rate_limiter.record_diagnosis(node_name)
                    diagnosis_history.append({
                        "timestamp": datetime.now().isoformat(),
                        "resource": node_name,
                        "resource_type": "Node",
                        "diagnosis": diagnosis,
                    })

                    # Apply remediation
                    remediation_result = None
                    if AUTO_FIX and severity == "high":
                        remediation_result = remediation_engine.apply_remediation(
                            "node",
                            "cluster",
                            node_name,
                            diagnosis,
                        )
                        if remediation_result and remediation_result.get("success"):
                            monitoring_status["fixes_applied"] += 1

                    # Send notification
                    notification_service.send_node_alert(
                        node_name,
                        diagnosis,
                        remediation_result,
                        SEND_LOW_SEVERITY_ALERTS,
                    )

    except Exception as e:
        logger.error(f"Error monitoring nodes: {e}")


def monitor_deployments():
    """Monitor deployments for issues."""
    for namespace in TARGET_NAMESPACES:
        try:
            deployments = k8s_client.list_deployments(namespace)
            monitoring_status["deployments_checked"] = len(deployments)

            for deployment in deployments:
                deployment_name = deployment["name"]
                resource_key = f"{namespace}/{deployment_name}"

                # Detect errors
                errors, severity = ErrorDetector.detect_deployment_errors(deployment)

                if errors:
                    monitoring_status["issues_detected"] += 1
                    logger.warning(f"Deployment {resource_key}: {errors} (severity: {severity})")

                    # Check rate limit
                    if not rate_limiter.can_diagnose(resource_key):
                        continue

                    # Diagnose
                    diagnosis = diagnosis_engine.diagnose_deployment_issue(
                        deployment_name, namespace, deployment, None, errors
                    )

                    if diagnosis:
                        rate_limiter.record_diagnosis(resource_key)
                        diagnosis_history.append({
                            "timestamp": datetime.now().isoformat(),
                            "resource": resource_key,
                            "resource_type": "Deployment",
                            "diagnosis": diagnosis,
                        })

                        # Apply remediation
                        remediation_result = None
                        if AUTO_FIX and severity == "high":
                            remediation_result = remediation_engine.apply_remediation(
                                "deployment",
                                namespace,
                                deployment_name,
                                diagnosis,
                            )
                            if remediation_result and remediation_result.get("success"):
                                monitoring_status["fixes_applied"] += 1

                        # Send notification
                        notification_service.send_deployment_alert(
                            namespace,
                            deployment_name,
                            diagnosis,
                            remediation_result,
                            SEND_LOW_SEVERITY_ALERTS,
                        )

        except Exception as e:
            logger.error(f"Error monitoring deployments in {namespace}: {e}")


def monitor_statefulsets():
    """Monitor StatefulSets for issues."""
    for namespace in TARGET_NAMESPACES:
        try:
            statefulsets = k8s_client.list_statefulsets(namespace)

            for sts in statefulsets:
                sts_name = sts["name"]
                resource_key = f"{namespace}/{sts_name}"

                # Detect errors
                errors, severity = ErrorDetector.detect_workload_errors(sts, "StatefulSet")

                if errors:
                    monitoring_status["issues_detected"] += 1
                    logger.warning(f"StatefulSet {resource_key}: {errors} (severity: {severity})")

                    if not rate_limiter.can_diagnose(resource_key):
                        continue

                    # Diagnose
                    diagnosis = diagnosis_engine.diagnose_workload_issue(
                        sts_name, "StatefulSet", namespace, sts, None, errors
                    )

                    if diagnosis:
                        rate_limiter.record_diagnosis(resource_key)
                        diagnosis_history.append({
                            "timestamp": datetime.now().isoformat(),
                            "resource": resource_key,
                            "resource_type": "StatefulSet",
                            "diagnosis": diagnosis,
                        })

                        # Send notification (don't auto-fix StatefulSets)
                        notification_service.send_workload_alert(
                            "StatefulSet",
                            namespace,
                            sts_name,
                            diagnosis,
                            None,
                            SEND_LOW_SEVERITY_ALERTS,
                        )

        except Exception as e:
            logger.error(f"Error monitoring StatefulSets in {namespace}: {e}")


def monitor_daemonsets():
    """Monitor DaemonSets for issues."""
    for namespace in TARGET_NAMESPACES:
        try:
            daemonsets = k8s_client.list_daemonsets(namespace)

            for ds in daemonsets:
                ds_name = ds["name"]
                resource_key = f"{namespace}/{ds_name}"

                # Detect errors
                errors, severity = ErrorDetector.detect_workload_errors(ds, "DaemonSet")

                if errors:
                    monitoring_status["issues_detected"] += 1
                    logger.warning(f"DaemonSet {resource_key}: {errors} (severity: {severity})")

                    if not rate_limiter.can_diagnose(resource_key):
                        continue

                    # Diagnose
                    diagnosis = diagnosis_engine.diagnose_workload_issue(
                        ds_name, "DaemonSet", namespace, ds, None, errors
                    )

                    if diagnosis:
                        rate_limiter.record_diagnosis(resource_key)
                        diagnosis_history.append({
                            "timestamp": datetime.now().isoformat(),
                            "resource": resource_key,
                            "resource_type": "DaemonSet",
                            "diagnosis": diagnosis,
                        })

                        # Send notification
                        notification_service.send_workload_alert(
                            "DaemonSet",
                            namespace,
                            ds_name,
                            diagnosis,
                            None,
                            SEND_LOW_SEVERITY_ALERTS,
                        )

        except Exception as e:
            logger.error(f"Error monitoring DaemonSets in {namespace}: {e}")


def monitoring_loop():
    """Main monitoring loop."""
    logger.info("K8s Doctor monitoring loop started")
    logger.info(f"Target namespaces: {TARGET_NAMESPACES}")
    logger.info(f"Check interval: {CHECK_INTERVAL}s")
    logger.info(f"Auto-fix: {AUTO_FIX}")

    while True:
        try:
            monitoring_status["last_check"] = datetime.now().isoformat()

            if MONITOR_PODS:
                monitor_pods()

            if MONITOR_NODES:
                monitor_nodes()

            if MONITOR_DEPLOYMENTS:
                monitor_deployments()

            if MONITOR_STATEFULSETS:
                monitor_statefulsets()

            if MONITOR_DAEMONSETS:
                monitor_daemonsets()

            time.sleep(CHECK_INTERVAL)

        except Exception as e:
            logger.error(f"Error in monitoring loop: {e}")
            time.sleep(CHECK_INTERVAL)


# --- Flask Endpoints ---

@app.route("/health")
def health():
    """Health check endpoint."""
    try:
        k8s_client.get_namespaces()
        status = "healthy"
    except:
        status = "degraded"

    return jsonify({
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "monitoring": {
            "pods": MONITOR_PODS,
            "nodes": MONITOR_NODES,
            "deployments": MONITOR_DEPLOYMENTS,
            "statefulsets": MONITOR_STATEFULSETS,
            "daemonsets": MONITOR_DAEMONSETS,
        },
        "namespaces": TARGET_NAMESPACES,
        "rate_limit": rate_limiter.get_stats() if rate_limiter else {},
        "diagnoses_count": len(diagnosis_history),
        "fixes_applied": monitoring_status.get("fixes_applied", 0),
    })


@app.route("/status")
def status():
    """Get current monitoring status."""
    return jsonify({
        "status": monitoring_status,
        "recent_diagnoses": len([d for d in diagnosis_history if d]),
    })


@app.route("/history")
def history():
    """Get recent diagnosis history."""
    return jsonify({
        "total": len(diagnosis_history),
        "recent": diagnosis_history[-50:],
    })


@app.route("/stats")
def stats():
    """Get detailed statistics."""
    return jsonify({
        "monitoring_status": monitoring_status,
        "rate_limiter": rate_limiter.get_stats() if rate_limiter else {},
        "remediation_stats": remediation_engine.get_stats() if remediation_engine else {},
        "diagnosis_history_count": len(diagnosis_history),
    })


@app.route("/metrics")
def metrics():
    """Get Prometheus-style metrics."""
    metrics_text = f"""# HELP k8s_doctor_diagnoses_total Total diagnoses performed
# TYPE k8s_doctor_diagnoses_total counter
k8s_doctor_diagnoses_total {len(diagnosis_history)}

# HELP k8s_doctor_fixes_applied_total Total fixes applied
# TYPE k8s_doctor_fixes_applied_total counter
k8s_doctor_fixes_applied_total {monitoring_status.get('fixes_applied', 0)}

# HELP k8s_doctor_issues_detected_total Total issues detected
# TYPE k8s_doctor_issues_detected_total counter
k8s_doctor_issues_detected_total {monitoring_status.get('issues_detected', 0)}

# HELP k8s_doctor_rate_limit_remaining Rate limit remaining
# TYPE k8s_doctor_rate_limit_remaining gauge
k8s_doctor_rate_limit_remaining {rate_limiter.get_remaining_capacity() if rate_limiter else 0}
"""
    return metrics_text, 200, {"Content-Type": "text/plain"}


def main():
    """Main entry point."""
    logger.info("Starting K8s Doctor...")

    # Validate API key
    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not set. Exiting.")
        return

    # Initialize services
    if not initialize_services():
        logger.error("Failed to initialize services. Exiting.")
        return

    # Start monitoring thread
    monitor_thread = Thread(target=monitoring_loop, daemon=True)
    monitor_thread.start()

    # Start Flask app
    try:
        logger.info(f"Health endpoint available at http://{HEALTH_CHECK_HOST}:{HEALTH_CHECK_PORT}/health")
        app.run(host=HEALTH_CHECK_HOST, port=HEALTH_CHECK_PORT, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("K8s Doctor shutting down...")


if __name__ == "__main__":
    main()

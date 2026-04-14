"""
K8s error and issue detection patterns.
Identifies problematic states in pods, nodes, and deployments.
"""

import logging
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)


class ErrorDetector:
    """Detects Kubernetes error patterns and anomalies."""

    # Pod error patterns
    POD_ERROR_PATTERNS = {
        "CrashLoopBackOff": ["CrashLoopBackOff", "crash", "restarting"],
        "ImagePullBackOff": ["ImagePullBackOff", "image pull", "pull back off"],
        "ImagePullError": ["ImagePullError", "failed to pull image"],
        "Pending": ["Pending", "0/1"],
        "OOMKilled": ["OOMKilled", "out of memory", "oomkiller"],
        "Evicted": ["Evicted", "eviction"],
        "Failed": ["Failed"],
        "Unknown": ["Unknown"],
        "RunContainerError": ["RunContainerError", "failed to run container"],
        "CreateContainerConfigError": ["CreateContainerConfigError"],
    }

    # Container log error patterns
    LOG_ERROR_PATTERNS = [
        "error", "exception", "traceback", "failed", "crash",
        "fatal", "panic", "segmentation fault", "out of memory",
        "killed", "oomkiller", "connection refused", "timeout",
        "permission denied", "no such file", "errno", "cannot connect",
        "connection reset", "broken pipe", "access denied",
        "authentication failed", "unauthorized", "forbidden",
        "invalid", "corrupted", "corrupted data", "checksum",
    ]

    # Node error patterns
    NODE_ERROR_PATTERNS = {
        "MemoryPressure": ["MemoryPressure", "memory", "high memory"],
        "DiskPressure": ["DiskPressure", "disk", "no space", "full"],
        "NetworkUnavailable": ["NetworkUnavailable", "network"],
        "NotReady": ["NotReady", "not ready"],
        "PIDPressure": ["PIDPressure", "too many processes"],
        "CordonDrain": ["unschedulable", "cordoned"],
    }

    # Deployment error patterns
    DEPLOYMENT_ERROR_PATTERNS = {
        "ReplicasMismatch": ["ReplicasMismatch", "replicas", "desired"],
        "ProgressDeadlineExceeded": ["ProgressDeadlineExceeded", "progress"],
        "FailedCreate": ["FailedCreate", "failed to create"],
        "ImagePullError": ["ImagePullError", "image pull"],
    }

    @staticmethod
    def detect_pod_errors(pod_info: Dict) -> Tuple[List[str], str]:
        """
        Detect errors in pod status.
        Returns (error_patterns, severity).
        """
        errors = []
        severity = "low"

        phase = pod_info.get("phase", "Unknown")
        ready_status = pod_info.get("ready", (0, 0))
        ready_count, total_count = ready_status
        restart_count = pod_info.get("restart_count", 0)
        
        # Check phase
        if phase != "Running":
            errors.append(phase)
            if phase in ["Failed", "Unknown"]:
                severity = "high"
            elif phase in ["CrashLoopBackOff", "ImagePullBackOff"]:
                severity = "high"
            elif phase == "Pending":
                severity = "medium" if restart_count > 0 else "low"

        # Check ready status
        if ready_count < total_count:
            errors.append("NotReady")
            if total_count > 0 and ready_count == 0:
                severity = "high"

        # Check restart count
        if restart_count > 3:
            errors.append("HighRestartCount")
            severity = "high"

        # Check container conditions
        for condition in pod_info.get("conditions", []):
            if condition.get("status") == "False":
                errors.append(condition.get("type", "UnknownCondition"))
                if condition.get("type") == "Ready":
                    severity = "high"

        # Check container statuses
        for container in pod_info.get("container_statuses", []):
            if not container.get("ready", False):
                if container.get("state") == "waiting":
                    errors.append(f"Waiting: {container.get('reason', 'Unknown')}")
                    if "ImagePull" in container.get("reason", ""):
                        severity = "high"
                elif container.get("state") == "terminated":
                    errors.append(f"Terminated: {container.get('reason', 'Unknown')}")
                    exit_code = container.get("exit_code", 0)
                    if exit_code != 0:
                        severity = "high"

        return (errors, severity)

    @staticmethod
    def detect_node_errors(node_info: Dict) -> Tuple[List[str], str]:
        """
        Detect errors in node status.
        Returns (error_patterns, severity).
        """
        errors = []
        severity = "low"

        status = node_info.get("status", "unknown")
        
        if status != "ready":
            errors.append(status)
            if status == "not-ready":
                severity = "high"
            elif status == "cordoned":
                severity = "medium"

        # Check conditions
        for condition in node_info.get("conditions", []):
            cond_type = condition.get("type", "")
            cond_status = condition.get("status", "")
            
            # These are "pressure" conditions - True means problem
            if cond_type in ["MemoryPressure", "DiskPressure", "PIDPressure"]:
                if cond_status == "True":
                    errors.append(cond_type)
                    severity = "high"
            
            # These are "ready" conditions - False means problem
            elif cond_type in ["Ready", "NetworkUnavailable"]:
                if cond_status == "False":
                    errors.append(cond_type)
                    severity = "high"

        return (errors, severity)

    @staticmethod
    def detect_deployment_errors(deployment_info: Dict) -> Tuple[List[str], str]:
        """
        Detect errors in deployment status.
        Returns (error_patterns, severity).
        """
        errors = []
        severity = "low"

        replicas = deployment_info.get("replicas", 0)
        ready_replicas = deployment_info.get("ready_replicas", 0)
        updated_replicas = deployment_info.get("updated_replicas", 0)
        available_replicas = deployment_info.get("available_replicas", 0)

        # Check replica mismatch
        if ready_replicas < replicas:
            errors.append("ReplicasMismatch")
            severity = "high" if ready_replicas == 0 else "medium"

        if updated_replicas < replicas:
            errors.append("RolloutInProgress")
            severity = "medium"

        if available_replicas < replicas:
            errors.append("NotAllAvailable")
            severity = "high" if available_replicas == 0 else "medium"

        # Check conditions
        for condition in deployment_info.get("conditions", []):
            if condition.get("status") == "False":
                reason = condition.get("reason", "")
                errors.append(reason)
                
                if "ProgressDeadlineExceeded" in reason:
                    severity = "high"
                elif "FailedCreate" in reason or "ImagePull" in reason:
                    severity = "high"

        return (errors, severity)

    @staticmethod
    def detect_log_errors(logs: str) -> List[str]:
        """Detect error patterns in logs."""
        if not logs:
            return []

        errors = []
        logs_lower = logs.lower()

        for pattern in ErrorDetector.LOG_ERROR_PATTERNS:
            if pattern in logs_lower:
                errors.append(pattern)

        return list(set(errors))  # Remove duplicates

    @staticmethod
    def detect_workload_errors(workload_info: Dict, workload_type: str) -> Tuple[List[str], str]:
        """
        Detect errors in workload status (StatefulSet, DaemonSet, etc.).
        Returns (error_patterns, severity).
        """
        errors = []
        severity = "low"

        if workload_type == "StatefulSet":
            desired = workload_info.get("replicas", 0)
            ready = workload_info.get("ready_replicas", 0)
            updated = workload_info.get("updated_replicas", 0)

            if ready < desired:
                errors.append("ReplicasMismatch")
                severity = "high" if ready == 0 else "medium"

            if updated < desired:
                errors.append("RolloutInProgress")
                severity = "medium"

        elif workload_type == "DaemonSet":
            desired = workload_info.get("desired", 0)
            ready = workload_info.get("ready", 0)
            available = workload_info.get("available", 0)

            if ready < desired:
                errors.append("NotAllReady")
                severity = "high" if ready == 0 else "medium"

            if available < desired:
                errors.append("NotAllAvailable")
                severity = "high"

        # Check conditions
        for condition in workload_info.get("conditions", []):
            if condition.get("status") == "False":
                reason = condition.get("reason", "")
                errors.append(reason)
                severity = max(severity, "medium")

        return (errors, severity)

    @staticmethod
    def prioritize_errors(errors: List[str]) -> str:
        """
        Determine overall severity based on specific errors.
        """
        high_severity_errors = {
            "CrashLoopBackOff", "ImagePullBackOff", "Failed", "OOMKilled",
            "Evicted", "HighRestartCount", "NotReady", "MemoryPressure",
            "DiskPressure", "NotReady", "ReplicasMismatch", "ProgressDeadlineExceeded",
            "FailedCreate", "RunContainerError", "CreateContainerConfigError",
            "NotAllAvailable", "NotAllReady",
        }

        medium_severity_errors = {
            "Pending", "ImagePullError", "RolloutInProgress", "CordonDrain",
            "PIDPressure", "NetworkUnavailable", "RunContainerError",
        }

        for error in errors:
            if any(high in error for high in high_severity_errors):
                return "high"
        
        for error in errors:
            if any(medium in error for medium in medium_severity_errors):
                return "medium"

        return "low"

"""
Remediation engine for applying safe fixes to Kubernetes issues.
Implements auto-fix logic with safety guards and rollback capabilities.
"""

import logging
from typing import Optional, Dict
from datetime import datetime, timedelta
from collections import defaultdict

from k8s_client import K8sClient

logger = logging.getLogger(__name__)


class RemediationEngine:
    """Engine for safely applying remediation to K8s issues."""

    def __init__(self, k8s_client: K8sClient):
        """Initialize remediation engine."""
        self.k8s_client = k8s_client
        self.fix_history = defaultdict(list)
        self.restart_history = defaultdict(list)
        self.rollback_history = defaultdict(list)

    def apply_remediation(
        self,
        issue_type: str,
        namespace: str,
        resource_name: str,
        diagnosis: Dict,
        allow_restart: bool = True,
        allow_rollback: bool = True,
        max_restarts_per_hour: int = 5,
    ) -> Dict:
        """
        Apply remediation based on diagnosis and issue type.
        Returns action result with success status and details.
        """
        result = {
            "success": False,
            "action": None,
            "message": "",
            "timestamp": datetime.now().isoformat(),
        }

        # Check if auto-fix is safe
        if not diagnosis.get("auto_restart_safe", False) and not diagnosis.get("auto_fix_safe", False):
            result["message"] = "Diagnosis indicates auto-fix is not safe"
            logger.warning(f"Skipping fix for {namespace}/{resource_name}: diagnosis says unsafe")
            return result

        # Route to appropriate remediation
        if issue_type == "pod":
            result = self._remediate_pod(
                namespace, resource_name, diagnosis, allow_restart, max_restarts_per_hour
            )
        elif issue_type == "deployment":
            result = self._remediate_deployment(
                namespace, resource_name, diagnosis, allow_rollback, max_restarts_per_hour
            )
        elif issue_type == "node":
            result = self._remediate_node(namespace, resource_name, diagnosis)
        elif issue_type in ["statefulset", "daemonset"]:
            result = self._remediate_workload(
                issue_type, namespace, resource_name, diagnosis, allow_restart, max_restarts_per_hour
            )

        if result["success"]:
            self._record_fix(f"{namespace}/{resource_name}", issue_type, result["action"])

        return result

    def _remediate_pod(
        self,
        namespace: str,
        pod_name: str,
        diagnosis: Dict,
        allow_restart: bool,
        max_restarts_per_hour: int,
    ) -> Dict:
        """Remediate pod issues."""
        result = {
            "success": False,
            "action": None,
            "message": "",
        }

        resource_key = f"{namespace}/{pod_name}"

        # Check restart throttle
        if not self._can_restart(resource_key, max_restarts_per_hour):
            result["message"] = (
                f"Pod {resource_key} already restarted {max_restarts_per_hour} times this hour. "
                "Something deeper is wrong. Manual intervention needed."
            )
            logger.warning(result["message"])
            return result

        if not allow_restart:
            result["message"] = "Pod restart disabled"
            return result

        # Restart the pod
        if self.k8s_client.restart_pod(namespace, pod_name):
            self.restart_history[resource_key].append(datetime.now())
            result["success"] = True
            result["action"] = "restart"
            result["message"] = f"Pod {resource_key} restarted successfully"
            logger.info(result["message"])
            return result
        else:
            result["message"] = f"Failed to restart pod {resource_key}"
            logger.error(result["message"])
            return result

    def _remediate_deployment(
        self,
        namespace: str,
        deployment_name: str,
        diagnosis: Dict,
        allow_rollback: bool,
        max_restarts_per_hour: int,
    ) -> Dict:
        """Remediate deployment issues."""
        result = {
            "success": False,
            "action": None,
            "message": "",
        }

        resource_key = f"{namespace}/{deployment_name}"

        # Check for scale adjustments
        scale_adjustment = diagnosis.get("scale_adjustment")
        if scale_adjustment and scale_adjustment.get("desired_replicas"):
            desired_replicas = scale_adjustment["desired_replicas"]
            reason = scale_adjustment.get("reason", "Unknown")
            
            if self.k8s_client.scale_deployment(namespace, deployment_name, desired_replicas):
                result["success"] = True
                result["action"] = f"scale_to_{desired_replicas}"
                result["message"] = (
                    f"Deployment {resource_key} scaled to {desired_replicas} replicas. "
                    f"Reason: {reason}"
                )
                logger.info(result["message"])
                return result

        # Check for rollback/rollout restart
        if allow_rollback and diagnosis.get("auto_rollback_safe", False):
            resource_key_rollback = f"{resource_key}_rollback"
            
            # Check rollback throttle (max 1 per day)
            rollback_count = sum(
                1 for t in self.rollback_history[resource_key_rollback]
                if t > datetime.now() - timedelta(hours=24)
            )
            
            if rollback_count >= 1:
                result["message"] = (
                    f"Deployment {resource_key} already rolled back once today. "
                    "Manual review needed."
                )
                logger.warning(result["message"])
                return result

            if self.k8s_client.rollout_restart_deployment(namespace, deployment_name):
                self.rollback_history[resource_key_rollback].append(datetime.now())
                result["success"] = True
                result["action"] = "rollout_restart"
                result["message"] = f"Deployment {resource_key} rolled out with restart"
                logger.info(result["message"])
                return result

        result["message"] = f"No applicable remediation for deployment {resource_key}"
        return result

    def _remediate_node(self, namespace: str, node_name: str, diagnosis: Dict) -> Dict:
        """Remediate node issues."""
        result = {
            "success": False,
            "action": None,
            "message": "",
        }

        recommended_action = diagnosis.get("recommended_action", "investigate")

        if recommended_action == "cordon":
            if self.k8s_client.cordon_node(node_name):
                result["success"] = True
                result["action"] = "cordon"
                result["message"] = f"Node {node_name} cordoned to prevent new pod scheduling"
                logger.info(result["message"])
            else:
                result["message"] = f"Failed to cordon node {node_name}"
                logger.error(result["message"])

        elif recommended_action == "uncordon":
            if self.k8s_client.uncordon_node(node_name):
                result["success"] = True
                result["action"] = "uncordon"
                result["message"] = f"Node {node_name} uncordoned"
                logger.info(result["message"])
            else:
                result["message"] = f"Failed to uncordon node {node_name}"
                logger.error(result["message"])

        else:
            result["message"] = f"Manual intervention required for node {node_name}: {recommended_action}"

        return result

    def _remediate_workload(
        self,
        workload_type: str,
        namespace: str,
        workload_name: str,
        diagnosis: Dict,
        allow_restart: bool,
        max_restarts_per_hour: int,
    ) -> Dict:
        """Remediate StatefulSet or DaemonSet issues."""
        result = {
            "success": False,
            "action": None,
            "message": "",
        }

        resource_key = f"{namespace}/{workload_name}"

        # For StatefulSets and DaemonSets, be more conservative
        # Usually need manual review
        if not allow_restart:
            result["message"] = f"Manual intervention required for {workload_type} {resource_key}"
            return result

        # Only restart if high severity and safe
        if (diagnosis.get("severity") == "high" and 
            diagnosis.get("auto_restart_safe", False) and
            not self._can_restart(resource_key, max_restarts_per_hour)):
            
            result["message"] = (
                f"{workload_type} {resource_key} already restarted multiple times. "
                "Manual intervention needed."
            )
            logger.warning(result["message"])
            return result

        result["message"] = f"Manual intervention recommended for {workload_type} {resource_key}"
        return result

    def _can_restart(self, resource_key: str, max_per_hour: int) -> bool:
        """Check if resource can be restarted based on throttle."""
        recent_restarts = [
            t for t in self.restart_history[resource_key]
            if t > datetime.now() - timedelta(hours=1)
        ]
        
        if len(recent_restarts) >= max_per_hour:
            logger.warning(
                f"Restart throttle reached for {resource_key}: "
                f"{len(recent_restarts)}/{max_per_hour} in last hour"
            )
            return False

        return True

    def _record_fix(self, resource_key: str, issue_type: str, action: str) -> None:
        """Record fix in history."""
        self.fix_history[resource_key].append({
            "timestamp": datetime.now().isoformat(),
            "issue_type": issue_type,
            "action": action,
        })

    def get_fix_history(self, resource_key: Optional[str] = None, limit: int = 50) -> Dict:
        """Get remediation history."""
        if resource_key:
            return {
                resource_key: self.fix_history.get(resource_key, [])[-limit:]
            }
        
        return {k: v[-limit:] for k, v in self.fix_history.items()}

    def get_stats(self) -> Dict:
        """Get remediation statistics."""
        total_fixes = sum(len(v) for v in self.fix_history.values())
        total_restarts = sum(len(v) for v in self.restart_history.values())
        total_rollbacks = sum(len(v) for v in self.rollback_history.values())

        return {
            "total_fixes": total_fixes,
            "total_restarts": total_restarts,
            "total_rollbacks": total_rollbacks,
            "resources_fixed": len(self.fix_history),
            "fix_history_by_resource": dict(self.fix_history),
        }

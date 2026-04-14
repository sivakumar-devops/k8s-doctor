"""
Kubernetes API client wrapper for monitoring pods, nodes, and deployments.
Provides unified interface for cluster interactions.
"""

import logging
from typing import List, Dict, Optional, Tuple
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class K8sClient:
    """Unified Kubernetes API client."""

    def __init__(self, kubeconfig_path: Optional[str] = None):
        """Initialize Kubernetes client."""
        try:
            if kubeconfig_path:
                config.load_kube_config(config_file=kubeconfig_path)
            else:
                config.load_kube_config()
            logger.info("Kubernetes client initialized successfully")
        except config.ConfigException:
            try:
                config.load_incluster_config()
                logger.info("Kubernetes client initialized with in-cluster config")
            except config.ConfigException as e:
                logger.error(f"Failed to initialize Kubernetes client: {e}")
                raise

        self.v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.batch_v1 = client.BatchV1Api()

    def get_namespaces(self) -> List[str]:
        """Get all namespaces in cluster."""
        try:
            namespaces = self.v1.list_namespace()
            return [ns.metadata.name for ns in namespaces.items]
        except ApiException as e:
            logger.error(f"Failed to list namespaces: {e}")
            return []

    def list_pods(self, namespace: str) -> List[Dict]:
        """List all pods in namespace with detailed info."""
        try:
            pods = self.v1.list_namespaced_pod(namespace)
            result = []
            for pod in pods.items:
                pod_info = {
                    "name": pod.metadata.name,
                    "namespace": namespace,
                    "phase": pod.status.phase,
                    "ready": self._get_pod_ready_status(pod),
                    "restart_count": self._get_pod_restart_count(pod),
                    "conditions": self._get_pod_conditions(pod),
                    "container_statuses": self._get_container_statuses(pod),
                    "creation_timestamp": pod.metadata.creation_timestamp,
                    "deletion_timestamp": pod.metadata.deletion_timestamp,
                }
                result.append(pod_info)
            return result
        except ApiException as e:
            logger.error(f"Failed to list pods in {namespace}: {e}")
            return []

    def list_nodes(self) -> List[Dict]:
        """List all nodes with health status."""
        try:
            nodes = self.v1.list_node()
            result = []
            for node in nodes.items:
                node_info = {
                    "name": node.metadata.name,
                    "status": self._get_node_status(node),
                    "conditions": self._get_node_conditions(node),
                    "capacity": node.status.capacity if node.status.capacity else {},
                    "allocatable": node.status.allocatable if node.status.allocatable else {},
                    "creation_timestamp": node.metadata.creation_timestamp,
                }
                result.append(node_info)
            return result
        except ApiException as e:
            logger.error(f"Failed to list nodes: {e}")
            return []

    def list_deployments(self, namespace: str) -> List[Dict]:
        """List all deployments with status."""
        try:
            deployments = self.apps_v1.list_namespaced_deployment(namespace)
            result = []
            for dep in deployments.items:
                dep_info = {
                    "name": dep.metadata.name,
                    "namespace": namespace,
                    "replicas": dep.spec.replicas or 0,
                    "ready_replicas": dep.status.ready_replicas or 0,
                    "updated_replicas": dep.status.updated_replicas or 0,
                    "available_replicas": dep.status.available_replicas or 0,
                    "conditions": self._get_deployment_conditions(dep),
                    "image": self._get_deployment_image(dep),
                    "creation_timestamp": dep.metadata.creation_timestamp,
                }
                result.append(dep_info)
            return result
        except ApiException as e:
            logger.error(f"Failed to list deployments in {namespace}: {e}")
            return []

    def list_statefulsets(self, namespace: str) -> List[Dict]:
        """List all StatefulSets with status."""
        try:
            statefulsets = self.apps_v1.list_namespaced_stateful_set(namespace)
            result = []
            for sts in statefulsets.items:
                sts_info = {
                    "name": sts.metadata.name,
                    "namespace": namespace,
                    "replicas": sts.spec.replicas or 0,
                    "ready_replicas": sts.status.ready_replicas or 0,
                    "updated_replicas": sts.status.updated_replicas or 0,
                    "conditions": self._get_statefulset_conditions(sts),
                    "creation_timestamp": sts.metadata.creation_timestamp,
                }
                result.append(sts_info)
            return result
        except ApiException as e:
            logger.error(f"Failed to list StatefulSets in {namespace}: {e}")
            return []

    def list_daemonsets(self, namespace: str) -> List[Dict]:
        """List all DaemonSets with status."""
        try:
            daemonsets = self.apps_v1.list_namespaced_daemon_set(namespace)
            result = []
            for ds in daemonsets.items:
                ds_info = {
                    "name": ds.metadata.name,
                    "namespace": namespace,
                    "desired": ds.status.desired_number_scheduled or 0,
                    "ready": ds.status.number_ready or 0,
                    "updated": ds.status.updated_number_scheduled or 0,
                    "available": ds.status.number_available or 0,
                    "conditions": self._get_daemonset_conditions(ds),
                    "creation_timestamp": ds.metadata.creation_timestamp,
                }
                result.append(ds_info)
            return result
        except ApiException as e:
            logger.error(f"Failed to list DaemonSets in {namespace}: {e}")
            return []

    def get_pod_logs(self, namespace: str, pod_name: str, lines: int = 100) -> Optional[str]:
        """Get recent logs from pod."""
        try:
            logs = self.v1.read_namespaced_pod_log(
                pod_name,
                namespace,
                tail_lines=lines,
                timestamps=True
            )
            return logs
        except ApiException as e:
            logger.warning(f"Failed to get logs for pod {pod_name}: {e}")
            return None

    def get_pod_events(self, namespace: str, pod_name: str, hours: int = 1) -> List[Dict]:
        """Get recent events for a pod."""
        try:
            events = self.v1.list_namespaced_event(namespace)
            result = []
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            
            for event in events.items:
                # Filter events related to this pod
                if event.involved_object.name == pod_name:
                    if event.first_timestamp and event.first_timestamp.replace(tzinfo=None) > cutoff:
                        result.append({
                            "reason": event.reason,
                            "message": event.message,
                            "type": event.type,
                            "count": event.count,
                            "first_timestamp": event.first_timestamp,
                            "last_timestamp": event.last_timestamp,
                        })
            return result
        except ApiException as e:
            logger.warning(f"Failed to get events for pod {pod_name}: {e}")
            return []

    def restart_pod(self, namespace: str, pod_name: str) -> bool:
        """Delete pod to trigger restart (via replica controller)."""
        try:
            self.v1.delete_namespaced_pod(
                pod_name,
                namespace,
                grace_period_seconds=30
            )
            logger.info(f"Pod {namespace}/{pod_name} deleted for restart")
            return True
        except ApiException as e:
            logger.error(f"Failed to restart pod {namespace}/{pod_name}: {e}")
            return False

    def scale_deployment(self, namespace: str, deployment_name: str, replicas: int) -> bool:
        """Scale deployment to specified number of replicas."""
        try:
            deployment = self.apps_v1.read_namespaced_deployment(deployment_name, namespace)
            deployment.spec.replicas = replicas
            self.apps_v1.patch_namespaced_deployment(deployment_name, namespace, deployment)
            logger.info(f"Deployment {namespace}/{deployment_name} scaled to {replicas} replicas")
            return True
        except ApiException as e:
            logger.error(f"Failed to scale deployment {namespace}/{deployment_name}: {e}")
            return False

    def rollout_restart_deployment(self, namespace: str, deployment_name: str) -> bool:
        """Trigger rollout restart of deployment."""
        try:
            deployment = self.apps_v1.read_namespaced_deployment(deployment_name, namespace)
            if deployment.spec.template.metadata.annotations is None:
                deployment.spec.template.metadata.annotations = {}
            deployment.spec.template.metadata.annotations["kubectl.kubernetes.io/restartedAt"] = datetime.utcnow().isoformat()
            self.apps_v1.patch_namespaced_deployment(deployment_name, namespace, deployment)
            logger.info(f"Deployment {namespace}/{deployment_name} rollout restarted")
            return True
        except ApiException as e:
            logger.error(f"Failed to rollout restart deployment {namespace}/{deployment_name}: {e}")
            return False

    def cordon_node(self, node_name: str) -> bool:
        """Cordon a node to prevent new pod scheduling."""
        try:
            node = self.v1.read_node(node_name)
            node.spec.unschedulable = True
            self.v1.patch_node(node_name, node)
            logger.info(f"Node {node_name} cordoned")
            return True
        except ApiException as e:
            logger.error(f"Failed to cordon node {node_name}: {e}")
            return False

    def uncordon_node(self, node_name: str) -> bool:
        """Uncordon a node."""
        try:
            node = self.v1.read_node(node_name)
            node.spec.unschedulable = False
            self.v1.patch_node(node_name, node)
            logger.info(f"Node {node_name} uncordoned")
            return True
        except ApiException as e:
            logger.error(f"Failed to uncordon node {node_name}: {e}")
            return False

    # --- Private Helper Methods ---

    def _get_pod_ready_status(self, pod) -> Tuple[int, int]:
        """Get pod ready containers count."""
        ready = 0
        total = len(pod.spec.containers)
        if pod.status.conditions:
            for condition in pod.status.conditions:
                if condition.type == "Ready" and condition.status == "True":
                    ready = total
        return (ready, total)

    def _get_pod_restart_count(self, pod) -> int:
        """Get total restart count for pod."""
        count = 0
        if pod.status.container_statuses:
            for status in pod.status.container_statuses:
                count += status.restart_count
        return count

    def _get_pod_conditions(self, pod) -> List[Dict]:
        """Extract pod conditions."""
        conditions = []
        if pod.status.conditions:
            for condition in pod.status.conditions:
                conditions.append({
                    "type": condition.type,
                    "status": condition.status,
                    "reason": condition.reason,
                    "message": condition.message,
                })
        return conditions

    def _get_container_statuses(self, pod) -> List[Dict]:
        """Extract container statuses."""
        statuses = []
        if pod.status.container_statuses:
            for status in pod.status.container_statuses:
                container_info = {
                    "name": status.name,
                    "ready": status.ready,
                    "restart_count": status.restart_count,
                    "image": status.image,
                }
                if status.state and status.state.waiting:
                    container_info["state"] = "waiting"
                    container_info["reason"] = status.state.waiting.reason
                elif status.state and status.state.running:
                    container_info["state"] = "running"
                elif status.state and status.state.terminated:
                    container_info["state"] = "terminated"
                    container_info["exit_code"] = status.state.terminated.exit_code
                    container_info["reason"] = status.state.terminated.reason
                statuses.append(container_info)
        return statuses

    def _get_node_status(self, node) -> str:
        """Get node status."""
        if node.spec.unschedulable:
            return "cordoned"
        if node.status.conditions:
            for condition in node.status.conditions:
                if condition.type == "Ready" and condition.status == "True":
                    return "ready"
        return "not-ready"

    def _get_node_conditions(self, node) -> List[Dict]:
        """Extract node conditions."""
        conditions = []
        if node.status.conditions:
            for condition in node.status.conditions:
                conditions.append({
                    "type": condition.type,
                    "status": condition.status,
                    "reason": condition.reason,
                    "message": condition.message,
                })
        return conditions

    def _get_deployment_conditions(self, deployment) -> List[Dict]:
        """Extract deployment conditions."""
        conditions = []
        if deployment.status.conditions:
            for condition in deployment.status.conditions:
                conditions.append({
                    "type": condition.type,
                    "status": condition.status,
                    "reason": condition.reason,
                    "message": condition.message,
                })
        return conditions

    def _get_deployment_image(self, deployment) -> str:
        """Get primary container image from deployment."""
        if deployment.spec.template.spec.containers:
            return deployment.spec.template.spec.containers[0].image
        return "unknown"

    def _get_statefulset_conditions(self, statefulset) -> List[Dict]:
        """Extract StatefulSet conditions."""
        conditions = []
        if statefulset.status.conditions:
            for condition in statefulset.status.conditions:
                conditions.append({
                    "type": condition.type,
                    "status": condition.status,
                    "reason": condition.reason,
                    "message": condition.message,
                })
        return conditions

    def _get_daemonset_conditions(self, daemonset) -> List[Dict]:
        """Extract DaemonSet conditions."""
        conditions = []
        if daemonset.status.conditions:
            for condition in daemonset.status.conditions:
                conditions.append({
                    "type": condition.type,
                    "status": condition.status,
                    "reason": condition.reason,
                    "message": condition.message,
                })
        return conditions

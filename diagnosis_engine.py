"""
Claude AI-based diagnosis engine for Kubernetes issues.
Analyzes logs, events, and metrics to determine root causes and remediation.
"""

import json
import logging
from typing import Optional, Dict, List
from anthropic import Anthropic
from datetime import datetime

logger = logging.getLogger(__name__)

client = Anthropic()


class DiagnosisEngine:
    """Engine for diagnosing K8s issues using Claude."""

    def __init__(self, model: str = "claude-sonnet-4-20250514"):
        """Initialize diagnosis engine."""
        self.model = model
        self.conversation_history = {}

    def diagnose_pod_issue(
        self,
        pod_name: str,
        namespace: str,
        pod_status: Dict,
        logs: Optional[str] = None,
        events: Optional[List[Dict]] = None,
        detected_patterns: Optional[List[str]] = None,
    ) -> Optional[Dict]:
        """Diagnose pod-related issues."""
        
        prompt = self._build_pod_diagnosis_prompt(
            pod_name, namespace, pod_status, logs, events, detected_patterns
        )
        
        return self._send_diagnosis_request(prompt, f"{namespace}/{pod_name}")

    def diagnose_node_issue(
        self,
        node_name: str,
        node_status: Dict,
        pods_on_node: Optional[List[Dict]] = None,
        detected_patterns: Optional[List[str]] = None,
    ) -> Optional[Dict]:
        """Diagnose node-related issues."""
        
        prompt = self._build_node_diagnosis_prompt(
            node_name, node_status, pods_on_node, detected_patterns
        )
        
        return self._send_diagnosis_request(prompt, f"node/{node_name}")

    def diagnose_deployment_issue(
        self,
        deployment_name: str,
        namespace: str,
        deployment_status: Dict,
        pod_logs: Optional[List[str]] = None,
        detected_patterns: Optional[List[str]] = None,
    ) -> Optional[Dict]:
        """Diagnose deployment-related issues."""
        
        prompt = self._build_deployment_diagnosis_prompt(
            deployment_name, namespace, deployment_status, pod_logs, detected_patterns
        )
        
        return self._send_diagnosis_request(prompt, f"{namespace}/{deployment_name}")

    def diagnose_workload_issue(
        self,
        workload_name: str,
        workload_type: str,  # statefulset, daemonset, etc.
        namespace: str,
        workload_status: Dict,
        pod_logs: Optional[List[str]] = None,
        detected_patterns: Optional[List[str]] = None,
    ) -> Optional[Dict]:
        """Diagnose general workload issues."""
        
        prompt = self._build_workload_diagnosis_prompt(
            workload_name, workload_type, namespace, workload_status, pod_logs, detected_patterns
        )
        
        return self._send_diagnosis_request(prompt, f"{namespace}/{workload_name}")

    # --- Private Helper Methods ---

    def _build_pod_diagnosis_prompt(
        self,
        pod_name: str,
        namespace: str,
        pod_status: Dict,
        logs: Optional[str] = None,
        events: Optional[List[Dict]] = None,
        detected_patterns: Optional[List[str]] = None,
    ) -> str:
        """Build structured prompt for pod diagnosis."""
        
        patterns_text = ", ".join(detected_patterns) if detected_patterns else "none detected"
        events_text = self._format_events(events) if events else "no recent events"
        logs_text = logs if logs else "no logs available"
        
        prompt = f"""You are an expert Kubernetes troubleshooter analyzing a pod issue.

Pod: {pod_name}
Namespace: {namespace}
Timestamp: {datetime.now().isoformat()}
Phase: {pod_status.get('phase', 'Unknown')}
Ready Status: {pod_status.get('ready', (0, 0))}
Restart Count: {pod_status.get('restart_count', 0)}
Detected Patterns: {patterns_text}

Pod Conditions:
{json.dumps(pod_status.get('conditions', []), indent=2)}

Container Statuses:
{json.dumps(pod_status.get('container_statuses', []), indent=2)}

Recent Events:
{events_text}

Recent Logs:
---
{logs_text}
---

Analyze this pod issue and respond with ONLY valid JSON (no markdown, no explanation):
{{
    "root_cause": "One sentence explaining what went wrong",
    "severity": "low|medium|high",
    "issue_type": "CrashLoopBackOff|ImagePullBackOff|Pending|OOMKilled|Evicted|Other",
    "suggested_fix": "Step-by-step fix for the operator",
    "auto_restart_safe": true or false,
    "estimated_recovery_time": "in minutes",
    "requires_manual_intervention": true or false,
    "related_resources": ["namespace/resource to check", "..."],
    "config_suggestions": ["CONFIG_CHANGE=value", "..."],
    "likely_recurring": true or false,
    "estimated_impact": "What breaks if not fixed"
}}
"""
        return prompt

    def _build_node_diagnosis_prompt(
        self,
        node_name: str,
        node_status: Dict,
        pods_on_node: Optional[List[Dict]] = None,
        detected_patterns: Optional[List[str]] = None,
    ) -> str:
        """Build structured prompt for node diagnosis."""
        
        patterns_text = ", ".join(detected_patterns) if detected_patterns else "none detected"
        pods_text = json.dumps(pods_on_node, indent=2) if pods_on_node else "unknown"
        
        prompt = f"""You are an expert Kubernetes cluster administrator analyzing node health.

Node: {node_name}
Timestamp: {datetime.now().isoformat()}
Status: {node_status.get('status', 'Unknown')}
Detected Patterns: {patterns_text}

Node Conditions:
{json.dumps(node_status.get('conditions', []), indent=2)}

Node Capacity:
{json.dumps(node_status.get('capacity', {}), indent=2)}

Node Allocatable:
{json.dumps(node_status.get('allocatable', {}), indent=2)}

Pods Running on Node:
{pods_text}

Analyze this node issue and respond with ONLY valid JSON (no markdown, no explanation):
{{
    "root_cause": "Why this node is having problems",
    "severity": "low|medium|high",
    "issue_type": "MemoryPressure|DiskPressure|NetworkUnavailable|NotReady|CordonDrain|Other",
    "suggested_fix": "Steps to remediate the issue",
    "auto_fix_safe": true or false,
    "requires_manual_intervention": true or false,
    "recommended_action": "cordon|uncordon|drain|investigate|scale_workloads",
    "affected_pods": [count of pods that will be affected],
    "estimated_recovery_time": "in minutes",
    "likely_recurring": true or false,
    "estimated_impact": "Impact on workloads"
}}
"""
        return prompt

    def _build_deployment_diagnosis_prompt(
        self,
        deployment_name: str,
        namespace: str,
        deployment_status: Dict,
        pod_logs: Optional[List[str]] = None,
        detected_patterns: Optional[List[str]] = None,
    ) -> str:
        """Build structured prompt for deployment diagnosis."""
        
        patterns_text = ", ".join(detected_patterns) if detected_patterns else "none detected"
        logs_text = "\n---\n".join(pod_logs) if pod_logs else "no logs available"
        replicas_status = (
            f"{deployment_status.get('ready_replicas', 0)}/{deployment_status.get('replicas', 0)}"
        )
        
        prompt = f"""You are a Kubernetes deployment expert analyzing rollout issues.

Deployment: {deployment_name}
Namespace: {namespace}
Timestamp: {datetime.now().isoformat()}
Replicas Ready: {replicas_status}
Image: {deployment_status.get('image', 'unknown')}
Detected Patterns: {patterns_text}

Deployment Conditions:
{json.dumps(deployment_status.get('conditions', []), indent=2)}

Pod Logs from Failed Replicas:
---
{logs_text}
---

Analyze this deployment issue and respond with ONLY valid JSON (no markdown, no explanation):
{{
    "root_cause": "Why replicas are not becoming ready",
    "severity": "low|medium|high",
    "issue_type": "ImagePullError|ResourceConstraint|ConfigError|HealthCheckFailed|Other",
    "suggested_fix": "Steps to fix the deployment",
    "auto_rollback_safe": true or false,
    "scale_adjustment": null or {{desired_replicas: number, reason: "string"}},
    "requires_manual_intervention": true or false,
    "estimated_time_to_fix": "in minutes",
    "likely_recurring": true or false,
    "resource_recommendations": {{cpu: "100m or null", memory: "128Mi or null"}},
    "estimated_impact": "Impact of this deployment failure"
}}
"""
        return prompt

    def _build_workload_diagnosis_prompt(
        self,
        workload_name: str,
        workload_type: str,
        namespace: str,
        workload_status: Dict,
        pod_logs: Optional[List[str]] = None,
        detected_patterns: Optional[List[str]] = None,
    ) -> str:
        """Build structured prompt for general workload diagnosis."""
        
        patterns_text = ", ".join(detected_patterns) if detected_patterns else "none detected"
        logs_text = "\n---\n".join(pod_logs) if pod_logs else "no logs available"
        
        prompt = f"""You are a Kubernetes expert analyzing {workload_type} workload health.

Workload: {workload_name} ({workload_type})
Namespace: {namespace}
Timestamp: {datetime.now().isoformat()}
Detected Patterns: {patterns_text}

Workload Status:
{json.dumps(workload_status, indent=2)}

Pod Logs:
---
{logs_text}
---

Analyze this {workload_type} issue and respond with ONLY valid JSON (no markdown, no explanation):
{{
    "root_cause": "Root cause analysis",
    "severity": "low|medium|high",
    "suggested_fix": "Recommended remediation steps",
    "auto_fix_safe": true or false,
    "requires_manual_intervention": true or false,
    "likely_recurring": true or false,
    "estimated_impact": "What breaks if not fixed",
    "next_steps": ["step 1", "step 2"]
}}
"""
        return prompt

    def _format_events(self, events: List[Dict]) -> str:
        """Format events for prompt."""
        if not events:
            return "no recent events"
        
        formatted = []
        for event in events:
            formatted.append(
                f"[{event.get('type', 'Unknown')}] {event.get('reason', '')}: "
                f"{event.get('message', '')} (count: {event.get('count', 1)})"
            )
        return "\n".join(formatted[:10])  # Limit to 10 most recent

    def _send_diagnosis_request(self, prompt: str, context_key: str) -> Optional[Dict]:
        """Send diagnosis request to Claude and parse response."""
        try:
            message = client.messages.create(
                model=self.model,
                max_tokens=800,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            response_text = message.content[0].text
            diagnosis = self._parse_diagnosis_response(response_text)
            
            if diagnosis:
                diagnosis["timestamp"] = datetime.now().isoformat()
                diagnosis["context"] = context_key
                logger.info(f"Diagnosis for {context_key}: severity={diagnosis.get('severity')}")
            
            return diagnosis
        except Exception as e:
            logger.error(f"Failed to get diagnosis from Claude: {e}")
            return None

    def _parse_diagnosis_response(self, response_text: str) -> Optional[Dict]:
        """Extract and parse JSON from Claude response."""
        try:
            start = response_text.find("{")
            end = response_text.rfind("}") + 1
            
            if start >= 0 and end > start:
                json_str = response_text[start:end]
                return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw response: {response_text}")
        except Exception as e:
            logger.error(f"Unexpected error parsing diagnosis: {e}")
        
        return None

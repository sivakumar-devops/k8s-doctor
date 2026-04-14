"""
Notification system for sending alerts via Slack and other channels.
"""

import logging
import requests
from typing import Dict, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications about K8s issues."""

    SEVERITY_EMOJI = {
        "low": "🟡",
        "medium": "🟠",
        "high": "🔴",
    }

    def __init__(self, slack_webhook_url: Optional[str] = None):
        """Initialize notification service."""
        self.slack_webhook_url = slack_webhook_url

    def send_pod_alert(
        self,
        namespace: str,
        pod_name: str,
        diagnosis: Dict,
        remediation_result: Optional[Dict] = None,
        send_low_severity: bool = False,
    ) -> bool:
        """Send pod issue alert."""
        if not self.slack_webhook_url:
            return False

        severity = diagnosis.get("severity", "unknown")
        
        # Filter low severity
        if severity == "low" and not send_low_severity:
            logger.debug(f"Skipping low-severity alert for pod {namespace}/{pod_name}")
            return True

        return self._send_slack_alert(
            title=f"Pod Issue: {pod_name}",
            namespace=namespace,
            resource=pod_name,
            resource_type="Pod",
            diagnosis=diagnosis,
            remediation_result=remediation_result,
            severity=severity,
        )

    def send_node_alert(
        self,
        node_name: str,
        diagnosis: Dict,
        remediation_result: Optional[Dict] = None,
        send_low_severity: bool = False,
    ) -> bool:
        """Send node issue alert."""
        if not self.slack_webhook_url:
            return False

        severity = diagnosis.get("severity", "unknown")
        
        if severity == "low" and not send_low_severity:
            return True

        return self._send_slack_alert(
            title=f"Node Issue: {node_name}",
            namespace="cluster-wide",
            resource=node_name,
            resource_type="Node",
            diagnosis=diagnosis,
            remediation_result=remediation_result,
            severity=severity,
        )

    def send_deployment_alert(
        self,
        namespace: str,
        deployment_name: str,
        diagnosis: Dict,
        remediation_result: Optional[Dict] = None,
        send_low_severity: bool = False,
    ) -> bool:
        """Send deployment issue alert."""
        if not self.slack_webhook_url:
            return False

        severity = diagnosis.get("severity", "unknown")
        
        if severity == "low" and not send_low_severity:
            return True

        return self._send_slack_alert(
            title=f"Deployment Issue: {deployment_name}",
            namespace=namespace,
            resource=deployment_name,
            resource_type="Deployment",
            diagnosis=diagnosis,
            remediation_result=remediation_result,
            severity=severity,
        )

    def send_workload_alert(
        self,
        workload_type: str,
        namespace: str,
        workload_name: str,
        diagnosis: Dict,
        remediation_result: Optional[Dict] = None,
        send_low_severity: bool = False,
    ) -> bool:
        """Send general workload issue alert."""
        if not self.slack_webhook_url:
            return False

        severity = diagnosis.get("severity", "unknown")
        
        if severity == "low" and not send_low_severity:
            return True

        return self._send_slack_alert(
            title=f"{workload_type} Issue: {workload_name}",
            namespace=namespace,
            resource=workload_name,
            resource_type=workload_type,
            diagnosis=diagnosis,
            remediation_result=remediation_result,
            severity=severity,
        )

    def _send_slack_alert(
        self,
        title: str,
        namespace: str,
        resource: str,
        resource_type: str,
        diagnosis: Dict,
        remediation_result: Optional[Dict],
        severity: str,
    ) -> bool:
        """Send Slack notification."""
        try:
            emoji = self.SEVERITY_EMOJI.get(severity, "⚪")
            
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{emoji} K8s Doctor Alert: {title}",
                        "emoji": True,
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Severity:*\n{severity.upper()}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Resource Type:*\n{resource_type}",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Namespace:*\n`{namespace}`",
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Resource:*\n`{resource}`",
                        },
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Root Cause:*\n{diagnosis.get('root_cause', 'Unknown')}",
                    }
                },
            ]

            # Add suggested fix
            suggested_fix = diagnosis.get("suggested_fix")
            if suggested_fix:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Suggested Fix:*\n{suggested_fix}",
                    }
                })

            # Add remediation result if available
            if remediation_result and remediation_result.get("success"):
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"✅ *Action Taken:* {remediation_result.get('message', 'Fix applied')}",
                    }
                })

            # Add impact assessment
            estimated_impact = diagnosis.get("estimated_impact")
            if estimated_impact:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Impact if Not Fixed:*\n{estimated_impact}",
                    }
                })

            # Add config suggestions
            config_suggestions = diagnosis.get("config_suggestions", [])
            if config_suggestions:
                suggestions = "\n".join(f"• `{s}`" for s in config_suggestions)
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Config Suggestions:*\n{suggestions}",
                    }
                })

            # Add footer
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Diagnosed by K8s Doctor • {datetime.now().isoformat()}",
                    }
                ]
            })

            payload = {"blocks": blocks}
            
            response = requests.post(
                self.slack_webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Slack notification failed: {response.status_code} - {response.text}")
                return False
            
            logger.info(f"Slack alert sent for {resource_type} {resource}")
            return True

        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
            return False

    def send_health_check_alert(self, status: Dict) -> bool:
        """Send health check status."""
        if not self.slack_webhook_url:
            return False

        try:
            is_healthy = status.get("status") == "healthy"
            emoji = "✅" if is_healthy else "⚠️"
            color = "good" if is_healthy else "warning"

            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{emoji} *K8s Doctor Health Check*\nStatus: {'Healthy' if is_healthy else 'Degraded'}",
                    }
                }
            ]

            payload = {"blocks": blocks}
            
            requests.post(self.slack_webhook_url, json=payload, timeout=10)
            return True

        except Exception as e:
            logger.error(f"Failed to send health check alert: {e}")
            return False

import json
import logging
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

# UTF-8 Support for Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('alerts.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class AlertWebhookHandler(BaseHTTPRequestHandler):
    """Handle incoming webhook alerts from Prometheus/Grafana"""

    def do_POST(self):
        """Process POST requests with alert data"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                self._send_error(400, "No content provided")
                return

            body = self.rfile.read(content_length)
            alert_data = json.loads(body)

            # payload None / non‑dict ho to ignore
            if not isinstance(alert_data, dict):
                logger.error("Payload is not a JSON object: %r", alert_data)
                self._send_error(400, "Payload must be JSON object")
                return

            status = str(alert_data.get("status", "unknown")).upper()

            title = alert_data.get("title") or ""
            common_labels = alert_data.get("commonLabels") or {}
            labels_root = alert_data.get("labels") or {}

            if not isinstance(common_labels, dict):
                common_labels = {}
            if not isinstance(labels_root, dict):
                labels_root = {}

            alert_name = (
                common_labels.get("alertname")
                or labels_root.get("alertname")
                or (title.split()[-1] if title else "Unknown")
            )

            logger.info("=" * 70)
            logger.info("ALERT RECEIVED | Status: %s | Alert: %s", status, alert_name)
            logger.info("=" * 70)

            # Alerts list safely extract karo
            alerts = alert_data.get("alerts") or []
            if not isinstance(alerts, list):
                alerts = []

            if alerts:
                logger.info("Total Alerts: %d", len(alerts))
                for idx, alert in enumerate(alerts, 1):
                    if not isinstance(alert, dict):
                        continue

                    alert_status = str(alert.get("status", "UNKNOWN")).upper()
                    labels = alert.get("labels") or {}
                    if not isinstance(labels, dict):
                        labels = {}

                    # Grafana sometimes sends 'value', sometimes 'values' with keys
                    values_field = alert.get("values") or {}
                    if not isinstance(values_field, dict):
                        values_field = {}

                    value = (
                        values_field.get("A")
                        or alert.get("value")
                        or "N/A"
                    )

                    instance = labels.get("instance", "N/A")

                    logger.info(
                        "   [%d] Status: %s | Instance: %s | Value: %s",
                        idx,
                        alert_status,
                        instance,
                        value
                    )
            else:
                logger.info("No 'alerts' array in payload; nothing to list.")

            logger.info("")
            self._send_success()

        except json.JSONDecodeError as e:
            logger.error("JSON Parse Error: %s", str(e))
            self._send_error(400, "Invalid JSON")
        except Exception as e:
            logger.error("Handler Error: %s", str(e))
            self._send_error(500, "Internal server error")

    def _send_success(self):
        """Send 200 success response"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        response = json.dumps({"status": "ok", "message": "Alert received"})
        self.wfile.write(response.encode('utf-8'))

    def _send_error(self, code, message):
        """Send error response"""
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        response = json.dumps({"status": "error", "message": message})
        self.wfile.write(response.encode('utf-8'))

    def log_message(self, format, *args):
        """Suppress default HTTP logging"""
        pass


def main():
    """Start webhook server"""
    print("\n" + "=" * 70)
    print("LEGAL DOC SIMPLIFIER - ALERT WEBHOOK SERVER")
    print("=" * 70)
    print("Server: 0.0.0.0:9091")
    print("Logs: alerts.log (in current directory)")
    print("=" * 70 + "\n")

    logger.info("Webhook server starting on 0.0.0.0:9091...")

    server = HTTPServer(('0.0.0.0', 9091), AlertWebhookHandler)

    logger.info("Webhook server is LIVE and listening for alerts!")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Webhook server shutting down...")
        server.shutdown()
    except Exception as e:
        logger.error("Fatal error: %s", str(e))


if __name__ == "__main__":
    main()

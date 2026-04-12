"""
ZEUS Gateway — minimal HTTP bridge between Python swarm and Node.js agents.

Receives proposals/events from autonomous_run.py (_notify_zeus_gateway)
and queues them for Node.js side consumption.

Auth: Authorization: Bearer <GATEWAY_SECRET>
Endpoints:
  GET  /health  — healthcheck (Railway)
  POST /event   — receive proposal from Python swarm
  GET  /queue   — read queued events (Node.js polls this)
"""

import json
import os
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("zeus-gateway")

PORT = int(os.environ.get("PORT", 18789))
SECRET = os.environ.get("GATEWAY_SECRET", "")
QUEUE_FILE = os.path.join(os.path.dirname(__file__), "zeus_event_queue.jsonl")


def _auth_ok(headers) -> bool:
    auth = headers.get("Authorization", "")
    if not SECRET:
        log.warning("GATEWAY_SECRET not set — accepting all requests (unsafe)")
        return True
    return auth == f"Bearer {SECRET}"


class GatewayHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        log.info(f"{self.address_string()} {fmt % args}")

    def _send_json(self, code: int, body: dict):
        payload = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path == "/health":
            queue_size = 0
            try:
                with open(QUEUE_FILE, encoding="utf-8") as f:
                    queue_size = sum(1 for _ in f)
            except FileNotFoundError:
                pass
            self._send_json(200, {
                "status": "ok",
                "service": "zeus-gateway",
                "queue_size": queue_size,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

        elif self.path == "/queue":
            if not _auth_ok(self.headers):
                self._send_json(403, {"error": "Unauthorized"})
                return
            events = []
            try:
                with open(QUEUE_FILE, encoding="utf-8") as f:
                    events = [json.loads(line) for line in f if line.strip()]
                # Clear queue after read
                open(QUEUE_FILE, "w").close()
            except FileNotFoundError:
                pass
            self._send_json(200, {"events": events, "count": len(events)})

        else:
            self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        if self.path != "/event":
            self._send_json(404, {"error": "Not found"})
            return

        if not _auth_ok(self.headers):
            log.warning("Unauthorized POST to /event")
            self._send_json(403, {"error": "Unauthorized"})
            return

        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            self._send_json(400, {"error": "Empty body"})
            return

        try:
            body = json.loads(self.rfile.read(length))
        except json.JSONDecodeError as e:
            self._send_json(400, {"error": f"Invalid JSON: {e}"})
            return

        event = {
            "received_at": datetime.now(timezone.utc).isoformat(),
            "payload": body,
        }

        with open(QUEUE_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

        log.info(f"Event queued: {str(body)[:80]}")
        self._send_json(200, {"status": "queued"})


if __name__ == "__main__":
    if not SECRET:
        log.warning("⚠️  GATEWAY_SECRET not set — running in insecure mode")
    log.info(f"ZEUS Gateway starting on port {PORT}")
    server = HTTPServer(("0.0.0.0", PORT), GatewayHandler)
    log.info(f"Listening on 0.0.0.0:{PORT}")
    server.serve_forever()

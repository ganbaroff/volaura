"""
Flask wrapper for VOLAURA Web Checker.
Endpoint: POST /check with JSON payload.
"""

from flask import Flask, request, jsonify
import asyncio
import sys
import os

# Add checker to path
sys.path.insert(0, os.path.dirname(__file__))
from checker import checker, check_volaura

app = Flask(__name__)

# Startup: initialize browser
@app.before_request
async def startup():
    if not hasattr(app, 'checker_ready'):
        await checker.start()
        app.checker_ready = True

# Shutdown: cleanup
@app.teardown_appcontext
def shutdown(exception):
    # Browser will stay alive; we'll rely on process restart for cleanup
    pass

@app.post("/check")
async def check():
    """
    Batch check endpoint.

    Request body:
    {
      "tasks": [
        {"url": "...", "flow": "...", "assertions": [{"selector": "...", "expect": "..."}]}
      ],
      "return_screenshots": true
    }
    """
    try:
        payload = request.get_json()

        if not payload:
            return jsonify({"error": "No JSON payload"}), 400

        result = await check_volaura(payload)
        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.get("/health")
def health():
    """Health check for Railway."""
    return jsonify({"status": "ok", "service": "volaura-web-checker"}), 200

if __name__ == "__main__":
    # Run on 0.0.0.0:8080 (Railway default)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)), debug=False)

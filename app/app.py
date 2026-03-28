from flask import Flask, jsonify
from prometheus_flask_exporter import PrometheusMetrics
import logging
import os

app = Flask(__name__)
metrics = PrometheusMetrics(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def home():
    logger.info("Home endpoint hit")
    return jsonify({"message":"DevSecOps Pipeline Demo", "status":"running"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/api/users')
def users():
    return jsonify({"users": ["Alice", "Bob", "Charlie"]})

if __name__== "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

from flask import Flask, jsonify, request
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time
import random
import os
import psycopg2
import redis

app = Flask(__name__)

REQUEST_COUNT = Counter('backend_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('backend_request_duration_seconds', 'Request latency')
ERROR_COUNT = Counter('backend_errors_total', 'Total errors', ['error_type'])
ACTIVE_CONNECTIONS = Gauge('backend_active_connections', 'Active connections')

FAILURE_MODES = {
    'high_latency': False,
    'database_errors': False,
    'memory_leak': False,
    'cpu_spike': False,
    'intermittent_failures': False
}

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'timestamp': time.time()})

@app.route('/api/users')
@REQUEST_LATENCY.time()
def get_users():
    start_time = time.time()
    try:
        if FAILURE_MODES['high_latency']:
            time.sleep(random.uniform(2, 5))

        if FAILURE_MODES['database_errors'] and random.random() < 0.3:
            ERROR_COUNT.labels(error_type='database').inc()
            REQUEST_COUNT.labels(method='GET', endpoint='/api/users', status='500').inc()
            return jsonify({'error': 'Database connection failed'}), 500

        if FAILURE_MODES['intermittent_failures'] and random.random() < 0.1:
            ERROR_COUNT.labels(error_type='intermittent').inc()
            REQUEST_COUNT.labels(method='GET', endpoint='/api/users', status='503').inc()
            return jsonify({'error': 'Service temporarily unavailable'}), 503

        users = [
            {'id': 1, 'name': 'Alice', 'email': 'alice@example.com'},
            {'id': 2, 'name': 'Bob', 'email': 'bob@example.com'},
            {'id': 3, 'name': 'Charlie', 'email': 'charlie@example.com'}
        ]
        REQUEST_COUNT.labels(method='GET', endpoint='/api/users', status='200').inc()
        return jsonify(users)
    except Exception as e:
        ERROR_COUNT.labels(error_type='unexpected').inc()
        REQUEST_COUNT.labels(method='GET', endpoint='/api/users', status='500').inc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/orders')
@REQUEST_LATENCY.time()
def get_orders():
    if FAILURE_MODES['cpu_spike']:
        for i in range(1000000):
            _ = i ** 2

    orders = [
        {'id': 1, 'user_id': 1, 'total': 99.99, 'status': 'completed'},
        {'id': 2, 'user_id': 2, 'total': 149.99, 'status': 'pending'}
    ]
    REQUEST_COUNT.labels(method='GET', endpoint='/api/orders', status='200').inc()
    return jsonify(orders)

@app.route('/admin/failure-mode', methods=['POST'])
def set_failure_mode():
    data = request.json
    mode = data.get('mode')
    enabled = data.get('enabled', False)
    if mode in FAILURE_MODES:
        FAILURE_MODES[mode] = enabled
        return jsonify({'message': f'Failure mode {mode} set to {enabled}'})
    return jsonify({'error': 'Invalid failure mode'}), 400

@app.route('/admin/failure-modes')
def get_failure_modes():
    return jsonify(FAILURE_MODES)

@app.route('/metrics')
def metrics():
    return generate_latest()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
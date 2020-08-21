# helpers/middleware.py - testwebapplicatie

from flask import request
from prometheus_client import Counter, Histogram

import csv
import time

REQUEST_COUNT = Counter(
    'request_count', 'App Request Count',
    ['app_name', 'method', 'endpoint', 'http_status']
)

REQUEST_LATENCY = Histogram('request_latency_seconds', 'Request latency',
    ['app_name', 'endpoint']
)

def start_timer():
    request.start_time = time.time()

def stop_timer(response):
    REQUEST_COUNT.labels(
            'bap-app', request.method, request.path, response.status_code
        ).inc()

    resp_time = time.time() - request.start_time
    REQUEST_LATENCY.labels(
            'bap-app', request.path
        ).observe(resp_time)

    return response

def setup_metrics(app):
    app.before_request(start_timer)
    app.after_request(stop_timer)
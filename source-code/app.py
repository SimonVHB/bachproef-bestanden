# app.py - testwebapplicatie

import prometheus_client
import os, time
from helpers.middleware import setup_metrics

CONTENT_TYPE_LATEST = str('text/plain; version=0.0.4; charset=utf-8')

app = Flask(__name__)
setup_metrics(app)

@app.route('/')
def hello():
    return "Hello, world!"

@app.route('/metrics')
def metrics():
    return Response(prometheus_client.generate_latest(), mimetype=CONTENT_TYPE_LATEST)
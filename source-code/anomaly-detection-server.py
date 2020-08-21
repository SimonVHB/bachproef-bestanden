# anomaly-detection-server.py - webapplicatie waarme anomalie gedetecteerd worden

from flask import Flask, request, Response
import prometheus_client
from prometheus_api_client import PrometheusConnect
from datetime import datetime, timedelta
import pytz
import numpy as np
import pandas as pd

from rpy2.robjects import r, pandas2ri
from rpy2 import robjects as ro
from rpy2.robjects.conversion import localconverter

CONTENT_TYPE_LATEST = str('text/plain; version=0.0.4; charset=utf-8')

ANOMALY_GAUGE = prometheus_client.Gauge("application_rps_anomalies", "Contains 0 or 1 if anomaly detected in the last minute", labelnames=['value_type'])

app = Flask(__name__)

@app.route('/metrics')
def metrics():
    #get metrics of last 2 "seasons" - using UTC, because prom only saves in UTC
    start_time = datetime.now(tz=pytz.UTC) - timedelta(hours=5, minutes=10)
    end_time = datetime.now(tz=pytz.UTC)

    prom = PrometheusConnect(
        url="http://localhost:9090"
    )

    data = prom.custom_query_range(
        "rate(app_gunicorn_requests[10m])",
        start_time=start_time,
        end_time=end_time,
        step=5
    )

    if len(data) == 0:
        return Response(prometheus_client.generate_latest(), mimetype=CONTENT_TYPE_LATEST)

    timeseries = data[0].get("values")
    timeseries = pd.DataFrame(timeseries)
    timeseries[1] = pd.to_numeric(timeseries[1])
    
    lib = r.library("AnomalyDetection")
    with localconverter(ro.default_converter + pandas2ri.converter):
        R_df = ro.conversion.py2rpy(timeseries[1])
        anom_detect = r['ad_vec']
        res = anom_detect(R_df, max_anoms = 0.02, period=1800, direction = "both")

    anomaly = 0
    if len(res) == 0:
        ANOMALY_GAUGE.labels(value_type="anomaly").set(anomaly)
        return Response(prometheus_client.generate_latest(), mimetype=CONTENT_TYPE_LATEST)

    # check if last anomaly index is in the last datapoints of tested dataset
    index_last_anomaly = int(res.tail(1).iloc[0]['index']) - 1
    last_indices_dataset = timeseries.tail(20).index.values.tolist()

    
    if index_last_anomaly in last_indices_dataset:
        anomaly = 1

    ANOMALY_GAUGE.labels(value_type="anomaly").set(anomaly)

    return Response(prometheus_client.generate_latest(), mimetype=CONTENT_TYPE_LATEST)
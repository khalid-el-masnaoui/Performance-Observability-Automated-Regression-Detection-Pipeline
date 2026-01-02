from flask import Flask, request, jsonify
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter, A3
import os
import datetime
import json

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

app = Flask(__name__)

BASELINE_BASE_DIR = "/reports/baselines"
REGRESSION_BASE_DIR = "/reports/regressions"


BASELINE_DIR = f"{BASELINE_BASE_DIR}/baselines"
HISTORY_DIR = f"{BASELINE_BASE_DIR}/history"
CHART_DIR = f"{REGRESSION_BASE_DIR}/charts"

REGRESSION_DIR = f"{REGRESSION_BASE_DIR}/regressions"
REGRESSION_HISTORY_DIR = f"{REGRESSION_BASE_DIR}/history"
REGRESSION_CHART_DIR = f"{REGRESSION_BASE_DIR}/charts"

os.makedirs(BASELINE_DIR, exist_ok=True)
os.makedirs(HISTORY_DIR, exist_ok=True)
os.makedirs(CHART_DIR, exist_ok=True)

os.makedirs(REGRESSION_DIR, exist_ok=True)
os.makedirs(REGRESSION_HISTORY_DIR, exist_ok=True)
os.makedirs(REGRESSION_CHART_DIR, exist_ok=True)

# ---------------------------------------------------
# Format Numbers
# ---------------------------------------------------
def fmt(value):

    try:
        return f"{float(value):.4f}"
    except:
        return "0.0000"

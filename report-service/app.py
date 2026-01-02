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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

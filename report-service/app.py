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
CHART_DIR = f"{BASELINE_BASE_DIR}/charts"

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

# ---------------------------------------------------
# Format Latency in ms
# ---------------------------------------------------
def fmt_ms(value):
    return f"{float(value)*1000:.2f} ms"

# ---------------------------------------------------
# Save Baseline History
# ---------------------------------------------------
def save_history(route, metrics):

    safe_route = route.replace("/", "_")

    history_file = os.path.join(
        HISTORY_DIR,
        f"{safe_route}.json"
    )

    history = []

    if os.path.exists(history_file):
        with open(history_file, "r") as f:
            history = json.load(f)

    history.append({
        "timestamp": datetime.datetime.now().isoformat(),
        "p95": metrics["p95"],
        "p99": metrics["p99"],
        "avg": metrics["avg"],
        "error_rate": metrics["error_rate"],
        "max_latency": metrics["max_latency"],
        "throughput": metrics["throughput"]
    })

    with open(history_file, "w") as f:
        json.dump(history, f, indent=2)

    return history


# ---------------------------------------------------
# Generate Baseline Trend Chart (P95)
# ---------------------------------------------------
def generate_chart(route, history):

    df = pd.DataFrame(history)

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    safe_route = route.replace("/", "_")

    chart_path = os.path.join(
        CHART_DIR,
        f"{safe_route}_{timestamp}.png"
    )

    plt.figure(figsize=(10, 5))

    plt.plot(df["timestamp"], df["p95"], marker="o")

    plt.title(f"P95 Trend — {route}")

    plt.xlabel("Time")
    plt.ylabel("Latency (seconds)")

    plt.xticks(rotation=45)

    plt.tight_layout()

    plt.savefig(chart_path)

    plt.close()

    return chart_path


# ---------------------------------------------------
# Save Regression History
# ---------------------------------------------------
def save_regression_history(route, payload):

    safe_route = route.replace("/", "_")

    path = os.path.join(
        REGRESSION_HISTORY_DIR,
        f"{safe_route}.json"
    )

    history = []

    if os.path.exists(path):
        with open(path, "r") as f:
            history = json.load(f)

    history.append(payload)

    with open(path, "w") as f:
        json.dump(history, f, indent=2)

    return history

# ---------------------------------------------------
# Generate Regression Trend Chart (P95)
# ---------------------------------------------------
def generate_regression_chart(route, history):

    df = pd.DataFrame(history)

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    chart_path = os.path.join(
        REGRESSION_CHART_DIR,
        f"regression_{route.replace('/', '_')}_{timestamp}.png"
    )

    plt.figure(figsize=(10, 5))

    plt.plot(
        df["timestamp"],
        df["increase_percent"],
        marker="o"
    )

    plt.title(f"Regression Trend (P95) — {route}")

    plt.ylabel("Increase %")

    plt.xticks(rotation=45)

    plt.tight_layout()

    plt.savefig(chart_path)

    plt.close()

    return chart_path

# ---------------------------------------------------
# Generate Baseline PDF
# ---------------------------------------------------
@app.route("/generate-baseline", methods=["POST"])
def generate_baseline():

    data = request.json

    route = data.get("route")
    p95 = float(data.get("p95"))
    p99 = float(data.get("p99", 0))
    avg = float(data.get("avg", 0))
    error_rate = float(data.get("error_rate", 0))
    max_latency = float(data.get("max_latency", 0))
    throughput = float(data.get("throughput", 0))

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    safe_route = route.replace("/", "_")

    filename = f"{safe_route}_{timestamp}.pdf"

    filepath = os.path.join(BASELINE_DIR, filename)

    # ---------------------------------------------
    # Save historical trend
    # ---------------------------------------------
    history = save_history(route, {
        "p95": p95,
        "p99": p99,
        "avg": avg,
        "error_rate": error_rate,
        "max_latency": max_latency,
        "throughput": throughput
    })

    # ---------------------------------------------
    # Generate chart
    # ---------------------------------------------
    chart_path = generate_chart(route, history)

    # ---------------------------------------------
    # PDF
    # ---------------------------------------------
    doc = SimpleDocTemplate(filepath, pagesize=A3)

    styles = getSampleStyleSheet()

    elements = []

    # ---------------------------------------------
    # Title
    # ---------------------------------------------
    elements.append(
        Paragraph(f"<b>Baseline Report</b>", styles["Title"])
    )

    elements.append(Spacer(1, 20))

    # ---------------------------------------------
    # Summary Table
    # ---------------------------------------------
    table_data = [
        ["Metric", "Value"],
        ["Route", route],
        ["P95", f"{fmt_ms(p95)}"],
        ["P99", f"{fmt_ms(p99)}"],
        ["Average", f"{fmt_ms(avg)}"],
        ["Error Rate", fmt(error_rate)],
        ["Max Latency", fmt_ms(max_latency)],
        ["Throughput", fmt(throughput)],
        ["Generated", timestamp],
        ["Samples", str(len(history))]
    ]

    table = Table(table_data, colWidths=[150, 300])

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))

    elements.append(table)

    elements.append(Spacer(1, 30))

    # ---------------------------------------------
    # Trend chart
    # ---------------------------------------------

    elements.append(
        Paragraph(
            "<b>P95 Historical Trend</b>",
            styles["Heading2"]
        )
    )

    elements.append(Spacer(1, 10))

    elements.append(
        Image(chart_path, width=500, height=250)
    )

    elements.append(Spacer(1, 20))

    # ---------------------------------------------
    # Historical entries
    # ---------------------------------------------

    elements.append(
        Paragraph(
            "<b>Historical Baselines</b>",
            styles["Heading2"]
        )
    )

    history_table = [["Timestamp", "P95", "P99", "Average", "Error Rate", "Max Latency", "Throughput"]]

    for entry in history[-10:]:
        history_table.append([
            entry["timestamp"],
            f"{fmt_ms(entry['p95'])}",
            f"{fmt_ms(entry['p99'])}",
            f"{fmt_ms(entry['avg'])}",
            f"{fmt(entry['error_rate'])}",
            f"{fmt_ms(entry['max_latency'])}",
            f"{fmt(entry['throughput'])}"
        ])

    hist_table = Table(history_table, colWidths=[170, 75, 75, 75, 75, 90, 75])

    hist_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))

    elements.append(hist_table)

    # ---------------------------------------------
    # Build PDF
    # ---------------------------------------------
    doc.build(elements)

    return jsonify({
        "status": "generated",
        "file": filename,
        "history_entries": len(history)

    })


# ---------------------------------------------------
# Generate Regression PDF
# ---------------------------------------------------
@app.route("/generate", methods=["POST"])
def generate():

    data = request.json

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    filename = f"report_{timestamp}.pdf"

    filepath = os.path.join(REGRESSION_DIR, filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A3
    )

    styles = getSampleStyleSheet()

    content = []

    # ------------------------------------------------
    # Title
    # ------------------------------------------------
    content.append(
        Paragraph(
            "Performance Regression Report",
            styles["Title"]
        )
    )

    content.append(Spacer(1, 20))

    content.append(
        Paragraph(
            f"Generated at: {timestamp}",
            styles["Normal"]
        )
    )

    content.append(Spacer(1, 20))

    # ------------------------------------------------
    # Process each route
    # ------------------------------------------------
    for route, metrics in data.items():

        baseline = float(metrics.get("baseline", 0))

        current = metrics.get("current", {})

        current_p95 = float(current.get("p95", 0))


        increase = float(metrics.get("increase", 0) * 100)

        regression = metrics.get("regression", False)

        # --------------------------------------------
        # Store history
        # --------------------------------------------
        history_payload = {
            "timestamp": datetime.datetime.now().isoformat(),
            "route": route,
            "baseline_p95": baseline,
            "current_p95": current_p95,
            "increase_percent": increase,
            "regression": regression,
            "current_metrics": current
        }

        history = save_regression_history(
            route,
            history_payload
        )

        # --------------------------------------------
        # Generate chart
        # --------------------------------------------
        chart_path = generate_regression_chart(
            route,
            history
        )

        # --------------------------------------------
        # Route title
        # --------------------------------------------
        content.append(
            Paragraph(
                f"<b>Route:</b> {route}",
                styles["Heading2"]
            )
        )

        content.append(Spacer(1, 10))

        # --------------------------------------------
        # Summary table
        # --------------------------------------------
        table_data = [
            ["Metric", "Value"],
            ["Baseline p95", fmt_ms(baseline)],
            ["Current p95", fmt_ms(current_p95)],
            ["Increase %", f"{fmt(increase)}%"],
            ["Regression", str(regression)],
            ["History Samples", str(len(history))]
        ]

        table = Table(
            table_data,
            colWidths=[200, 250]
        )

        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ]))

        content.append(table)

        content.append(Spacer(1, 20))

        # --------------------------------------------
        # Trend chart
        # --------------------------------------------
        content.append(
            Paragraph(
                "<b>Regression Trend (P95) History</b>",
                styles["Heading3"]
            )
        )

        content.append(Spacer(1, 10))

        content.append(
            Image(
                chart_path,
                width=500,
                height=250
            )
        )

        content.append(Spacer(1, 20))

        # --------------------------------------------
        # Historical table
        # --------------------------------------------
        content.append(
            Paragraph(
                "<b>Previous Regression Entries</b>",
                styles["Heading3"]
            )
        )

        hist_table_data = [[
            "Timestamp",
            "Baseline",
            "Current",
            "Increase %",
            "P99",
            "AVG",
            "Error Rate",
            "Max Latency",
            "Throughput"
        ]]

        for entry in history[-10:]:

            hist_table_data.append([
                entry["timestamp"],
                fmt_ms(entry["baseline_p95"]),
                fmt_ms(entry["current_p95"]),
                fmt(entry["increase_percent"]),
                fmt_ms(entry["current_metrics"].get("p99", 0)),
                fmt_ms(entry["current_metrics"].get("avg", 0)),
                fmt(entry["current_metrics"].get("error_rate", 0)),
                fmt_ms(entry["current_metrics"].get("max_latency", 0)),
                fmt(entry["current_metrics"].get("throughput", 0))
            ])

        hist_table = Table(
            hist_table_data,
            colWidths=[170, 75, 75, 75, 75, 75, 75, 90, 75]
        )

        hist_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ]))

        content.append(hist_table)

        content.append(Spacer(1, 40))

    # ------------------------------------------------
    # Build PDF
    # ------------------------------------------------
    doc.build(content)

    return jsonify({
        "status": "generated",
        "file": filename,
        "path": filepath
    })

@app.route("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

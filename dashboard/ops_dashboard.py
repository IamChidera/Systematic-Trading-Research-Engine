#!/usr/bin/env python3
"""Streamlit dashboard for paper-live trading operations.

Set PAPER_OPS_ROOT to the folder that contains the paper-live reports and logs.
If it is not set, the dashboard looks for ../top5_ops from this file.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import streamlit as st


DEFAULT_OPS_ROOT = Path(__file__).resolve().parents[2] / "top5_ops"
OPS_ROOT = Path(os.environ.get("PAPER_OPS_ROOT", DEFAULT_OPS_ROOT)).resolve()
REPORT_DIR = OPS_ROOT / "reports"
LOG_DIR = OPS_ROOT / "logs"


def read_json(name: str) -> dict:
    path = REPORT_DIR / name
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def age_minutes(value: str | None) -> float | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    return (now - parsed.astimezone(timezone.utc)).total_seconds() / 60


def metric_value(value: object, default: str = "n/a") -> object:
    return default if value is None else value


def count_items(value: object) -> int:
    if value is None:
        return 0
    if isinstance(value, dict | list):
        return len(value)
    return 0


def report_created_at(report: dict) -> str | None:
    return report.get("created_at") or report.get("finished_at") or report.get("timestamp")


def best_signal(report: dict) -> dict:
    signals = report.get("signals", [])
    if not isinstance(signals, list) or not signals:
        return {}

    scored = [
        item
        for item in signals
        if isinstance(item, dict) and item.get("score") is not None
    ]
    if scored:
        return max(scored, key=lambda item: float(item.get("score") or 0.0))
    return signals[0] if isinstance(signals[0], dict) else {}


def gate_value(report: dict) -> object:
    for key in ("gate_ok", "btc_ok", "active", "eligible", "portfolio_active"):
        if key in report:
            return report.get(key)
    return "n/a"


def why_waiting(report: dict) -> str:
    if count_items(report.get("orders")):
        return "order generated"
    if count_items(report.get("positions")):
        return "position open"
    if count_items(report.get("targets")):
        return "target present"

    signal = best_signal(report)
    if report.get("gate_ok") is False or report.get("btc_ok") is False:
        return f"{report.get('gate_name') or 'gate'} closed"
    if signal:
        symbol = signal.get("symbol", "asset")
        if signal.get("eligible") is False or signal.get("healthy") is False:
            return f"{symbol} not eligible"
        if signal.get("above_ema100") is False or signal.get("above_ema200") is False:
            return f"{symbol} below trend"
        if signal.get("score") is not None:
            return f"best score {float(signal['score']):.2f}, no target"
    return "no target"


def summarize_report(path: Path) -> dict:
    report = json.loads(path.read_text(encoding="utf-8"))
    signal = best_signal(report)
    return {
        "bot": path.name.replace("_latest.json", ""),
        "gate": gate_value(report),
        "equity": report.get("equity") or report.get("paper_equity_normalized"),
        "orders": count_items(report.get("orders")),
        "positions": count_items(report.get("positions")),
        "targets": count_items(report.get("targets")),
        "best_asset": signal.get("symbol"),
        "best_score": signal.get("score"),
        "reason_waiting": why_waiting(report),
        "updated": report_created_at(report),
    }


st.set_page_config(page_title="Paper Trading Ops", layout="wide")
st.title("Paper Trading Operations")
st.caption(f"Reading reports from: {REPORT_DIR}")

heartbeat = read_json("paper_supervisor_heartbeat.json")
portfolio = read_json("portfolio_v3_growth_latest.json")
bot3_core = read_json("bot3_core_latest.json")
bot7 = read_json("bot7_v6_latest.json")
bot10 = read_json("bot10_growth_latest.json")

last_cycle = heartbeat.get("last_cycle_finished_at")
last_cycle_age = age_minutes(last_cycle)
bot3 = portfolio.get("bot3", {})
bot3_display = bot3_core if bot3_core else bot3

top = st.columns(6)
top[0].metric("Supervisor", heartbeat.get("status", "unknown"))
top[1].metric("Cycle", metric_value(heartbeat.get("cycle")))
top[2].metric("Last Cycle Age", "n/a" if last_cycle_age is None else f"{last_cycle_age:.1f} min")
top[3].metric("Portfolio Equity", metric_value(portfolio.get("paper_equity_normalized")))
top[4].metric("Return", f"{portfolio.get('paper_return_pct', 'n/a')}%")
top[5].metric("Bot3 Equity", metric_value(bot3_display.get("equity")))

alerts = portfolio.get("alerts", [])
if alerts:
    st.error("Alerts: " + ", ".join(alerts))
else:
    st.success("No portfolio alerts")

st.subheader("Bot State")
cols = st.columns(3)
with cols[0]:
    st.markdown("**Bot3 Core**")
    st.write("Latest log:", bot3_display.get("latest_log", "unknown"))
    st.write("Equity:", bot3_display.get("equity", "unknown"))
    st.write("Orders:", len(bot3_display.get("orders", [])))
    st.dataframe(pd.DataFrame(bot3_display.get("latest_actions", [])), use_container_width=True)

with cols[1]:
    st.markdown("**Bot7 Rotation**")
    st.write("BTC gate:", bot7.get("btc_ok", "unknown"))
    st.write("Equity:", bot7.get("equity", "unknown"))
    st.write("Orders:", len(bot7.get("orders", [])))
    st.json(bot7.get("positions", {}))

with cols[2]:
    st.markdown("**Bot10 Growth**")
    st.write("BTC gate:", bot10.get("btc_ok", "unknown"))
    st.write("Equity:", bot10.get("equity", "unknown"))
    st.write("Orders:", len(bot10.get("orders", [])))
    st.write("Leaders:", bot10.get("leaders", []))

st.subheader("Supervisor Components")
results = pd.DataFrame(heartbeat.get("results", []))
if not results.empty:
    columns = [column for column in ["name", "ok", "returncode", "started_at", "finished_at"] if column in results]
    st.dataframe(results[columns], use_container_width=True)
else:
    st.info("No supervisor results found.")

st.subheader("Why Nothing Has Fired Yet")
latest_reports = []
if REPORT_DIR.exists():
    for path in sorted(REPORT_DIR.glob("*_latest.json")):
        try:
            latest_reports.append(summarize_report(path))
        except (json.JSONDecodeError, OSError, TypeError, ValueError):
            continue

distance = pd.DataFrame(latest_reports)
if not distance.empty:
    preferred = [
        "bot",
        "gate",
        "equity",
        "orders",
        "positions",
        "targets",
        "best_asset",
        "best_score",
        "reason_waiting",
        "updated",
    ]
    display_distance = distance[preferred].copy()
    display_distance["gate"] = display_distance["gate"].astype(str)
    display_distance["updated"] = display_distance["updated"].astype(str)
    st.dataframe(display_distance, use_container_width=True)
else:
    st.info("No latest bot reports found.")

st.subheader("Bot7 Signals")
signals = pd.DataFrame(bot7.get("signals", []))
if not signals.empty:
    preferred = [
        column
        for column in ["symbol", "price", "score", "mom90", "mom30", "mom7", "healthy"]
        if column in signals
    ]
    st.dataframe(signals[preferred], use_container_width=True)
else:
    st.info("No Bot7 signal report found.")

st.subheader("Recent Logs")
if LOG_DIR.exists():
    recent_logs = sorted(LOG_DIR.glob("*.log"), key=lambda path: path.stat().st_mtime, reverse=True)[:8]
else:
    recent_logs = []

for path in recent_logs:
    with st.expander(path.name):
        text = path.read_text(encoding="utf-8", errors="replace")
        st.code("\n".join(text.splitlines()[-80:]), language="text")

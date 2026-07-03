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
import plotly.express as px
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
    if isinstance(value, (dict, list)):
        return len(value)
    return 0


def as_float(value: object, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default



def arrow_safe_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Make mixed dashboard records safe for Streamlit's Arrow serializer."""
    if df.empty:
        return df
    safe = df.copy()
    for column in safe.columns:
        if safe[column].dtype != "object":
            continue

        def normalize(value: object) -> str:
            if value is None:
                return ""
            if isinstance(value, float) and pd.isna(value):
                return ""
            if isinstance(value, (dict, list, tuple, set)):
                return json.dumps(value, sort_keys=True, default=str)
            return str(value)

        safe[column] = safe[column].map(normalize)
    return safe

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


def plot_equity(history: list | None):
    if not history:
        return None
    df = pd.DataFrame(history)
    if "timestamp" in df.columns and "equity" in df.columns:
        return px.line(df, x="timestamp", y="equity", title="Equity Curve")
    return None


def load_latest_reports() -> pd.DataFrame:
    latest_reports = []
    if REPORT_DIR.exists():
        for path in sorted(REPORT_DIR.glob("*_latest.json")):
            try:
                latest_reports.append(summarize_report(path))
            except (json.JSONDecodeError, OSError, TypeError, ValueError):
                continue
    return pd.DataFrame(latest_reports)


def flatten_seed_results(seed_report: dict) -> pd.DataFrame:
    rows = []
    for result in seed_report.get("results", []):
        bot = result.get("bot")
        if "results" in result:
            for item in result.get("results", []):
                rows.append(
                    {
                        "bot": bot,
                        "symbol": item.get("symbol"),
                        "status": item.get("status"),
                        "notional": item.get("notional"),
                        "format": item.get("format"),
                    }
                )
        elif "seeded" in result:
            for item in result.get("seeded", []):
                rows.append(
                    {
                        "bot": bot,
                        "symbol": item.get("symbol"),
                        "status": "seeded",
                        "notional": item.get("notional"),
                        "format": "native",
                    }
                )
        elif "repaired" in result:
            for item in result.get("repaired", []):
                rows.append(
                    {
                        "bot": bot,
                        "symbol": item.get("symbol"),
                        "status": "repaired",
                        "notional": None,
                        "format": item.get("format"),
                    }
                )
    return pd.DataFrame(rows)


def portfolio_tally(portfolio: dict) -> dict:
    weights = portfolio.get("weights", {})
    rows = []
    calculated = 0.0
    for bot_name, weight in weights.items():
        bot_report = portfolio.get(bot_name, {})
        equity = as_float(bot_report.get("normalized_equity", bot_report.get("equity")))
        weight_float = as_float(weight)
        contribution = equity * weight_float
        calculated += contribution
        rows.append(
            {
                "bot": bot_name,
                "weight": weight_float,
                "normalized_equity": equity,
                "weighted_contribution": contribution,
            }
        )
    reported = as_float(portfolio.get("paper_equity_normalized"))
    return {
        "reported": reported,
        "calculated": calculated,
        "difference": reported - calculated,
        "rows": rows,
    }


def show_bot_snapshot(name: str, report: dict, gate_label: str = "Gate") -> None:
    st.markdown(f"**{name}**")
    st.write(gate_label + ":", report.get("btc_ok", report.get("gate_ok", "unknown")))
    st.write("Equity:", report.get("equity", report.get("paper_equity_normalized", "unknown")))
    st.write("Orders:", count_items(report.get("orders")))
    if report.get("positions"):
        st.json(report.get("positions", {}))


st.set_page_config(page_title="Trading Ops Dashboard", layout="wide")
st.title("Systematic Trading Ops Dashboard")
st.caption(f"OPS root: {OPS_ROOT}")

with st.sidebar:
    st.subheader("Controls")
    st.write(f"Reports: `{REPORT_DIR}`")
    st.write(f"Logs: `{LOG_DIR}`")
    if st.button("Refresh Data", use_container_width=True):
        st.rerun()
    st.info("Set PAPER_OPS_ROOT for a custom report location.")

heartbeat = read_json("paper_supervisor_heartbeat.json")
portfolio = read_json("portfolio_v3_growth_latest.json")
bot3_core = read_json("bot3_core_latest.json")
bot7 = read_json("bot7_v6_latest.json")
bot10 = read_json("bot10_growth_latest.json")
bot26 = read_json("bot26_qqq_substitute_latest.json")
seed_report = read_json("seed_active_inventory_latest.json")
radar = read_json("signal_proximity_radar_latest.json")

last_cycle = heartbeat.get("last_cycle_finished_at")
last_cycle_age = age_minutes(last_cycle)
bot3 = portfolio.get("bot3", {})
bot3_display = bot3_core if bot3_core else bot3
distance = load_latest_reports()
tally = portfolio_tally(portfolio)

top = st.columns(7)
top[0].metric("Supervisor", heartbeat.get("status", "unknown"))
top[1].metric("Cycle", metric_value(heartbeat.get("cycle")))
top[2].metric("Last Cycle Age", "n/a" if last_cycle_age is None else f"{last_cycle_age:.1f} min")
top[3].metric("Portfolio Equity", metric_value(portfolio.get("paper_equity_normalized")))
top[4].metric("Return", f"{portfolio.get('paper_return_pct', 'n/a')}%")
top[5].metric("Bot3 Equity", metric_value(bot3_display.get("equity")))
top[6].metric("Tally Diff", f"{tally['difference']:.4f}")

alerts = portfolio.get("alerts", [])
if alerts:
    st.error("Alerts: " + ", ".join(alerts))
else:
    st.success("No portfolio alerts")

if abs(tally["difference"]) > 0.10:
    st.warning(
        "Portfolio tally mismatch: "
        f"reported={tally['reported']:.2f}, calculated={tally['calculated']:.2f}, "
        f"difference={tally['difference']:.4f}"
    )

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["Overview & Bots", "Signal Radar", "Why No Trades?", "Signals & Positions", "Charts & History", "Logs"]
)

with tab1:
    st.subheader("Bot State")
    cols = st.columns(4)
    with cols[0]:
        st.markdown("**Bot3 Core**")
        st.write("Latest log:", bot3_display.get("latest_log", "unknown"))
        st.write("Equity:", bot3_display.get("equity", "unknown"))
        st.write("Orders:", count_items(bot3_display.get("orders")))
    with cols[1]:
        show_bot_snapshot("Bot7 Rotation", bot7, "BTC gate")
    with cols[2]:
        show_bot_snapshot("Bot10 Growth", bot10, "BTC gate")
        st.write("Leaders:", bot10.get("leaders", []))
    with cols[3]:
        show_bot_snapshot("Bot26 QQQ Substitute", bot26, "Gate")

    actions = pd.DataFrame(bot3_display.get("latest_actions", []))
    if not actions.empty:
        st.subheader("Bot3 Latest Actions")
        st.dataframe(arrow_safe_dataframe(actions), use_container_width=True)

    st.subheader("Portfolio Tally")
    tally_rows = pd.DataFrame(tally["rows"])
    if not tally_rows.empty:
        st.dataframe(arrow_safe_dataframe(tally_rows), use_container_width=True)
    else:
        st.info("No portfolio weights found.")

    st.subheader("Seeded Inventory")
    seed_rows = flatten_seed_results(seed_report)
    if not seed_rows.empty:
        st.caption(f"Last seed action: {seed_report.get('created_at', 'unknown')}")
        st.dataframe(arrow_safe_dataframe(seed_rows), use_container_width=True)
    else:
        st.info("No seeded inventory report found.")

    st.subheader("Supervisor Components")
    results = pd.DataFrame(heartbeat.get("results", []))
    if not results.empty:
        columns = [
            column
            for column in ["name", "ok", "returncode", "started_at", "finished_at"]
            if column in results
        ]
        st.dataframe(arrow_safe_dataframe(results[columns]), use_container_width=True)
    else:
        st.info("No supervisor results found.")

with tab2:
    st.subheader("Signal Proximity Radar")
    st.caption("Heuristic operations score. It explains live-paper silence; it is not a trading signal.")

    radar_age = age_minutes(radar.get("created_at"))
    radar_cols = st.columns(6)
    radar_cols[0].metric("Radar Age", "n/a" if radar_age is None else f"{radar_age:.1f} min")
    radar_cols[1].metric("Reports Checked", metric_value(radar.get("reports_checked")))
    radar_cols[2].metric("Orders", metric_value(radar.get("orders_detected")))
    radar_cols[3].metric("Holding Bots", metric_value(radar.get("holding_bots")))
    radar_cols[4].metric("Waiting Bots", metric_value(radar.get("waiting_bots")))
    radar_cols[5].metric("Stale Reports", metric_value(radar.get("stale_reports")))

    closest = radar.get("closest_waiting", {})
    if closest:
        st.info(
            "Closest waiting: "
            f"{closest.get('bot', 'unknown')} / {closest.get('best_asset', 'n/a')} / "
            f"{closest.get('proximity_pct', 'n/a')}% proximity. "
            f"Blocker: {closest.get('blocker', 'n/a')}"
        )
    else:
        st.warning("No fresh signal-bearing waiting bot is currently close to firing.")

    radar_rows = pd.DataFrame(radar.get("top_rows", []))
    if not radar_rows.empty:
        columns = [
            column
            for column in [
                "bot",
                "status",
                "proximity_pct",
                "gate",
                "best_asset",
                "best_score",
                "blocker",
                "age_minutes",
                "stale",
                "signal_bearing",
            ]
            if column in radar_rows
        ]
        st.dataframe(arrow_safe_dataframe(radar_rows[columns]), use_container_width=True)

        chart_rows = radar_rows.copy()
        chart_rows["proximity_pct"] = pd.to_numeric(chart_rows["proximity_pct"], errors="coerce")
        chart_rows = chart_rows.dropna(subset=["proximity_pct"])
        if not chart_rows.empty:
            st.plotly_chart(
                px.bar(
                    chart_rows,
                    x="bot",
                    y="proximity_pct",
                    color="status",
                    title="Signal Proximity by Bot",
                ),
                use_container_width=True,
            )
    else:
        st.info("No signal proximity report found yet. The supervisor will create one on the next cycle.")

with tab3:
    st.subheader("Why Nothing Has Fired Yet")
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
        st.dataframe(arrow_safe_dataframe(display_distance), use_container_width=True)
    else:
        st.info("No latest bot reports found.")

with tab4:
    st.subheader("Bot7 Signals")
    signals = pd.DataFrame(bot7.get("signals", []))
    if not signals.empty:
        preferred = [
            column
            for column in ["symbol", "price", "score", "mom90", "mom30", "mom7", "healthy"]
            if column in signals
        ]
        st.dataframe(arrow_safe_dataframe(signals[preferred]), use_container_width=True)
    else:
        st.info("No Bot7 signal report found.")

    st.subheader("Open Positions")
    position_rows = []
    report_map = {"bot3": bot3_display}
    if REPORT_DIR.exists():
        for path in sorted(REPORT_DIR.glob("*_latest.json")):
            if path.name.startswith(("seed_active_inventory", "gate_audit")):
                continue
            try:
                report_map[path.name.replace("_latest.json", "")] = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue

    for bot_name, report in report_map.items():
        positions = report.get("positions", {})
        if isinstance(positions, dict):
            for symbol, position in positions.items():
                row = {"bot": bot_name, "symbol": symbol}
                if isinstance(position, dict):
                    row.update(position)
                else:
                    row["position"] = position
                position_rows.append(row)
    if position_rows:
        st.dataframe(arrow_safe_dataframe(pd.DataFrame(position_rows)), use_container_width=True)
    else:
        st.info("No open positions reported.")

with tab5:
    st.subheader("Equity & Performance Charts")
    eq_fig = plot_equity(portfolio.get("equity_history"))
    if eq_fig:
        st.plotly_chart(eq_fig, use_container_width=True)
    else:
        st.info("No equity history available in reports yet.")

    if not distance.empty and "equity" in distance:
        chart_df = distance.dropna(subset=["equity"]).copy()
        if not chart_df.empty:
            chart_df["equity"] = pd.to_numeric(chart_df["equity"], errors="coerce")
            chart_df = chart_df.dropna(subset=["equity"])
        if not chart_df.empty:
            st.plotly_chart(
                px.bar(chart_df, x="bot", y="equity", title="Latest Equity by Bot"),
                use_container_width=True,
            )

    if not distance.empty:
        activity = distance[["bot", "orders", "positions", "targets"]].melt(
            id_vars="bot",
            var_name="type",
            value_name="count",
        )
        st.plotly_chart(
            px.bar(activity, x="bot", y="count", color="type", barmode="group", title="Orders, Positions, and Targets"),
            use_container_width=True,
        )

with tab6:
    st.subheader("Recent Logs")
    if LOG_DIR.exists():
        recent_logs = sorted(LOG_DIR.glob("*.log"), key=lambda path: path.stat().st_mtime, reverse=True)[:8]
    else:
        recent_logs = []

    for path in recent_logs:
        with st.expander(path.name):
            text = path.read_text(encoding="utf-8", errors="replace")
            st.code("\n".join(text.splitlines()[-80:]), language="text")






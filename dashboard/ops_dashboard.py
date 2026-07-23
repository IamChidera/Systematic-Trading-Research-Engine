#!/usr/bin/env python3
"""Streamlit dashboard for paper-live trading operations.

Set PAPER_OPS_ROOT to the folder that contains the paper-live reports and logs.
If it is not set, the dashboard looks for ../top5_ops from this file.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


DEFAULT_OPS_ROOT = Path(__file__).resolve().parents[2] / "top5_ops"
OPS_ROOT = Path(os.environ.get("PAPER_OPS_ROOT", DEFAULT_OPS_ROOT)).resolve()
REPORT_DIR = OPS_ROOT / "reports"
LOG_DIR = OPS_ROOT / "logs"
DEMO_MODE = os.environ.get("TRADING_DASHBOARD_DEMO", "").strip().lower() in {"1", "true", "yes"}
LEGACY_REPORT_PREFIXES = ("bot10_det_ret60_damage", "bot10_det_sol_momentum")

BOT_NAME_ALIASES = {
    "bot16": "bot16_alt_snapback",
    "bot20": "bot20_alt_recovery",
    "bot21_v4": "bot21_alt_cohorts",
    "bot22": "bot22_dual_momentum",
    "bot24": "bot24_vol_adjusted",
    "bot31_candlestick_trend_volume": "bot31_candlestick",
    "bot39_bot7_no_wait": "bot39_no_wait",
    "bot81_crypto_liquid_winners": "bot81_liquid_winners",
    "bot92_daily_liquidity_confirmed": "bot92_daily_liquidity",
    "bot92_monthly_liquidity_confirmed": "bot92_monthly_liquidity",
    "bot97_30d_crypto_liquid_winners": "bot97_liquid_winners_30d",
}

VARIANT_BOT_ALIASES = {
    ("paper_trades_bot10_determinants.db", "momentum"): "bot10_det_momentum",
    ("paper_trades_bot10_determinants.db", "volume"): "bot10_det_volume",
    ("paper_trades_bot10_determinants.db", "ret60_volume"): "bot10_det_ret60_volume",
    ("paper_trades_bot10_determinants.db", "sol_momentum"): "bot10_det_sol_momentum",
    ("paper_trades_bot10_sol_momentum_shadow.db", "sol_momentum_shadow"): "bot10_sol_momentum_shadow",
}

def is_legacy_report(path: Path) -> bool:
    name = path.name.replace("_latest.json", "")
    return name.startswith(LEGACY_REPORT_PREFIXES)

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


def display_status(value: object, default: str = "Unknown") -> str:
    if value is None or str(value).strip() == "":
        return default
    aliases = {
        "healthy_no_ticket": "No ticket",
        "no_action_required": "Aligned",
        "no_orders_to_dry_run": "No orders",
        "paper_shadow_no_eligible_components": "Waiting for signal",
        "kraken_dry_run_targets_ready": "Dry-run ready",
    }
    text = str(value).strip()
    return aliases.get(text, text.replace("_", " ").strip().title())


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


def canonical_bot_name(name: object) -> str:
    return BOT_NAME_ALIASES.get(str(name), str(name))


def read_csv_report(name: str) -> pd.DataFrame:
    path = REPORT_DIR / name
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except (OSError, ValueError, pd.errors.ParserError):
        return pd.DataFrame()


def positions_to_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return ", ".join(str(key) for key, item in value.items() if item not in ({}, 0, 0.0, None))
    if isinstance(value, list):
        rows = []
        for item in value:
            if isinstance(item, dict):
                rows.append(str(item.get("symbol") or item.get("name") or item))
            else:
                rows.append(str(item))
        return ", ".join(row for row in rows if row)
    return str(value)


def dashboard_verdict(row: dict) -> str:
    name = row.get("name")
    role = row.get("role")
    bucket = row.get("bucket")
    return_pct = as_float(row.get("return_pct"))
    status = row.get("status")
    if name == "bot3_core":
        return "core: presentable, still needs longer live audit"
    if bucket == "quarantine" or return_pct <= -2.5:
        return "quarantine: do not sell/promote"
    if role == "core_variant" and return_pct > 0:
        return "core variant: watchlist"
    if return_pct > 0.5:
        return "research candidate"
    if status == "positioned":
        return "risk watch"
    return "observe"


def add_trade_stat(stats: dict, bot: str, when: object, order: dict) -> None:
    bot = canonical_bot_name(bot)
    row = stats.setdefault(bot, {"hist_orders": 0, "buys": 0, "sells": 0, "realized_pnl": 0.0, "last_order_at": "", "last_order": ""})
    action = str(order.get("action") or order.get("side") or order.get("type") or "").upper()
    row["hist_orders"] += 1
    if "BUY" in action:
        row["buys"] += 1
    if "SELL" in action or "EXIT" in action:
        row["sells"] += 1
    if order.get("pnl") is not None:
        try:
            row["realized_pnl"] += float(order.get("pnl"))
        except (TypeError, ValueError):
            pass
    when_text = str(when or "")
    if when_text and when_text > row["last_order_at"]:
        symbol = order.get("symbol", "")
        pnl = order.get("pnl")
        suffix = ""
        if isinstance(pnl, (int, float)):
            suffix = f" pnl={pnl:.2f}"
        row["last_order_at"] = when_text
        row["last_order"] = f"{action} {symbol}{suffix}".strip()


def bot_name_from_db(db_name: str) -> str:
    return canonical_bot_name(db_name.replace("paper_trades_", "").replace(".db", ""))


@st.cache_data(ttl=45, show_spinner=False)
def load_trade_stats(ops_root: str, bot3_db_path: str | None = None) -> dict:
    root = Path(ops_root)
    stats: dict[str, dict] = {}

    def scan_db(db_path: Path, forced_bot: str | None = None) -> None:
        if not db_path.exists():
            return
        try:
            con = sqlite3.connect(db_path)
            cur = con.cursor()
            tables = [item[0] for item in cur.execute("select name from sqlite_master where type='table'").fetchall()]
            if "events" in tables:
                cols = [item[1] for item in cur.execute("pragma table_info(events)").fetchall()]
                if "payload" in cols:
                    time_col = "created_at" if "created_at" in cols else ("timestamp" if "timestamp" in cols else cols[0])
                    id_col = "id" if "id" in cols else "rowid"
                    variant_col = "variant" if "variant" in cols else None
                    select = f"select {time_col}, payload" + (f", {variant_col}" if variant_col else "") + f" from events order by {id_col} asc"
                    for event in cur.execute(select):
                        when = event[0]
                        payload = event[1]
                        variant = event[2] if variant_col else None
                        try:
                            parsed = json.loads(payload)
                        except (TypeError, json.JSONDecodeError):
                            continue
                        bot = forced_bot or VARIANT_BOT_ALIASES.get((db_path.name, variant), bot_name_from_db(db_path.name))
                        for order in parsed.get("orders") or []:
                            if isinstance(order, dict):
                                add_trade_stat(stats, bot, when, order)
            if "paper_logs" in tables:
                cols = [item[1] for item in cur.execute("pragma table_info(paper_logs)").fetchall()]
                if "action" in cols:
                    time_col = "timestamp" if "timestamp" in cols else cols[0]
                    for when, symbol, action, pnl in cur.execute(
                        f"select {time_col}, symbol, action, pnl from paper_logs "
                        "where lower(action) not in ('hold', '') order by rowid asc"
                    ):
                        add_trade_stat(stats, forced_bot or bot_name_from_db(db_path.name), when, {"action": action, "symbol": symbol, "pnl": pnl})
        except sqlite3.Error:
            return
        finally:
            try:
                con.close()
            except Exception:
                pass

    for db_path in root.glob("paper_trades*.db"):
        scan_db(db_path)
    if bot3_db_path:
        scan_db(Path(bot3_db_path), forced_bot="bot3_core")

    for row in stats.values():
        row["realized_pnl"] = round(float(row.get("realized_pnl", 0.0)), 2)
    return stats


def build_system_status_table(scorecard: dict, proximity: pd.DataFrame, trade_stats: dict) -> pd.DataFrame:
    rows = scorecard.get("leaderboard", []) if isinstance(scorecard, dict) else []
    if not rows:
        return pd.DataFrame()
    proximity_map = {}
    if not proximity.empty and "bot" in proximity.columns:
        for _, item in proximity.iterrows():
            proximity_map[canonical_bot_name(item.get("bot"))] = item.to_dict()

    output = []
    for row in rows:
        bot = row.get("name")
        prox = proximity_map.get(bot, {})
        trades = trade_stats.get(bot, {})
        output.append(
            {
                "rank": row.get("rank"),
                "bot": bot,
                "mode": "tiny-live + paper" if bot == "bot3_core" else "paper/shadow",
                "role": row.get("role"),
                "bucket": row.get("bucket"),
                "status": row.get("status"),
                "equity": row.get("equity"),
                "return_pct": row.get("return_pct"),
                "positions": positions_to_text(row.get("positions")),
                "blocker": prox.get("blocker") or ("position open" if row.get("position_count") else "no explicit blocker"),
                "best_asset": prox.get("best_asset") or row.get("top_signal"),
                "proximity_pct": prox.get("proximity_pct"),
                "hist_orders": trades.get("hist_orders", 0),
                "buys": trades.get("buys", 0),
                "sells": trades.get("sells", 0),
                "realized_pnl": trades.get("realized_pnl", 0.0),
                "last_order": trades.get("last_order", ""),
                "age_minutes": row.get("age_minutes"),
                "dashboard_verdict": dashboard_verdict(row),
            }
        )
    return pd.DataFrame(output)


def build_promoted_system_status_table(bot3: dict, bot80: dict, defensive_drift: dict, trade_stats: dict) -> pd.DataFrame:
    """Build the primary operating table without archived candidate clutter."""
    rows = []
    for rank, name, report, mode, role, bucket in (
        (1, "bot3_core", bot3, "tiny-live + paper", "core BTC engine", "promoted_core"),
        (
            2,
            "bot80_kraken_gbp",
            bot80,
            "Kraken GBP dry-run",
            "turnover-penalized alt sleeve",
            "promoted_dry_run",
        ),
        (
            3,
            "bot31_defensive_drift",
            defensive_drift,
            "Kraken GBP dry-run",
            "credit-permitted defensive alt sleeve",
            "promoted_dry_run",
        ),
    ):
        positions = report.get("positions") if isinstance(report.get("positions"), dict) else {}
        signals = report.get("signals") if isinstance(report.get("signals"), list) else []
        top_signal = signals[0] if signals and isinstance(signals[0], dict) else {}
        stats = trade_stats.get(name, {})
        if positions:
            status = "positioned"
            blocker = "position open; strategy remains free to resize or exit"
        elif name in {"bot80_kraken_gbp", "bot31_defensive_drift"} and report.get("gate_ok") is False:
            status = "cash_gate_closed"
            blocker = "strategy permission gate is closed"
        else:
            status = "cash_waiting"
            blocker = "no approved target this cycle"
        equity = as_float(report.get("equity"), 10_000.0)
        rows.append(
            {
                "rank": rank,
                "bot": name,
                "mode": mode,
                "role": role,
                "bucket": bucket,
                "status": status,
                "equity": equity,
                "return_pct": round((equity / 10_000.0 - 1.0) * 100.0, 4),
                "positions": positions_to_text(positions),
                "hist_orders": stats.get("hist_orders", 0),
                "buys": stats.get("buys", 0),
                "sells": stats.get("sells", 0),
                "realized_pnl": stats.get("realized_pnl", 0.0),
                "last_order": stats.get("last_order", ""),
                "blocker": blocker,
                "best_asset": top_signal.get("symbol"),
                "proximity_pct": None,
                "dashboard_verdict": "OPERATING" if rank == 1 else "PROMOTED DRY-RUN",
            }
        )
    return pd.DataFrame(rows)

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
            if path.name.startswith(("activation_audit", "activation_shadow")) or is_legacy_report(path):
                continue
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
st.caption("Presentation-safe operating snapshot" if DEMO_MODE else f"OPS root: {OPS_ROOT}")

with st.sidebar:
    st.subheader("Controls")
    if DEMO_MODE:
        st.write("Data source: fixed operating reports")
        st.caption("Private paths and live account values are masked.")
    else:
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
activation = read_json("activation_audit_latest.json")
activation_shadow = read_json("activation_shadow_latest.json")
scorecard = read_json("independent_engine_scorecard_latest.json")
graduation_board = read_json("candidate_graduation_board_v1_latest.json")
daily_journal = read_json("daily_journal_latest.json")
paper_trade_ledger = read_json("paper_trade_ledger_latest.json")
risk_report = read_json("risk_manager_latest.json")
kraken_live_state = read_json("kraken_live_state_latest.json")
bot3_autopilot = read_json("bot3_live_autopilot_latest.json")
portfolio_live_autopilot = read_json("kraken_portfolio_live_autopilot_v1_latest.json")
bot80_autopilot = read_json("bot80_live_autopilot_latest.json")
bot80_live_manager = read_json("bot80_live_account_manager_latest.json")
bot80_paper = read_json("bot80_kraken_gbp_latest.json")
bot31_defensive_drift = read_json("bot31_defensive_drift_latest.json")
bot80_phase3_shadow = read_json("bot80_phase3_locked_shadow_latest.json")
bot3_order_plan = read_json("bot3_live_order_plan_latest.json")
bot3_reconciliation = read_json("bot3_kraken_reconciliation_latest.json")
kraken_dry_run = read_json("kraken_dry_run_latest.json")
tiny_live_readiness = read_json("tiny_live_readiness_latest.json")
supervisor_health = read_json("supervisor_health_audit_latest.json")
growth_sleeve = read_json("growth_sleeve_v1_latest.json")
idle_sleeve = read_json("idle_sleeve_v1_latest.json")
idle_signal = read_json("idle_family_signal_builder_v1_latest.json")
sleeve_brakes = read_json("sleeve_drawdown_brakes_v1_latest.json")
unified_orchestrator = read_json("unified_portfolio_orchestrator_v1_latest.json")
promotion_portfolio = read_json("kraken_promotion_portfolio_v1_latest.json")
promotion_dry_run = read_json("kraken_promotion_dry_run_v1_latest.json")
portfolio_live_reconciliation = read_json("kraken_portfolio_live_reconciler_v1_latest.json")
dry_run_ticket_ledger = read_json("unified_dry_run_ticket_ledger_latest.json")
dry_run_quality = read_json("unified_dry_run_quality_latest.json")
gold_shadow = read_json("gold_shadow_v1_latest.json")
gold_v10_shadow = read_json("gold_v10_compression_shadow_latest.json")
bot40_signal_shadow = read_json("bot40_telegram_signals_latest.json")
bot40b_multi_provider = read_json("bot40b_multi_provider_latest.json")
proximity_csv = read_csv_report("signal_proximity_radar_latest.csv")
trade_stats = load_trade_stats(str(OPS_ROOT), str(bot3_core.get("db_path") or ""))
system_status = build_promoted_system_status_table(bot3_core, bot80_paper, bot31_defensive_drift, trade_stats)

last_cycle = heartbeat.get("last_cycle_finished_at")
last_cycle_age = age_minutes(last_cycle)
bot3 = portfolio.get("bot3", {})
bot3_display = bot3_core if bot3_core else bot3
distance = load_latest_reports()
tally = portfolio_tally(portfolio)

top = st.columns(4)
top[0].metric("Supervisor", display_status(heartbeat.get("status")))
top[1].metric("Cycle", metric_value(heartbeat.get("cycle")))
top[2].metric("Last Cycle Age", "n/a" if last_cycle_age is None else f"{last_cycle_age:.1f} min")
top[3].metric("Virtual Portfolio", f"GBP {as_float(promotion_dry_run.get('post_trade_equity_gbp')):.2f}")
dry_pnl = as_float(promotion_dry_run.get("post_trade_equity_gbp")) - as_float(promotion_dry_run.get("starting_capital_gbp"))
top_detail = st.columns(4)
top_detail[0].metric("Dry-Run P&L", f"GBP {dry_pnl:.2f}")
top_detail[1].metric("Bot3 Equity", f"{as_float(bot3_display.get('equity')):,.2f}")
top_detail[2].metric("Bot80 Gate", "Open" if bot80_paper.get("gate_ok") else "Cash")
top_detail[3].metric("Drift Gate", "Open" if bot31_defensive_drift.get("gate_ok") else "Cash")

alerts = promotion_portfolio.get("alerts", [])
if alerts:
    st.error("Alerts: " + ", ".join(alerts))
else:
    st.success("Promoted portfolio sources and weights are healthy")

health_windows = {item.get("hours"): item for item in supervisor_health.get("windows", [])}
health_24h = health_windows.get(24, {})
health_7d = health_windows.get(168, {})

tab0, tabg, tabp, tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
    [
        "System Status",
        "Gold Shadow",
        "Kraken Portfolio",
        "Overview & Bots",
        "Signal Radar",
        "Activation Audit",
        "Why No Trades?",
        "Signals & Positions",
        "Charts & History",
        "Logs",
    ]
)


with tab0:
    st.subheader("System Status And Commercial Readiness")
    st.caption("Real tiny-live value, promoted dry-run NAV, forward evidence, and historical archives are kept separate. This page is read-only.")

    journal_risk = daily_journal.get("risk", {}) if isinstance(daily_journal, dict) else {}
    journal_execution = daily_journal.get("execution", {}) if isinstance(daily_journal, dict) else {}
    live_cols = st.columns(4)
    live_value = "MASKED" if DEMO_MODE else f"GBP {as_float(kraken_live_state.get('equity_estimate_quote')):.2f}"
    live_cols[0].metric("Kraken Live Value", live_value)
    live_cols[1].metric("Promoted Dry-Run NAV", f"{as_float(journal_risk.get('total_equity_observed', risk_report.get('total_equity_observed'))):,.2f}")
    live_cols[2].metric("Open Notional", f"{as_float(journal_risk.get('total_open_notional', risk_report.get('total_open_notional'))):,.2f}")
    live_cols[3].metric("Gross Exposure", f"{as_float(journal_risk.get('gross_exposure_pct', risk_report.get('gross_exposure_pct'))) * 100:.1f}%")
    execution_cols = st.columns(4)
    active_controller = portfolio_live_autopilot if portfolio_live_autopilot else bot3_autopilot
    execution_cols[0].metric("Kraken Controller", display_status(active_controller.get("status")))
    execution_cols[1].metric("Bot80 Dry Run", display_status(promotion_dry_run.get("status")))
    execution_cols[2].metric("Live Tickets", metric_value(bot3_order_plan.get("tickets_count", 0)))
    execution_cols[3].metric("Cycle Orders", metric_value(journal_execution.get("orders_detected", 0)))

    st.subheader("Supervisor Health")
    health_cols = st.columns(3)
    health_cols[0].metric("Health", display_status(supervisor_health.get("status")))
    health_cols[1].metric("Heartbeat Age", "n/a" if supervisor_health.get("heartbeat_age_minutes") is None else f"{supervisor_health.get('heartbeat_age_minutes'):.1f} min")
    health_cols[2].metric("Restarts 24h", metric_value(health_24h.get("restarts")))
    health_detail_cols = st.columns(3)
    health_detail_cols[0].metric("Restarts 7d", metric_value(health_7d.get("restarts")))
    health_detail_cols[1].metric("Last Restart", display_status(health_24h.get("last_restart_reason") or health_7d.get("last_restart_reason"), default="None"))
    health_detail_cols[2].metric("PID", metric_value(supervisor_health.get("pid_file", {}).get("pid")))
    latest_cycle_health = supervisor_health.get("latest_cycle", {})
    if latest_cycle_health.get("failed") or latest_cycle_health.get("timed_out") or latest_cycle_health.get("slow"):
        st.dataframe(arrow_safe_dataframe(pd.DataFrame({
            "failed": [", ".join(latest_cycle_health.get("failed", []))],
            "timed_out": [", ".join(latest_cycle_health.get("timed_out", []))],
            "slow": [json.dumps(latest_cycle_health.get("slow", []), default=str)],
            "alerts": [", ".join(latest_cycle_health.get("alerts", []))],
        })), use_container_width=True, hide_index=True)

    status_cols = st.columns(3)
    status_cols[0].metric("Supervisor Failed", metric_value(daily_journal.get("supervisor", {}).get("failed_count", 0)))
    status_cols[1].metric("Risk Warnings", len(journal_risk.get("warnings", []) or []))
    status_cols[2].metric("Kraken Orders", metric_value(kraken_live_state.get("open_order_count", 0)))
    readiness_cols = st.columns(2)
    readiness_cols[0].metric("Dry Run", display_status(kraken_dry_run.get("status")))
    readiness_cols[1].metric(
        "Tiny Live Ready",
        "Ready" if tiny_live_readiness.get("tiny_live_ready") else "Not ready",
    )
    live_account_warnings = (risk_report.get("accounting") or {}).get("actual_live_warnings") or []
    if live_account_warnings:
        st.warning(
            "Live account review: "
            + " | ".join(
                f"{row.get('symbol')} concentration {as_float(row.get('value_pct')) * 100:.1f}% "
                f"(review line {as_float(row.get('limit_pct')) * 100:.0f}%)"
                for row in live_account_warnings
            )
        )

    st.subheader("Historical Paper-Trade Archive")
    ledger_cols = st.columns(3)
    ledger_cols[0].metric("Closed Events", metric_value(paper_trade_ledger.get("closed_events_total", 0)))
    ledger_cols[1].metric("P&L Supported", metric_value(paper_trade_ledger.get("realized_pnl_available_closes", 0)))
    ledger_cols[2].metric("P&L Unavailable", metric_value(paper_trade_ledger.get("realized_pnl_unavailable_closes", 0)))
    ledger_value_cols = st.columns(3)
    ledger_value_cols[0].metric("Supported P&L Sum", f"{as_float(paper_trade_ledger.get('realized_pnl_supported_total')):,.2f}")
    ledger_value_cols[1].metric("Reconciled", f"{as_float(paper_trade_ledger.get('realized_pnl_exact_or_reconciled_total')):,.2f}")
    ledger_value_cols[2].metric("Estimated", f"{as_float(paper_trade_ledger.get('realized_pnl_estimated_total')):,.2f}")
    st.caption(
        "Each bot is a separate virtual account. The supported P&L figure is an evidence sum, not unified portfolio NAV; "
        "estimated historical closes are labelled separately and unsupported closes are never counted as zero."
    )
    recent_closes = pd.DataFrame(paper_trade_ledger.get("recent_closed_events", []))
    if not recent_closes.empty:
        close_columns = [
            column
            for column in (
                "created_at", "bot", "symbol", "entry_price", "exit_price", "realized_pnl",
                "pnl_method", "pnl_confidence",
            )
            if column in recent_closes.columns
        ]
        st.dataframe(
            arrow_safe_dataframe(recent_closes[close_columns]),
            use_container_width=True,
            hide_index=True,
        )

    if bot3_reconciliation.get("status") == "aligned":
        st.success("Bot3 live reconciliation is aligned. No live order is currently required.")
    elif bot3_reconciliation:
        st.warning(f"Bot3 live reconciliation: {bot3_reconciliation.get('status')}")

    if not system_status.empty:
        st.subheader("Per-Bot Operating Table")
        preferred = [
            "rank", "bot", "mode", "role", "bucket", "status", "equity", "return_pct",
            "positions", "hist_orders", "buys", "sells", "realized_pnl", "last_order",
            "blocker", "best_asset", "proximity_pct", "dashboard_verdict",
        ]
        st.dataframe(arrow_safe_dataframe(system_status[preferred]), use_container_width=True, height=720)

        chart_df = system_status.copy()
        chart_df["return_pct"] = pd.to_numeric(chart_df["return_pct"], errors="coerce")
        chart_df = chart_df.dropna(subset=["return_pct"])
        if not chart_df.empty:
            st.plotly_chart(
                px.bar(
                    chart_df,
                    x="bot",
                    y="return_pct",
                    color="bucket",
                    title="Current Paper Return By Bot",
                ),
                use_container_width=True,
            )

        st.subheader("Promoted Operating Buckets")
        bucket_counts = system_status.groupby(["bucket", "dashboard_verdict"], dropna=False).size().reset_index(name="count")
        st.dataframe(arrow_safe_dataframe(bucket_counts), use_container_width=True)
    else:
        st.info("No promoted operating reports found yet. The supervisor will create them on the next cycle.")

    st.subheader("Candidate Graduation Board")
    graduation_summary = graduation_board.get("summary", {}) if isinstance(graduation_board, dict) else {}
    graduation_cols = st.columns(7)
    graduation_cols[0].metric("Candidates", metric_value(graduation_summary.get("candidate_count", 0)))
    graduation_cols[1].metric("Operating", metric_value(graduation_summary.get("operating_count", 0)))
    graduation_cols[2].metric("Active Workbench", metric_value(graduation_summary.get("active_workbench_count", 0)))
    graduation_cols[3].metric("Waiting", metric_value(graduation_summary.get("waiting_count", 0)))
    graduation_cols[4].metric("Visible Archive", metric_value(graduation_summary.get("archive_visible_count", 0)))
    graduation_cols[5].metric("Growth Eligible", metric_value(graduation_summary.get("growth_sleeve_eligible_count", 0)))
    graduation_cols[6].metric("Positive Preserved", metric_value(graduation_summary.get("positive_evidence_preserved_count", 0)))
    st.caption("Positive edges receive route-specific proof obligations. Modified formulas keep their own evidence and never inherit a parent's backtest.")
    graduation_rows = pd.DataFrame(graduation_board.get("rows", [])) if isinstance(graduation_board, dict) else pd.DataFrame()
    if not graduation_rows.empty:
        graduation_rows["forward_return_pct"] = graduation_rows["forward"].apply(
            lambda value: value.get("return_pct") if isinstance(value, dict) else None
        )
        graduation_columns = [
            column
            for column in (
                "display_name", "parent_id", "lane", "promotion_route", "stage", "formula_status",
                "historically_winning", "active_queue", "forward_return_pct", "next_gate",
            )
            if column in graduation_rows.columns
        ]
        st.dataframe(
            arrow_safe_dataframe(graduation_rows[graduation_columns]),
            use_container_width=True,
            hide_index=True,
            height=520,
        )
    else:
        st.info("The graduation board has not been generated yet.")

with tabg:
    st.subheader("Gold Paper Shadows")
    st.caption("Isolated Pepperstone research lanes. Neither can submit MT5 or Kraken orders.")
    st.markdown("**Locked baseline: Gold MA 20/80**")
    gold_signal = gold_shadow.get("signal", {}) if isinstance(gold_shadow, dict) else {}
    gold_source = gold_shadow.get("source", {}) if isinstance(gold_shadow, dict) else {}
    gold_account = gold_shadow.get("shadow_account", {}) if isinstance(gold_shadow, dict) else {}
    gold_cols = st.columns(7)
    gold_cols[0].metric("Status", gold_shadow.get("status", "unknown"))
    gold_cols[1].metric("Target", metric_value(gold_signal.get("target_exposure", 0)))
    gold_cols[2].metric("Trend Long", str(gold_signal.get("trend_long", False)))
    gold_cols[3].metric("Action", gold_signal.get("action", "n/a"))
    gold_cols[4].metric("Shadow Equity", f"GBP {as_float(gold_account.get('equity_gbp')):.2f}")
    gold_cols[5].metric("Shadow Return", f"{as_float(gold_account.get('return_pct')):.2f}%")
    gold_cols[6].metric("Data Age", f"{as_float(gold_source.get('data_age_hours')):.1f}h")

    gold_warnings = gold_shadow.get("warnings", []) if isinstance(gold_shadow, dict) else []
    if gold_warnings:
        st.warning("Gold shadow warnings: " + ", ".join(str(item) for item in gold_warnings))

    st.write("Locked candidate:", (gold_shadow.get("locked_config") or {}).get("candidate", "n/a"))
    st.write("Formula hash:", gold_shadow.get("formula_hash", "n/a"))
    st.write("Latest broker bar:", gold_source.get("latest_data_timestamp", "n/a"))

    signal_rows = pd.DataFrame([gold_signal]) if gold_signal else pd.DataFrame()
    if not signal_rows.empty:
        st.subheader("Current Gold Decision")
        st.dataframe(arrow_safe_dataframe(signal_rows), use_container_width=True, hide_index=True)

    gold_tickets = gold_shadow.get("demo_tickets", []) if isinstance(gold_shadow, dict) else []
    if gold_tickets:
        st.subheader("Demo-Only Tickets")
        st.dataframe(arrow_safe_dataframe(pd.DataFrame(gold_tickets)), use_container_width=True, hide_index=True)
    else:
        st.info("No Gold demo ticket this cycle. A ticket appears only when the locked target changes on fresh broker data.")

    st.divider()
    st.markdown("**Validated challenger: V10 Compression Release**")
    challenger_signal = gold_v10_shadow.get("signal", {}) if isinstance(gold_v10_shadow, dict) else {}
    challenger_source = gold_v10_shadow.get("source", {}) if isinstance(gold_v10_shadow, dict) else {}
    challenger_account = gold_v10_shadow.get("shadow_account", {}) if isinstance(gold_v10_shadow, dict) else {}
    challenger_cols = st.columns(8)
    challenger_cols[0].metric("Status", gold_v10_shadow.get("status", "unknown"))
    challenger_cols[1].metric("Target", metric_value(challenger_signal.get("target_exposure", 0)))
    challenger_cols[2].metric("Trend", str(challenger_signal.get("trend_long", False)))
    challenger_cols[3].metric("Compressed", str(challenger_signal.get("compressed", False)))
    challenger_cols[4].metric("Release", str(challenger_signal.get("release_up", False)))
    challenger_cols[5].metric("Action", challenger_signal.get("action", "n/a"))
    challenger_cols[6].metric("Equity", f"GBP {as_float(challenger_account.get('equity_gbp')):.2f}")
    challenger_cols[7].metric("Return", f"{as_float(challenger_account.get('return_pct')):.2f}%")

    challenger_warnings = gold_v10_shadow.get("warnings", []) if isinstance(gold_v10_shadow, dict) else []
    if challenger_warnings:
        st.warning("V10 warnings: " + ", ".join(str(item) for item in challenger_warnings))
    evidence = gold_v10_shadow.get("promotion_evidence", {}) if isinstance(gold_v10_shadow, dict) else {}
    st.write(
        "Strict validation:",
        f"{evidence.get('strict_checks_passed', 'n/a')}/{evidence.get('strict_checks_total', 'n/a')}",
        "| Latest broker bar:",
        challenger_source.get("latest_data_timestamp", "n/a"),
        "| Formula hash:",
        gold_v10_shadow.get("formula_hash", "n/a"),
    )
    if challenger_signal:
        st.dataframe(
            arrow_safe_dataframe(pd.DataFrame([challenger_signal])),
            use_container_width=True,
            hide_index=True,
        )
    challenger_tickets = gold_v10_shadow.get("paper_tickets", []) if isinstance(gold_v10_shadow, dict) else []
    if challenger_tickets:
        st.subheader("V10 Paper Tickets")
        st.dataframe(
            arrow_safe_dataframe(pd.DataFrame(challenger_tickets)),
            use_container_width=True,
            hide_index=True,
        )


with tabp:
    st.subheader("Promoted Kraken Portfolio")
    st.caption("Active backfill portfolio: Bot3 keeps unused specialist capital working; Bot80 and Defensive Drift take capital only when their exact formulas hold positions. Dry-run only.")

    selected = promotion_portfolio.get("selected_portfolio", {}) if isinstance(promotion_portfolio, dict) else {}
    bot80_selected = selected.get("bot80_turnover_penalized_kraken_gbp", {}) if isinstance(selected, dict) else {}
    drift_selected = selected.get("bot31_defensive_drift_kraken_gbp", {}) if isinstance(selected, dict) else {}
    bot3_selected = selected.get("bot3_core", {}) if isinstance(selected, dict) else {}
    promo_cols = st.columns(4)
    promo_cols[0].metric("Portfolio", display_status(promotion_portfolio.get("status")))
    promo_cols[1].metric("Bot3 Active", f"{as_float(bot3_selected.get('dynamic_target_weight')) * 100:.0f}%")
    promo_cols[2].metric("Bot80 Budget", f"{as_float(bot80_selected.get('budget_weight')) * 100:.0f}%")
    promo_cols[3].metric("Bot80 Gate", "Open" if bot80_selected.get("gate_ok") else "Cash")
    promo_detail_cols = st.columns(4)
    promo_detail_cols[0].metric("Drift Budget", f"{as_float(drift_selected.get('budget_weight')) * 100:.0f}%")
    promo_detail_cols[1].metric("Drift Gate", "Open" if drift_selected.get("gate_ok") else "Cash")
    promo_detail_cols[2].metric("Dry Run", display_status(promotion_dry_run.get("status")))
    promo_detail_cols[3].metric("Virtual Equity", f"GBP {as_float(promotion_dry_run.get('post_trade_equity_gbp')):.2f}")
    st.caption(f"Expanded target weight sum: {metric_value(promotion_portfolio.get('expanded_target_weight_sum', 'n/a'))}")
    bot80_cadence = bot80_selected.get("cadence") or {}
    st.caption(
        f"Bot80 evaluates each supervisor cycle but rotates on its validated "
        f"{bot80_cadence.get('locked_rebalance_days', 'n/a')}-day cadence | "
        f"next rotation: {bot80_cadence.get('next_rotation_date', 'n/a')} | "
        f"top candidate: {bot80_cadence.get('top_candidate', 'n/a')} | "
        f"score gap: {bot80_cadence.get('score_gap_to_entry', 'n/a')}"
    )
    st.caption(
        f"Defensive Drift evaluates daily risk and fresh credit data; allocation cadence "
        f"{(drift_selected.get('cadence') or {}).get('locked_rebalance_days', 'n/a')} days | "
        f"active: {drift_selected.get('active', False)} | target: {drift_selected.get('current_target_symbol', 'cash')} | "
        f"Bot3 backfill: {as_float(bot3_selected.get('dynamic_target_weight')):.0%}"
    )

    st.subheader("Bot80 Timing-Diversification Shadow")
    phase_activity = bot80_phase3_shadow.get("activity") or {}
    phase_cols = st.columns(5)
    phase_cols[0].metric("Status", bot80_phase3_shadow.get("status", "unknown"))
    phase_cols[1].metric("Gate", "OPEN" if bot80_phase3_shadow.get("gate_ok") else "CASH")
    phase_cols[2].metric("Next Cohort", phase_activity.get("next_decision_date", "n/a"))
    phase_cols[3].metric("Open Positions", metric_value(phase_activity.get("open_position_count", 0)))
    phase_cols[4].metric("Aggregate Target", f"{sum((bot80_phase3_shadow.get('target_weights') or {}).values()) * 100:.1f}%")
    st.caption(
        "Three equal cohorts keep the exact 30-day Bot80 formula and share one capital cap. "
        "Their phase dates are 10 days apart; this is paper shadow, not extra live exposure."
    )
    cohort_rows = bot80_phase3_shadow.get("cohorts") or []
    if cohort_rows:
        cohort_table = [
            {
                "cohort": row.get("cohort"),
                "equity": row.get("equity"),
                "positions": len(row.get("positions") or []),
                "last_rebalance": row.get("last_rebalance"),
                "next_rebalance": row.get("next_rebalance_date"),
                "due_this_cycle": row.get("rebalance_due"),
                "orders": len(row.get("orders") or []),
            }
            for row in cohort_rows
        ]
        st.dataframe(arrow_safe_dataframe(pd.DataFrame(cohort_table)), use_container_width=True, hide_index=True)

    promo_alerts = promotion_portfolio.get("alerts", []) or []
    promo_warnings = promotion_dry_run.get("warnings", []) or []
    promo_blockers = promotion_dry_run.get("blockers", []) or []
    if promo_alerts or promo_warnings or promo_blockers:
        st.warning(" | ".join(str(item) for item in [*promo_alerts, *promo_warnings, *promo_blockers]))
    else:
        st.success("Portfolio sources, formula lock, Kraken prices, and target weights are healthy.")

    st.subheader("Live Account Handoff")
    handoff_cols = st.columns(5)
    handoff_cols[0].metric("Reconciliation", portfolio_live_reconciliation.get("status", "unknown"))
    handoff_cols[1].metric("Live Equity", f"GBP {as_float(portfolio_live_reconciliation.get('live_account_equity_gbp')):.2f}")
    handoff_cols[2].metric("Current Controller", portfolio_live_reconciliation.get("current_controller", "unknown"))
    handoff_cols[3].metric("Proposed Tickets", metric_value(portfolio_live_reconciliation.get("tickets_count", 0)))
    handoff_cols[4].metric("Full Exit", "NO" if portfolio_live_reconciliation.get("full_exit_recommended") is False else "REVIEW")
    if portfolio_live_autopilot:
        bot80_dormancy = portfolio_live_autopilot.get("bot80_dormancy") or {}
        st.caption(
            f"Unified controller: {portfolio_live_autopilot.get('status', 'unknown')} | "
            f"Bot80 cash intentional: {bot80_dormancy.get('intentional_cash', 'n/a')} | "
            f"Top candidate: {bot80_dormancy.get('top_candidate', 'n/a')} | "
            f"Score: {bot80_dormancy.get('top_candidate_score', 'n/a')} / {bot80_dormancy.get('required_score', 'n/a')} | "
            f"Next rotation: {bot80_dormancy.get('next_rotation_date', 'n/a')}"
        )
    handoff_tickets = portfolio_live_reconciliation.get("proposed_tickets", []) or []
    if handoff_tickets:
        st.dataframe(arrow_safe_dataframe(pd.DataFrame(handoff_tickets)), use_container_width=True, hide_index=True)
    handoff_blockers = portfolio_live_reconciliation.get("activation_blockers", []) or []
    if handoff_blockers:
        st.info("Live execution remains blocked: " + " | ".join(str(item) for item in handoff_blockers))

    target_rows = []
    for name, weight in (promotion_portfolio.get("paper_shadow_targets") or {}).items():
        target_rows.append({"view": "strategy sleeve", "target": name, "weight": weight})
    for name, weight in (promotion_portfolio.get("paper_shadow_targets_expanded") or {}).items():
        target_rows.append({"view": "Kraken asset", "target": name, "weight": weight})
    if target_rows:
        target_df = pd.DataFrame(target_rows)
        st.subheader("Current Targets")
        st.dataframe(arrow_safe_dataframe(target_df), use_container_width=True, hide_index=True)
        st.plotly_chart(
            px.bar(target_df, x="target", y="weight", color="view", barmode="group", title="Sleeves and Current Kraken Exposure"),
            use_container_width=True,
        )

    dry_state = promotion_dry_run.get("simulated_state", {}) if isinstance(promotion_dry_run, dict) else {}
    state_rows = [
        {"holding": symbol, "quantity": qty}
        for symbol, qty in (dry_state.get("holdings") or {}).items()
    ]
    state_rows.append({"holding": "CASH_GBP", "quantity": dry_state.get("cash_gbp", 0.0)})
    st.subheader("Virtual Kraken Account")
    st.dataframe(arrow_safe_dataframe(pd.DataFrame(state_rows)), use_container_width=True, hide_index=True)

    ticket_rows = promotion_dry_run.get("tickets", []) if isinstance(promotion_dry_run, dict) else []
    if ticket_rows:
        st.subheader("Latest Simulated Fills")
        st.dataframe(arrow_safe_dataframe(pd.DataFrame(ticket_rows)), use_container_width=True, hide_index=True)
    else:
        st.info("No new simulated fill this cycle. Targets and current virtual holdings are already aligned.")

    exclusions = promotion_portfolio.get("excluded_at_final_gate", {}) or {}
    if exclusions:
        st.subheader("Final-Gate Exclusions")
        st.dataframe(
            arrow_safe_dataframe(pd.DataFrame([{"candidate": name, "reason": reason} for name, reason in exclusions.items()])),
            use_container_width=True,
            hide_index=True,
        )

with tab1:
    st.subheader("Primary Operating Systems")
    cols = st.columns(5)
    with cols[0]:
        st.markdown("**Bot3 Core**")
        st.write("Latest log:", bot3_display.get("latest_log", "unknown"))
        st.write("Equity:", bot3_display.get("equity", "unknown"))
        st.write("Orders:", count_items(bot3_display.get("orders")))
    with cols[1]:
        show_bot_snapshot("Bot80 Kraken", bot80_paper, "BTC gate")
        st.write("Formula lock:", (bot80_paper.get("formula_lock") or {}).get("leader_mode", "unknown"))
    with cols[2]:
        show_bot_snapshot("Defensive Drift", bot31_defensive_drift, "Credit gate")
        st.write("Formula lock:", (bot31_defensive_drift.get("formula_lock") or {}).get("score_family", "unknown"))
    with cols[3]:
        show_bot_snapshot("Gold Shadow", gold_shadow, "Trend")
        st.write("Target:", gold_shadow.get("target_weight", gold_shadow.get("target", 0.0)))
    with cols[4]:
        show_bot_snapshot("Bot40 Telegram", bot40_signal_shadow, "Decision")

    actions = pd.DataFrame(bot3_display.get("latest_actions", []))
    if not actions.empty:
        st.subheader("Bot3 Latest Actions")
        st.dataframe(arrow_safe_dataframe(actions), use_container_width=True)

    st.subheader("Promoted Portfolio Targets")
    primary_targets = pd.DataFrame(
        [{"target": name, "weight": weight} for name, weight in (promotion_portfolio.get("paper_shadow_targets_expanded") or {}).items()]
    )
    if not primary_targets.empty:
        st.dataframe(arrow_safe_dataframe(primary_targets), use_container_width=True, hide_index=True)

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
            f"Blocker: {closest.get('blocker', 'n/a')} | "
            f"Needs: {closest.get('needs_to_change', 'n/a')}"
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
                "gate_explanation",
                "needs_to_change",
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
    st.subheader("Activation Audit")
    st.caption("Audit is read-only. Activation Shadow is paper-only and tracks loosened-rule behavior.")

    activation_age = age_minutes(activation.get("created_at"))
    decision = activation.get("decision", {})
    summary = activation.get("summary", {})
    current_state = activation.get("current_state", {})

    audit_cols = st.columns(5)
    audit_cols[0].metric("Audit Age", "n/a" if activation_age is None else f"{activation_age:.1f} min")
    audit_cols[1].metric("Live Change", decision.get("live_rule_change", "n/a"))
    audit_cols[2].metric("Candidates", metric_value(summary.get("candidate_rows")))
    audit_cols[3].metric("Watch Rows", metric_value(summary.get("watch_rows")))
    audit_cols[4].metric("Rejected", metric_value(summary.get("rejected_rows")))

    if decision:
        st.info(f"Decision: {decision.get('reason', 'n/a')}")
        st.write("Next action:", decision.get("next_action", "n/a"))
    if current_state:
        st.caption(
            "Current: "
            f"orders={current_state.get('orders_detected', 'n/a')}, "
            f"holding={current_state.get('holding_bots', 'n/a')}, "
            f"waiting={current_state.get('waiting_bots', 'n/a')}, "
            f"stale={current_state.get('stale_reports', 'n/a')}"
        )

    audit_rows = pd.DataFrame(activation.get("rows", []))
    if not audit_rows.empty:
        preferred = [
            column
            for column in [
                "section", "test", "family", "hypothetical_fires", "sample",
                "return_pct", "sharpe", "max_dd_pct", "profit_factor", "trades",
                "trade_delta_vs_baseline", "sharpe_delta_vs_baseline", "dd_delta_vs_baseline",
                "verdict", "notes",
            ]
            if column in audit_rows
        ]
        st.dataframe(arrow_safe_dataframe(audit_rows[preferred]), use_container_width=True)
        verdict_counts = audit_rows["verdict"].value_counts().reset_index()
        verdict_counts.columns = ["verdict", "count"]
        st.plotly_chart(
            px.bar(verdict_counts, x="verdict", y="count", title="Activation Audit Verdicts"),
            use_container_width=True,
        )
    else:
        st.info("No activation audit report found yet. The supervisor will create one after the radar step.")

    st.divider()
    st.subheader("Activation Shadow Live-Paper Test")
    shadow_age = age_minutes(activation_shadow.get("created_at"))
    shadow_positions = activation_shadow.get("positions", [])
    shadow_orders = activation_shadow.get("orders", [])
    shadow_equity = activation_shadow.get("equity_by_variant", {})
    shadow_counts = activation_shadow.get("candidate_counts", {})

    shadow_cols = st.columns(5)
    shadow_cols[0].metric("Shadow Age", "n/a" if shadow_age is None else f"{shadow_age:.1f} min")
    shadow_cols[1].metric("Paper Orders", count_items(shadow_orders))
    shadow_cols[2].metric("Open Positions", count_items(shadow_positions))
    shadow_cols[3].metric("Soft Candidates", metric_value(shadow_counts.get("soft_gate")))
    shadow_cols[4].metric("Starter Candidates", metric_value(shadow_counts.get("starter_position")))

    if activation_shadow:
        st.info(activation_shadow.get("interpretation", "Paper-only loosened activation test."))
    else:
        st.info("No activation shadow report found yet. The supervisor will create one after the radar step.")

    equity_rows = pd.DataFrame(
        [
            {"variant": variant, **values}
            for variant, values in shadow_equity.items()
            if isinstance(values, dict)
        ]
    )
    if not equity_rows.empty:
        st.markdown("**Variant Equity**")
        st.dataframe(arrow_safe_dataframe(equity_rows), use_container_width=True)

    order_rows = pd.DataFrame(shadow_orders)
    if not order_rows.empty:
        st.markdown("**Latest Shadow Orders**")
        st.dataframe(arrow_safe_dataframe(order_rows), use_container_width=True)

    position_rows = pd.DataFrame(shadow_positions)
    if not position_rows.empty:
        st.markdown("**Open Shadow Positions**")
        st.dataframe(arrow_safe_dataframe(position_rows), use_container_width=True)

with tab4:
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

with tab5:
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

    st.subheader("Bot40 Telegram Signal Intake")
    bot40_cols = st.columns(6)
    bot40_cols[0].metric("Status", bot40_signal_shadow.get("status", "unknown"))
    bot40_cols[1].metric("Decision", bot40_signal_shadow.get("decision", "n/a"))
    bot40_cols[2].metric("Provider", bot40_signal_shadow.get("provider", "n/a"))
    bot40_cols[3].metric("New Candidates", metric_value(bot40_signal_shadow.get("new_signal_candidates", 0)))
    bot40_cols[4].metric("Open Positions", count_items(bot40_signal_shadow.get("positions")))
    bot40_cols[5].metric("Paper Orders", count_items(bot40_signal_shadow.get("orders")))
    bot40_reasons = bot40_signal_shadow.get("no_action_reasons", [])
    if bot40_reasons:
        st.info("Why no Bot40 action: " + "; ".join(str(item) for item in bot40_reasons))
    bot40_recent = pd.DataFrame(bot40_signal_shadow.get("recent_selected_provider_dispositions", []))
    if not bot40_recent.empty:
        visible = [
            column for column in [
                "timestamp", "signal_id", "symbol", "side", "message_type",
                "complete_signal", "disposition", "reason",
            ] if column in bot40_recent
        ]
        st.dataframe(
            arrow_safe_dataframe(bot40_recent[visible]),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No Bot40 signal dispositions have been recorded yet.")

    st.subheader("Bot40b Multi-Provider Paper Executor")
    bot40b_intake = bot40b_multi_provider.get("intake_health", {})
    bot40b_cols = st.columns(6)
    bot40b_cols[0].metric("Status", bot40b_multi_provider.get("status", "unknown"))
    bot40b_cols[1].metric("Decision", bot40b_multi_provider.get("decision", "n/a"))
    bot40b_cols[2].metric("Channels", metric_value(bot40b_intake.get("configured_channels_count", 0)))
    bot40b_cols[3].metric("Open Positions", count_items(bot40b_multi_provider.get("positions")))
    bot40b_cols[4].metric("Closed Trades", metric_value(bot40b_multi_provider.get("closed_trades_count", 0)))
    bot40b_cols[5].metric("Equity", metric_value(bot40b_multi_provider.get("equity_estimate")))
    bot40b_reasons = bot40b_multi_provider.get("no_action_reasons", [])
    if bot40b_reasons:
        st.info("Why no Bot40b action: " + "; ".join(str(item) for item in bot40b_reasons))
    bot40b_stitching = bot40b_multi_provider.get("thread_stitching", {})
    if bot40b_stitching:
        st.caption(
            "Thread reconstruction: "
            f"{bot40b_stitching.get('reconstructed_signals_total', 0)} reconstructed, "
            f"{bot40b_stitching.get('new_reconstructed_candidates', 0)} new this cycle, "
            f"methods {bot40b_stitching.get('methods', {})}"
        )

    bot40b_scoreboard = pd.DataFrame(bot40b_multi_provider.get("provider_scoreboard", []))
    if not bot40b_scoreboard.empty:
        st.caption("Provider scorecard from forward-only Bot40b paper activity")
        scoreboard_columns = [
            column for column in [
                "provider", "open_positions", "closed_trades", "wins", "losses",
                "win_rate", "realized_pnl", "unrealized_pnl",
            ] if column in bot40b_scoreboard
        ]
        st.dataframe(
            arrow_safe_dataframe(bot40b_scoreboard[scoreboard_columns]),
            use_container_width=True,
            hide_index=True,
        )

    bot40b_recent = pd.DataFrame(bot40b_multi_provider.get("recent_signal_dispositions", []))
    if not bot40b_recent.empty:
        st.caption("Latest multi-provider message dispositions")
        disposition_columns = [
            column for column in [
                "timestamp", "provider", "symbol", "side", "complete_signal",
                "assembled", "stitch_method", "stitch_confidence",
                "validation_reason", "disposition", "reason",
            ] if column in bot40b_recent
        ]
        st.dataframe(
            arrow_safe_dataframe(bot40b_recent[disposition_columns]),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No Bot40b signal dispositions have been recorded yet.")

    with st.expander("Bot40b channel coverage", expanded=False):
        bot40b_coverage = pd.DataFrame(bot40b_multi_provider.get("provider_coverage", []))
        if not bot40b_coverage.empty:
            st.dataframe(
                arrow_safe_dataframe(bot40b_coverage),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No parsed provider coverage is available yet.")
        bot40b_raw_coverage = pd.DataFrame(bot40b_intake.get("raw_provider_coverage", []))
        if not bot40b_raw_coverage.empty:
            st.caption("Raw collector coverage")
            st.dataframe(
                arrow_safe_dataframe(bot40b_raw_coverage),
                use_container_width=True,
                hide_index=True,
            )

    st.subheader("Open Positions")
    position_rows = []
    report_map = {"bot3": bot3_display}
    if REPORT_DIR.exists():
        for path in sorted(REPORT_DIR.glob("*_latest.json")):
            if path.name.startswith(("seed_active_inventory", "gate_audit", "activation_audit", "activation_shadow")) or is_legacy_report(path):
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

with tab6:
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

with tab7:
    st.subheader("Recent Logs")
    if LOG_DIR.exists():
        recent_logs = sorted(LOG_DIR.glob("*.log"), key=lambda path: path.stat().st_mtime, reverse=True)[:8]
    else:
        recent_logs = []

    for path in recent_logs:
        with st.expander(path.name):
            text = path.read_text(encoding="utf-8", errors="replace")
            st.code("\n".join(text.splitlines()[-80:]), language="text")

from __future__ import annotations

import argparse
from pathlib import Path

from trading_research.paper_state import PaperStateStore


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-file", type=Path, required=True)
    args = parser.parse_args()

    store = PaperStateStore(args.state_file)
    state = store.load()
    store.log_event("paper_cycle", {"cash": state["cash"], "positions": state["positions"]})
    store.save(state)
    print({"cash": state["cash"], "positions": state["positions"]})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

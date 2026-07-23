#!/usr/bin/env python3
"""Capture a rendered, presentation-safe dashboard screenshot."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from playwright.sync_api import sync_playwright


DEFAULT_CHROME_PATHS = (
    Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Google/Chrome/Application/chrome.exe",
    Path(os.environ.get("PROGRAMFILES", "")) / "Google/Chrome/Application/chrome.exe",
    Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe",
)


def find_chrome() -> Path:
    for path in DEFAULT_CHROME_PATHS:
        if path.is_file():
            return path
    raise FileNotFoundError("Chrome was not found; pass --chrome-path explicitly")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8502/")
    parser.add_argument("--output", type=Path, default=Path("docs/screenshots/system_status.png"))
    parser.add_argument("--chrome-path", type=Path)
    parser.add_argument("--tab", help="Optional dashboard tab to select before capture")
    parser.add_argument("--width", type=int, default=1440)
    parser.add_argument("--height", type=int, default=900)
    args = parser.parse_args()

    chrome_path = args.chrome_path or find_chrome()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=str(chrome_path),
            headless=True,
        )
        page = browser.new_page(viewport={"width": args.width, "height": args.height})
        page.goto(args.url, wait_until="domcontentloaded")
        page.get_by_role("heading", name="Systematic Trading Ops Dashboard").wait_for(timeout=30_000)
        page.get_by_text("Promoted portfolio sources and weights are healthy").wait_for(timeout=30_000)
        if args.tab:
            page.get_by_role("tab", name=args.tab, exact=True).click()
        page.wait_for_timeout(1_500)
        page.screenshot(path=str(args.output), full_page=False)
        browser.close()
    print(f"Saved rendered dashboard screenshot to {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

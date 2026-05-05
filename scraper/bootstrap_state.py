from __future__ import annotations

import asyncio
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import async_playwright


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def _domain_key(url: str) -> str:
    host = urlparse(url).netloc.lower().replace("www.", "")
    parts = host.split(".")
    if len(parts) >= 2:
        return ".".join(parts[-2:])
    return host or "unknown"


async def main() -> None:
    url = os.environ.get("BOOTSTRAP_URL", "").strip()
    if not url:
        raise SystemExit("Set BOOTSTRAP_URL to the retailer PDP URL you want to bootstrap.")

    out = os.environ.get("BOOTSTRAP_OUT", "").strip()
    state_dir = os.environ.get("SCRAPER_STORAGE_STATE_DIR", str(Path(__file__).parent / "storage_state")).strip()
    if not out:
        Path(state_dir).mkdir(parents=True, exist_ok=True)
        out = str(Path(state_dir) / f"{_domain_key(url)}.json")

    out_path = Path(out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    engine = os.environ.get("BOOTSTRAP_ENGINE", "chromium").strip().lower()
    headless = os.environ.get("BOOTSTRAP_HEADLESS", "false").strip().lower() in ("1", "true", "yes")
    timeout_s = int(os.environ.get("BOOTSTRAP_TIMEOUT_S", "300") or "300")

    # Wait for a buy-control to appear before saving state (best-effort).
    ready_selector = os.environ.get(
        "BOOTSTRAP_READY_SELECTOR",
        'button:has-text("Add to Cart"), button:has-text("Add to cart"), '
        'button:has-text("Add to Bag"), button:has-text("Add to bag"), '
        '[id*="add-to-cart"], [data-action="add-to-cart"], '
        '[data-automation-id="atc"], [data-automation-id="add-to-cart-button"], '
        'button:has-text("Continue shopping")',
    ).strip()

    print(f"Bootstrapping storage state for {_domain_key(url)}")
    print(f"URL: {url}")
    print(f"Engine: {engine} headless={headless} timeout={timeout_s}s")
    print(f"Output: {out_path}")
    print("")
    print("Steps:")
    print("- A browser window will open.")
    print("- If you see a captcha / access prompt, solve it manually.")
    print("- Once the PDP is reached, this script will save storage_state and exit.")
    print("")

    async with async_playwright() as p:
        if engine == "firefox":
            browser = await p.firefox.launch(headless=headless)
        elif engine == "webkit":
            browser = await p.webkit.launch(headless=headless)
        else:
            browser = await p.chromium.launch(headless=headless)

        ctx = await browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1400, "height": 900},
            locale="en-US",
            timezone_id="America/New_York",
        )
        page = await ctx.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=90_000)
            try:
                await page.wait_for_selector(ready_selector, timeout=timeout_s * 1000, state="visible")
            except Exception:
                # If selector fails, still allow saving state after timeout
                await page.wait_for_timeout(min(timeout_s, 30) * 1000)

            shot_dir = Path(os.environ.get("BOOTSTRAP_SHOT_DIR", str(Path(__file__).parent / "test_artifacts"))).resolve()
            shot_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            shot = shot_dir / f"{ts}__bootstrap__{_domain_key(url)}.png"
            try:
                await page.screenshot(path=str(shot), full_page=False)
                print(f"Screenshot: {shot}")
            except Exception:
                pass

            await ctx.storage_state(path=str(out_path))
            print(f"Saved storage_state: {out_path}")
        finally:
            await page.close()
            await ctx.close()
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())


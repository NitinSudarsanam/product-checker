from __future__ import annotations

import asyncio
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import List
from urllib.parse import urlparse

from playwright.async_api import async_playwright


def _slug(s: str) -> str:
    s = re.sub(r"^https?://", "", s.strip())
    s = re.sub(r"[^a-zA-Z0-9._-]+", "_", s)
    return s[:140].strip("_") or "url"


async def _shot(url: str, out_dir: Path, *, timeout_ms: int, full_page: bool) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"{ts}__{_slug(url)}.png"

    async with async_playwright() as p:
        host = (urlparse(url).netloc or "").lower()
        use_firefox = any(d in host for d in ("staples.com", "officedepot.com"))
        if use_firefox:
            browser = await p.firefox.launch(headless=True)
        else:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled",
                ],
            )
        context = await browser.new_context(
            viewport={"width": 1400, "height": 900},
            locale="en-US",
            timezone_id="America/New_York",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            # small settle to let buy box render
            await page.wait_for_timeout(2000)
            await page.screenshot(path=str(out_path), full_page=full_page)
            return out_path
        finally:
            await page.close()
            await context.close()
            await browser.close()


async def main() -> None:
    env_urls = os.environ.get("SHOT_URLS", "").strip()
    if not env_urls:
        raise SystemExit("Set SHOT_URLS as a comma-separated list of URLs.")
    urls: List[str] = [u.strip() for u in env_urls.split(",") if u.strip()]

    out_dir = Path(os.environ.get("SHOT_OUT_DIR", "/app/scraper/screenshots"))
    timeout_s = int(os.environ.get("SHOT_TIMEOUT_S", "90") or "90")
    full_page = os.environ.get("SHOT_FULL_PAGE", "false").lower() in ("1", "true", "yes")
    timeout_ms = timeout_s * 1000

    print(f"Saving screenshots to: {out_dir}")
    print(f"timeout={timeout_s}s full_page={full_page} urls={len(urls)}")

    for i, url in enumerate(urls, start=1):
        t0 = time.time()
        try:
            path = await _shot(url, out_dir, timeout_ms=timeout_ms, full_page=full_page)
            print(f"[{i}/{len(urls)}] OK {url} -> {path} ({time.time()-t0:.1f}s)")
        except Exception as e:
            print(f"[{i}/{len(urls)}] FAIL {url}: {type(e).__name__}: {e} ({time.time()-t0:.1f}s)")


if __name__ == "__main__":
    asyncio.run(main())


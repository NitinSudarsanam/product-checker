from __future__ import annotations

import asyncio
import os
import re
import statistics
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

# Ensure /app (repo root in containers) is importable even when running from /app/scraper
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "backend") not in sys.path:
    sys.path.insert(0, str(ROOT / "backend"))

from app.config import settings  # type: ignore
from scraper.scraper import _playwright_scrape, detector, fetch_scrapingbee_html, scrape_url  # type: ignore


def _slug(url: str) -> str:
    s = re.sub(r"^https?://", "", url.strip())
    s = re.sub(r"[^a-zA-Z0-9._-]+", "_", s)
    # Keep short to avoid Windows path length issues when artifacts are volume-mounted.
    return s[:60].strip("_") or "url"


def _artifact_dir() -> Path:
    fixed = os.environ.get("BENCH_ARTIFACTS_DIR", "").strip()
    if fixed:
        out = Path(fixed)
        out.mkdir(parents=True, exist_ok=True)
        return out

    ts = time.strftime("%Y%m%dT%H%M%S")
    out = Path(os.environ.get("BENCH_OUT_DIR", "/app/scraper/bench_artifacts")) / ts
    out.mkdir(parents=True, exist_ok=True)
    return out


async def _screenshot_playwright(url: str, out_dir: Path, timeout_ms: int = 60000) -> Optional[str]:
    """Best-effort screenshot of the live URL via Playwright."""
    try:
        from playwright.async_api import async_playwright

        path = out_dir / "playwright.png"
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
            ctx = await browser.new_context(viewport={"width": 1400, "height": 900})
            page = await ctx.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                await page.wait_for_timeout(1500)
                await page.screenshot(path=str(path), full_page=False)
                return str(path)
            finally:
                await page.close()
                await ctx.close()
                await browser.close()
    except Exception as e:
        print(f"[shot] playwright failed for {url}: {type(e).__name__}: {e}")
        return None


async def _screenshot_html(html: str, url: str, out_dir: Path) -> Optional[str]:
    """Render HTML into a local Playwright page and screenshot (for ScrapingBee HTML)."""
    try:
        from playwright.async_api import async_playwright

        path = out_dir / "scrapingbee_html.png"
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"])
            ctx = await browser.new_context(viewport={"width": 1400, "height": 900})
            page = await ctx.new_page()
            try:
                await page.set_content(html, wait_until="domcontentloaded")
                await page.wait_for_timeout(800)
                await page.screenshot(path=str(path), full_page=False)
                return str(path)
            finally:
                await page.close()
                await ctx.close()
                await browser.close()
    except Exception as e:
        print(f"[shot] scrapingbee_html failed for {url}: {type(e).__name__}: {e}")
        return None


@dataclass
class MethodRun:
    url: str
    method: str  # playwright | scrapingbee
    ok: bool
    elapsed_s: float
    status: str
    add_to_cart: bool
    buy_now: bool
    variants_count: int
    error: Optional[str] = None
    html_primary: Optional[str] = None


def _pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def _p50(values: List[float]) -> Optional[float]:
    if not values:
        return None
    try:
        return statistics.median(values)
    except Exception:
        return None


async def _run_playwright(url: str) -> MethodRun:
    t0 = time.time()
    try:
        html, variants, _live = await _playwright_scrape(url)
        if not html:
            return MethodRun(
                url=url,
                method="playwright",
                ok=False,
                elapsed_s=round(time.time() - t0, 2),
                status="error",
                add_to_cart=False,
                buy_now=False,
                variants_count=0,
                error="no_html",
            )
        det = detector.detect_all_buttons(html, url)
        status = det.get("status") or "error"
        return MethodRun(
            url=url,
            method="playwright",
            ok=True,
            elapsed_s=round(time.time() - t0, 2),
            status=status,
            add_to_cart=bool(det.get("add_to_cart")),
            buy_now=bool(det.get("buy_now")),
            variants_count=len(variants or {}),
            error=None,
            html_primary="playwright",
        )
    except Exception as e:
        return MethodRun(
            url=url,
            method="playwright",
            ok=False,
            elapsed_s=round(time.time() - t0, 2),
            status="error",
            add_to_cart=False,
            buy_now=False,
            variants_count=0,
            error=f"{type(e).__name__}: {e}",
        )


async def _run_scrapingbee(url: str, html: Optional[str] = None) -> MethodRun:
    t0 = time.time()
    try:
        if html is None:
            html = await fetch_scrapingbee_html(url)
        if not html:
            return MethodRun(
                url=url,
                method="scrapingbee",
                ok=False,
                elapsed_s=round(time.time() - t0, 2),
                status="error",
                add_to_cart=False,
                buy_now=False,
                variants_count=0,
                error="no_html",
            )
        det = detector.detect_all_buttons(html, url)
        status = det.get("status") or "error"
        return MethodRun(
            url=url,
            method="scrapingbee",
            ok=True,
            elapsed_s=round(time.time() - t0, 2),
            status=status,
            add_to_cart=bool(det.get("add_to_cart")),
            buy_now=bool(det.get("buy_now")),
            variants_count=0,
            error=None,
            html_primary="scrapingbee",
        )
    except Exception as e:
        return MethodRun(
            url=url,
            method="scrapingbee",
            ok=False,
            elapsed_s=round(time.time() - t0, 2),
            status="error",
            add_to_cart=False,
            buy_now=False,
            variants_count=0,
            error=f"{type(e).__name__}: {e}",
            html_primary=None,
        )


async def _run_hybrid(url: str) -> MethodRun:
    """Run the real production path (Playwright-first + fallback to ScrapingBee)."""
    t0 = time.time()
    try:
        r = await scrape_url(url, use_playwright=True)
        status = r.get("status") or "error"
        ok = status in ("available", "unavailable") and not r.get("error_message")
        return MethodRun(
            url=url,
            method="hybrid",
            ok=bool(ok),
            elapsed_s=round(time.time() - t0, 2),
            status=str(status),
            add_to_cart=bool(r.get("add_to_cart")),
            buy_now=bool(r.get("buy_now")),
            variants_count=len(r.get("variants") or {}),
            error=r.get("error_message"),
            html_primary=r.get("html_primary_source"),
        )
    except Exception as e:
        return MethodRun(
            url=url,
            method="hybrid",
            ok=False,
            elapsed_s=round(time.time() - t0, 2),
            status="error",
            add_to_cart=False,
            buy_now=False,
            variants_count=0,
            error=f"{type(e).__name__}: {e}",
            html_primary=None,
        )


def _summarize(runs: List[MethodRun], method: str) -> str:
    m = [r for r in runs if r.method == method]
    ok = [r for r in m if r.ok]
    times = [r.elapsed_s for r in ok]
    p50 = _p50(times)
    ok_rate = (len(ok) / len(m)) if m else 0.0
    status_counts: Dict[str, int] = {}
    for r in ok:
        status_counts[r.status] = status_counts.get(r.status, 0) + 1
    statuses = " ".join(f"{k}={v}" for k, v in sorted(status_counts.items()))
    return (
        f"{method:11} ok={len(ok)}/{len(m)} ({_pct(ok_rate)}) "
        f"p50={p50 if p50 is not None else '—'}s "
        f"{statuses}"
    )


def _diff(play: MethodRun, bee: MethodRun) -> str:
    if not play.ok and not bee.ok:
        return "both_error"
    if play.ok and not bee.ok:
        return "playwright_only"
    if bee.ok and not play.ok:
        return "scrapingbee_only"
    # both ok
    if play.status != bee.status:
        return f"status:{play.status}->{bee.status}"
    if play.add_to_cart != bee.add_to_cart or play.buy_now != bee.buy_now:
        return "button_mismatch"
    return "match"


async def main():
    # URLs: either provided via env, or use a small built-in set
    env_urls = os.environ.get("BENCH_URLS", "").strip()
    urls = [u.strip() for u in env_urls.split(",") if u.strip()] if env_urls else []
    if not urls:
        urls = [
            "https://www.amazon.com/dp/B08N5WRWNW",
            "https://www.walmart.com/ip/21130579",
            "https://www.wayfair.com/decor-pillows/pdp/bedsure-cozy-winter-collection-bedsure-279gsm-super-soft-cozy-blanket-for-bed-couch-gentlesoft%EF%B8%8F-bdur1464.html?piid=105505780%2C105505775",
            "https://example.com",
        ]

    # Limit total runtime
    timeout_s = int(os.environ.get("BENCH_PER_METHOD_TIMEOUT_S", "160") or "160")
    urls = urls[: int(os.environ.get("BENCH_URL_LIMIT", "12") or "12")]

    if not settings.scraper_use_playwright:
        raise SystemExit("settings.scraper_use_playwright is false; benchmark needs Playwright enabled.")
    if not settings.scrapingbee_api_key:
        raise SystemExit("settings.scrapingbee_api_key is empty; benchmark needs ScrapingBee key.")

    out_dir = _artifact_dir()
    print(f"Benchmarking {len(urls)} URLs. per-method timeout={timeout_s}s variants={settings.scraper_check_variants}")
    print(f"Artifacts: {out_dir}")

    # Work around Playwright/Chromium memory growth by running each URL in a fresh process.
    fork_per_url = os.environ.get("BENCH_FORK_PER_URL", "0").strip().lower() in {"1", "true", "yes"}
    if fork_per_url and len(urls) > 1:
        for i, u in enumerate(urls, start=1):
            env = os.environ.copy()
            env["BENCH_URLS"] = u
            env["BENCH_URL_LIMIT"] = "1"
            env["BENCH_FORK_PER_URL"] = "0"
            dom = (urlparse(u).netloc or "url").replace("www.", "")
            env["BENCH_ARTIFACTS_DIR"] = str(out_dir / f"{i:02d}__{dom}")
            Path(env["BENCH_ARTIFACTS_DIR"]).mkdir(parents=True, exist_ok=True)
            print(f"\n== Forked run {i}/{len(urls)}: {u}")
            subprocess.run([sys.executable, __file__], env=env, check=False)
        return

    runs: List[MethodRun] = []
    hybrid_mode = os.environ.get("BENCH_HYBRID_MODE", "reuse").strip().lower()
    for url in urls:
        print(f"\nURL: {url}")
        dom = (urlparse(url).netloc or "url").replace("www.", "")
        url_dir = out_dir / f"{dom}__{_slug(url)}"
        url_dir.mkdir(parents=True, exist_ok=True)

        # Always capture a live Playwright screenshot (even if we later compare ScrapingBee)
        await _screenshot_playwright(url, url_dir, timeout_ms=timeout_s * 1000)
        try:
            play = await asyncio.wait_for(_run_playwright(url), timeout=timeout_s)
        except Exception as e:
            play = MethodRun(url=url, method="playwright", ok=False, elapsed_s=timeout_s, status="error", add_to_cart=False, buy_now=False, variants_count=0, error=f"timeout_or_error:{e}")
        # ScrapingBee: also save HTML + screenshot of rendered HTML (best-effort)
        bee_html: Optional[str] = None
        try:
            bee_html = await asyncio.wait_for(fetch_scrapingbee_html(url), timeout=timeout_s)
        except Exception:
            bee_html = None

        if bee_html:
            try:
                (url_dir / "scrapingbee.html").write_text(bee_html, encoding="utf-8", errors="ignore")
            except Exception:
                pass
            await _screenshot_html(bee_html, url, url_dir)

        try:
            bee = await asyncio.wait_for(_run_scrapingbee(url, bee_html), timeout=timeout_s)
        except Exception as e:
            bee = MethodRun(url=url, method="scrapingbee", ok=False, elapsed_s=timeout_s, status="error", add_to_cart=False, buy_now=False, variants_count=0, error=f"timeout_or_error:{e}")

        if hybrid_mode == "real":
            try:
                hybrid = await asyncio.wait_for(_run_hybrid(url), timeout=timeout_s)
            except Exception as e:
                hybrid = MethodRun(url=url, method="hybrid", ok=False, elapsed_s=timeout_s, status="error", add_to_cart=False, buy_now=False, variants_count=0, error=f"timeout_or_error:{e}", html_primary=None)
        else:
            # Reuse already-fetched results to avoid double-running Playwright/ScrapingBee.
            if play.ok:
                hybrid = MethodRun(
                    url=url,
                    method="hybrid",
                    ok=True,
                    elapsed_s=play.elapsed_s,
                    status=play.status,
                    add_to_cart=play.add_to_cart,
                    buy_now=play.buy_now,
                    variants_count=play.variants_count,
                    error=None,
                    html_primary="playwright",
                )
            elif bee.ok:
                hybrid = MethodRun(
                    url=url,
                    method="hybrid",
                    ok=True,
                    elapsed_s=bee.elapsed_s,
                    status=bee.status,
                    add_to_cart=bee.add_to_cart,
                    buy_now=bee.buy_now,
                    variants_count=bee.variants_count,
                    error=None,
                    html_primary="scrapingbee",
                )
            else:
                hybrid = MethodRun(
                    url=url,
                    method="hybrid",
                    ok=False,
                    elapsed_s=round(play.elapsed_s + bee.elapsed_s, 2),
                    status="error",
                    add_to_cart=False,
                    buy_now=False,
                    variants_count=0,
                    error="both_error",
                    html_primary=None,
                )

        runs.extend([play, bee, hybrid])

        print(f"  playwright : ok={play.ok} t={play.elapsed_s}s status={play.status} atc={play.add_to_cart} bn={play.buy_now} variants={play.variants_count} err={play.error}")
        print(f"  scrapingbee: ok={bee.ok} t={bee.elapsed_s}s status={bee.status} atc={bee.add_to_cart} bn={bee.buy_now} variants={bee.variants_count} err={bee.error}")
        print(f"  hybrid     : ok={hybrid.ok} t={hybrid.elapsed_s}s status={hybrid.status} atc={hybrid.add_to_cart} bn={hybrid.buy_now} variants={hybrid.variants_count} html={hybrid.html_primary} err={hybrid.error}")
        print(f"  diff: {_diff(play, bee)}")

    print("\n=== Summary ===")
    print(_summarize(runs, "playwright"))
    print(_summarize(runs, "scrapingbee"))
    print(_summarize(runs, "hybrid"))

    # high-level diff counts
    diffs: Dict[str, int] = {}
    for url in urls:
        play = next(r for r in runs if r.url == url and r.method == "playwright")
        bee = next(r for r in runs if r.url == url and r.method == "scrapingbee")
        d = _diff(play, bee)
        diffs[d] = diffs.get(d, 0) + 1
    print("Diffs:", " ".join(f"{k}={v}" for k, v in sorted(diffs.items())))


if __name__ == "__main__":
    asyncio.run(main())


"""Capture SIRIN UI screenshots, jank metrics, and motion video for visual verification.

Usage (any python with playwright + chromium installed):
    python scripts/dev/ui_capture.py --base http://localhost:8611 --out /tmp/ui_shots --mode all

Modes: shots (screenshot matrix), jank (rAF frame-time + resource weights), video
(10s recording of the default motion), all.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

JANK_JS = """
async (durationMs) => {
  const frames = [];
  let last = performance.now();
  const t0 = last;
  await new Promise((resolve) => {
    function tick(now) {
      frames.push(now - last);
      last = now;
      if (now - t0 < durationMs) requestAnimationFrame(tick);
      else resolve();
    }
    requestAnimationFrame(tick);
  });
  frames.shift();
  const sorted = [...frames].sort((a, b) => a - b);
  const pct = (p) => sorted[Math.min(sorted.length - 1, Math.floor(sorted.length * p))];
  return {
    frames: frames.length,
    mean: +(frames.reduce((a, b) => a + b, 0) / frames.length).toFixed(1),
    p50: +pct(0.5).toFixed(1),
    p95: +pct(0.95).toFixed(1),
    over33ms: frames.filter((f) => f > 33.4).length,
  };
}
"""

RESOURCES_JS = """
() => {
  const rs = performance.getEntriesByType('resource')
    .map(r => ({name: r.name.split('/').slice(-1)[0].slice(0, 60), kb: Math.round(r.transferSize / 1024)}))
    .sort((a, b) => b.kb - a.kb);
  return {totalKb: rs.reduce((a, r) => a + r.kb, 0), count: rs.length, top: rs.slice(0, 10)};
}
"""


def log(msg: str) -> None:
    print(f"[ui_capture] {msg}", flush=True)


def wait_app(page, base: str, timeout_s: int = 240) -> float:
    t0 = time.time()
    last = None
    while time.time() - t0 < timeout_s:
        try:
            page.goto(base, wait_until="domcontentloaded", timeout=15000)
            last = None
            break
        except Exception as exc:  # server may still be booting
            last = exc
            time.sleep(3)
    if last is not None:
        raise last
    page.get_by_text("Generate & score").first.wait_for(state="visible", timeout=timeout_s * 1000)
    ready = time.time() - t0
    log(f"workspace interactive after {ready:.1f}s")
    time.sleep(4)
    return ready


def select_sidebar_option(page, label: str, option_text: str, wait: float = 6.0) -> bool:
    """Drive a native Streamlit sidebar selectbox (React Aria ComboBox).

    Appearance now lives only in the native sidebar. Find the ``stSelectbox`` whose label matches,
    then filter by typing the option into its ``input[role="combobox"]`` and commit with Enter. Its
    option list ``[role="option"]`` renders in a portal that can fall outside a short viewport, so
    keyboard filtering is more reliable than clicking an off-screen option.
    """
    try:
        box = page.locator(f'div[data-testid="stSelectbox"]:has-text("{label}")').first
        field = box.locator('input[role="combobox"]').first
        field.click(timeout=6000)
        field.press("Control+a")
        field.press("Delete")
        field.type(option_text, delay=30)
        time.sleep(0.4)
        field.press("Enter")
        time.sleep(wait)
        return True
    except Exception as exc:
        log(f"sidebar select '{label}={option_text}' failed: {type(exc).__name__}")
        return False


def select_option_anywhere(page, option_text: str, wait: float = 6.0) -> bool:
    """Fallback for any native <select> still rendered inside the component (non-appearance)."""
    try:
        sel = page.locator(f'select:has(option:text-is("{option_text}"))').first
        sel.select_option(label=option_text, timeout=6000)
        time.sleep(wait)
        return True
    except Exception:
        pass
    try:
        value = option_text.lower()
        sel = page.locator(f'select:has(option[value="{value}"])').first
        sel.select_option(value=value, timeout=6000)
        time.sleep(wait)
        return True
    except Exception as exc:
        log(f"select '{option_text}' failed: {type(exc).__name__}")
        return False


def set_appearance(page, label: str, option_text: str, wait: float = 6.0) -> bool:
    """Sidebar selectbox first (the single home for Theme / Background motion); fall back to the
    old native-<select> path so other component selects keep working."""
    if select_sidebar_option(page, label, option_text, wait=wait):
        return True
    return select_option_anywhere(page, option_text, wait=wait)


def click_text(page, text: str, wait: float = 5.0) -> bool:
    try:
        page.get_by_text(text, exact=True).first.click(timeout=6000)
        time.sleep(wait)
        return True
    except Exception as exc:
        log(f"click '{text}' failed: {type(exc).__name__}")
        return False


def shots(browser, base: str, out: Path) -> None:
    for width, height, tag in ((1920, 1080, "1920"), (1280, 720, "1280")):
        ctx = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=1)
        page = ctx.new_page()
        wait_app(page, base)
        page.screenshot(path=str(out / f"analyze_light_{tag}.png"))
        page.screenshot(path=str(out / f"analyze_light_{tag}_full.png"), full_page=True)
        if width == 1920:
            if click_text(page, "Census number", wait=6):
                page.screenshot(path=str(out / "example_filled.png"), full_page=True)
            for view in ("Runs", "Diagnostics"):
                if click_text(page, view):
                    page.screenshot(path=str(out / f"{view.lower()}_light.png"), full_page=True)
            click_text(page, "Analyze")
            if set_appearance(page, "Theme", "Dark"):
                page.screenshot(path=str(out / "analyze_dark.png"))
                page.screenshot(path=str(out / "analyze_dark_full.png"), full_page=True)
                set_appearance(page, "Theme", "Light")
        ctx.close()
    log("shots done")


def jank(browser, base: str, out: Path) -> None:
    ctx = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = ctx.new_page()
    wait_app(page, base)
    report = {"resources": page.evaluate(RESOURCES_JS)}
    for mode in ("Subtle", "Lively", "Static"):
        set_appearance(page, "Background motion", mode, wait=4)
        report[f"jank_{mode.lower()}"] = page.evaluate(JANK_JS, 8000)
    ctx.close()
    (out / "jank.json").write_text(json.dumps(report, indent=2))
    log("jank: " + json.dumps({k: v for k, v in report.items() if k.startswith("jank")}))


def video(browser, base: str, out: Path) -> None:
    ctx = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        record_video_dir=str(out / "video"),
        record_video_size={"width": 1920, "height": 1080},
    )
    page = ctx.new_page()
    wait_app(page, base)
    set_appearance(page, "Background motion", "Lively", wait=2)
    time.sleep(12)
    ctx.close()
    log("video recorded")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default="http://localhost:8611")
    parser.add_argument("--out", default="/tmp/sirin_ui_capture")
    parser.add_argument("--mode", default="all", choices=("shots", "jank", "video", "all"))
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--force-color-profile=srgb"])
        if args.mode in ("shots", "all"):
            shots(browser, args.base, out)
        if args.mode in ("jank", "all"):
            jank(browser, args.base, out)
        if args.mode in ("video", "all"):
            video(browser, args.base, out)
        browser.close()
    log("done")


if __name__ == "__main__":
    main()

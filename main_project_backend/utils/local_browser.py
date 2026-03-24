from __future__ import annotations

import os
import platform
import shutil
from pathlib import Path


SUPPORTED_STANDALONE_BROWSERS = ("chrome", "chromium", "msedge", "firefox", "webkit")

_SYSTEM_BROWSER_LABELS = {
    "chrome": "Google Chrome",
    "chromium": "Chromium",
    "msedge": "Microsoft Edge",
    "firefox": "Firefox",
    "webkit": "WebKit",
}

_SYSTEM_BROWSER_CANDIDATES = {
    "linux": {
        "chrome": [
            "/opt/google/chrome/chrome",
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "google-chrome",
            "google-chrome-stable",
        ],
        "chromium": [
            "/usr/bin/chromium",
            "/usr/bin/chromium-browser",
            "chromium",
            "chromium-browser",
        ],
        "msedge": [
            "/opt/microsoft/msedge/msedge",
            "/usr/bin/microsoft-edge",
            "/usr/bin/microsoft-edge-stable",
            "microsoft-edge",
            "microsoft-edge-stable",
        ],
        "firefox": [
            "/usr/bin/firefox",
            "/snap/bin/firefox",
            "firefox",
        ],
    },
    "darwin": {
        "chrome": [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            str(Path.home() / "Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        ],
        "chromium": [
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
            str(Path.home() / "Applications/Chromium.app/Contents/MacOS/Chromium"),
        ],
        "msedge": [
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            str(Path.home() / "Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
        ],
        "firefox": [
            "/Applications/Firefox.app/Contents/MacOS/firefox",
            str(Path.home() / "Applications/Firefox.app/Contents/MacOS/firefox"),
        ],
    },
    "windows": {
        "chrome": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            str(Path.home() / "AppData/Local/Google/Chrome/Application/chrome.exe"),
            "chrome",
        ],
        "chromium": [
            r"C:\Program Files\Chromium\Application\chrome.exe",
            r"C:\Program Files (x86)\Chromium\Application\chrome.exe",
            str(Path.home() / "AppData/Local/Chromium/Application/chrome.exe"),
            "chromium",
        ],
        "msedge": [
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            str(Path.home() / "AppData/Local/Microsoft/Edge/Application/msedge.exe"),
            "msedge",
        ],
        "firefox": [
            r"C:\Program Files\Mozilla Firefox\firefox.exe",
            r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
            str(Path.home() / "AppData/Local/Mozilla Firefox/firefox.exe"),
            "firefox",
        ],
    },
}


def normalize_standalone_browser(value: str | None) -> str | None:
    normalized = str(value or "").strip().lower()
    return normalized if normalized in SUPPORTED_STANDALONE_BROWSERS else None


def _platform_key() -> str:
    current = platform.system().strip().lower()
    if current.startswith("darwin"):
        return "darwin"
    if current.startswith("windows"):
        return "windows"
    return "linux"


def _resolve_existing_path(candidate: str) -> str | None:
    text = str(candidate or "").strip()
    if not text:
        return None
    path_candidate = Path(text)
    if path_candidate.is_absolute():
        return str(path_candidate) if path_candidate.exists() else None
    resolved = shutil.which(text)
    return resolved or None


def _playwright_cache_root() -> Path:
    key = _platform_key()
    if key == "windows":
        return Path.home() / "AppData/Local/ms-playwright"
    if key == "darwin":
        return Path.home() / "Library/Caches/ms-playwright"
    return Path.home() / ".cache/ms-playwright"


def _find_playwright_runtime(browser: str) -> str | None:
    cache_root = _playwright_cache_root()
    if not cache_root.exists():
        return None

    prefixes = {
        "chromium": ("chromium-",),
        "firefox": ("firefox-",),
        "webkit": ("webkit-",),
    }.get(browser, ())

    for child in sorted(cache_root.iterdir()):
        if not child.is_dir():
            continue
        if any(child.name.startswith(prefix) for prefix in prefixes):
            return str(child)
    return None


def scan_local_browsers() -> list[dict[str, str | bool | None]]:
    results: list[dict[str, str | bool | None]] = []
    key = _platform_key()
    seen: set[tuple[str, str | None, str]] = set()

    for browser in SUPPORTED_STANDALONE_BROWSERS:
        label = _SYSTEM_BROWSER_LABELS[browser]

        for candidate in _SYSTEM_BROWSER_CANDIDATES.get(key, {}).get(browser, []):
            resolved = _resolve_existing_path(candidate)
            if not resolved:
                continue
            record_key = (browser, resolved, "system")
            if record_key in seen:
                continue
            seen.add(record_key)
            results.append(
                {
                    "browser": browser,
                    "label": label,
                    "source": "system",
                    "location": resolved,
                    "executable_path": resolved,
                    "available": True,
                }
            )

        runtime_location = _find_playwright_runtime(browser)
        if runtime_location:
            record_key = (browser, runtime_location, "playwright-runtime")
            if record_key not in seen:
                seen.add(record_key)
                results.append(
                    {
                        "browser": browser,
                        "label": f"{label} (Playwright Runtime)",
                        "source": "playwright-runtime",
                        "location": runtime_location,
                        "executable_path": None,
                        "available": True,
                    }
                )

    results.sort(key=lambda item: (str(item["browser"]), str(item["source"]), str(item["location"] or "")))
    return results


def get_preferred_standalone_browser() -> tuple[str | None, str | None]:
    items = scan_local_browsers()

    priorities = [
        ("chromium", "playwright-runtime"),
        ("chromium", "system"),
        ("chrome", "system"),
        ("msedge", "system"),
        ("firefox", "system"),
        ("webkit", "playwright-runtime"),
    ]

    for browser, source in priorities:
        for entry in items:
            if entry.get("browser") != browser or entry.get("source") != source:
                continue
            executable_path = str(entry.get("executable_path") or "").strip() or None
            if browser == "webkit":
                executable_path = None
            return browser, executable_path

    return "chromium", None


def build_standalone_launch_overrides(
    browser: str | None,
    executable_path: str | None,
) -> tuple[str | None, str | None]:
    normalized_browser = normalize_standalone_browser(browser)
    normalized_path = str(executable_path or "").strip() or None

    if normalized_browser == "webkit":
        return normalized_browser, None

    if normalized_path:
        return normalized_browser, normalized_path

    return normalized_browser, None

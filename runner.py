import os
import subprocess
import sys
import time

import requests

UPSTREAM_MAIN = "/app/upstream/main.py"
DEFAULT_READ_NUM = 40


def send_bark(title: str, body: str) -> None:
    key = os.getenv("BARK_KEY", "").strip()
    if not key:
        return

    server = os.getenv("BARK_SERVER", "https://api.day.app").rstrip("/")
    payload = {
        "device_key": key,
        "title": title,
        "body": body,
        "group": os.getenv("BARK_GROUP", "wxread"),
    }

    try:
        response = requests.post(f"{server}/push", json=payload, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        print(f"Bark push failed: {exc}", file=sys.stderr, flush=True)


def read_num() -> int:
    try:
        return int(os.getenv("READ_NUM") or DEFAULT_READ_NUM)
    except ValueError:
        return DEFAULT_READ_NUM


def planned_minutes() -> str:
    return f"{read_num() * 0.5:g}"


def run_timeout_seconds() -> int:
    # Upstream sleeps for about 30 seconds per read. Keep a generous guard so a
    # network request without its own timeout cannot leave the daily job stuck.
    return max(3600, max(read_num(), 1) * 45 + 300)


def upstream_version() -> str:
    return os.getenv("WXREAD_UPSTREAM_SHA", "unknown")[:12]


def main() -> int:
    if not os.getenv("WXREAD_CURL_BASH", "").strip():
        message = "WXREAD_CURL_BASH is not configured."
        print(message, file=sys.stderr, flush=True)
        send_bark("微信读书-失败", f"{message}\n上游版本：{upstream_version()}")
        return 2

    started = time.monotonic()
    try:
        result = subprocess.run(
            [sys.executable, UPSTREAM_MAIN],
            cwd="/app/upstream",
            check=False,
            timeout=run_timeout_seconds(),
        )
    except subprocess.TimeoutExpired:
        elapsed = time.monotonic() - started
        message = f"自动阅读超时\n运行耗时：{elapsed / 60:.1f} 分钟\n上游版本：{upstream_version()}"
        print(message.replace("\n", " | "), file=sys.stderr, flush=True)
        send_bark("微信读书-失败", message)
        return 124

    elapsed = time.monotonic() - started

    if result.returncode == 0:
        send_bark(
            "微信读书-成功",
            f"自动阅读完成\n计划阅读：{planned_minutes()} 分钟\n运行耗时：{elapsed / 60:.1f} 分钟",
        )
    else:
        send_bark(
            "微信读书-失败",
            f"自动阅读失败\n退出码：{result.returncode}\n上游版本：{upstream_version()}\n请查看容器日志。",
        )

    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())

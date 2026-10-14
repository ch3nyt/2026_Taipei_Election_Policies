#!/usr/bin/env python3
"""在逐字稿中找關鍵字，列出時間點連結（用來替紀錄補上影片時間點）。

用法：
    python3 tools/find_in_transcripts.py 臨托
    python3 tools/find_in_transcripts.py 婚育宅 青年宅 --video 8WH53TUHS-s --context 1

輸出每個命中位置的時間、連結與前後文（預設前後各 1 段）。
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def fmt(sec: float) -> str:
    s = int(sec)
    return f"{s // 3600:d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("keywords", nargs="+")
    ap.add_argument("--video", action="append", help="只搜尋指定影片 ID，可重複")
    ap.add_argument("--context", type=int, default=1, help="前後各顯示幾段")
    ap.add_argument("--dir", default=str(ROOT / "transcripts"))
    args = ap.parse_args()

    files = sorted(Path(args.dir).glob("*.json"))
    if args.video:
        files = [f for f in files if f.stem in args.video]
    for f in files:
        rows = json.loads(f.read_text(encoding="utf-8"))
        hits = [i for i, r in enumerate(rows) if any(k in r["text"] for k in args.keywords)]
        shown = set()
        for i in hits:
            if i in shown:
                continue
            lo, hi = max(0, i - args.context), min(len(rows), i + args.context + 1)
            shown.update(range(lo, hi))
            ctx = "".join(r["text"] for r in rows[lo:hi])
            print(f"{f.stem} {fmt(rows[i]['start'])} t={int(rows[i]['start'])} | {ctx}")


if __name__ == "__main__":
    main()

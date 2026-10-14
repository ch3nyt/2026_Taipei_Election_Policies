#!/usr/bin/env python3
"""在自己的電腦上抓 YouTube 字幕，輸出帶時間點連結的逐字稿。

雲端環境會被 YouTube 擋下，請在自己的電腦執行：

    pip install youtube-transcript-api
    python3 tools/fetch_captions_local.py 8WH53TUHS-s w8yObdiOzYM
    python3 tools/fetch_captions_local.py 8WH53TUHS-s --grep 臨托

輸出存在 transcripts/<影片ID>.md，每一行都附可直接跳到該秒數的連結，
方便核對「候選人在影片幾分幾秒說了什麼」。

注意：自動字幕常聽錯人名與數字，引用數字前請點連結聽原音確認。
逐字稿僅供核對用，請勿整份公開轉載。
"""
import argparse
import sys
from pathlib import Path

try:
    from youtube_transcript_api import YouTubeTranscriptApi
except ImportError:
    sys.exit("請先執行：pip install youtube-transcript-api")

LANGS = ["zh-TW", "zh-Hant", "zh", "zh-Hans", "zh-CN"]


def fmt(sec: float) -> str:
    s = int(sec)
    return f"{s // 3600:d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video_ids", nargs="+")
    ap.add_argument("--grep", help="只輸出含有這個關鍵字的段落")
    args = ap.parse_args()

    out_dir = Path(__file__).resolve().parent.parent / "transcripts"
    out_dir.mkdir(exist_ok=True)
    api = YouTubeTranscriptApi()
    for vid in args.video_ids:
        try:
            tl = api.list(vid)
            try:
                tr = tl.find_transcript(LANGS)
            except Exception:
                tr = next(iter(tl))
            rows = tr.fetch()
        except Exception as e:  # noqa: BLE001
            print(f"{vid}: 無法取得字幕（{type(e).__name__}）")
            continue
        kind = "自動字幕" if tr.is_generated else "人工字幕"
        lines = [f"# {vid}（{kind}，{tr.language_code}）", ""]
        for s in rows:
            if args.grep and args.grep not in s.text:
                continue
            url = f"https://www.youtube.com/watch?v={vid}&t={int(s.start)}s"
            lines.append(f"- [{fmt(s.start)}]({url}) {s.text}")
        path = out_dir / f"{vid}.md"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"{vid}: {len(lines) - 2} 行 → {path}")


if __name__ == "__main__":
    main()

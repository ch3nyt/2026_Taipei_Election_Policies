#!/usr/bin/env python3
"""在自己的電腦上把 YouTube 影片轉成逐字稿（不需要影片有字幕）。

流程：yt-dlp 下載音訊 → faster-whisper 語音辨識 → 轉繁體 → 輸出帶時間點連結的逐字稿。
全部在本機執行，不使用任何雲端 AI 額度。

安裝：
    pip install yt-dlp faster-whisper opencc-python-reimplemented
    （另需 ffmpeg）

用法：
    python3 tools/transcribe_local.py 8WH53TUHS-s E2eL-qVqgUI
    python3 tools/transcribe_local.py 8WH53TUHS-s --model medium   # 較準但較慢

輸出（transcripts/ 已列入 .gitignore，不會上傳）：
    transcripts/<影片ID>.json   每段的開始秒數、結束秒數、文字
    transcripts/<影片ID>.md     每行附可直接跳到該秒數的 YouTube 連結
    transcripts/<影片ID>.log    進度紀錄

注意：語音辨識常聽錯人名與數字，引用前請點時間點連結聽原音確認。
逐字稿僅供核對用，請勿整份公開轉載。
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

PROMPT = ("以下是台北市長選舉的記者會與政見發表。沈伯洋、蔣萬安、台北市政府、北士科、"
          "輝達、松山機場、TPASS、捷運、社會住宅、婚育宅、青年宅、臨托、長照、敬老卡、"
          "內湖科技園區、民生汐止線、環狀線東環段、都更、AI園區。")


def fmt(sec: float) -> str:
    s = int(sec)
    return f"{s // 3600:d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def log(path: Path, msg: str) -> None:
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def download(vid: str, audio_dir: Path) -> Path:
    audio_dir.mkdir(parents=True, exist_ok=True)
    existing = sorted(audio_dir.glob(f"{vid}.*"))
    if existing:
        return existing[0]
    subprocess.run([
        sys.executable, "-m", "yt_dlp", "-q", "--no-warnings",
        "-f", "ba[abr<=64]/worstaudio/bestaudio",
        "-o", str(audio_dir / f"{vid}.%(ext)s"),
        f"https://www.youtube.com/watch?v={vid}",
    ], check=True)
    return sorted(audio_dir.glob(f"{vid}.*"))[0]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("video_ids", nargs="+")
    ap.add_argument("--model", default="small", help="tiny / base / small / medium")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "transcripts"))
    ap.add_argument("--audio-dir", default=None, help="音訊暫存位置，預設 <out>/audio")
    args = ap.parse_args()

    from faster_whisper import WhisperModel
    try:
        from opencc import OpenCC
        to_trad = OpenCC("s2twp").convert
    except ImportError:
        to_trad = lambda s: s  # noqa: E731

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    audio_dir = Path(args.audio_dir) if args.audio_dir else out / "audio"
    model = WhisperModel(args.model, device="cpu", compute_type="int8")

    for vid in args.video_ids:
        logf = out / f"{vid}.log"
        if (out / f"{vid}.json").exists():
            log(logf, "已有逐字稿，略過")
            continue
        log(logf, "下載音訊")
        audio = download(vid, audio_dir)
        log(logf, f"開始辨識（模型 {args.model}）：{audio.name}")
        # 用 ffmpeg 解碼成 16kHz 單聲道，避開部分 PyAV 版本不相容的問題
        import numpy as np
        pcm = subprocess.run(
            ["ffmpeg", "-nostdin", "-loglevel", "error", "-i", str(audio),
             "-f", "s16le", "-ac", "1", "-ar", "16000", "-"],
            check=True, stdout=subprocess.PIPE).stdout
        samples = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768.0
        # 每 10 分鐘一段分開辨識，避免長影片佔用過多記憶體
        total = len(samples) / 16000
        chunk = 600 * 16000
        rows = []
        for off in range(0, len(samples), chunk):
            segments, _ = model.transcribe(
                samples[off:off + chunk], language="zh", beam_size=1, vad_filter=True,
                initial_prompt=PROMPT, condition_on_previous_text=False,
            )
            base = off / 16000
            for seg in segments:
                rows.append({"start": round(base + seg.start, 1), "end": round(base + seg.end, 1),
                             "text": to_trad(seg.text.strip())})
            log(logf, f"進度 {fmt(min(base + 600, total))} / {fmt(total)}")
        (out / f"{vid}.json").write_text(json.dumps(rows, ensure_ascii=False, indent=0), encoding="utf-8")
        lines = [f"# {vid}（語音辨識，模型 {args.model}，未經人工校對）", ""]
        for r in rows:
            url = f"https://www.youtube.com/watch?v={vid}&t={int(r['start'])}s"
            lines.append(f"- [{fmt(r['start'])}]({url}) {r['text']}")
        (out / f"{vid}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        log(logf, f"完成：{len(rows)} 段")


if __name__ == "__main__":
    main()

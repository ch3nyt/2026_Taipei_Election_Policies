#!/usr/bin/env python3
"""檢查資料格式，並輸出 CSV 與統計。

用法：python3 scripts/validate.py
- 任何錯誤都會列出並以非零狀態結束。
- 通過後會重新產生 data/records.csv（方便用 Excel / Google 試算表開啟）。
"""
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

TOPICS = [
    "居住與都更", "交通", "育兒與教育", "長照與高齡", "青年與就業",
    "產業與AI", "城市治理", "環境與韌性", "運動與文化",
]
STATUSES = {"提議", "規劃中", "已宣布", "已上路"}
CAPACITIES = {"參選人", "市長／市府"}
IMPL_KEYS = ["method", "timeline", "budget", "authority", "target"]
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def main() -> int:
    errors = []
    sources = json.loads((DATA / "sources.json").read_text(encoding="utf-8"))
    records = json.loads((DATA / "records.json").read_text(encoding="utf-8"))
    cands = json.loads((DATA / "candidates.json").read_text(encoding="utf-8"))

    cand_keys = {c["key"] for c in cands["candidates"]}
    src_by_id = {}
    for s in sources:
        if s["id"] in src_by_id:
            errors.append(f"來源 id 重複：{s['id']}")
        src_by_id[s["id"]] = s
        if not s["url"].startswith("https://"):
            errors.append(f"{s['id']}：網址需為 https")
        if s["kind"] not in {"新聞", "影片", "官方"}:
            errors.append(f"{s['id']}：kind 不在允許清單")
        if s.get("date") and not DATE_RE.match(s["date"]):
            errors.append(f"{s['id']}：日期格式錯誤 {s['date']}")

    def check_src(ref, where):
        if ref not in src_by_id:
            errors.append(f"{where}：找不到來源 {ref}")

    used = set()
    for c in cands["candidates"]:
        refs = [c.get("slogan_src")] + list(c.get("platform_status_srcs", []))
        for ref in filter(None, refs):
            check_src(ref, f"候選人 {c['key']}")
            used.add(ref)
    for m in cands["election"]["milestones"]:
        check_src(m["src"], "選舉日程")
        used.add(m["src"])
    if cands["election"].get("other_candidates_src"):
        used.add(cands["election"]["other_candidates_src"])

    ids = [r["id"] for r in records]
    dup = [i for i, n in Counter(ids).items() if n > 1]
    if dup:
        errors.append(f"紀錄 id 重複：{dup}")
    id_set = set(ids)

    for r in records:
        rid = r["id"]
        if r["candidate"] not in cand_keys:
            errors.append(f"{rid}：候選人代碼錯誤")
        if not rid.startswith(r["candidate"] + "-"):
            errors.append(f"{rid}：id 前綴與候選人不符")
        if r["topic"] not in TOPICS:
            errors.append(f"{rid}：議題 {r['topic']} 不在清單")
        if r["status"] not in STATUSES:
            errors.append(f"{rid}：狀態 {r['status']} 不在清單")
        if r["capacity"] not in CAPACITIES:
            errors.append(f"{rid}：身分 {r['capacity']} 不在清單")
        if not DATE_RE.match(r["date"]):
            errors.append(f"{rid}：日期格式錯誤")
        if list(r["implementation"].keys()) != IMPL_KEYS:
            errors.append(f"{rid}：implementation 欄位需為 {IMPL_KEYS}")
        if not r["sources"]:
            errors.append(f"{rid}：至少需要一個來源")
        for s in r["sources"]:
            check_src(s, rid)
            if s in src_by_id and src_by_id[s]["kind"] == "影片":
                errors.append(f"{rid}：影片請放在 videos 欄位")
        for vt in r.get("video_times", []):
            if vt["src"] not in r["videos"]:
                errors.append(f"{rid}：video_times 的影片 {vt['src']} 不在 videos 欄位")
            if not isinstance(vt["t"], int) or vt["t"] < 0 or not vt.get("label"):
                errors.append(f"{rid}：video_times 格式錯誤")
        for v in r["videos"]:
            check_src(v, rid)
            if v in src_by_id and src_by_id[v]["kind"] != "影片":
                errors.append(f"{rid}：videos 只能放影片來源")
        for item in r["context"] + r["responses"]:
            check_src(item["src"], rid)
            used.add(item["src"])
        used.update(r["sources"], r["videos"])
        for rel in r["related"]:
            if rel not in id_set:
                errors.append(f"{rid}：related 找不到 {rel}")

    if errors:
        print("檢查未通過：")
        for e in errors:
            print("  -", e)
        return 1

    # 匯出 CSV
    with open(DATA / "records.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["id", "候選人", "議題", "標題", "日期", "身分", "狀態", "摘要",
                    "具體做法", "時程", "經費與財源", "執行單位與所需同意", "量化目標",
                    "來源網址", "影片網址"])
        names = {c["key"]: c["name"] for c in cands["candidates"]}
        for r in records:
            im = r["implementation"]
            w.writerow([
                r["id"], names[r["candidate"]], r["topic"], r["title"], r["date"],
                r["capacity"], r["status"], r["summary"],
                *[im[k] or "" for k in IMPL_KEYS],
                " ".join(src_by_id[s]["url"] for s in r["sources"]),
                " ".join(src_by_id[v]["url"] for v in r["videos"]),
            ])

    # 統計（對稱檢查用）
    print(f"檢查通過：{len(records)} 筆紀錄、{len(sources)} 個來源")
    orphans = sorted(set(src_by_id) - used)
    if orphans:
        print("  提醒：以下來源沒有被任何紀錄引用：", orphans)
    for key in sorted(cand_keys):
        rs = [r for r in records if r["candidate"] == key]
        n_resp = sum(len(r["responses"]) for r in rs)
        n_single = sum(1 for r in rs if len(r["sources"]) < 2)
        print(f"  {key}: 回應 {n_resp} 則；單一來源紀錄 {n_single} 筆")
    for key in sorted(cand_keys):
        rs = [r for r in records if r["candidate"] == key]
        filled = sum(1 for r in rs for k in IMPL_KEYS if r["implementation"][k])
        print(f"  {key}: {len(rs)} 筆；落實欄位已填 {filled}/{len(rs) * len(IMPL_KEYS)}")
        print("    議題分布：", dict(Counter(r["topic"] for r in rs)))
        print("    身分分布：", dict(Counter(r["capacity"] for r in rs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())

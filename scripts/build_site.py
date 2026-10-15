#!/usr/bin/env python3
"""產生 GitHub Pages 用的網站檔案。

- index.html：由 site/page.html 加上完整外框，並把「30 秒看懂」與全部政見預先寫進 HTML，
  讓搜尋引擎與 AI 不執行 JavaScript 也讀得到內容（瀏覽器載入後會換成互動版）。
- topics/*.html：每個議題一頁的靜態比較頁，方便搜尋與單獨分享。
- quiz.html：複製 site/quiz.html，補上連結預覽資訊。
- sitemap.xml、robots.txt、llms.txt：給搜尋引擎與 AI 爬蟲。
- og.png：連結預覽圖（需要 playwright；沒有就略過，沿用舊圖）。

修改網頁請改 site/page.html 或 site/quiz.html，再執行本腳本。
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
BASE = "https://ch3nyt.github.io/2026_Taipei_Election_Policies/"
SITE_TITLE = "2026 台北市長政見比較｜蔣萬安、沈伯洋政見對照與來源"
IMPL = [("method", "具體做法"), ("timeline", "時程"), ("budget", "經費與財源"),
        ("authority", "執行單位與所需同意"), ("target", "量化目標")]
SLUGS = {
    "居住與都更": "housing", "交通": "transport", "育兒與教育": "childcare-education",
    "長照與高齡": "elderly-care", "青年與就業": "youth-jobs", "產業與AI": "industry-ai",
    "城市治理": "governance", "環境與韌性": "environment", "運動與文化": "sports-culture",
    "兩岸城市交流": "cross-strait", "城市韌性與民防": "civil-defense", "毒品防制": "drug-policy",
    "中央與地方財政": "fiscal", "食品安全": "food-safety", "能源與供電": "energy",
}


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


e = html.escape
records = load("records.json")
sources = {s["id"]: s for s in load("sources.json")}
cands = load("candidates.json")
meta = load("meta.json")
highlights = load("highlights.json")
national = {n["topic"]: n["mayor_role"] for n in load("national_topics.json")}
order = cands["candidates"]
names = {c["key"]: c["name"] for c in order}
desc = meta["description"]
updated = meta["last_updated"]


def head(title, description, url, extra=""):
    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="台北市長政見對照">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE}og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:locale" content="zh_TW">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{BASE}og.png">
{extra}"""


def src_line(sid):
    s = sources[sid]
    date = s.get("date") or ""
    return f'<li>{e(s["outlet"])} {e(date)}：<a href="{e(s["url"])}">{e(s["title"])}</a></li>'


def static_record(r, href_prefix=""):
    im = r["implementation"]
    rows = "".join(f"<li>{lbl}：{e(im[k]) if im[k] else '目前來源未提及'}</li>" for k, lbl in IMPL)
    srcs = "".join(src_line(s) for s in r["sources"])
    return (f'<article id="{r["id"]}"><h4>{e(r["title"])}</h4>'
            f'<p>{e(names[r["candidate"]])}｜{e(r["capacity"])}｜{e(r["status"])}｜{e(r["date"])}</p>'
            f'<p>{e(r["summary"])}</p><ul>{rows}</ul><ul>{srcs}</ul></article>')


def static_highlights():
    out = [f"<h2>{e(highlights['title'])}</h2><p>{e(highlights['note'])}</p><dl>"]
    for it in highlights["items"]:
        out.append(f"<dt>{e(it['topic'])}</dt>")
        for c in order:
            x = it.get(c["key"])
            if x:
                out.append(f"<dd>{e(c['name'])}：{e(x['text'])}</dd>")
    out.append("</dl>")
    return "".join(out)


def topics_in_use():
    seen = []
    for t in SLUGS:
        if any(r["topic"] == t for r in records):
            seen.append(t)
    return seen


def static_list():
    out = []
    for t in topics_in_use():
        out.append(f'<section><h3><a href="topics/{SLUGS[t]}.html">{e(t)}</a></h3>')
        for c in order:
            rs = [r for r in records if r["topic"] == t and r["candidate"] == c["key"]]
            out.append(f"<h4>{e(c['name'])}</h4>")
            out.append("".join(static_record(r) for r in rs) or "<p>本資料庫目前沒有這個議題的紀錄。</p>")
        out.append("</section>")
    return "".join(out)


TOPIC_CSS = """:root{--paper:#f5f4f7;--surface:#fff;--ink:#1f1d24;--muted:#625e6b;--line:#dcd9e2;--accent:#5a3e75;color-scheme:light}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--paper:#151419;--surface:#1d1c23;--ink:#ebe9f0;--muted:#a6a2b0;--line:#34323d;--accent:#c4a8e2;color-scheme:dark}}
:root[data-theme="dark"]{--paper:#151419;--surface:#1d1c23;--ink:#ebe9f0;--muted:#a6a2b0;--line:#34323d;--accent:#c4a8e2;color-scheme:dark}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font-family:"Noto Sans TC","PingFang TC","Microsoft JhengHei",system-ui,sans-serif;line-height:1.7}
a{color:var(--accent)}.wrap{max-width:1080px;margin:0 auto;padding-inline:16px;padding-block:24px 56px}
h1{font-family:"Noto Serif TC","Songti TC",serif;font-size:clamp(24px,5vw,34px);line-height:1.3;margin:8px 0}
.muted{color:var(--muted);font-size:14.5px}.cols{display:grid;gap:20px;margin-top:20px}@media(min-width:860px){.cols{grid-template-columns:1fr 1fr}}
.col{min-width:0;display:grid;gap:12px;align-content:start}.col h2{font-size:18px;margin:0;padding-bottom:4px;border-bottom:1px solid var(--line)}
article{background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:14px 16px;min-width:0;overflow-wrap:anywhere}
article h3{margin:0 0 4px;font-size:17px}article p{margin:4px 0}article ul{margin:6px 0;padding-left:1.1em;font-size:14.5px}
.role{background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:10px 14px;margin-top:12px}
nav{display:flex;flex-wrap:wrap;gap:8px 14px;margin-top:28px;font-size:14.5px}"""


def topic_page(t):
    slug = SLUGS[t]
    url = f"{BASE}topics/{slug}.html"
    title = f"2026 台北市長「{t}」政見比較：沈伯洋、蔣萬安"
    rs_all = [r for r in records if r["topic"] == t]
    first = "；".join(f"{names[c['key']]}：" + "、".join(r["title"] for r in rs_all if r["candidate"] == c["key"])[:80]
                     for c in order if any(r["candidate"] == c["key"] for r in rs_all))
    description = f"{t}議題下兩位台北市長候選人的政見、落實方式與新聞來源。{first}"
    cols = []
    for c in order:
        rs = [r for r in rs_all if r["candidate"] == c["key"]]
        body = "".join(
            f'<article id="{r["id"]}"><h3>{e(r["title"])}</h3>'
            f'<p class="muted">{e(r["capacity"])}｜{e(r["status"])}｜{e(r["date"])}</p><p>{e(r["summary"])}</p>'
            "<ul>" + "".join(f"<li>{lbl}：{e(r['implementation'][k]) if r['implementation'][k] else '目前來源未提及'}</li>" for k, lbl in IMPL) + "</ul>"
            "<p class=\"muted\">來源</p><ul>" + "".join(src_line(s) for s in r["sources"]) + "</ul>"
            f'<p class="muted"><a href="../index.html#{r["id"]}">在互動版查看</a></p></article>'
            for r in rs) or "<p class=\"muted\">本資料庫目前沒有這個議題的紀錄。</p>"
        cols.append(f'<div class="col"><h2>{e(c["name"])}（{e(c["party"])}）</h2>{body}</div>')
    role = f'<p class="role"><strong>市長能管到的部分：</strong>{e(national[t])}</p>' if t in national else ""
    nav = "".join(f'<a href="{SLUGS[x]}.html">{e(x)}</a>' for x in topics_in_use() if x != t)
    ld = json.dumps({"@context": "https://schema.org", "@type": "WebPage", "name": title, "url": url,
                     "inLanguage": "zh-Hant-TW", "dateModified": updated,
                     "isPartOf": {"@type": "WebSite", "name": "台北市長政見對照", "url": BASE}}, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
{head(title, description, url, f'<script type="application/ld+json">{ld}</script>')}
<style>{TOPIC_CSS}</style>
</head>
<body><div class="wrap">
<p class="muted"><a href="../index.html">← 台北市長政見對照（完整互動版）</a>｜最後更新 {e(updated)}</p>
<h1>{e(title)}</h1>
<p>整理兩位台北市長候選人在「{e(t)}」議題的政見與落實方式。每筆都附新聞或官方來源，摘要以我們自己的話改寫；來源沒提到的落實細節標示「目前來源未提及」。</p>
{role}
<div class="cols">{''.join(cols)}</div>
<nav><strong>其他議題：</strong>{nav}</nav>
<p class="muted">發現錯誤請到 <a href="{e(meta['repo'])}/issues">GitHub</a> 回報。編輯與查核原則見 <a href="{e(meta['repo'])}/blob/main/METHODOLOGY.md">METHODOLOGY.md</a>。</p>
</div></body></html>
"""


def build_index():
    body = (ROOT / "site" / "page.html").read_text(encoding="utf-8")
    body = re.sub(r"<title>.*?</title>\s*", "", body, count=1, flags=re.S)
    body = body.replace('<section id="highlights" class="hl" aria-label="30 秒看懂"></section>',
                        f'<section id="highlights" class="hl" aria-label="30 秒看懂">{static_highlights()}</section>', 1)
    body = body.replace('<main id="list"><p class="loading">資料載入中…</p></main>',
                        f'<main id="list">{static_list()}</main>', 1)
    ld = json.dumps({
        "@context": "https://schema.org", "@type": "Dataset",
        "name": "2026 台北市長候選人政見資料庫",
        "description": desc, "url": BASE, "inLanguage": "zh-Hant-TW", "dateModified": updated,
        "isAccessibleForFree": True, "keywords": ["2026 台北市長", "蔣萬安", "沈伯洋", "政見比較", "九合一選舉"],
        "creator": {"@type": "Person", "name": "ch3nyt", "url": "https://github.com/ch3nyt"},
        "distribution": [
            {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": BASE + "data/records.json"},
            {"@type": "DataDownload", "encodingFormat": "text/csv", "contentUrl": BASE + "data/records.csv"}],
    }, ensure_ascii=False)
    page = f"""<!doctype html>
<html lang="zh-Hant">
<head>
{head(SITE_TITLE, desc, BASE, f'<script type="application/ld+json">{ld}</script>')}
<!-- 本檔由 scripts/build_site.py 產生，請勿直接修改，改 site/page.html -->
</head>
<body>
{body}
</body>
</html>
"""
    (ROOT / "index.html").write_text(page, encoding="utf-8")


def build_quiz():
    q = (ROOT / "site" / "quiz.html").read_text(encoding="utf-8")
    title = "11 題政策盲測｜2026 台北市長：不看名字，你比較認同誰的政策？"
    qdesc = "從沈伯洋、蔣萬安的公開政見隨機抽 11 題，不顯示名字，選你比較認同的做法，最後揭曉。每個選項都附新聞來源。"
    q = re.sub(r"<title>.*?</title>", "", q, count=1, flags=re.S)
    q = re.sub(r'<meta name="description"[^>]*>', "", q, count=1)
    q = re.sub(r'<meta charset="utf-8">\s*<meta name="viewport"[^>]*>', head(title, qdesc, BASE + "quiz.html"), q, count=1)
    (ROOT / "quiz.html").write_text(q, encoding="utf-8")


def build_meta_files(topic_slugs):
    urls = [BASE, BASE + "quiz.html"] + [f"{BASE}topics/{s}.html" for s in topic_slugs]
    sm = "".join(f"<url><loc>{u}</loc><lastmod>{updated}</lastmod></url>" for u in urls)
    (ROOT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>\n', encoding="utf-8")
    (ROOT / "robots.txt").write_text(
        "# 歡迎搜尋引擎與 AI 助理讀取本站內容；引用時請附上原始新聞來源。\n"
        "User-agent: *\nAllow: /\n\n"
        "User-agent: GPTBot\nAllow: /\n\nUser-agent: OAI-SearchBot\nAllow: /\n\n"
        "User-agent: ClaudeBot\nAllow: /\n\nUser-agent: Claude-SearchBot\nAllow: /\n\n"
        "User-agent: PerplexityBot\nAllow: /\n\nUser-agent: Google-Extended\nAllow: /\n\n"
        f"Sitemap: {BASE}sitemap.xml\n", encoding="utf-8")
    lines = [
        "# 2026 台北市長政見比較（蔣萬安、沈伯洋）", "",
        f"> {desc}", "",
        f"最後更新：{updated}。每筆政見都附新聞、官方或影片來源；摘要為本站改寫，引用時請以原始來源為準。",
        "本站為中立整理，不推薦任何候選人。", "",
        "## 主要頁面",
        f"- [完整互動版]({BASE})：依議題並排比較，含落實說明、相關回應、過去職務紀錄",
        f"- [11 題政策盲測]({BASE}quiz.html)",
    ]
    lines += [f"- [{t}議題比較]({BASE}topics/{SLUGS[t]}.html)" for t in topics_in_use()]
    lines += ["", "## 開放資料",
              f"- [全部政見紀錄 JSON]({BASE}data/records.json)",
              f"- [全部政見紀錄 CSV]({BASE}data/records.csv)",
              f"- [來源清單]({BASE}data/sources.json)",
              f"- [過去職務紀錄]({BASE}data/track_records.json)",
              f"- [編輯與查核原則]({meta['repo']}/blob/main/METHODOLOGY.md)", ""]
    (ROOT / "llms.txt").write_text("\n".join(lines), encoding="utf-8")
    (ROOT / ".nojekyll").write_text("", encoding="utf-8")


def build_og():
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("略過 og.png（沒有 playwright）")
        return
    rows = "".join(f"<div class='r'><b>{e(it['topic'])}</b></div>" for it in highlights["items"])
    card = f"""<html><head><meta charset="utf-8"><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@500;700&family=Noto+Serif+TC:wght@700&display=swap">
<style>body{{margin:0;width:1200px;height:630px;background:#f5f4f7;color:#1f1d24;font-family:'Noto Sans TC',sans-serif;display:flex}}
.l{{flex:1;padding:64px 70px;display:flex;flex-direction:column;justify-content:space-between;border-right:3px solid #1f1d24}}
h1{{font-family:'Noto Serif TC',serif;font-size:76px;line-height:1.15;margin:0}}.s{{font-size:30px;color:#625e6b;margin-top:18px}}
.n{{font-size:44px;font-weight:700}}.n span{{color:#625e6b;font-weight:500;font-size:30px;margin:0 14px}}
.f{{font-size:24px;color:#5a3e75}}.rt{{width:330px;padding:64px 40px;display:flex;flex-direction:column;gap:18px;justify-content:center}}
.r{{font-size:30px;border-bottom:1px solid #dcd9e2;padding-bottom:10px}}.t{{font-size:22px;color:#625e6b}}</style></head>
<body><div class="l"><div><div class="s">2026 台北市長選舉</div><h1>政見對照</h1>
<div class="n" style="margin-top:28px">沈伯洋<span>×</span>蔣萬安</div></div>
<div class="f">每筆政見附來源｜11 題政策盲測｜開放資料</div></div>
<div class="rt"><div class="t">議題並排比較</div>{rows}<div class="t">…等 15 個議題</div></div></body></html>"""
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": 1200, "height": 630})
            pg.set_content(card, wait_until="networkidle")
            pg.wait_for_timeout(500)
            pg.screenshot(path=str(ROOT / "og.png"))
            b.close()
    except Exception as ex:  # noqa: BLE001
        print("略過 og.png：", ex)


if __name__ == "__main__":
    build_index()
    build_quiz()
    out = ROOT / "topics"
    out.mkdir(exist_ok=True)
    slugs = []
    for t in topics_in_use():
        (out / f"{SLUGS[t]}.html").write_text(topic_page(t), encoding="utf-8")
        slugs.append(SLUGS[t])
    build_meta_files(slugs)
    build_og()
    print(f"index.html、quiz.html、{len(slugs)} 個議題頁、sitemap.xml、robots.txt、llms.txt 已更新")

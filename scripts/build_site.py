#!/usr/bin/env python3
"""由 site/page.html 產生 GitHub Pages 用的 index.html。

site/page.html 是頁面主體（不含 <html>/<head>/<body> 外框），
這裡補上完整的 HTML 文件外框。修改頁面請改 site/page.html，再執行本腳本。
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
body = (ROOT / "site" / "page.html").read_text(encoding="utf-8")
meta = json.loads((ROOT / "data" / "meta.json").read_text(encoding="utf-8"))
desc = meta["description"].replace('"', "&quot;")

html = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="{desc}">
<!-- 本檔由 scripts/build_site.py 產生，請勿直接修改，改 site/page.html -->
</head>
<body>
{body}
</body>
</html>
"""
(ROOT / "index.html").write_text(html, encoding="utf-8")
(ROOT / "quiz.html").write_text((ROOT / "site" / "quiz.html").read_text(encoding="utf-8"), encoding="utf-8")
print("index.html、quiz.html 已更新")

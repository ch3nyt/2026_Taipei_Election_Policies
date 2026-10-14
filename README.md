# 2026 台北市長政見對照

使用 Claude Code 透過網路爬蟲，整理蔣萬安、沈伯洋的北市選舉政見，讓大家好比較雙方的異同。每則資訊都會附上影片、新聞的出處，如果有誤請不吝告知， 也祝大家支持的候選人都成功當選~

## 怎麼看

- **網站**：開啟本 repo 的 GitHub Pages 網址，可以依議題篩選、搜尋，並排比較兩位候選人。
- **原始資料**：`data/records.json`（全部紀錄）、`data/sources.json`（來源清單）、`data/records.csv`（可用 Excel 或 Google 試算表開啟）。

每筆紀錄都有：
- 政策摘要（以我們自己的話改寫）
- **落實說明**：具體做法、時程、經費與財源、執行單位與所需同意、量化目標。來源沒提到的欄位會標示「目前來源未提及」
- 與政策內容相關的回應
- 可點開核對的新聞與影片來源

## 發現錯誤？

請到 [Issues](../../issues/new/choose) 選「資料更正」，附上紀錄編號（例如 `shen-013`）與正確的來源網址。網站每張卡片右下角也有「回報錯誤」連結。所有修改都會留下公開紀錄。

## 收錄原則（摘要）

1. 只收錄政策與落實方式；人身攻擊、爭議指控與政治評論不收錄。
2. 每一筆都要有可核對的來源，數字以候選人或市府的一手說法為準。
3. 雙方使用同一套措辭與收錄標準。
4. 現任市長以市長身分推動的市政措施，標示「市長／市府」，與參選人政見分開。
5. 筆數多寡反映政見公布時間與蒐集進度，不代表政見好壞。

完整說明見 [METHODOLOGY.md](METHODOLOGY.md)，修改紀錄見 [CHANGELOG.md](CHANGELOG.md)。

## 檔案結構

```
data/
  records.json      全部紀錄
  sources.json      來源清單（標題、日期、記者、網址）
  candidates.json   候選人與選舉日程
  meta.json         最後更新日期
  records.csv       由 validate.py 自動產生
site/page.html      網頁主體（修改網頁請改這個檔）
index.html          由 build_site.py 產生，GitHub Pages 使用
scripts/
  validate.py       檢查資料格式並輸出 CSV 與雙方統計
  build_site.py     產生 index.html
tools/
  fetch_captions_local.py  在自己電腦上抓 YouTube 字幕（附時間點）
UPDATING.md         每日更新流程
```

## 本機預覽

```bash
python3 scripts/validate.py
python3 scripts/build_site.py
python3 -m http.server 8000   # 打開 http://localhost:8000
```

## 著作權

新聞與影片內容的著作權屬於原媒體，本專案只提供連結與自行改寫的摘要。

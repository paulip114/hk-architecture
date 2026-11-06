# 體量研究方法（香港）

目的：喺未畫平面之前，用最少時間搵出「法規容許、商業可行、城市合理」嘅體量，再揀一個深化。所有數字都係設計階段估算，交畀客戶或入則前要用真實面積表再跑 `tools/bpr_check.py`。

## 1. 先定發展參數（Development parameters）

由嚴到寬逐層疊，最嚴嗰條話事：

| 來源 | 要查嘅嘢 | 備註 |
| --- | --- | --- |
| 地契 (Lease / Conditions of Grant) | 最高／最低 GFA、高度、上蓋、Design & Disposition、Non-building area、車位、綠化條款 | 地契嘅 GFA 定義可以同 B(P)R 唔同，要逐條睇 |
| 分區計劃大綱圖 OZP | 用途地帶、最高 PR／GFA、高度 (mPD)、SC、非建築用地、建築物間距、後移 | 睇 Notes 同 Explanatory Statement；高度係 mPD，唔係由街面量 |
| B(P)R Cap. 123F | 地盤類別、First Schedule SC／PR（按高度分級）、reg 22 獻地獎勵、休憩用地 | `bpr/bpr-rules.md`，`tools/bpr_check.py` |
| PNAP APP-151 / APP-152 | GFA 寬免 10% 上限；SBD：樓宇間距、後移、綠化覆蓋率 | 申請寬免嘅前提，體量階段已要預留 |
| FS Code 2011 | 樓梯數目、避火層（> 25 層要設，相距唔超過 25 層；Use Class 6 為 20 層，B18）、EVA 覆蓋 | `fs-code/moe-rules.md`、`fs-code/cd-rules.md` |
| HKPSG / 其他 | 交通、噪音（第 9 章）、空氣流通 (AVA)、視覺 (TPB PG-No. 41) | 大型或規劃申請項目要做評估 |

快速判斷：`OZP PR × 地盤面積` 同 `First Schedule PR × 地盤面積` 邊個細，就係目標 GFA。用 envelope 模式睇邊個高度級別最著數：

```
python3 tools/massing_study.py --envelope --site-area 1000 --site-class B \
        --use domestic --ftf 3.15 --ground-ftf 4.5 --max-height 110
```

（輸出例子：`examples/demo_envelope_report.md`）住宅地盤喺 61 m 以上先攞到 PR 8 / 9 / 10，但上蓋跌到 33.33–40%，所以塔樓樓面細、層數多；呢個係香港「瘦高塔」嘅法規根源。

## 2. 高度同層高

- 高度 (reg 23(1))：由最低指明街道嘅平均水平量到最高可用樓層上面屋頂嘅平均高度。OZP 高度用 mPD，要加返街面 mPD。
- 常用層高（經驗值，要按結構同機電核實）：

| 用途 | 層高 m | 說明 |
| --- | --- | --- |
| 住宅標準層 | 3.0–3.15 | 樓底 ≥ 2.5 m (reg 24) |
| 寫字樓 | 4.0–4.2 | 包高架地台／假天花 |
| 零售平台 | 4.5–6.0 | 地下通常較高 |
| 轉換層 | 4.5–8.0 | 視乎轉換大樑 |
| 停車場 | 3.0–3.6 | 淨高、機電、坡道 |
| 避火層 | 約 3.0–4.5 | 淨高 ≥ 2.3 m，可兼機電層 |

- 超過 25 層就要預避火層（每隔 ≤ 25 層，B18），佢唔計 GFA（APP-2）但佔高度，排層數時一齊計。

## 3. 揀類型（Typology）

| 類型 | 適用 | 優點 | 代價 |
| --- | --- | --- | --- |
| 平台＋單塔 | 細至中型市區地盤 | 平台用盡 100% 非住用上蓋（≤ 15 m），塔樓景觀好 | 轉換層成本；平台壓街 |
| 平台＋雙／多塔 | 較闊地盤 | 塔距做通風廊，單位景觀好 | 核心筒重複，實用率低；要核 APP-152 間距 |
| 板式 (Slab) | 學校、工廈、公屋舊式 | 結構簡單、兩邊採光 | 屏風效應，SBD 立面長度限制 |
| 點式 (Point block) | 住宅塔 | 四面景觀、外牆多 | 每層單位數有限 |
| 退台式 (Stepped) | 山坡、海旁、低密度 | 呼應地形、天台花園 | 樓面損失、防水 |
| 庭院式 (Courtyard) | 機構、校園、低層高密度 | 微氣候好 | 內向；消防通道要入到 |
| 架空 (Podium-free / Permeable) | 通風要求高嘅地方 | 地面通透，改善行人風環境 | 商業樓面少 |

## 4. 樓面數學（GFA Balance）

```
目標 GFA          = min(OZP PR, B(P)R PR, 地契 GFA) × 地盤面積
標準層樓面 (gross) = (目標 GFA − 平台 GFA) ÷ 標準層數 ÷ (1 − 寬免比例)
標準層數           = (高度限制 − 平台高度 − 轉換層 − 屋頂) ÷ 層高
上蓋檢查           = 每層 footprint ÷ 地盤面積 ≤ First Schedule SC
```

- 複合用途 (reg 21(2))：Dd/Pd + Dn/Pn ≤ 1。非住用每用多一份，住用就少一份；`bpr_check` 會計出「呢個非住用 PR 之下最多住用 PR」。
- 寬免比例粗估（只作體量用）：住宅標準層 3–6%（機房、垃圾房、空調機位、露台等），平台 3–8%，地庫車場可以 100%。APP-151 嘅非強制機電＋綠色設施合共唔超過 GFA 10%。
- 實用率 (efficiency)：住宅單塔核心筒約佔標準層 15–25%；寫字樓 75–85%。數字係經驗值，要用平面驗證。

## 5. 環境同城市測試

逐個方案記低，唔使一開始就做模擬，但要知道邊個方案贏：

1. 日照同陰影：香港北緯約 22.3°，夏至太陽高角度近天頂，冬至正午約 44°。對住北面嘅學校、公園、休憩用地睇冬至陰影。
2. 通風：盛行風夏季東南／西南、冬季東北（以天文台／PlanD 風環境數據為準）。塔距、平台開口、街道走向對準風向。大型項目做 AVA（HPLB 及 ETWB 技術通告 1/06）。
3. 視覺：由公眾觀景點（TPB PG-No. 41）睇天際線同山脊線；保持山脊線 20–30% 冇建築遮擋係規劃署 Urban Design Guidelines 嘅原則。
4. 噪音：住宅向大路要做單位朝向、減音窗、隔聲鰭（HKPSG 第 9 章）。
5. SBD (APP-152)：
   - 樓宇間距：地盤 ≥ 2 ha 或連續立面投影長度 ≥ 60 m 時適用，要留透風度 (permeability)。
   - 後移：臨 < 15 m 闊街道嘅地盤，要後移令建築唔入街中心線 7.5 m 範圍（街面以上 15 m 內）。數字憑記憶，以 APP-152 原文為準。
   - 綠化：地盤 ≥ 1,000 m² 要有綠化覆蓋；≥ 2 ha 要求更高，部分要喺行人區。
6. 消防同 EVA：EVA 要覆蓋規定比例嘅立面周長；超過 25 層要避火層 (B18)；樓梯數目同闊度受人數控制（`tools/moe_check.py`）。

## 6. 方案比較（Option matrix）

每個方案至少做三個：「規條用盡」、「設計最好」、「折衷」。用 `tools/massing_study.py` 一次過跑：

```
python3 tools/massing_study.py examples/demo_massing.json \
        -o examples/demo_massing_report.md --write-projects projects/<名>/massing
```

- 輸入：每個方案一組 blocks（平台、轉換層、塔樓），層數、層高、樓面、footprint、寬免估算。並排塔樓用 `start_level_m`。
- 輸出：每個方案嘅層數、高度（街面及 mPD）、GFA、PR、上蓋、複合地積比，同 B(P)R PASS/FAIL；`--write-projects` 存成 `bpr_check` 格式，揀定方案後可以繼續加消防資料再跑其他工具。
- 比較表再加質性欄：景觀、通風、陰影、結構（轉換層）、建造期、實用率、成本、立面長度 (SBD)。用 1–5 分，寫埋點解。

## 7. 工具對應

| 階段 | 工具 | 備註 |
| --- | --- | --- |
| 規條包絡 | `massing_study.py --envelope` | 第一日用 |
| 方案比較 | `massing_study.py options.json` → `bpr_check.py` | 本 repo |
| 3D 體量 | Revit Mass / Rhino + Grasshopper / SketchUp | 腳本見 Dynamo、pyRevit、Grasshopper 嗰部分（另一個工作流） |
| 陰影、日照 | Rhino Ladybug、Revit Sun Path、SketchUp Shadows | |
| 通風 | Butterfly / OpenFOAM、顧問 CFD | AVA 正式評估由顧問做 |
| 視覺 | 照片合成 (photomontage)，按 TPB PG-No. 41 揀觀景點 | |

## 8. 常見錯誤

- 用由街面量嘅高度對 OZP mPD 限制，或者反過嚟。
- 忘記 61 m 以上住宅 SC 只得 33.33–40%，平台以上塔樓太肥。
- 複合用途以為 OZP 總 PR 夠就得，冇計 reg 21(2)。
- 預咗所有綠色設施寬免，結果超出 APP-151 10% 上限，或者 SBD 唔達標冇得寬免。
- 冇預避火層、轉換層、天台機房高度，最後超高。
- 地契 GFA 定義同 B(P)R 唔同，冇分開計。

## 參考

- Cap. 123F B(P)R（`bpr/`）；PNAP APP-2、APP-151、APP-152（屋宇署網站，以最新版為準）
- 規劃署《香港規劃標準與準則》第 11 章 Urban Design Guidelines；TPB PG-No. 41；HPLB/ETWB TC 1/06 (AVA)
- 本 repo：`bpr/bpr-rules.md`、`planning/planning-rules.md`（OZP、JPN 4/5）、`lands/lands-rules.md`（地契 GFA）、`fs-code/moe-rules.md`、`fs-code/cd-rules.md`；OZP 及地契檢查用 `tools/planning_lease_check.py`

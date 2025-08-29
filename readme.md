# ArXiv Paper Processing Pipeline

一個用於處理 ArXiv 學術論文資料的 ETL 管道系統。

## 專案簡介

這個系統從 Kaggle 的 ArXiv 資料集（280萬篇論文）中收集、處理、儲存學術論文 metadata，並提供全文檢索功能。主要用於支援學術研究分析、論文趨勢追蹤、以及未來的推薦系統開發。

## 專案結構

```
HackMD/
├── main.py                    # 主程式入口
├── config.py                  # 設定檔
├── requirements.txt           # 套件相依
├── docker-compose.yml         # OpenSearch 設定
├── readme.md                  # 專案說明文檔
├── TaskDescription.txt        # 需求文件
├── src/
│   ├── collector.py          # 資料收集
│   ├── dataset_collector.py  # 資料集處理
│   ├── processor.py          # 標準資料處理（≤1000筆）
│   ├── processor_parallel.py # 並行資料處理（>1000筆）
│   ├── storage.py            # 資料儲存 (含 S3 功能、批次索引)
│   └── monitor.py            # 監控統計
└── data/
    ├── kaggle_arxiv/         # ArXiv 資料集
    │   └── arxiv-metadata-oai-snapshot.json
    ├── dataset_*.json        # 原始收集的資料
    ├── processed_*.csv       # 處理後的 CSV 檔案
    ├── processed_*.json      # 處理後的 JSON 檔案
    └── metrics.json          # 執行統計
```

## 系統架構

```
資料流程:
Kaggle Dataset → Collector → Processor → Storage → OpenSearch
                                ↓
                            Monitor (品質追蹤)
```

### 核心模組

- **Collector** (`src/collector.py`, `src/dataset_collector.py`)
  - 從 Kaggle ArXiv 資料集讀取論文
  - 支援多種篩選條件（類別、年份、關鍵字）
  - 使用進度條顯示處理狀態

- **Processor** (`src/processor.py`, `src/processor_parallel.py`)  
  - 資料清理與轉換
  - 提取機構資訊
  - 自動產生關鍵字（基於詞頻）
  - 計算衍生指標
  - 智慧處理器選擇：≤1000筆用標準版，>1000筆用並行版

- **Storage** (`src/storage.py`)
  - OpenSearch 索引管理
  - CSV/JSON 檔案輸出
  - 資料統計分析

- **Monitor** (`src/monitor.py`)
  - 執行時間追蹤
  - 資料品質評分
  - 處理統計累積

## 安裝與設定

### 前置需求

1. Python 3.8+
2. Docker (for OpenSearch)
3. 4.6GB 磁碟空間（ArXiv 資料集）

### 安裝步驟

```bash
# 1. 安裝相依套件
pip install -r requirements.txt

# 2. 下載 ArXiv 資料集
# 從 Kaggle 下載: https://www.kaggle.com/datasets/Cornell-University/arxiv
# 解壓縮到 data/kaggle_arxiv/

# 3. 啟動 OpenSearch
docker-compose up -d

# 4. 確認 OpenSearch 運作
curl http://localhost:9200
```

## 使用方式

### 可用參數說明

```bash
python main.py [OPTIONS]

可用參數：
  --category    篩選 arXiv 分類 (如: cs, cs.CV, math.GT)
  --year        篩選年份 (如: 2023, 2024)
  --limit       處理論文數量上限 (預設: 1000)
  --keyword     搜尋關鍵字 (在 title/abstract 中搜尋)
  --search      在已索引的 OpenSearch 資料中搜尋
  --stats       顯示資料集統計資訊
```

### 基本指令範例

```bash
# 處理 100 篇論文
python main.py --limit 100

# 處理特定類別
python main.py --category cs.CV --limit 50

# 關鍵字搜尋
python main.py --keyword "transformer" --limit 30

# 年份篩選
python main.py --year 2023 --limit 100

# 組合條件
python main.py --category cs.AI --keyword "neural" --year 2023 --limit 50

# 在 OpenSearch 中搜尋已索引資料
python main.py --search "deep learning"

# 查看資料集統計
python main.py --stats
```

### 執行後產生的檔案

每次執行 `python main.py` 會產生以下檔案：

```
data/
├── dataset_{category}_{timestamp}.json    # 原始收集的論文資料
├── processed_{category}_{timestamp}.csv   # 處理後的 CSV (29 個欄位)
├── processed_{category}_{timestamp}.json  # 處理後的 JSON 格式
└── metrics.json                          # 累積的執行統計

範例檔名：
- dataset_cs.CV_20240829_143022.json
- processed_cs.CV_20240829_143022.csv
- processed_cs.CV_20240829_143022.json
```

### 輸出訊息解讀

執行時會看到的訊息：

```
============================================================
ArXiv Data Pipeline - 2024-08-29 14:30:22
============================================================

Step 1: Collecting data from Kaggle Dataset...
Collecting papers: 50 papers [00:03, 15.23 papers/s, collected=50]
# 進度條顯示：已收集數量、速度

Step 2: Processing data...
Using standard processor for 50 papers (≤1000)
# 自動選擇處理器：標準版（≤1000）或並行版（>1000）
Processing 50 papers
Data quality score: 96.69%
# 資料品質分數：非空欄位的比例

Step 3: Data quality check...
Quality score: 96.69%

Step 4: Storing data...
✓ Uploaded to s3://chloe-arxiv-data/processed/batch_20240829_143022.csv
# S3 上傳狀態（如有設定 AWS）
Indexed 50/50 papers by OpenSearch (bulk mode)
# OpenSearch 批次索引成功率

Database statistics:
  Total papers: 150
  Top categories:
    - cs.CV: 80 papers
    - cs.AI: 70 papers

==================================================
PIPELINE SUMMARY
==================================================
Total runs: 5              # 總執行次數
Total papers: 250          # 累計處理論文數
Average time: 12.3 seconds # 平均執行時間
Average papers/run: 50     # 平均每次處理數量

Last run:
  Time: 2024-08-29 14:30:22
  Papers: 50
  Duration: 15.2s
```

### 特殊情況的輸出訊息

```bash
# 處理大資料集時（>1000筆）
Step 2: Processing data...
Using parallel processor for 2000 papers (>1000)
Processing 2000 papers with parallel processing
# 自動啟用並行處理，使用多核心加速

# 當關鍵字搜尋結果不足時
⚠️  Found only 23 papers containing 'blockchain' (requested: 50)
    Scanned 200,000 papers total

# 當完全找不到符合條件的論文時
❌ No papers found containing 'xyz123' after scanning 200,000 papers
    Try: 1) Different keyword  2) Remove category filter  3) Check spelling

# S3 上傳失敗時（沒有 AWS 設定）
S3 upload skipped: Unable to locate credentials
  (File saved locally: data/processed_cs.CV_20240829_143022.csv)

# 當 OpenSearch 未啟動時
OpenSearch not available
(系統仍會產生 CSV/JSON 檔案，但不會建立索引)

# 查看資料集統計時（使用進度條）
Calculating dataset statistics...
Scanning: 100%|████████| 2800000/2800000 [00:45<00:00, 62222.22 papers/s]

Dataset Statistics:
Total papers: 2,800,000
File size: 4621.3 MB

Top categories:
  cs: 450,123 papers
  math: 380,456 papers
  physics: 350,789 papers
```

### OpenSearch 查詢

```bash
# 查看索引狀態
curl -X GET "localhost:9200/_cat/indices?v"
# 輸出範例：
# health status index         uuid                   pri rep docs.count
# green  open   arxiv_papers  kM4O3nB9QOmT6I1Pfbtxow   1   0       150

# 計算文件數量
curl -X GET "localhost:9200/arxiv_papers/_count"
# 輸出範例：
# {"count":150,"_shards":{"total":1,"successful":1,"skipped":0,"failed":0}}

# 搜尋論文
curl -X GET "localhost:9200/arxiv_papers/_search?q=transformer"
# 回傳符合的論文 JSON 資料
```

## 資料欄位說明（29個欄位）

### 基礎識別資訊
- `arxiv_id`: ArXiv 論文編號（如 "2301.12345"）
- `title`: 論文標題
- `abstract`: 論文摘要
- `doi`: 數位物件識別碼（如果有發表）
- `journal_ref`: 期刊參考資訊（如 "Nature 2023"）

### 作者與機構
- `authors`: 作者列表 ["Author A", "Author B"]
- `author_count`: 作者數量
- `author_affiliations`: 作者所屬機構原始資料
- `institutions`: 提取的機構列表
- `is_collaborative`: 是否為合作論文（作者>1）

### 分類資訊
- `categories`: 所有分類標籤 ["cs.CV", "cs.AI"]
- `primary_category`: 主要分類
- `is_interdisciplinary`: 是否跨領域
- `keywords`: 自動提取的關鍵字（基於詞頻）

### 時間資訊
- `published_date`: ArXiv 首次發布日期
- `updated_date`: 最後更新日期
- `year`: 發布年份
- `month`: 發布月份
- `days_since_published`: 距今天數

### 版本資訊
- `version_count`: 版本更新次數
- `versions`: 所有版本詳細資訊
- `first_version_date`: 第一版日期
- `last_version_date`: 最新版日期

### 內容指標
- `title_length`: 標題長度
- `abstract_length`: 摘要長度
- `comments`: 作者備註（頁數、會議等）

### 預留擴充欄位
- `publication_date`: 期刊正式發表日期（需外部 API）
- `publication_type`: 發表類型（預設 "preprint"）
- `citation_count`: 引用次數（需外部 API）

## 效能優化

### 處理器選擇
系統會根據資料量自動選擇最適合的處理器：
- **≤1000 筆論文**：使用標準處理器
- **>1000 筆論文**：使用並行處理器

### 批次索引
- OpenSearch 使用 bulk API 批次索引

### 執行範例
```bash
# 小資料集（自動用標準處理器）
python main.py --limit 500
# 輸出：Using standard processor for 500 papers (≤1000)

# 大資料集（自動用並行處理器）
python main.py --limit 5000
# 輸出：Using parallel processor for 5000 papers (>1000)
```

## 設計理念

### 關鍵設計決策

- **為什麼有 29 個欄位？** 
  - 涵蓋論文的各個面向（內容、作者、時間、分類）
  - 為未來分析預留空間（排名、推薦、趨勢）
  - 部分欄位現在是空的，等待外部 API 整合

- **為什麼用 OpenSearch？**
  - 支援全文檢索
  - 彈性的聚合分析
  - 可擴展到大規模資料

- **keyword 的雙重含義**
  - 使用者輸入的 `--keyword`: 用於搜尋篩選
  - CSV 中的 `keywords` 欄位: 論文主題摘要



## 使用範例

### 範例 1: 研究特定領域趨勢
```bash
# 找 2023 年 computer vision 的 transformer 相關論文
python main.py --category cs.CV --keyword transformer --year 2023 --limit 100

# 分析結果
# - 可以看到 transformer 在 CV 領域的應用增長
# - 提取的關鍵字顯示主要研究方向
```

### 範例 2: 機構研究產出分析
```bash
# 收集大量論文後分析
python main.py --limit 10000

# 查詢 OpenSearch 統計
curl -X GET "localhost:9200/arxiv_papers/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "top_institutions": {
      "terms": {
        "field": "institutions",
        "size": 20
      }
    }
  }
}'
```

## 已知限制

1. **資料來源限制**
   - 部分欄位（如機構）資料不完整

2. **處理能力限制**
   - 關鍵字提取使用簡單詞頻
   - 無法處理非英文論文

3. **分析深度限制**
   - 無法判斷論文質量
   - 不能追蹤引用影響力
   - 缺乏領域特定的分析邏輯

## 未來改進方向
- [ ] 改善關鍵字提取演算法
- [ ] 加入向量化搜尋（語意相似度）
- [ ] 建立推薦系統
- [ ] 支援多語言論文

## 系統能力評估

### ✅ 可以做到
- 快速檢索 280 萬篇論文
- 多維度篩選（類別、年份、關鍵字）
- 基礎統計分析（論文數量、分類分布）
- 資料品質監控
- 批次處理與增量更新

### ⚠️ 有限支援
- 簡單的趨勢分析（需要更多時間維度資料）
- 作者合作網路（有作者姓名歧義問題）
- 機構統計（機構名稱不統一）

### 未來開發需求支援度

#### 1. Management Dashboard 支援度

| Dashboard 需求 | 現有支援 | 缺少部分 | 可行性 |
|---------------|---------|----------|--------|
| **論文更新頻率統計** | ✅ `version_count` 欄位 | - | **可直接實現** |
| **發表延遲時間分析** | ⚠️ 有 `journal_ref` | 需要外部 API 取得準確發表日期 | **需要擴充** |
| **機構/作者投稿統計** | ✅ `institutions`, `authors` 欄位 | - | **可直接實現** |
| **合作網路分析** | ⚠️ 有作者列表 | 作者歧義問題需解決 | **基礎版可實現** |

#### 2. Institutional Rankings 支援度

| Ranking 需求 | 現有支援 | 缺少部分 | 可行性 |
|-------------|---------|----------|--------|
| **論文數量統計** | ✅ 完全支援 | - | **可直接實現** |
| **論文質量評估** | ❌ 無引用資料 | 需整合 Semantic Scholar API | **需要大幅擴充** |
| **影響因子** | ❌ 無期刊資料 | 需整合 JCR/Scopus | **需要外部資料** |
| **CORE 排名** | ❌ 無會議等級 | 需整合 CORE Rankings | **需要外部資料** |

#### 3. Paper Recommendation System 支援度

| 推薦系統需求 | 現有支援 | 缺少部分 | 可行性 |
|-------------|---------|----------|--------|
| **基礎 metadata** | ✅ 29 個欄位完整 | - | **已就緒** |
| **關鍵字提取** | ✅ 已實作詞頻提取 | 可升級為 TF-IDF | **可優化** |
| **向量化搜尋** | ❌ 無向量嵌入 | 需要 NLP 模型（BERT等） | **需要實作** |
| **使用者行為** | ❌ 無追蹤機制 | 需要前端整合 | **需要新系統** |

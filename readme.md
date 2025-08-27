# ArXiv資料系統

一個用於收集和處理 arXiv 學術論文元數據的資料管道系統，資料來源為 Kaggle 的 Cornell University arXiv 資料集。

## 功能特色

- **資料來源**: Kaggle Cornell University arXiv 資料集（280萬篇以上論文）
- **資料處理**: 清理和豐富論文元數據
- **儲存方式**: 支援本地檔案、AWS S3 和 OpenSearch
- **監控功能**: 追蹤管道執行效能和資料品質
- **搜尋功能**: 查詢已索引的論文

## 系統架構

### 架構總覽

```
┌─────────────────────────────────────────────────────┐
│                   資料來源層                          │
│  Kaggle Dataset: arxiv-metadata-oai-snapshot.json   │
│              (280萬篇論文, 4.6GB)                     │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│                   收集層 (Collector)                 │
│  • ArxivCollector: 主控制器                          │
│  • DatasetCollector: 讀取本地 JSON                   │
│  • 支援篩選: 類別、年份、數量限制                      │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│                  處理層 (Processor)                  │
│  • 資料清理: 截斷過長文字                             │
│  • 特徵提取: 版本數量、機構識別                        │
│  • 計算指標: 作者數量、合作關係                        │
│  • 品質評分: 完整性、有效性、唯一性                    │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│                   儲存層 (Storage)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ 本地檔案  │  │  AWS S3  │  │   OpenSearch     │  │
│  │ CSV/JSON │  │ 雲端備份  │  │  索引與搜尋       │  │
│  └──────────┘  └──────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│                  監控層 (Monitor)                    │
│  • 執行指標: 處理時間、成功率                         │
│  • 資料品質: 缺失值檢測、異常偵測                      │
│  • 歷史記錄: metrics.json                           │
└─────────────────────────────────────────────────────┘
```

### 檔案結構

```
main.py
├── collector.py         # Main collector interface
├── dataset_collector.py # Handles Kaggle dataset download and parsing
├── processor.py         # Processes and enriches data
├── storage.py           # Handles S3 and OpenSearch
└── monitor.py           # Tracks metrics and quality
```

## Quick Start

### 安裝

```bash
pip install -r requirements.txt
```

### 基本使用

```bash
# 首次執行會自動下載 Kaggle 資料集（約 1GB）

# 收集 1000 篇論文（所有類別）
python main.py --limit 1000

# 收集 CS 類別論文
python main.py --category cs --limit 1000

# 依年份篩選
python main.py --category math --year 2023 --limit 500

# 取得資料集統計資訊
python main.py --stats

# 搜尋已索引的論文
python main.py --search "neural networks"
```

## Command Line Options

```bash
python main.py [OPTIONS]

Options:
  --category CATEGORY   arXiv category to filter (e.g., cs, math, physics)
  --year YEAR          Filter papers by year
  --limit N            Max papers to process (default: 1000)
  --stats              Show dataset statistics
  --search QUERY       Search indexed papers
```

## 環境設定

建立 `.env` 檔案：

```env
AWS_REGION=us-east-1
S3_BUCKET=arxiv-data
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9200
```

## 資料處理流程

1. **資料收集**: 從 Kaggle 280萬篇論文資料集下載和讀取
2. **資料處理**: 清理、驗證和豐富元數據
3. **品質檢查**: 計算資料品質分數
4. **資料儲存**: 儲存至本地檔案、S3 和 OpenSearch
5. **執行監控**: 追蹤效能指標

## 資料品質指標

- **完整性**: 檢查缺失欄位
- **有效性**: 驗證資料格式
- **唯一性**: 偵測重複資料
- **異常偵測**: 識別異常值

## Running with Docker

### 啟動OpenSearch
Step 1. 
  ```bash 
  docker-compose pull opensearch
  ```
Step 2. 
  ```bash 
  docker images | grep opensearch
  ```
Step 3. 
  ```bash 
  docker-compose up -d opensearch
  ```
Step 4. 
  ```bash 
  curl http://localhost:9200
  ```

## Output Files

- `data/raw_*.json`: Raw API responses
- `data/processed_*.csv`: Cleaned data
- `data/metrics.json`: Pipeline metrics

## Categories

Common arXiv categories:
- `cs.AI`: Artificial Intelligence
- `cs.LG`: Machine Learning
- `math.ST`: Statistics Theory
- `physics.data-an`: Data Analysis

## Performance

- Processing speed: ~1000 papers/second from local cache
- Kaggle dataset: 2M+ papers, ~1GB compressed
- First-time download: Automatically downloads and caches dataset

## Monitoring

The pipeline tracks:
- Total papers processed
- Processing time
- Success rate
- Data quality score
- Anomalies detected



## OpenSearch 查詢範例

### 基本查詢
```bash
# 查看索引中的論文總數
curl -X GET "localhost:9200/arxiv_papers/_count"

# 查看一篇論文的完整資料
curl -X GET "localhost:9200/arxiv_papers/_search?size=1" | python3 -m json.tool
```

### 統計分析查詢

#### 1. 各學科平均作者數
```bash
curl -X POST "localhost:9200/arxiv_papers/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "by_category": {
      "terms": {"field": "primary_category", "size": 20},
      "aggs": {
        "avg_authors": {
          "avg": {"field": "author_count"}
        }
      }
    }
  }
}'
```

#### 2. 論文版本更新統計
```bash
curl -X POST "localhost:9200/arxiv_papers/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "avg_versions": {
      "avg": {"field": "version_count"}
    },
    "by_category": {
      "terms": {"field": "primary_category"},
      "aggs": {
        "avg_updates": {
          "avg": {"field": "version_count"}
        }
      }
    }
  }
}'
```

#### 3. 機構發表統計（如果有機構資料）
```bash
curl -X POST "localhost:9200/arxiv_papers/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "top_institutions": {
      "terms": {
        "field": "institutions",
        "size": 10
      }
    }
  }
}'
```

#### 4. 有期刊發表的論文
```bash
curl -X POST "localhost:9200/arxiv_papers/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "exists": {"field": "journal_ref"}
  },
  "size": 5
}'
```

#### 5. 特定年份論文統計
```bash
curl -X POST "localhost:9200/arxiv_papers/_search" -H 'Content-Type: application/json' -d'
{
  "size": 0,
  "aggs": {
    "papers_by_year": {
      "terms": {
        "field": "year",
        "size": 20,
        "order": {"_key": "desc"}
      }
    }
  }
}'
```

### 搜尋查詢

#### 6. 全文搜尋
```bash
curl -X POST "localhost:9200/arxiv_papers/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "multi_match": {
      "query": "machine learning",
      "fields": ["title^2", "abstract", "comments"]
    }
  },
  "size": 5
}'
```

#### 7. 特定作者的論文
```bash
curl -X POST "localhost:9200/arxiv_papers/_search" -H 'Content-Type: application/json' -d'
{
  "query": {
    "match": {
      "authors": "Hinton"
    }
  }
}'
```

### 查詢結果說明
- `took`: 查詢執行時間（毫秒）
- `hits.total.value`: 符合的文件總數
- `aggregations`: 統計結果
  - `buckets`: 分組統計結果
  - `value`: 聚合計算值（平均、總和等）

## 資料欄位說明

### 已實現欄位（從 arXiv 資料集提取或計算）

#### 基本資訊
- `arxiv_id`: 論文唯一識別碼
- `title`: 標題
- `abstract`: 摘要
- `authors`: 作者列表
- `author_count`: 作者數量

#### 分類資訊
- `categories`: 所有學科分類
- `primary_category`: 主要學科分類

#### 時間資訊
- `published_date`: arXiv 首次提交日期
- `updated_date`: 最後更新日期
- `year`: 發表年份
- `month`: 發表月份
- `days_since_published`: 距今天數（計算得出）

#### 版本資訊
- `version_count`: 版本數量
- `versions`: 完整版本歷史（JSON 格式）
- `first_version_date`: 第一版日期
- `last_version_date`: 最後版本日期

#### 發表資訊
- `journal_ref`: 期刊參考資訊（如果有）
- `doi`: 數位物件識別碼（如果有）
- `comments`: 作者備註
- `publication_type`: 發表類型（預設為 "preprint"）

#### 機構與作者資訊
- `institutions`: 機構識別（從作者資訊提取）
- `author_affiliations`: 作者隸屬關係（字串格式）

#### 計算指標
- `title_length`: 標題長度
- `abstract_length`: 摘要長度
- `is_collaborative`: 是否為合作論文（作者數 > 1）
- `is_interdisciplinary`: 是否跨領域（多個主類別）

### 預留欄位（需外部 API 整合）
這些欄位目前為空值或預設值，設計用於未來擴充：

| 欄位 | 預設值 | 用途 | 建議資料來源 |
|------|--------|------|-------------|
| `publication_date` | `None` | 期刊正式發表日期 | Crossref API |
| `citation_count` | `0` | 引用次數 | Semantic Scholar API |
| `keywords` | `[]` | 關鍵字提取 | NLP 模型（BERT/GPT） |

這些預留欄位支援 TaskDescription 中提到的未來需求：
- 計算從 arXiv 到期刊發表的時間
- 機構排名（需要引用數據）
- 論文推薦系統（需要向量嵌入）

## Kaggle Dataset

The pipeline can use the Cornell University arXiv dataset from Kaggle:
- **Size**: ~1GB compressed, 2M+ papers
- **Coverage**: Papers from 1991 to present
- **Auto-download**: First run downloads automatically
- **Location**: Cached in `~/.cache/kagglehub/`

# ArXiv Data Pipeline - Kaggle Dataset

A data pipeline for collecting and processing arXiv scholarly articles metadata from Kaggle's Cornell University arXiv dataset.

## Features

- **Data Source**: Kaggle's Cornell University arXiv dataset (2M+ papers)
- **Data Processing**: Cleans and enriches paper metadata
- **Storage**: Supports local files, AWS S3, and OpenSearch
- **Monitoring**: Tracks pipeline performance and data quality
- **Search**: Query indexed papers

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```bash
# First time: automatically downloads ~1GB dataset from Kaggle

# Collect 1000 papers (any category)
python main.py --limit 1000

# Collect CS papers
python main.py --category cs --limit 1000

# Filter by year
python main.py --category math --year 2023 --limit 500

# Get dataset statistics
python main.py --stats

# Search indexed papers
python main.py --search "neural networks"
```

## Architecture

```
main.py
├── collector.py         # Main collector interface
├── dataset_collector.py # Handles Kaggle dataset download and parsing
├── processor.py         # Processes and enriches data
├── storage.py           # Handles S3 and OpenSearch
└── monitor.py           # Tracks metrics and quality
```

## Configuration

Create a `.env` file:

```env
AWS_REGION=us-east-1
S3_BUCKET=arxiv-data
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9200
```

## Data Pipeline Flow

1. **Collection**: Downloads and reads from Kaggle's 2M+ paper dataset
2. **Processing**: Cleans, validates, and enriches metadata
3. **Quality Check**: Calculates data quality score
4. **Storage**: Saves to local files, S3, and OpenSearch
5. **Monitoring**: Tracks performance metrics

## Data Quality Metrics

- Completeness: Checks for missing fields
- Validity: Validates data formats
- Uniqueness: Detects duplicates
- Anomaly Detection: Identifies outliers

## Running with Docker

```bash
# Start OpenSearch locally
docker-compose up -d

# Run pipeline
python main.py
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

## Kaggle Dataset

The pipeline can use the Cornell University arXiv dataset from Kaggle:
- **Size**: ~1GB compressed, 2M+ papers
- **Coverage**: Papers from 1991 to present
- **Auto-download**: First run downloads automatically
- **Location**: Cached in `~/.cache/kagglehub/`

## License

MIT
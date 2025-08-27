import os
from dotenv import load_dotenv

load_dotenv()

# Kaggle Dataset Configuration
KAGGLE_DATASET = "Cornell-University/arxiv"
DEFAULT_LIMIT = 1000

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET = os.getenv("S3_BUCKET", "arxiv-data")

OPENSEARCH_HOST = os.getenv("OPENSEARCH_HOST", "localhost")
OPENSEARCH_PORT = int(os.getenv("OPENSEARCH_PORT", "9200"))
OPENSEARCH_INDEX = "arxiv_papers"

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
import json
import boto3
from opensearchpy import OpenSearch
import pandas as pd
from typing import Dict, List, Optional

import config

class StorageManager:
    def __init__(self):
        self.s3_client = None
        self.opensearch_client = None
        self._init_clients()
    
    def _init_clients(self):
        try:
            self.s3_client = boto3.client('s3', region_name=config.AWS_REGION)
        except:
            print("S3 client not available, will use local storage")
        
        try:
            self.opensearch_client = OpenSearch(
                hosts=[{'host': config.OPENSEARCH_HOST, 'port': config.OPENSEARCH_PORT}],
                use_ssl=False,
                verify_certs=False
            )
            self._create_index()
        except:
            print("OpenSearch not available, will skip indexing")
    
    def _create_index(self):
        index_body = {
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0
            },
            "mappings": {
                "properties": {
                    "arxiv_id": {"type": "keyword"},
                    "title": {"type": "text"},
                    "abstract": {"type": "text"},
                    "authors": {"type": "keyword"},
                    "categories": {"type": "keyword"},
                    "primary_category": {"type": "keyword"},
                    "published_date": {"type": "date"},
                    "author_count": {"type": "integer"},
                    "year": {"type": "integer"},
                    "month": {"type": "integer"}
                }
            }
        }
        
        try:
            if not self.opensearch_client.indices.exists(index=config.OPENSEARCH_INDEX):
                self.opensearch_client.indices.create(index=config.OPENSEARCH_INDEX, body=index_body)
                print(f"Created OpenSearch index: {config.OPENSEARCH_INDEX}")
        except Exception as e:
            print(f"Error creating index: {e}")
    
    def upload_to_s3(self, local_file: str, s3_key: str):
        if not self.s3_client:
            print("S3 not configured, skipping upload")
            return False
        
        try:
            self.s3_client.upload_file(local_file, config.S3_BUCKET, s3_key)
            print(f"Uploaded {local_file} to s3://{config.S3_BUCKET}/{s3_key}")
            return True
        except Exception as e:
            print(f"Error uploading to S3: {e}")
            return False
    
    def index_papers(self, df: pd.DataFrame):
        if not self.opensearch_client:
            print("OpenSearch not configured, skipping indexing")
            return
        
        success_count = 0
        for _, row in df.iterrows():
            try:
                doc = row.to_dict()
                doc['authors'] = doc.get('authors', [])
                doc['categories'] = doc.get('categories', [])
                
                self.opensearch_client.index(
                    index=config.OPENSEARCH_INDEX,
                    id=doc['arxiv_id'],
                    body=doc
                )
                success_count += 1
            except Exception as e:
                print(f"Error indexing paper {row['arxiv_id']}: {e}")
        
        print(f"Indexed {success_count}/{len(df)} papers to OpenSearch")
    
    def search_papers(self, query: str, size: int = 10) -> List[Dict]:
        if not self.opensearch_client:
            print("OpenSearch not configured")
            return []
        
        search_body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title", "abstract", "authors"]
                }
            },
            "size": size
        }
        
        try:
            response = self.opensearch_client.search(
                index=config.OPENSEARCH_INDEX,
                body=search_body
            )
            return [hit["_source"] for hit in response["hits"]["hits"]]
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        if not self.opensearch_client:
            return {}
        
        try:
            stats = self.opensearch_client.count(index=config.OPENSEARCH_INDEX)
            
            agg_body = {
                "size": 0,
                "aggs": {
                    "categories": {
                        "terms": {"field": "primary_category", "size": 10}
                    },
                    "papers_by_year": {
                        "terms": {"field": "year", "size": 10}
                    },
                    "avg_authors": {
                        "avg": {"field": "author_count"}
                    }
                }
            }
            
            response = self.opensearch_client.search(
                index=config.OPENSEARCH_INDEX,
                body=agg_body
            )
            
            return {
                "total_papers": stats["count"],
                "categories": response["aggregations"]["categories"]["buckets"],
                "papers_by_year": response["aggregations"]["papers_by_year"]["buckets"],
                "avg_authors": response["aggregations"]["avg_authors"]["value"]
            }
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}
import json
import pandas as pd
from typing import Dict, List
from opensearchpy import OpenSearch
import config

class StorageManager:
    def __init__(self):
        self.opensearch = None
        self._connect_opensearch()
    
    def _connect_opensearch(self):
        """Connect to OpenSearch if available"""
        try:
            self.opensearch = OpenSearch(
                hosts=[{'host': config.OPENSEARCH_HOST, 'port': config.OPENSEARCH_PORT}],
                use_ssl=False,
                verify_certs=False
            )
            # Create index if not exists
            if not self.opensearch.indices.exists(index=config.OPENSEARCH_INDEX):
                self._create_index()
        except:
            print("OpenSearch not available")
    
    def _create_index(self):
        """Create OpenSearch index with basic mappings"""
        index_body = {
            "mappings": {
                "properties": {
                    "arxiv_id": {"type": "keyword"},
                    "title": {"type": "text"},
                    "abstract": {"type": "text"},
                    "authors": {"type": "keyword"},
                    "primary_category": {"type": "keyword"},
                    "year": {"type": "integer"},
                    "keywords": {"type": "keyword"}
                }
            }
        }
        
        self.opensearch.indices.create(index=config.OPENSEARCH_INDEX, body=index_body)
        print(f"Created index: {config.OPENSEARCH_INDEX}")
    
    def upload_to_s3(self, local_file: str, s3_key: str):
        """Placeholder for S3 upload"""
        print(f"S3 upload skipped: {local_file} -> {s3_key}")
        return True
    
    def index_papers(self, df: pd.DataFrame):
        """Index papers to OpenSearch"""
        if not self.opensearch:
            print("OpenSearch not available")
            return
        
        success = 0
        for _, row in df.iterrows():
            try:
                doc = row.to_dict()
                # Convert lists to proper format
                if 'authors' in doc and isinstance(doc['authors'], str):
                    doc['authors'] = [doc['authors']]
                    
                self.opensearch.index(
                    index=config.OPENSEARCH_INDEX,
                    id=doc['arxiv_id'],
                    body=doc
                )
                success += 1
            except Exception as e:
                print(f"Error indexing {row['arxiv_id']}: {e}")
        
        print(f"Indexed {success}/{len(df)} papers by OpenSearch")
    
    def search_papers(self, query: str, size: int = 10) -> List[Dict]:
        """Search papers in OpenSearch"""
        if not self.opensearch:
            return []
        
        search_body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["title", "abstract"]
                }
            },
            "size": size
        }
        
        try:
            response = self.opensearch.search(
                index=config.OPENSEARCH_INDEX,
                body=search_body
            )
            return [hit["_source"] for hit in response["hits"]["hits"]]
        except Exception as e:
            print(f"Search error: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """Get meaningful statistics from OpenSearch"""
        if not self.opensearch:
            return {}
        
        try:
            count = self.opensearch.count(index=config.OPENSEARCH_INDEX)
            
            # Get top categories and recent years distribution
            agg_body = {
                "size": 0,
                "aggs": {
                    "top_categories": {
                        "terms": {"field": "primary_category", "size": 5}
                    },
                    "recent_years": {
                        "terms": {"field": "year", "size": 5, "order": {"_key": "desc"}}
                    }
                }
            }
            
            response = self.opensearch.search(
                index=config.OPENSEARCH_INDEX,
                body=agg_body
            )
            
            return {
                "total_papers": count["count"],
                "top_categories": response["aggregations"]["top_categories"]["buckets"],
                "recent_years": response["aggregations"]["recent_years"]["buckets"]
            }
        except:
            return {"total_papers": 0}
import json
import time
from datetime import datetime
from typing import Dict, List
import os
import pandas as pd

import config

class PipelineMonitor:
    def __init__(self):
        self.metrics_file = f"{config.DATA_DIR}/metrics.json"
        self.metrics = self._load_metrics()
    
    def _load_metrics(self) -> Dict:
        if os.path.exists(self.metrics_file):
            with open(self.metrics_file, 'r') as f:
                return json.load(f)
        return {
            "runs": [],
            "total_papers_processed": 0,
            "total_errors": 0,
            "average_processing_time": 0
        }
    
    def start_monitoring(self, batch_id: str) -> Dict:
        return {
            "batch_id": batch_id,
            "start_time": time.time(),
            "timestamp": datetime.now().isoformat()
        }
    
    def end_monitoring(self, session: Dict, papers_count: int, errors: int = 0):
        session["end_time"] = time.time()
        session["processing_time"] = session["end_time"] - session["start_time"]
        session["papers_processed"] = papers_count
        session["errors"] = errors
        session["success_rate"] = (papers_count - errors) / papers_count if papers_count > 0 else 0
        
        self.metrics["runs"].append(session)
        self.metrics["total_papers_processed"] += papers_count
        self.metrics["total_errors"] += errors
        
        processing_times = [r["processing_time"] for r in self.metrics["runs"]]
        self.metrics["average_processing_time"] = sum(processing_times) / len(processing_times)
        
        self._save_metrics()
        
        return session
    
    def _save_metrics(self):
        with open(self.metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)
    
    def check_data_quality(self, df) -> Dict:
        quality_report = {
            "total_records": len(df),
            "missing_values": df.isnull().sum().to_dict(),
            "duplicate_ids": df['arxiv_id'].duplicated().sum(),
            "avg_abstract_length": df['abstract_length'].mean(),
            "avg_authors_per_paper": df['author_count'].mean(),
            "categories_distribution": df['primary_category'].value_counts().head(10).to_dict()
        }
        
        quality_score = 1.0
        
        if quality_report["duplicate_ids"] > 0:
            quality_score -= 0.2
        
        missing_ratio = sum(quality_report["missing_values"].values()) / (len(df) * len(df.columns))
        quality_score -= missing_ratio
        
        if quality_report["avg_abstract_length"] < 100:
            quality_score -= 0.1
        
        quality_report["quality_score"] = max(0, quality_score)
        
        return quality_report
    
    def detect_anomalies(self, df) -> List[Dict]:
        anomalies = []
        
        if len(df[df['abstract_length'] < 50]) > 0:
            anomalies.append({
                "type": "short_abstracts",
                "count": len(df[df['abstract_length'] < 50]),
                "arxiv_ids": df[df['abstract_length'] < 50]['arxiv_id'].tolist()[:5]
            })
        
        if len(df[df['author_count'] > 20]) > 0:
            anomalies.append({
                "type": "excessive_authors",
                "count": len(df[df['author_count'] > 20]),
                "arxiv_ids": df[df['author_count'] > 20]['arxiv_id'].tolist()[:5]
            })
        
        future_papers = df[pd.to_datetime(df['published_date']) > datetime.now()]
        if len(future_papers) > 0:
            anomalies.append({
                "type": "future_dates",
                "count": len(future_papers),
                "arxiv_ids": future_papers['arxiv_id'].tolist()[:5]
            })
        
        return anomalies
    
    def print_summary(self):
        print("\n" + "="*50)
        print("PIPELINE MONITORING SUMMARY")
        print("="*50)
        print(f"Total runs: {len(self.metrics['runs'])}")
        print(f"Total papers processed: {self.metrics['total_papers_processed']}")
        print(f"Total errors: {self.metrics['total_errors']}")
        print(f"Average processing time: {self.metrics['average_processing_time']:.2f} seconds")
        
        if self.metrics['runs']:
            latest = self.metrics['runs'][-1]
            print(f"\nLatest run:")
            print(f"  - Batch ID: {latest['batch_id']}")
            print(f"  - Papers: {latest['papers_processed']}")
            print(f"  - Success rate: {latest['success_rate']:.2%}")
            print(f"  - Processing time: {latest['processing_time']:.2f} seconds")
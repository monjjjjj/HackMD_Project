from datetime import datetime
import json
from typing import List, Dict, Optional

import config
from src.dataset_collector import DatasetCollector  # Using simplified version

class ArxivCollector:
    def __init__(self, use_dataset: bool = True):
        self.use_dataset = True  # Always use dataset
        self.dataset_collector = DatasetCollector()
        
    def collect_papers(self, category: str = None, days_back: int = None, year: Optional[int] = None, limit: int = 1000, keyword: str = None) -> List[Dict]:
        papers = self.dataset_collector.collect_from_dataset(
            category=category,
            year=year,
            limit=limit,
            keyword=keyword
        )
        return papers
    
    
    def save_raw_data(self, papers: List[Dict], category: str):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{config.DATA_DIR}/dataset_{category}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(papers, f, indent=2)
        
        print(f"Saved {len(papers)} papers to {filename}")
        return filename
    
    def get_dataset_stats(self) -> Dict:
        """Get dataset statistics if using Kaggle dataset"""
        if self.dataset_collector:
            return self.dataset_collector.get_dataset_stats()
        return {}
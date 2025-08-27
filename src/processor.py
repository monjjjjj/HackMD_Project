import json
import pandas as pd
from datetime import datetime
from typing import List, Dict
import re

import config

class DataProcessor:
    def __init__(self):
        self.quality_threshold = 0.8
        
    def process_papers(self, filename: str) -> pd.DataFrame:
        with open(filename, 'r') as f:
            papers = json.load(f)
        
        print(f"Processing {len(papers)} papers")
        
        processed = []
        for paper in papers:
            processed_paper = self._process_single_paper(paper)
            if processed_paper:
                processed.append(processed_paper)
        
        df = pd.DataFrame(processed)
        
        df = self._add_metrics(df)
        
        quality_score = self._calculate_quality(df)
        print(f"Data quality score: {quality_score:.2%}")
        
        return df
    
    def _process_single_paper(self, paper: Dict) -> Dict:
        try:
            return {
                'arxiv_id': paper['arxiv_id'],
                'title': paper['title'][:500],  
                'abstract': paper['abstract'][:2000],  
                'authors': paper['authors'],
                'author_count': len(paper['authors']),
                'categories': paper['categories'],
                'primary_category': paper.get('primary_category', paper['categories'][0] if paper['categories'] else 'unknown'),
                'published_date': self._parse_date(paper['published']),
                'updated_date': self._parse_date(paper['updated']),
                'year': self._parse_date(paper['published']).year,
                'month': self._parse_date(paper['published']).month,
            }
        except Exception as e:
            print(f"Error processing paper {paper.get('arxiv_id')}: {e}")
            return None
    
    def _parse_date(self, date_str: str) -> datetime:
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            return datetime.now()
    
    def _add_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        df['title_length'] = df['title'].str.len()
        df['abstract_length'] = df['abstract'].str.len()
        
        df['is_collaborative'] = df['author_count'] > 1
        df['is_interdisciplinary'] = df['categories'].apply(
            lambda cats: len(set([c.split('.')[0] for c in cats])) > 1
        )
        
        df['days_since_published'] = (datetime.now() - pd.to_datetime(df['published_date'])).dt.days
        
        return df
    
    def _calculate_quality(self, df: pd.DataFrame) -> float:
        scores = []
        
        completeness = 1 - (df.isnull().sum().sum() / (len(df) * len(df.columns)))
        scores.append(completeness)
        
        validity = len(df[df['abstract_length'] > 50]) / len(df)
        scores.append(validity)
        
        uniqueness = 1 - (df['arxiv_id'].duplicated().sum() / len(df))
        scores.append(uniqueness)
        
        return sum(scores) / len(scores)
    
    def save_processed_data(self, df: pd.DataFrame, category: str):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        csv_file = f"{config.DATA_DIR}/processed_{category}_{timestamp}.csv"
        df.to_csv(csv_file, index=False)
        print(f"Saved processed data to {csv_file}")
        
        json_file = f"{config.DATA_DIR}/processed_{category}_{timestamp}.json"
        df.to_json(json_file, orient='records', date_format='iso')
        print(f"Saved processed data to {json_file}")
        
        return csv_file, json_file
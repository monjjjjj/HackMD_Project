import json
import os
from typing import List, Dict, Optional
from datetime import datetime
from tqdm import tqdm
import config

class DatasetCollector:
    def __init__(self):
        self.metadata_file = os.path.join(config.DATA_DIR, "kaggle_arxiv", "arxiv-metadata-oai-snapshot.json")
    
    def check_dataset(self) -> bool:
        """Check if dataset exists"""
        if not os.path.exists(self.metadata_file):
            print(f"Dataset not found at: {self.metadata_file}")
            return False
        return True
    
    def collect_from_dataset(
        self, 
        category: Optional[str] = None,
        year: Optional[int] = None,
        limit: int = 1000,
        keyword: Optional[str] = None
    ) -> List[Dict]:
        """Collect papers from dataset with filters"""
        
        if not self.check_dataset():
            raise FileNotFoundError("Dataset not found")
        
        papers = []
        
        with open(self.metadata_file, 'r', encoding='utf-8') as f:
            pbar = tqdm(desc="Collecting papers", unit=" papers")
            
            for line in f:
                # Stop if we have enough
                if len(papers) >= limit:
                    break
                
                try:
                    paper = json.loads(line)
                    
                    # Apply filters
                    if category and category not in paper.get('categories', ''):
                        continue
                    
                    if keyword:
                        text = (paper.get('title', '') + ' ' + paper.get('abstract', '')).lower()
                        if keyword.lower() not in text:
                            continue
                    
                    if year:
                        # Simple year check in versions
                        versions = paper.get('versions', [])
                        if versions and str(year) not in str(versions[0].get('created', '')):
                            continue
                    
                    # Transform and add
                    papers.append(self._transform_paper(paper))
                    pbar.update(1)
                    pbar.set_postfix({'collected': len(papers)})
                    
                except:
                    continue
            
            pbar.close()
        
        print(f"Collected {len(papers)} papers")
        return papers
    
    def _transform_paper(self, paper: Dict) -> Dict:
        """Transform to standard format"""
        # Parse authors
        authors = paper.get('authors', '')
        if isinstance(authors, str):
            authors = [a.strip() for a in authors.replace(' and ', ', ').split(',') if a.strip()]
        
        # Parse categories
        categories = paper.get('categories', '').split()
        
        # Get first version date
        versions = paper.get('versions', [])
        published = versions[0].get('created') if versions else None
        
        return {
            'arxiv_id': paper.get('id', ''),
            'title': paper.get('title', '').replace('\n', ' ').strip(),
            'abstract': paper.get('abstract', '').replace('\n', ' ').strip(),
            'authors': authors,
            'categories': categories,
            'primary_category': categories[0] if categories else '',
            'published': published,
            'updated': paper.get('update_date'),
            'doi': paper.get('doi'),
            'journal-ref': paper.get('journal-ref'),
            'comments': paper.get('comments'),
            'versions': versions,
            'authors_parsed': paper.get('authors_parsed', [])
        }
    
    def get_dataset_stats(self) -> Dict:
        """Get basic dataset statistics"""
        if not self.check_dataset():
            return {}
        
        print("Calculating dataset statistics...")
        
        total = 0
        categories = {}
        
        with open(self.metadata_file, 'r', encoding='utf-8') as f:
            for line in tqdm(f, desc="Scanning"):
                try:
                    paper = json.loads(line)
                    total += 1
                    
                    # Count categories
                    for cat in paper.get('categories', '').split():
                        main_cat = cat.split('.')[0]
                        categories[main_cat] = categories.get(main_cat, 0) + 1
                        
                except:
                    continue
        
        # Top 10 categories
        top_categories = dict(sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10])
        
        return {
            'total_papers': total,
            'categories': top_categories,
            'file_size_mb': os.path.getsize(self.metadata_file) / (1024 * 1024)
        }
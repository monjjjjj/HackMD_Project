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
        if not os.path.exists(self.metadata_file):
            print(f"\n{'='*60}")
            print("Dataset not found! Please:")
            print("1. Download from: https://www.kaggle.com/datasets/Cornell-University/arxiv")
            print(f"2. Extract to: {os.path.dirname(self.metadata_file)}")
            print(f"{'='*60}\n")
            return False
        return True
    
    def collect_from_dataset(
        self, 
        category: Optional[str] = None,
        year: Optional[int] = None,
        limit: int = 1000
    ) -> List[Dict]:
        """Collect papers from dataset"""
        
        if not self.check_dataset():
            raise FileNotFoundError("Dataset not found")
        
        print(f"Reading papers from dataset...")
        papers = []
        
        with open(self.metadata_file, 'r', encoding='utf-8') as f:
            # Use tqdm with dynamic total (will stop at limit)
            pbar = tqdm(desc="Collecting papers", unit=" papers")
            for line in f:
                if len(papers) >= limit:
                    break
                
                try:
                    paper = json.loads(line)
                    
                    # Filter by category
                    if category and category not in paper.get('categories', ''):
                        continue
                    
                    # Filter by year (simple check from versions)
                    if year and 'versions' in paper and paper['versions']:
                        date_str = paper['versions'][0].get('created', '')
                        if str(year) not in date_str:
                            continue
                    
                    # Transform to standard format
                    papers.append(self._transform_paper(paper))
                    pbar.update(1)
                    pbar.set_postfix({'collected': len(papers)})
                        
                except Exception:
                    continue
            pbar.close()
        
        print(f"Collected {len(papers)} papers from dataset")
        return papers
    
    def _transform_paper(self, paper: Dict) -> Dict:
        """Transform to standard format"""
        
        # Handle authors
        authors = []
        if 'authors' in paper:
            if isinstance(paper['authors'], str):
                authors = [a.strip() for a in paper['authors'].replace(' and ', ', ').split(',')]
            else:
                authors = paper['authors']
        
        # Handle categories
        categories = paper.get('categories', '').split() if 'categories' in paper else []
        
        # Get date from first version
        published = None
        if 'versions' in paper and paper['versions']:
            published = paper['versions'][0].get('created')
        
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
            'versions': paper.get('versions', []),
            'authors_parsed': paper.get('authors_parsed', [])
        }
    
    def get_dataset_stats(self) -> Dict:
        """Get basic dataset statistics"""
        
        if not self.check_dataset():
            return {}
        
        print("Calculating dataset statistics...")
        
        stats = {
            'total_papers': 0,
            'categories': {},
            'file_size_mb': os.path.getsize(self.metadata_file) / (1024 * 1024)
        }
        
        # First count total lines for progress bar
        total_lines = sum(1 for _ in open(self.metadata_file, 'r', encoding='utf-8'))
        
        with open(self.metadata_file, 'r', encoding='utf-8') as f:
            for line in tqdm(f, total=total_lines, desc="Processing papers", unit=" papers"):
                try:
                    paper = json.loads(line)
                    stats['total_papers'] += 1
                    
                    # Count main categories
                    cats = paper.get('categories', '').split()
                    for cat in cats:
                        main_cat = cat.split('.')[0]
                        stats['categories'][main_cat] = stats['categories'].get(main_cat, 0) + 1
                        
                except Exception:
                    continue
        
        # Keep top 10 categories
        stats['categories'] = dict(sorted(
            stats['categories'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10])
        
        return stats
    
    def save_sample(self, papers: List[Dict], category: str = "sample"):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{config.DATA_DIR}/dataset_{category}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(papers, f, indent=2)
        
        print(f"Saved {len(papers)} papers to {filename}")
        return filename

    # Compatibility method (kept for backward compatibility)
    def download_dataset(self):
        if self.check_dataset():
            return os.path.dirname(self.metadata_file)
        raise FileNotFoundError("Dataset not found")
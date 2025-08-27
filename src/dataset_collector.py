import kagglehub
import json
import os
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
import gzip

import config

class DatasetCollector:
    def __init__(self):
        self.dataset_path = None
        self.metadata_file = None
        
    def download_dataset(self) -> str:
        """Load the arXiv dataset from local directory"""
        import zipfile
        
        # Create a data directory for Kaggle downloads
        kaggle_dir = os.path.join(config.DATA_DIR, "kaggle_arxiv")
        os.makedirs(kaggle_dir, exist_ok=True)
        
        # Check if already extracted
        metadata_path = os.path.join(kaggle_dir, "arxiv-metadata-oai-snapshot.json")
        if os.path.exists(metadata_path):
            print(f"Dataset already extracted at: {kaggle_dir}")
            self.dataset_path = kaggle_dir
            self.metadata_file = metadata_path
            return self.dataset_path
        
        # Check for zip file in data directory
        zip_path = os.path.join(config.DATA_DIR, "arxiv.zip")
        if not os.path.exists(zip_path):
            print("\n" + "="*60)
            print("MANUAL DOWNLOAD REQUIRED")
            print("="*60)
            print("\nPlease download the arXiv dataset manually:")
            print("1. Go to: https://www.kaggle.com/datasets/Cornell-University/arxiv")
            print("2. Click 'Download' button (requires Kaggle account)")
            print(f"3. Place the downloaded 'arxiv.zip' file in: {config.DATA_DIR}/")
            print(f"4. Run this script again")
            print("\nExpected file location: " + zip_path)
            print("="*60 + "\n")
            raise FileNotFoundError(f"Please download arxiv.zip and place it in {config.DATA_DIR}/")
        
        print(f"Found dataset zip at: {zip_path}")
        print("Extracting dataset (this may take a few minutes)...")
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(kaggle_dir)
            print("Dataset extracted successfully!")
            
            self.dataset_path = kaggle_dir
            
            # Find the metadata file
            for file in os.listdir(self.dataset_path):
                if 'arxiv-metadata' in file or file.endswith('.json'):
                    self.metadata_file = os.path.join(self.dataset_path, file)
                    break
            
            if not self.metadata_file:
                # Try to find any JSON file
                json_files = [f for f in os.listdir(self.dataset_path) if f.endswith('.json') or f.endswith('.json.gz')]
                if json_files:
                    self.metadata_file = os.path.join(self.dataset_path, json_files[0])
                else:
                    raise FileNotFoundError("No metadata file found in dataset")
            
            print(f"Dataset ready at: {self.dataset_path}")
            print(f"Found metadata file: {self.metadata_file}")
            return self.dataset_path
            
        except Exception as e:
            print(f"Error processing dataset: {e}")
            raise
    
    def collect_from_dataset(
        self, 
        category: Optional[str] = None,
        year: Optional[int] = None,
        limit: int = 1000
    ) -> List[Dict]:
        """Collect papers from the downloaded dataset"""
        
        if not self.metadata_file:
            self.download_dataset()
        
        print(f"Reading papers from dataset...")
        if category:
            print(f"Filtering by category: {category}")
        if year:
            print(f"Filtering by year: {year}")
        
        papers = []
        count = 0
        
        try:
            # Check if file is gzipped
            if self.metadata_file.endswith('.gz'):
                file_opener = gzip.open
                mode = 'rt'
            else:
                file_opener = open
                mode = 'r'
            
            with file_opener(self.metadata_file, mode, encoding='utf-8') as f:
                for line in f:
                    if count >= limit:
                        break
                    
                    try:
                        paper = json.loads(line)
                        
                        # Apply filters
                        if category and category not in paper.get('categories', ''):
                            continue
                        
                        if year:
                            # Parse date from versions or update_date
                            paper_date = self._extract_date(paper)
                            if not paper_date or paper_date.year != year:
                                continue
                        
                        # Transform to our format
                        transformed = self._transform_paper(paper)
                        papers.append(transformed)
                        count += 1
                        
                        if count % 100 == 0:
                            print(f"Processed {count} papers...")
                            
                    except json.JSONDecodeError:
                        continue
                    except Exception as e:
                        print(f"Error processing paper: {e}")
                        continue
            
        except Exception as e:
            print(f"Error reading dataset: {e}")
            raise
        
        print(f"Collected {len(papers)} papers from dataset")
        return papers
    
    def _transform_paper(self, paper: Dict) -> Dict:
        """Transform Kaggle dataset format to our standard format"""
        
        # Extract authors (handle different formats)
        authors = []
        if 'authors' in paper:
            if isinstance(paper['authors'], str):
                # Parse author string like "Author1, Author2 and Author3"
                authors_str = paper['authors'].replace(' and ', ', ')
                authors = [a.strip() for a in authors_str.split(',')]
            elif isinstance(paper['authors'], list):
                authors = paper['authors']
        
        # Extract categories
        categories = []
        if 'categories' in paper:
            categories = paper['categories'].split() if isinstance(paper['categories'], str) else paper['categories']
        
        # Extract dates
        submitted_date = self._extract_date(paper)
        
        return {
            'arxiv_id': paper.get('id', ''),
            'title': paper.get('title', '').replace('\n', ' ').strip(),
            'abstract': paper.get('abstract', '').replace('\n', ' ').strip(),
            'authors': authors,
            'categories': categories,
            'primary_category': categories[0] if categories else '',
            'published': submitted_date.isoformat() if submitted_date else None,
            'updated': paper.get('update_date'),
            'doi': paper.get('doi'),
            'journal_ref': paper.get('journal-ref'),
            'comments': paper.get('comments'),
            'versions': paper.get('versions', [])
        }
    
    def _extract_date(self, paper: Dict) -> Optional[datetime]:
        """Extract submission date from paper metadata"""
        
        # Try versions field first
        if 'versions' in paper and paper['versions']:
            try:
                if isinstance(paper['versions'], list) and len(paper['versions']) > 0:
                    first_version = paper['versions'][0]
                    if 'created' in first_version:
                        date_str = first_version['created']
                        # Parse date like "Mon, 2 Apr 2007 19:18:42 GMT"
                        return datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z')
            except:
                pass
        
        # Try update_date field
        if 'update_date' in paper and paper['update_date']:
            try:
                return datetime.fromisoformat(paper['update_date'])
            except:
                pass
        
        # Try submitter field date
        if 'submitter' in paper and isinstance(paper['submitter'], str):
            # Sometimes date is embedded in submitter field
            try:
                import re
                date_match = re.search(r'\d{4}-\d{2}-\d{2}', paper['submitter'])
                if date_match:
                    return datetime.strptime(date_match.group(), '%Y-%m-%d')
            except:
                pass
        
        return None
    
    def get_dataset_stats(self) -> Dict:
        """Get statistics about the downloaded dataset"""
        
        if not self.metadata_file:
            self.download_dataset()
        
        print("Calculating dataset statistics...")
        
        stats = {
            'total_papers': 0,
            'categories': {},
            'years': {},
            'file_size_mb': 0
        }
        
        try:
            # Get file size
            stats['file_size_mb'] = os.path.getsize(self.metadata_file) / (1024 * 1024)
            
            # Count papers and categories
            if self.metadata_file.endswith('.gz'):
                file_opener = gzip.open
                mode = 'rt'
            else:
                file_opener = open
                mode = 'r'
            
            with file_opener(self.metadata_file, mode, encoding='utf-8') as f:
                for line in f:
                    try:
                        paper = json.loads(line)
                        stats['total_papers'] += 1
                        
                        # Count categories
                        if 'categories' in paper:
                            cats = paper['categories'].split() if isinstance(paper['categories'], str) else paper['categories']
                            for cat in cats:
                                main_cat = cat.split('.')[0]
                                stats['categories'][main_cat] = stats['categories'].get(main_cat, 0) + 1
                        
                        # Count years
                        paper_date = self._extract_date(paper)
                        if paper_date:
                            year = paper_date.year
                            stats['years'][year] = stats['years'].get(year, 0) + 1
                        
                        if stats['total_papers'] % 10000 == 0:
                            print(f"Processed {stats['total_papers']} papers...")
                            
                    except:
                        continue
            
            # Sort categories and years
            stats['categories'] = dict(sorted(stats['categories'].items(), key=lambda x: x[1], reverse=True)[:10])
            stats['years'] = dict(sorted(stats['years'].items())[-10:])
            
        except Exception as e:
            print(f"Error calculating statistics: {e}")
        
        return stats
    
    def save_sample(self, papers: List[Dict], category: str = "sample"):
        """Save a sample of papers to local file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{config.DATA_DIR}/dataset_{category}_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(papers, f, indent=2)
        
        print(f"Saved {len(papers)} papers to {filename}")
        return filename
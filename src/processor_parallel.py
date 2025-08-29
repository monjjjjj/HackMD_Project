"""
Parallel version of processor for better performance
"""
import json
import pandas as pd
from datetime import datetime
from typing import List, Dict
import re
from multiprocessing import Pool, cpu_count
import config

class DataProcessor:
    def __init__(self):
        self.quality_threshold = 0.8
        
    def process_papers(self, filename: str) -> pd.DataFrame:
        with open(filename, 'r') as f:
            papers = json.load(f)
        
        print(f"Processing {len(papers)} papers with parallel processing")
        
        # Use multiprocessing for large datasets
        if len(papers) > 100:
            # Use half of available CPUs to avoid overload
            num_workers = max(1, cpu_count() // 2)
            chunk_size = len(papers) // num_workers
            
            with Pool(num_workers) as pool:
                processed = pool.map(self._process_single_paper, papers)
        else:
            # For small datasets, use sequential processing
            processed = [self._process_single_paper(paper) for paper in papers]
        
        # Filter out None values
        processed = [p for p in processed if p is not None]
        
        df = pd.DataFrame(processed)
        df = self._add_metrics(df)
        
        quality_score = self._calculate_quality(df)
        print(f"Data quality score: {quality_score:.2%}")
        
        return df
    
    def _process_single_paper(self, paper: Dict) -> Dict:
        """Same as original processor.py"""
        try:
            # Extract version information
            versions = paper.get('versions', [])
            version_count = len(versions) if versions else 1
            
            # Get first and last version dates
            first_version_date = None
            last_version_date = None
            if versions:
                if len(versions) > 0 and 'created' in versions[0]:
                    first_version_date = versions[0].get('created')
                if len(versions) > 0 and 'created' in versions[-1]:
                    last_version_date = versions[-1].get('created')
            
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
                'version_count': version_count,
                'versions': versions,
                'first_version_date': first_version_date,
                'last_version_date': last_version_date,
                'journal_ref': paper.get('journal-ref') or paper.get('journal_ref'),
                'doi': paper.get('doi'),
                'comments': paper.get('comments'),
                'institutions': self._extract_institutions(paper),
                'author_affiliations': str(paper.get('authors_parsed', [])) if paper.get('authors_parsed') else "",
                'publication_date': None,
                'publication_type': 'preprint',
                'citation_count': 0,
                'keywords': self._extract_keywords(paper['title'], paper['abstract'])
            }
        except Exception as e:
            return None
    
    def _parse_date(self, date_str: str) -> datetime:
        """Same as original"""
        if not date_str:
            return datetime.now()
        
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            try:
                return datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z')
            except:
                try:
                    if date_str.isdigit() and len(date_str) == 4:
                        return datetime(int(date_str), 1, 1)
                except:
                    pass
                return datetime.now()
    
    def _extract_institutions(self, paper: Dict) -> List[str]:
        """Same as original"""
        institutions = []
        authors_parsed = paper.get('authors_parsed', [])
        for author in authors_parsed:
            if len(author) > 2 and author[2]:
                affiliation = author[2].strip()
                if affiliation and affiliation not in institutions:
                    institutions.append(affiliation)
        return institutions
    
    def _extract_keywords(self, title: str, abstract: str, max_keywords: int = 5) -> List[str]:
        """Same as original"""
        try:
            text = f"{title} {title} {abstract}"
            text = text.lower()
            text = re.sub(r'[^\w\s]', ' ', text)
            
            stopwords = {
                'the', 'a', 'an', 'and', 'or', 'in', 'on', 'to', 'for', 'of', 'with',
                'is', 'are', 'was', 'were', 'be', 'we', 'our', 'this', 'that', 'these'
            }
            
            words = text.split()
            word_freq = {}
            
            for word in words:
                if len(word) >= 2 and word not in stopwords:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            keywords = [word for word, freq in sorted_words[:max_keywords]]
            
            return keywords
        except Exception:
            return []
    
    def _add_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Same as original"""
        df['title_length'] = df['title'].str.len()
        df['abstract_length'] = df['abstract'].str.len()
        df['is_collaborative'] = df['author_count'] > 1
        df['is_interdisciplinary'] = df['categories'].apply(
            lambda cats: len(set([c.split('.')[0] for c in cats])) > 1
        )
        df['days_since_published'] = (datetime.now() - pd.to_datetime(df['published_date'])).dt.days
        return df
    
    def _calculate_quality(self, df: pd.DataFrame) -> float:
        """Same as original"""
        scores = []
        completeness = 1 - (df.isnull().sum().sum() / (len(df) * len(df.columns)))
        scores.append(completeness)
        validity = len(df[df['abstract_length'] > 50]) / len(df)
        scores.append(validity)
        uniqueness = 1 - (df['arxiv_id'].duplicated().sum() / len(df))
        scores.append(uniqueness)
        return sum(scores) / len(scores)
    
    def save_processed_data(self, df: pd.DataFrame, category: str):
        """Same as original"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        csv_file = f"{config.DATA_DIR}/processed_{category}_{timestamp}.csv"
        df.to_csv(csv_file, index=False)
        print(f"Saved processed data to {csv_file}")
        
        json_file = f"{config.DATA_DIR}/processed_{category}_{timestamp}.json"
        df.to_json(json_file, orient='records', date_format='iso')
        print(f"Saved processed data to {json_file}")
        
        return csv_file, json_file
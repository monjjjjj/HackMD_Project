#!/usr/bin/env python3

import sys
import argparse
from datetime import datetime

from src.collector import ArxivCollector
from src.processor import DataProcessor
from src.processor_parallel import DataProcessor as ParallelDataProcessor
from src.storage import StorageManager
from src.monitor import PipelineMonitor

def run_pipeline(category: str = None, year: int = None, limit: int = 1000, keyword: str = None):
    print(f"\n{'='*60}")
    print(f"ArXiv Data Pipeline - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    print(f"Data Source: Kaggle Dataset (Cornell-University/arxiv)")
    
    monitor = PipelineMonitor()
    batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    session = monitor.start_monitoring(batch_id)
    
    try:
        print(f"\nStep 1: Collecting data from Kaggle Dataset...")
        collector = ArxivCollector(use_dataset=True)
        
        if not category:
            # Show dataset stats first
            print("\nGetting dataset statistics...")
            stats = collector.get_dataset_stats()
            if stats:
                print(f"Total papers in dataset: {stats.get('total_papers', 'unknown')}")
                print(f"File size: {stats.get('file_size_mb', 0):.1f} MB")
                if stats.get('categories'):
                    print("\nTop categories:")
                    for cat, count in list(stats['categories'].items())[:5]:
                        print(f"  {cat}: {count} papers")
        
        papers = collector.collect_papers(category, days_back=None, year=year, limit=limit, keyword=keyword)
        
        if not papers:
            print("No papers found!")
            return
        
        raw_file = collector.save_raw_data(papers, category)
        
        print("\nStep 2: Processing data...")
        # Choose processor based on data size
        if len(papers) > 1000:
            print(f"Using parallel processor for {len(papers)} papers (>1000)")
            processor = ParallelDataProcessor()
        else:
            print(f"Using standard processor for {len(papers)} papers (≤1000)")
            processor = DataProcessor()
        
        df = processor.process_papers(raw_file)
        # Note: keyword filtering already done during collection
        if keyword:
            print(f"(Papers already filtered for keyword '{keyword}' during collection)")
        
        csv_file, json_file = processor.save_processed_data(df, category)
        
        print("\nStep 3: Data quality check...")
        quality_report = monitor.check_data_quality(df)
        print(f"Quality score: {quality_report['quality_score']:.2%}")
        
        print("\nStep 4: Storing data...")
        storage = StorageManager()
        
        storage.upload_to_s3(csv_file, f"processed/{batch_id}.csv")
        
        storage.index_papers(df)
        
        stats = storage.get_statistics()
        if stats and stats.get('total_papers', 0) > 0:
            print(f"\nDatabase statistics:")
            print(f"  Total papers: {stats.get('total_papers', 0)}")
            
            # Show top categories
            if stats.get('top_categories'):
                print(f"  Top categories:")
                for cat in stats['top_categories'][:3]:
                    print(f"    - {cat['key']}: {cat['doc_count']} papers")
            
            # Show recent years
            if stats.get('recent_years'):
                print(f"  Papers by year:")
                for year in stats['recent_years'][:3]:
                    print(f"    - {year['key']}: {year['doc_count']} papers")
        
        monitor.end_monitoring(session, len(df))
        
    except Exception as e:
        print(f"\nError in pipeline: {e}")
        monitor.end_monitoring(session, 0, errors=1)
        raise
    
    monitor.print_summary()
    print(f"\n{'='*60}")
    print("Pipeline completed successfully!")
    print(f"{'='*60}\n")

def search_papers(query: str):
    storage = StorageManager()
    results = storage.search_papers(query)
    
    if not results:
        print("No results found")
        return
    
    print(f"\nFound {len(results)} papers matching '{query}':\n")
    for i, paper in enumerate(results, 1):
        print(f"{i}. {paper['title']}")
        print(f"   Authors: {', '.join(paper.get('authors', []))}")
        print(f"   Category: {paper.get('primary_category', 'N/A')}")
        print(f"   arXiv ID: {paper['arxiv_id']}\n")

def main():
    parser = argparse.ArgumentParser(description='ArXiv Data Pipeline - Kaggle Dataset')
    parser.add_argument('--category', help='arXiv category to filter (e.g., cs, math, physics)')
    parser.add_argument('--year', type=int, help='Filter papers by year')
    parser.add_argument('--limit', type=int, default=1000, help='Maximum number of papers to process')
    parser.add_argument('--keyword', help='Filter papers by keyword in title/abstract')
    parser.add_argument('--search', help='Search for papers in indexed data')
    parser.add_argument('--stats', action='store_true', help='Show dataset statistics')
    
    args = parser.parse_args()
    
    if args.stats:
        print("Getting dataset statistics...")
        collector = ArxivCollector(use_dataset=True)
        stats = collector.get_dataset_stats()
        
        print(f"\nDataset Statistics:")
        print(f"Total papers: {stats.get('total_papers', 'unknown')}")
        print(f"File size: {stats.get('file_size_mb', 0):.1f} MB")
        
        if stats.get('categories'):
            print("\nTop categories:")
            for cat, count in stats['categories'].items():
                print(f"  {cat}: {count:,} papers")
        
        if stats.get('years'):
            print("\nPapers by year (last 10 years):")
            for year, count in stats['years'].items():
                print(f"  {year}: {count:,} papers")
    
    elif args.search:
        search_papers(args.search)
    else:
        run_pipeline(
            category=args.category,
            year=args.year,
            limit=args.limit,
            keyword=args.keyword
        )

if __name__ == "__main__":
    main()
import json
import time
from datetime import datetime
import os
import config

class PipelineMonitor:
    def __init__(self):
        self.metrics_file = f"{config.DATA_DIR}/metrics.json"
        self.metrics = self._load_metrics()
    
    def _load_metrics(self) -> dict:
        if os.path.exists(self.metrics_file):
            try:
                with open(self.metrics_file, 'r') as f:
                    data = json.load(f)
                    return data
            except:
                pass
        
        return {
            "total_runs": 0,
            "total_papers": 0,
            "total_time": 0,
            "last_run": None
        }
    
    def start_monitoring(self, batch_id: str) -> dict:
        return {
            "batch_id": batch_id,
            "start_time": time.time(),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def end_monitoring(self, session: dict, papers_count: int, errors: int = 0):
        # 計算執行時間
        session["processing_time"] = time.time() - session["start_time"]
        session["papers_processed"] = papers_count
        session["success"] = errors == 0
        
        # 更新總體統計
        self.metrics["total_runs"] += 1
        self.metrics["total_papers"] += papers_count
        self.metrics["total_time"] += session["processing_time"]
        self.metrics["last_run"] = session
        
        self._save_metrics()
        return session
    
    def _save_metrics(self):
        with open(self.metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)
    
    def check_data_quality(self, df) -> dict:
        total_cells = len(df) * len(df.columns)
        missing_cells = df.isnull().sum().sum()
        
        quality_score = 1.0 - (missing_cells / total_cells)
        
        return {
            "quality_score": quality_score,
            "total_records": len(df),
            "missing_ratio": missing_cells / total_cells
        }
    
    def print_summary(self):
        print("\n" + "="*50)
        print("PIPELINE SUMMARY")
        print("="*50)
        
        if self.metrics["total_runs"] > 0:
            avg_time = self.metrics["total_time"] / self.metrics["total_runs"]
            avg_papers = self.metrics["total_papers"] / self.metrics["total_runs"]
            
            print(f"Total runs: {self.metrics['total_runs']}")
            print(f"Total papers: {self.metrics['total_papers']:,}")
            print(f"Average time: {avg_time:.1f} seconds")
            print(f"Average papers/run: {avg_papers:.0f}")
            
            if self.metrics["last_run"]:
                print(f"\nLast run:")
                print(f"  Time: {self.metrics['last_run']['timestamp']}")
                print(f"  Papers: {self.metrics['last_run']['papers_processed']}")
                print(f"  Duration: {self.metrics['last_run']['processing_time']:.1f}s")
        else:
            print("No runs recorded yet.")
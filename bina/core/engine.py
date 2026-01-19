import os
import concurrent.futures
import multiprocessing
from typing import List, Optional
from .models import Finding
from .registry import RuleRegistry
from .config import Config
from .baseline import BaselineManager

# Worker function must be top-level for pickling
def analyze_file_wrapper(args):
    file_path, config = args
    if file_path.endswith(".py"):
        from ..python.parser import PythonAnalyzer
        return PythonAnalyzer.analyze(file_path, config=config)
    return []

class Engine:
    def __init__(self, config: Optional[Config] = None, baseline_manager: Optional[BaselineManager] = None):
        self.registry = RuleRegistry()
        self.config = config or Config()
        self.baseline_manager = baseline_manager

    def scan_path(self, path: str) -> List[Finding]:
        findings = []
        files_to_scan = []

        if os.path.isfile(path):
            if not self.config.is_path_excluded(path):
                files_to_scan.append(path)
        elif os.path.isdir(path):
            # Collect files first
            for root, _, files in os.walk(path):
                for file in files:
                    full_path = os.path.join(root, file)
                    # Skip hidden directories like .git, but allow . and ..
                    if any(part.startswith('.') and part not in ('.', '..') for part in full_path.split(os.sep)):
                        continue
                    
                    if self.config.is_path_excluded(full_path):
                        continue
                    
                    files_to_scan.append(full_path)
        
        # Run parallel analysis
        # Max workers = cpu_count
        max_workers = os.cpu_count() or 1
        
        with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Prepare args
            tasks = [(f, self.config) for f in files_to_scan]
            results = executor.map(analyze_file_wrapper, tasks)
            
            for res in results:
                findings.extend(res)
        
        # Apply Baseline Filtering if manager exists
        if self.baseline_manager:
            findings = self.baseline_manager.filter(findings)

        return findings

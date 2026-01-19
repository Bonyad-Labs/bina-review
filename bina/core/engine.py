# Copyright 2025-2026 Bonyad-Labs
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import concurrent.futures
import multiprocessing
from typing import List, Optional
from .models import Finding
from .registry import RuleRegistry
from .config import Config
from .baseline import BaselineManager
from .loader import RuleLoader

# Worker function must be top-level for pickling
def analyze_file_wrapper(args):
    file_path, config = args
    if file_path.endswith(".py"):
        from ..python.parser import PythonAnalyzer
        return PythonAnalyzer.analyze(file_path, config=config)
    return []

def initialize_worker(custom_rule_paths: List[str]):
    """Initialize worker process by adding custom rule paths to sys.path and loading them."""
    import sys
    from .loader import RuleLoader
    from .registry import RuleRegistry
    # Ensure built-in rules are registered
    import bina.python.rules
    
    for path in custom_rule_paths:
        rules = RuleLoader.load_from_directory(path)
        for rule in rules:
            RuleRegistry.register_rule(rule)

class Engine:
    def __init__(self, config: Optional[Config] = None, baseline_manager: Optional[BaselineManager] = None):
        self.config = config or Config()
        self.baseline_manager = baseline_manager
        
        # Load custom rules if any
        from .registry import RuleRegistry
        for path in self.config.custom_rules:
            rules = RuleLoader.load_from_directory(path)
            for rule in rules:
                RuleRegistry.register_rule(rule)

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
        
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=max_workers,
            initializer=initialize_worker,
            initargs=(self.config.custom_rules,)
        ) as executor:
            # Prepare args
            tasks = [(f, self.config) for f in files_to_scan]
            results = executor.map(analyze_file_wrapper, tasks)
            
            for res in results:
                findings.extend(res)
        
        # Apply Baseline Filtering if manager exists
        if self.baseline_manager:
            findings = self.baseline_manager.filter(findings)

        return findings

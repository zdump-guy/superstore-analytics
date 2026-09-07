"""
Superstore Analytics Package
----------------------------
Advanced Python Data Exploration, Memory Optimization, and Automated Reporting Suite.
"""

from src.config import (
    BASE_DIR,
    CLEANED_DATA_PATH,
    DATA_DIR,
    EXPORTS_DIR,
    FIGURES_DIR,
    RAW_DATA_PATH,
    REPORT_PATH,
)
from src.data_pipeline import SuperstoreDataPipeline
from src.analyzer import SuperstoreAnalyzer
from src.visualizer import SuperstoreVisualizer
from src.reporter import SuperstoreReporter

__all__ = [
    "SuperstoreDataPipeline",
    "SuperstoreAnalyzer",
    "SuperstoreVisualizer",
    "SuperstoreReporter",
    "BASE_DIR",
    "DATA_DIR",
    "EXPORTS_DIR",
    "FIGURES_DIR",
    "RAW_DATA_PATH",
    "CLEANED_DATA_PATH",
    "REPORT_PATH"
]

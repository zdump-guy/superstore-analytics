"""
Configuration settings, file paths, visual constants, and schema definitions
for the Superstore Analytics and Automated Reporting Pipeline.
"""

from pathlib import Path
from typing import Dict, List

# ==========================================
# 1. PATH CONFIGURATION
# ==========================================
BASE_DIR: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = BASE_DIR / "data"
EXPORTS_DIR: Path = BASE_DIR / "exports"
FIGURES_DIR: Path = EXPORTS_DIR / "figures"

# Data Files
RAW_DATA_PATH: Path = DATA_DIR / "Sample - Superstore 2019.xls"
FALLBACK_RAW_DATA_PATH: Path = DATA_DIR / "Sample - Superstore.xls"
CLEANED_DATA_PATH: Path = EXPORTS_DIR / "cleaned_superstore.csv"
REPORT_PATH: Path = EXPORTS_DIR / "automated_kpi_report.md"

# Canonical Remote Dataset URLs (for automatic bootstrap if local raw file is absent)
DATASET_URLS: List[str] = [
    "https://raw.githubusercontent.com/slidescope/data/master/Sample%20-%20Superstore.xls",
    "https://raw.githubusercontent.com/ameenmanna8824/DATASETS/master/Sample%20-%20Superstore.xls",
    "https://raw.githubusercontent.com/priyank1204/Sample-Superstore-powerBI-report/master/Sample%20-%20Superstore.xls"
]

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# ==========================================
# 2. SCHEMA & DATA TYPES
# ==========================================
CATEGORICAL_COLUMNS: List[str] = [
    "Ship Mode",
    "Segment",
    "Region",
    "Category",
    "Sub-Category",
    "Country",
    "State",
    "City"
]

STRING_COLUMNS_TO_STRIP: List[str] = [
    "Order ID",
    "Customer ID",
    "Customer Name",
    "Segment",
    "Country",
    "City",
    "State",
    "Region",
    "Product ID",
    "Category",
    "Sub-Category",
    "Product Name",
    "Ship Mode"
]

DATE_COLUMNS: List[str] = ["Order Date", "Ship Date"]

FLOAT_DOWNCAST_COLS: List[str] = ["Sales", "Discount", "Profit"]

INT_DOWNCAST_COLS: Dict[str, str] = {
    "Quantity": "int16",
    "Row ID": "int32"
}

# Ordered Categoricals for Visual & Tabular Sorting
SHIP_MODE_ORDER: List[str] = ["Same Day", "First Class", "Second Class", "Standard Class"]
SEGMENT_ORDER: List[str] = ["Consumer", "Corporate", "Home Office"]
REGION_ORDER: List[str] = ["Central", "East", "South", "West"]
SALES_TIERS: List[str] = ["Low", "Medium", "High", "Very High"]

# Key Numerical Columns for Statistics & Correlations
NUMERICAL_FEATURES: List[str] = [
    "Sales",
    "Quantity",
    "Discount",
    "Profit",
    "Profit Margin",
    "Shipping Duration"
]

# ==========================================
# 3. VISUALIZATION & STYLING CONSTANTS
# ==========================================
PLOT_DPI: int = 300
PLOT_FORMAT: str = "png"
SEABORN_THEME: str = "whitegrid"

# Corporate Color Palette
COLORS = {
    "primary": "#1f77b4",       # Corporate Blue
    "secondary": "#2ca02c",     # Forest Green
    "accent": "#ff7f0e",        # Warm Orange
    "danger": "#d62728",        # Alert Coral / Red
    "dark": "#2c3e50",          # Navy / Slate
    "light": "#ecf0f1",         # Soft Gray
    "neutral": "#7f7f7f",       # Neutral Slate
    "loss": "#e74c3c",          # Loss Red
    "profit": "#27ae60",        # Profit Green
    "palette_name": "deep"
}

# Regional Colors
REGION_PALETTE: Dict[str, str] = {
    "Central": "#e74c3c",
    "East": "#3498db",
    "South": "#f39c12",
    "West": "#2ecc71"
}

# Segment Colors
SEGMENT_PALETTE: Dict[str, str] = {
    "Consumer": "#1f77b4",
    "Corporate": "#ff7f0e",
    "Home Office": "#2ca02c"
}

# Figure Names Mapping
FIGURE_FILENAMES: Dict[str, str] = {
    "fig1": "fig1_correlation_heatmap.png",
    "fig2": "fig2_sales_profit_by_subcategory.png",
    "fig3": "fig3_monthly_sales_trend.png",
    "fig4": "fig4_discount_vs_profit_margin.png",
    "fig5": "fig5_shipping_duration_by_mode.png",
    "fig6": "fig6_segment_profit_margin_dist.png",
    "fig7": "fig7_regional_performance_breakdown.png",
    "fig8": "fig8_sales_performance_category_dist.png"
}

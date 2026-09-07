# Software Requirements Specification (SRS) & Implementation Blueprint
## Mini-Project 1: Advanced Python Data Exploration & Automated Reporting
**Target System:** Automated Data Analytics & Reporting Pipeline (Superstore Dataset)  
**Grade Target:** 100 / 100 Marks  
**Target Execution Agent:** Antigravity CLI / Autonomous Coding Agent  

---

## 1. Project Overview & Business Scenario
A multinational retail enterprise requires an end-to-end, automated, and production-grade data analytics pipeline to ingest, clean, feature-engineer, analyze, and report on enterprise sales, customer purchasing behavior, operational delivery timelines, and product profitability.

The entire solution must be implemented with rigorous **Object-Oriented Programming (OOP)** principles, comprehensive **exception handling**, aggressive **memory optimization**, reusable **ETL pipelines**, and statistical depth. The final deliverables include a structured codebase, automated KPI reporting artifacts, high-resolution visual exports, and a self-contained, fully documented **Jupyter Notebook (`.ipynb`)**.

---

## 2. Environment & Project Architecture

### 2.1 Directory Structure
The agent must establish and populate the following directory structure:

```text
superstore-analytics/
├── data/
│   └── Sample - Superstore 2019.xls       # Primary raw dataset
├── exports/
│   ├── figures/                           # 300 DPI exported plots (.png)
│   │   ├── fig1_correlation_heatmap.png
│   │   ├── fig2_sales_profit_by_subcategory.png
│   │   ├── fig3_monthly_sales_trend.png
│   │   ├── fig4_discount_vs_profit_margin.png
│   │   ├── fig5_shipping_duration_by_mode.png
│   │   ├── fig6_segment_profit_margin_dist.png
│   │   ├── fig7_regional_performance_breakdown.png
│   │   └── fig8_sales_performance_category_dist.png
│   ├── cleaned_superstore.csv             # Cleaned, optimized export
│   └── automated_kpi_report.md            # Markdown summary report
├── src/
│   ├── __init__.py
│   ├── config.py                          # Paths, categorical order, color schemes
│   ├── data_pipeline.py                   # Data ingestion, cleaning, feature engineering
│   ├── analyzer.py                        # Statistical and correlation analysis
│   ├── visualizer.py                      # Matplotlib & Seaborn visualization suite
│   └── reporter.py                        # KPI summary generation & markdown exporter
├── superstore_analysis.ipynb              # Complete end-to-end documented notebook
├── requirements.txt                       # Locked dependencies
└── README.md                              # Execution guide and findings summary
```

### 2.2 Core Dependencies (`requirements.txt`)
The agent must create and verify the following dependencies:
```text
pandas>=2.0.0
numpy>=1.24.0
matplotlib>=3.7.0
seaborn>=0.12.0
xlrd>=2.0.1
openpyxl>=3.1.0
scipy>=1.10.0
tabulate>=0.9.0
```

---

## 3. Detailed Functional & Technical Specifications

### Phase 1: Ingestion & Structural Inspection
1. **Multi-Format Excel Engine Support:** Implement robust loading via `pd.read_excel()` wrapped in try/except blocks, falling back from `xlrd` (for legacy `.xls`) to `openpyxl` if needed.
2. **Metadata Profiling:**
   - Capture initial memory usage via `df.memory_usage(deep=True).sum()`.
   - Inspect and log `.shape`, data types (`.dtypes`), column names, and missing value counts.
   - Profile structural duplicates (`df.duplicated().sum()`).

### Phase 2: Data Cleaning & Preprocessing Pipeline
1. **Handling Inconsistent Formats:**
   - Strip leading/trailing whitespace across all string columns.
   - Standardize text casing where applicable.
2. **Duplicate & Null Handling:**
   - Explicitly identify and drop duplicate records (if any), logging dropped row counts.
   - Detect missing values; if postal codes or secondary fields have nulls, impute with appropriate domain defaults (e.g., `'Unknown'` or mode) without data leakage.
3. **Temporal Standardization:**
   - Parse `Order Date` and `Ship Date` into strict `datetime64[ns]` formats.
   - Validate temporal integrity: verify that `Ship Date >= Order Date`. Flag or correct anomalies.
4. **Outlier Detection & Auditing:**
   - Calculate statistical outliers for `Sales` and `Profit` using both the Interquartile Range (IQR) method ($Q_1 - 1.5 \times IQR, Q_3 + 1.5 \times IQR$) and Z-score ($|Z| > 3$).
   - Retain legitimate enterprise outliers but log and document their operational implications.

### Phase 3: Memory Optimization
1. **Categorical Encoding:** Downcast low-cardinality `object` columns to `category`:
   - `Ship Mode`, `Segment`, `Region`, `Category`, `Sub-Category`, `Country`.
2. **Numerical Downcasting:**
   - Convert `float64` to `float32`.
   - Downcast integer identifiers / counts (`Postal Code`, `Quantity`) to appropriate smaller integer types (`int32` / `int16`).
3. **Performance Benchmarking:**
   - Calculate and display memory consumption **Before** vs. **After** optimization in MB and percentage reduction (minimum target: $\ge 40\%$ memory reduction).

### Phase 4: Feature Engineering
Implement reusable vectorized pipeline methods to create the following columns:
1. **Profit Margin ($PM$):**
   $$PM = \frac{\text{Profit}}{\text{Sales}}$$
   *Edge Case Handling:* Handle zero sales gracefully using `np.where(Sales != 0, Profit / Sales, 0.0)`.
2. **Shipping Duration (Days):**
   $$\text{Shipping Duration} = (\text{Ship Date} - \text{Order Date}).\text{dt}.\text{days}$$
3. **Sales Performance Category:**
   - Segment transactions into four performance tiers based on quartiles/quantiles of `Sales` using `pd.qcut`:
     - `Low` (0 - 25th percentile)
     - `Medium` (25th - 50th percentile)
     - `High` (50th - 75th percentile)
     - `Very High` (75th - 100th percentile)
4. **Order Year & Month:** Extract `Year`, `Month`, and `Year-Month` string periods for trend aggregation.

### Phase 5: Statistical & Exploratory Data Analysis
1. **Descriptive Statistics:** Calculate mean, median, standard deviation, skewness, and kurtosis for numerical variables.
2. **Correlation Analysis:**
   - Compute Pearson and Spearman correlation matrices across:
     `['Sales', 'Quantity', 'Discount', 'Profit', 'Profit Margin', 'Shipping Duration']`.
   - Identify and document primary drivers of negative profit margins (e.g., deep discounts).

### Phase 6: Visualization Suite (Minimum 8 Mandatory Visualizations)
All plots must follow professional design standards: high DPI (`300`), clear titles, readable axis labels, formatted ticks, and cohesive color palettes (e.g., `Set2`, `viridis`, or corporate navy/teal). Each figure must be displayed in the notebook and exported to `exports/figures/`.

1. **Figure 1 — Correlation Heatmap:**
   - `sns.heatmap` displaying correlation values with `annot=True`, `fmt='.2f'`, masked upper triangle (`np.triu`), and diverging colormap (`coolwarm` or `vlag`).
2. **Figure 2 — Sales & Profit by Sub-Category (Dual Bar/Clustered):**
   - Horizontal clustered bar chart comparing total sales vs. total profit per sub-category, highlighting loss-making sub-categories (e.g., Tables, Bookcases).
3. **Figure 3 — Longitudinal Monthly Sales & Profit Trend:**
   - Multi-line chart tracking monthly sales and profit over time with annotated peak seasonal periods.
4. **Figure 4 — Discount vs. Profit Margin with Regression Trend:**
   - Scatter plot with overlaid trendline (`sns.regplot` or `lowess`) illustrating the critical discount threshold where profit turns negative.
5. **Figure 5 — Operational Shipping Duration by Ship Mode:**
   - Boxplot or violin plot showing the distribution, median, and variance of shipping days across `Same Day`, `First Class`, `Second Class`, and `Standard Class`.
6. **Figure 6 — Profit Margin Distribution Across Customer Segments:**
   - Density estimation plot (KDE) or faceted boxplot comparing Consumer, Corporate, and Home Office profitability spread.
7. **Figure 7 — Geographic Regional Contribution:**
   - Grouped bar chart depicting Sales, Profit, and Average Discount across `Central`, `East`, `South`, and `West` regions.
8. **Figure 8 — Sales Performance Category Distribution & Share:**
   - Donut chart or segmented count plot demonstrating order volumes and total revenue contribution across the 4 engineered sales categories (`Low`, `Medium`, `High`, `Very High`).

### Phase 7: Automated KPI Generation & Export Pipeline
1. **Automated KPI Summary:** Calculate and compile:
   - Total Gross Revenue ($)
   - Total Net Profit ($)
   - Overall Enterprise Profit Margin (%)
   - Total Orders & Unique Customers
   - Average Order Value (AOV)
   - Average Shipping Turnaround Time (Days)
   - Loss-making Orders Count & Percentage (%)
   - Top 3 Most Profitable Sub-Categories
   - Top 3 Highest Loss-Making Sub-Categories
2. **Artifact Exporters:**
   - Export optimized DataFrame to `exports/cleaned_superstore.csv`.
   - Export high-resolution plot PNGs to `exports/figures/`.
   - Compile a polished markdown report (`exports/automated_kpi_report.md`) containing executive commentary, markdown tables, and KPI metrics.

---

## 4. Object-Oriented Architecture Specification

The agent must organize code into modular classes adhering to SOLID principles:

```python
class SuperstoreDataPipeline:
    """Handles ingestion, validation, cleaning, and feature engineering."""
    def __init__(self, raw_filepath: str): ...
    def load_data(self) -> pd.DataFrame: ...
    def clean_data(self) -> pd.DataFrame: ...
    def optimize_memory(self) -> pd.DataFrame: ...
    def engineer_features(self) -> pd.DataFrame: ...
    def run_pipeline(self) -> pd.DataFrame: ...

class SuperstoreAnalyzer:
    """Handles descriptive statistics, correlation matrices, and aggregations."""
    def __init__(self, df: pd.DataFrame): ...
    def compute_summary_statistics(self) -> pd.DataFrame: ...
    def compute_correlations(self) -> pd.DataFrame: ...
    def compute_kpis(self) -> dict: ...
    def analyze_regional_performance(self) -> pd.DataFrame: ...

class SuperstoreVisualizer:
    """Generates and saves the 8 required figures."""
    def __init__(self, df: pd.DataFrame, output_dir: str = "exports/figures"): ...
    def plot_correlation_heatmap(self) -> str: ...
    def plot_subcategory_performance(self) -> str: ...
    def plot_monthly_trend(self) -> str: ...
    def plot_discount_impact(self) -> str: ...
    def plot_shipping_duration(self) -> str: ...
    def plot_segment_profitability(self) -> str: ...
    def plot_regional_breakdown(self) -> str: ...
    def plot_sales_performance_tiers(self) -> str: ...
    def generate_all_plots(self) -> list: ...

class SuperstoreReporter:
    """Compiles KPI metrics and visual references into an executive Markdown report."""
    def __init__(self, kpis: dict, export_dir: str = "exports"): ...
    def export_cleaned_data(self, df: pd.DataFrame, filename: str = "cleaned_superstore.csv") -> str: ...
    def generate_markdown_report(self, filename: str = "automated_kpi_report.md") -> str: ...
```

---

## 5. Jupyter Notebook (`superstore_analysis.ipynb`) Requirements
The notebook must be runnable top-to-bottom without errors and include:
1. **Title and Executive Overview:** Project scope, grading objectives, and business context.
2. **Environment & Import Cells:** Imports with verified version logging.
3. **Pipeline Execution:** Step-by-step invocation of OOP classes with printed outputs and formatted markdown tables.
4. **EDA & Visual Storytelling:** High-resolution charts displayed inline with clear analytical takeaways below each plot.
5. **Memory Profiling Section:** Displaying precise Before vs. After memory numbers.
6. **Executive Summary & Business Recommendations:** Actionable insights derived from the data (e.g., capping discounts at 20% in the Central region to prevent catastrophic margin loss).

---

## 6. Acceptance Criteria for Agent Verification
- [ ] Code strictly utilizes OOP classes (no raw scripts or loose functions).
- [ ] Every I/O operation and data transformation includes `try...except` exception handling.
- [ ] Memory optimization reduces DataFrame memory footprint by $\ge 40\%$.
- [ ] All 3 required engineered columns (`Profit Margin`, `Shipping Duration`, `Sales Performance Category`) are present and mathematically verified.
- [ ] Exactly 8 distinct, styled figures are rendered and exported as 300 DPI PNGs.
- [ ] Cleaned dataset is saved to CSV without index.
- [ ] Automated markdown KPI summary report is generated.
- [ ] `superstore_analysis.ipynb` executes cleanly from start to finish (`Kernel -> Restart & Run All`).

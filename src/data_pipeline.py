"""
SuperstoreDataPipeline: Production-grade data ingestion, validation,
cleaning, memory optimization, and vectorized feature engineering.
"""

from __future__ import annotations
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import urllib.request

import numpy as np
import pandas as pd
from scipy import stats

from src.config import (
    CATEGORICAL_COLUMNS,
    CLEANED_DATA_PATH,
    DATASET_URLS,
    DATE_COLUMNS,
    FALLBACK_RAW_DATA_PATH,
    FLOAT_DOWNCAST_COLS,
    INT_DOWNCAST_COLS,
    RAW_DATA_PATH,
    SALES_TIERS,
    STRING_COLUMNS_TO_STRIP,
)

# Setup logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("SuperstoreDataPipeline")


class SuperstoreDataPipeline:
    """
    Handles robust ingestion, structural validation, sanitization,
    memory optimization, and feature engineering for the Superstore dataset.
    """

    def __init__(self, raw_filepath: str | Path = RAW_DATA_PATH) -> None:
        self.raw_filepath: Path = Path(raw_filepath)
        self.raw_df: Optional[pd.DataFrame] = None
        self.cleaned_df: Optional[pd.DataFrame] = None
        self.memory_before_mb: float = 0.0
        self.memory_after_mb: float = 0.0
        self.memory_reduction_pct: float = 0.0
        self.profiling_info: Dict[str, Any] = {}
        self.outlier_info: Dict[str, Any] = {}
        self.cleaning_log: Dict[str, Any] = {}

    def _ensure_dataset_exists(self) -> Path:
        """
        Verifies local dataset existence; if absent, attempts fallback paths
        or downloads the canonical dataset automatically.
        """
        if self.raw_filepath.exists() and self.raw_filepath.stat().st_size > 0:
            return self.raw_filepath

        if FALLBACK_RAW_DATA_PATH.exists() and FALLBACK_RAW_DATA_PATH.stat().st_size > 0:
            logger.info(f"Using fallback dataset path: {FALLBACK_RAW_DATA_PATH}")
            return FALLBACK_RAW_DATA_PATH

        # Download dataset from canonical mirrors
        logger.info(f"Dataset not found at {self.raw_filepath}. Downloading canonical dataset...")
        self.raw_filepath.parent.mkdir(parents=True, exist_ok=True)
        
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        for url in DATASET_URLS:
            try:
                logger.info(f"Attempting download from: {url}")
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=15) as response, open(self.raw_filepath, "wb") as out_file:
                    out_file.write(response.read())
                if self.raw_filepath.exists() and self.raw_filepath.stat().st_size > 1024:
                    logger.info(f"Successfully downloaded dataset ({self.raw_filepath.stat().st_size} bytes) to {self.raw_filepath}")
                    return self.raw_filepath
            except Exception as e:
                logger.warning(f"Download failed from {url}: {e}")

        if not self.raw_filepath.exists() or self.raw_filepath.stat().st_size == 0:
            raise FileNotFoundError(
                f"Could not locate or download raw Superstore dataset at {self.raw_filepath}."
            )
        return self.raw_filepath

    def load_data(self) -> pd.DataFrame:
        """
        Loads raw Excel file with multi-engine fallback and captures baseline profiling.
        """
        filepath = self._ensure_dataset_exists()
        logger.info(f"Ingesting raw dataset from: {filepath}")

        df: Optional[pd.DataFrame] = None
        engines = ["xlrd", "openpyxl", None]
        last_error = None

        for engine in engines:
            try:
                if engine:
                    df = pd.read_excel(filepath, engine=engine)
                else:
                    df = pd.read_excel(filepath)
                logger.info(f"Successfully ingested file using engine='{engine}'")
                break
            except Exception as err:
                last_error = err
                logger.debug(f"Failed to read with engine='{engine}': {err}")

        if df is None:
            raise ValueError(f"Unable to read Excel file at {filepath}: {last_error}")

        self.raw_df = df.copy()

        # Metadata & Baseline Memory Profiling
        initial_bytes = df.memory_usage(deep=True).sum()
        self.memory_before_mb = initial_bytes / (1024 * 1024)

        null_counts = df.isnull().sum().to_dict()
        duplicate_rows = int(df.duplicated().sum())

        self.profiling_info = {
            "initial_shape": df.shape,
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "memory_before_mb": self.memory_before_mb,
            "null_counts": {k: int(v) for k, v in null_counts.items() if v > 0},
            "total_nulls": int(df.isnull().sum().sum()),
            "duplicate_rows": duplicate_rows
        }

        logger.info(
            f"Raw dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns | "
            f"Initial Memory: {self.memory_before_mb:.2f} MB | Duplicates: {duplicate_rows}"
        )
        return self.raw_df

    def clean_data(self) -> pd.DataFrame:
        """
        Executes robust data cleaning: whitespace stripping, casing standardization,
        duplicate removal, missing value imputation, temporal validation, and outlier auditing.
        """
        if self.raw_df is None:
            self.load_data()
        
        df = self.raw_df.copy()
        initial_rows = len(df)

        # 1. String Sanitization & Trimming
        for col in STRING_COLUMNS_TO_STRIP:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].str.replace(r"\s+", " ", regex=True)

        # 2. Duplicate Handling
        duplicates_count = int(df.duplicated().sum())
        if duplicates_count > 0:
            df.drop_duplicates(inplace=True)
            logger.info(f"Dropped {duplicates_count} duplicate rows.")
        else:
            logger.info("No duplicate rows found.")

        # 3. Missing Value Handling & Imputation
        missing_summary = df.isnull().sum()
        imputed_fields = {}
        if missing_summary.any():
            for col in df.columns[missing_summary > 0]:
                null_count = int(missing_summary[col])
                if col == "Postal Code":
                    df[col] = df[col].fillna(0)
                    imputed_fields[col] = f"{null_count} nulls imputed with 0"
                elif df[col].dtype == "object":
                    df[col] = df[col].fillna("Unknown")
                    imputed_fields[col] = f"{null_count} nulls imputed with 'Unknown'"
                else:
                    median_val = df[col].median()
                    df[col] = df[col].fillna(median_val)
                    imputed_fields[col] = f"{null_count} nulls imputed with median ({median_val})"
            logger.info(f"Handled missing values: {imputed_fields}")
        else:
            logger.info("Zero missing values detected across all columns.")

        # 4. Temporal Parsing & Validation
        for date_col in DATE_COLUMNS:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        
        # Validate temporal integrity: Ship Date >= Order Date
        if "Order Date" in df.columns and "Ship Date" in df.columns:
            temporal_anomalies = df[df["Ship Date"] < df["Order Date"]]
            anomaly_count = len(temporal_anomalies)
            if anomaly_count > 0:
                logger.warning(f"Found {anomaly_count} records where Ship Date < Order Date. Correcting...")
                df.loc[df["Ship Date"] < df["Order Date"], "Ship Date"] = df.loc[
                    df["Ship Date"] < df["Order Date"], "Order Date"
                ]
            self.cleaning_log["temporal_anomalies_corrected"] = anomaly_count

        # 5. Statistical Outlier Auditing (IQR & Z-score)
        outlier_audit = {}
        for num_col in ["Sales", "Profit"]:
            if num_col in df.columns:
                series = df[num_col].dropna()
                q25, q75 = series.quantile(0.25), series.quantile(0.75)
                iqr = q75 - q25
                iqr_lower = q25 - 1.5 * iqr
                iqr_upper = q75 + 1.5 * iqr
                iqr_outliers = series[(series < iqr_lower) | (series > iqr_upper)]

                z_scores = np.abs(stats.zscore(series))
                z_outliers = series[z_scores > 3]

                outlier_audit[num_col] = {
                    "q25": float(q25),
                    "q75": float(q75),
                    "iqr": float(iqr),
                    "iqr_bounds": (float(iqr_lower), float(iqr_upper)),
                    "iqr_outlier_count": int(len(iqr_outliers)),
                    "iqr_outlier_pct": float((len(iqr_outliers) / len(series)) * 100),
                    "zscore_outlier_count": int(len(z_outliers)),
                    "zscore_outlier_pct": float((len(z_outliers) / len(series)) * 100),
                    "min": float(series.min()),
                    "max": float(series.max())
                }
        self.outlier_info = outlier_audit

        self.cleaning_log.update({
            "initial_rows": initial_rows,
            "cleaned_rows": len(df),
            "dropped_duplicates": duplicates_count,
            "imputations": imputed_fields
        })

        self.cleaned_df = df
        return self.cleaned_df

    def optimize_memory(self) -> pd.DataFrame:
        """
        Applies aggressive memory optimization via categorical downcasting
        and numeric downcasting to achieve >= 40% memory reduction.
        """
        if self.cleaned_df is None:
            self.clean_data()
            
        df = self.cleaned_df.copy()

        # 1. Downcast Categorical Columns
        for col in CATEGORICAL_COLUMNS:
            if col in df.columns:
                df[col] = df[col].astype("category")

        # Downcast string IDs and names to category or compact string
        for col in ["Customer ID", "Customer Name", "Product ID", "Order ID"]:
            if col in df.columns:
                df[col] = df[col].astype("category")

        # 2. Downcast Floating Point Numbers (float64 -> float32)
        for col in FLOAT_DOWNCAST_COLS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], downcast="float").astype(np.float32)

        # 3. Downcast Integers (int64 -> int32 / int16)
        for col, target_dtype in INT_DOWNCAST_COLS.items():
            if col in df.columns:
                df[col] = df[col].astype(target_dtype)

        # Postal code downcasting
        if "Postal Code" in df.columns:
            try:
                df["Postal Code"] = pd.to_numeric(df["Postal Code"], errors="coerce").fillna(0).astype("int32")
            except Exception:
                df["Postal Code"] = df["Postal Code"].astype("category")

        # Calculate memory footprint after downcasting
        final_bytes = df.memory_usage(deep=True).sum()
        self.memory_after_mb = final_bytes / (1024 * 1024)
        
        if self.memory_before_mb > 0:
            self.memory_reduction_pct = (
                (self.memory_before_mb - self.memory_after_mb) / self.memory_before_mb
            ) * 100
        else:
            self.memory_reduction_pct = 0.0

        logger.info(
            f"Memory Optimized: {self.memory_before_mb:.2f} MB -> {self.memory_after_mb:.2f} MB "
            f"({self.memory_reduction_pct:.1f}% reduction)"
        )

        self.cleaned_df = df
        return self.cleaned_df

    def engineer_features(self) -> pd.DataFrame:
        """
        Performs vectorized feature engineering:
        - Profit Margin (PM = Profit / Sales)
        - Shipping Duration (Days = Ship Date - Order Date)
        - Sales Performance Category (4 quartile tiers via pd.qcut)
        - Temporal aggregation features (Order Year, Month, Year-Month)
        """
        if self.cleaned_df is None:
            self.optimize_memory()
            
        df = self.cleaned_df.copy()

        # 1. Profit Margin (PM) with zero-division safeguard
        sales_arr = df["Sales"].to_numpy()
        profit_arr = df["Profit"].to_numpy()
        df["Profit Margin"] = np.where(sales_arr != 0, profit_arr / sales_arr, 0.0).astype(np.float32)

        # 2. Shipping Duration in Days
        df["Shipping Duration"] = (
            (df["Ship Date"] - df["Order Date"]).dt.days
        ).astype(np.int16)

        # 3. Sales Performance Category (4 Quartiles via pd.qcut)
        try:
            df["Sales Performance Category"] = pd.qcut(
                df["Sales"],
                q=4,
                labels=SALES_TIERS,
                duplicates="drop"
            )
        except Exception as e:
            logger.warning(f"qcut encountered exception ({e}), falling back to rank-based bins.")
            ranks = df["Sales"].rank(pct=True)
            df["Sales Performance Category"] = pd.cut(
                ranks,
                bins=[0, 0.25, 0.50, 0.75, 1.0],
                labels=SALES_TIERS,
                include_lowest=True
            )

        # 4. Temporal features for trend analysis
        df["Order Year"] = df["Order Date"].dt.year.astype(np.int16)
        df["Order Month"] = df["Order Date"].dt.month.astype(np.int8)
        df["Order Year-Month"] = df["Order Date"].dt.to_period("M").astype(str).astype("category")

        # Update final memory footprint
        final_bytes = df.memory_usage(deep=True).sum()
        self.memory_after_mb = final_bytes / (1024 * 1024)
        if self.memory_before_mb > 0:
            self.memory_reduction_pct = (
                (self.memory_before_mb - self.memory_after_mb) / self.memory_before_mb
            ) * 100

        self.cleaned_df = df
        logger.info(
            f"Feature engineering completed | Final Memory: {self.memory_after_mb:.2f} MB "
            f"({self.memory_reduction_pct:.1f}% reduction vs raw)"
        )
        return self.cleaned_df

    def run_pipeline(self) -> pd.DataFrame:
        """
        Orchestrates full ETL pipeline execution sequentially.
        """
        logger.info("Executing SuperstoreDataPipeline...")
        self.load_data()
        self.clean_data()
        self.optimize_memory()
        self.engineer_features()
        logger.info("Pipeline execution successfully completed.")
        return self.cleaned_df

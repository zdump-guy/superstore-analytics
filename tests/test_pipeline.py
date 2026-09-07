"""
Comprehensive unit and integration test suite for the Superstore Analytics pipeline.
"""

import os
from pathlib import Path
import unittest

import numpy as np
import pandas as pd

from src.config import (
    CLEANED_DATA_PATH,
    FIGURE_FILENAMES,
    FIGURES_DIR,
    RAW_DATA_PATH,
    REPORT_PATH,
    SALES_TIERS,
)
from src.data_pipeline import SuperstoreDataPipeline
from src.analyzer import SuperstoreAnalyzer
from src.visualizer import SuperstoreVisualizer
from src.reporter import SuperstoreReporter


class TestSuperstoreAnalyticsPipeline(unittest.TestCase):
    """
    Validates end-to-end functionality, mathematical correctness,
    memory optimization benchmarks, and artifact exports.
    """

    @classmethod
    def setUpClass(cls):
        """Initializes and runs the full pipeline once for all test assertions."""
        cls.pipeline = SuperstoreDataPipeline(raw_filepath=RAW_DATA_PATH)
        cls.df = cls.pipeline.run_pipeline()
        cls.analyzer = SuperstoreAnalyzer(cls.df)
        cls.kpis = cls.analyzer.compute_kpis()
        cls.visualizer = SuperstoreVisualizer(cls.df, output_dir=FIGURES_DIR)
        cls.reporter = SuperstoreReporter(kpis=cls.kpis, df=cls.df, export_dir=REPORT_PATH.parent)

    def test_01_ingestion_and_shape(self):
        """Validates that raw dataset was loaded with valid dimensions."""
        self.assertIsNotNone(self.pipeline.raw_df)
        self.assertGreater(len(self.pipeline.raw_df), 1000, "Raw dataset should have > 1000 records.")
        self.assertIn("Sales", self.pipeline.raw_df.columns)
        self.assertIn("Profit", self.pipeline.raw_df.columns)

    def test_02_data_cleaning_and_temporal_integrity(self):
        """Validates that dates are valid and Ship Date >= Order Date."""
        self.assertFalse(self.df["Order Date"].isnull().any(), "Order Date should not have nulls.")
        self.assertFalse(self.df["Ship Date"].isnull().any(), "Ship Date should not have nulls.")
        invalid_dates = self.df[self.df["Ship Date"] < self.df["Order Date"]]
        self.assertEqual(len(invalid_dates), 0, "All Ship Dates must be >= Order Date.")

    def test_03_memory_optimization_target(self):
        """Validates memory reduction target of >= 40%."""
        self.assertGreaterEqual(
            self.pipeline.memory_reduction_pct,
            40.0,
            f"Memory reduction was {self.pipeline.memory_reduction_pct:.2f}%, which is below the 40% threshold."
        )
        self.assertLess(self.pipeline.memory_after_mb, self.pipeline.memory_before_mb)

    def test_04_feature_engineering_correctness(self):
        """Validates calculations of Profit Margin, Shipping Duration, and Sales Performance Category."""
        # Check Profit Margin
        self.assertIn("Profit Margin", self.df.columns)
        sales = self.df["Sales"].to_numpy()
        profit = self.df["Profit"].to_numpy()
        expected_pm = np.where(sales != 0, profit / sales, 0.0).astype(np.float32)
        np.testing.assert_allclose(self.df["Profit Margin"].to_numpy(), expected_pm, rtol=1e-4)

        # Check Shipping Duration
        self.assertIn("Shipping Duration", self.df.columns)
        expected_duration = (self.df["Ship Date"] - self.df["Order Date"]).dt.days
        np.testing.assert_array_equal(self.df["Shipping Duration"].to_numpy(), expected_duration.to_numpy())
        self.assertTrue((self.df["Shipping Duration"] >= 0).all())

        # Check Sales Performance Category
        self.assertIn("Sales Performance Category", self.df.columns)
        categories = set(self.df["Sales Performance Category"].dropna().unique())
        for tier in SALES_TIERS:
            self.assertIn(tier, categories)

    def test_05_analyzer_kpis_and_statistics(self):
        """Validates KPI computation and descriptive statistics."""
        summary_stats = self.analyzer.compute_summary_statistics()
        self.assertIn("Mean", summary_stats.columns)
        self.assertIn("Skewness", summary_stats.columns)
        self.assertIn("Kurtosis", summary_stats.columns)

        kpis = self.kpis
        self.assertGreater(kpis["total_gross_revenue"], 0)
        self.assertGreater(kpis["total_unique_orders"], 0)
        self.assertGreater(kpis["average_order_value"], 0)
        self.assertGreater(kpis["loss_making_pct"], 0)
        self.assertEqual(len(kpis["top_3_profitable_subcategories"]), 3)
        self.assertEqual(len(kpis["top_3_loss_making_subcategories"]), 3)

        corrs = self.analyzer.compute_correlations()
        self.assertIn("pearson", corrs)
        self.assertIn("spearman", corrs)

    def test_06_visualizer_figures_generation(self):
        """Validates generation of all 8 required figures."""
        paths = self.visualizer.generate_all_plots()
        self.assertEqual(len(paths), 8, "Must generate exactly 8 figures.")
        for fig_key, fig_filename in FIGURE_FILENAMES.items():
            fig_path = FIGURES_DIR / fig_filename
            self.assertTrue(fig_path.exists(), f"Figure file {fig_filename} does not exist.")
            self.assertGreater(fig_path.stat().st_size, 10000, f"Figure {fig_filename} size is too small.")

    def test_07_reporter_exports(self):
        """Validates CSV and Markdown artifact export."""
        csv_path = self.reporter.export_cleaned_data(filename="cleaned_superstore.csv")
        self.assertTrue(csv_path.exists())
        self.assertGreater(csv_path.stat().st_size, 10000)

        report_path = self.reporter.generate_markdown_report(filename="automated_kpi_report.md")
        self.assertTrue(report_path.exists())
        self.assertGreater(report_path.stat().st_size, 1000)
        
        with open(report_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Executive Analytics & Automated KPI Report", content)
        self.assertIn("Total Gross Revenue", content)
        self.assertIn("Strategic Business Recommendations", content)


if __name__ == "__main__":
    unittest.main()

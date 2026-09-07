"""
SuperstoreAnalyzer: Descriptive statistics, correlation matrices,
enterprise KPI calculations, and multidimensional business aggregations.
"""

from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from src.config import NUMERICAL_FEATURES, REGION_ORDER, SEGMENT_ORDER, SHIP_MODE_ORDER

logger = logging.getLogger("SuperstoreAnalyzer")


class SuperstoreAnalyzer:
    """
    Performs comprehensive statistical, correlation, and business intelligence
    analysis on the cleaned and feature-engineered Superstore dataset.
    """

    def __init__(self, df: pd.DataFrame) -> None:
        if df is None or df.empty:
            raise ValueError("SuperstoreAnalyzer requires a non-empty DataFrame.")
        self.df: pd.DataFrame = df.copy()

    def compute_summary_statistics(self, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Calculates parametric and non-parametric descriptive statistics:
        mean, std, median, IQR, skewness, kurtosis, min, max.
        """
        cols = columns or [c for c in NUMERICAL_FEATURES if c in self.df.columns]
        stats_list = []

        for col in cols:
            series = pd.to_numeric(self.df[col], errors="coerce").dropna()
            q25 = float(series.quantile(0.25))
            q75 = float(series.quantile(0.75))
            iqr = q75 - q25
            
            stats_list.append({
                "Feature": col,
                "Mean": float(series.mean()),
                "Std Dev": float(series.std()),
                "Median": float(series.median()),
                "IQR": float(iqr),
                "Min": float(series.min()),
                "Max": float(series.max()),
                "Skewness": float(stats.skew(series, bias=False)),
                "Kurtosis": float(stats.kurtosis(series, bias=False))
            })

        summary_df = pd.DataFrame(stats_list).set_index("Feature")
        return summary_df

    def compute_correlations(self, columns: Optional[List[str]] = None) -> Dict[str, pd.DataFrame]:
        """
        Computes Pearson (linear) and Spearman (monotonic rank) correlation matrices.
        """
        cols = columns or [c for c in NUMERICAL_FEATURES if c in self.df.columns]
        numeric_df = self.df[cols].apply(pd.to_numeric, errors="coerce")

        pearson_corr = numeric_df.corr(method="pearson")
        spearman_corr = numeric_df.corr(method="spearman")

        return {
            "pearson": pearson_corr,
            "spearman": spearman_corr
        }

    def compute_kpis(self) -> Dict[str, Any]:
        """
        Calculates automated executive KPIs across financial, operational,
        and customer dimensions.
        """
        df = self.df

        total_gross_revenue = float(df["Sales"].sum())
        total_net_profit = float(df["Profit"].sum())
        enterprise_pm_pct = (total_net_profit / total_gross_revenue * 100) if total_gross_revenue != 0 else 0.0

        total_records = len(df)
        unique_orders = int(df["Order ID"].nunique()) if "Order ID" in df.columns else total_records
        unique_customers = int(df["Customer ID"].nunique()) if "Customer ID" in df.columns else 0

        # Average Order Value (Gross Revenue / Unique Orders)
        aov = total_gross_revenue / unique_orders if unique_orders > 0 else 0.0

        # Average shipping turnaround
        avg_shipping_days = float(df["Shipping Duration"].mean()) if "Shipping Duration" in df.columns else 0.0
        median_shipping_days = float(df["Shipping Duration"].median()) if "Shipping Duration" in df.columns else 0.0

        # Loss-making transactions
        loss_df = df[df["Profit"] < 0]
        loss_orders_count = int(len(loss_df))
        loss_orders_pct = (loss_orders_count / total_records * 100) if total_records > 0 else 0.0
        total_loss_value = float(loss_df["Profit"].sum())

        # Sub-category rankings
        subcat_summary = df.groupby("Sub-Category", observed=True).agg(
            Total_Profit=("Profit", "sum"),
            Total_Sales=("Sales", "sum"),
            Order_Count=("Sales", "count")
        ).reset_index()
        subcat_summary["Profit_Margin_Pct"] = (
            subcat_summary["Total_Profit"] / subcat_summary["Total_Sales"] * 100
        )
        
        top3_profitable = (
            subcat_summary.sort_values(by="Total_Profit", ascending=False)
            .head(3)
            .to_dict(orient="records")
        )
        
        top3_loss_making = (
            subcat_summary.sort_values(by="Total_Profit", ascending=True)
            .head(3)
            .to_dict(orient="records")
        )

        kpis = {
            "total_gross_revenue": total_gross_revenue,
            "total_net_profit": total_net_profit,
            "enterprise_profit_margin_pct": enterprise_pm_pct,
            "total_line_items": total_records,
            "total_unique_orders": unique_orders,
            "total_unique_customers": unique_customers,
            "average_order_value": aov,
            "average_shipping_days": avg_shipping_days,
            "median_shipping_days": median_shipping_days,
            "loss_making_count": loss_orders_count,
            "loss_making_pct": loss_orders_pct,
            "total_loss_value": total_loss_value,
            "top_3_profitable_subcategories": top3_profitable,
            "top_3_loss_making_subcategories": top3_loss_making
        }

        return kpis

    def analyze_regional_performance(self) -> pd.DataFrame:
        """
        Aggregates sales, profit, profit margin, average discount, and volume by region.
        """
        regional = self.df.groupby("Region", observed=True).agg(
            Total_Sales=("Sales", "sum"),
            Total_Profit=("Profit", "sum"),
            Avg_Discount=("Discount", "mean"),
            Order_Count=("Sales", "count"),
            Avg_Shipping_Days=("Shipping Duration", "mean")
        ).reset_index()

        regional["Profit_Margin_Pct"] = (
            regional["Total_Profit"] / regional["Total_Sales"] * 100
        )
        regional["Sales_Share_Pct"] = (
            regional["Total_Sales"] / regional["Total_Sales"].sum() * 100
        )
        regional["Profit_Share_Pct"] = (
            regional["Total_Profit"] / regional["Total_Profit"].sum() * 100
        )

        return regional.sort_values(by="Total_Sales", ascending=False)

    def analyze_subcategory_performance(self) -> pd.DataFrame:
        """
        Aggregates financial performance across Category and Sub-Category.
        """
        subcat = self.df.groupby(["Category", "Sub-Category"], observed=True).agg(
            Total_Sales=("Sales", "sum"),
            Total_Profit=("Profit", "sum"),
            Avg_Discount=("Discount", "mean"),
            Order_Count=("Sales", "count")
        ).reset_index()

        subcat["Profit_Margin_Pct"] = (
            subcat["Total_Profit"] / subcat["Total_Sales"] * 100
        )
        return subcat.sort_values(by="Total_Profit", ascending=False)

    def analyze_shipping_performance(self) -> pd.DataFrame:
        """
        Aggregates shipping turnaround duration and volume across Ship Modes.
        """
        shipping = self.df.groupby("Ship Mode", observed=True).agg(
            Order_Count=("Sales", "count"),
            Avg_Shipping_Days=("Shipping Duration", "mean"),
            Median_Shipping_Days=("Shipping Duration", "median"),
            Min_Shipping_Days=("Shipping Duration", "min"),
            Max_Shipping_Days=("Shipping Duration", "max"),
            Total_Sales=("Sales", "sum"),
            Total_Profit=("Profit", "sum")
        ).reset_index()

        shipping["Profit_Margin_Pct"] = (
            shipping["Total_Profit"] / shipping["Total_Sales"] * 100
        )
        return shipping

    def analyze_segment_performance(self) -> pd.DataFrame:
        """
        Aggregates customer segment profitability and average basket value.
        """
        segment = self.df.groupby("Segment", observed=True).agg(
            Total_Sales=("Sales", "sum"),
            Total_Profit=("Profit", "sum"),
            Avg_Discount=("Discount", "mean"),
            Order_Count=("Sales", "count")
        ).reset_index()

        segment["Profit_Margin_Pct"] = (
            segment["Total_Profit"] / segment["Total_Sales"] * 100
        )
        segment["Revenue_Share_Pct"] = (
            segment["Total_Sales"] / segment["Total_Sales"].sum() * 100
        )
        return segment

    def analyze_sales_tiers(self) -> pd.DataFrame:
        """
        Aggregates order count, revenue share, and profit margin across sales tiers.
        """
        tiers = self.df.groupby("Sales Performance Category", observed=True).agg(
            Order_Count=("Sales", "count"),
            Total_Sales=("Sales", "sum"),
            Total_Profit=("Profit", "sum"),
            Avg_Sales=("Sales", "mean"),
            Avg_Profit_Margin=("Profit Margin", "mean")
        ).reset_index()

        tiers["Revenue_Share_Pct"] = (
            tiers["Total_Sales"] / tiers["Total_Sales"].sum() * 100
        )
        tiers["Profit_Share_Pct"] = (
            tiers["Total_Profit"] / tiers["Total_Profit"].sum() * 100
        )
        return tiers

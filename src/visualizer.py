"""
SuperstoreVisualizer: Publication-grade visualization suite producing 8 high-DPI (300 DPI)
charts adhering to professional corporate design guidelines.
"""

from __future__ import annotations
import logging
from pathlib import Path
from typing import List, Optional, Tuple

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import pandas as pd
import seaborn as sns

from src.config import (
    COLORS,
    FIGURE_FILENAMES,
    FIGURES_DIR,
    NUMERICAL_FEATURES,
    PLOT_DPI,
    REGION_ORDER,
    REGION_PALETTE,
    SALES_TIERS,
    SEGMENT_ORDER,
    SEGMENT_PALETTE,
    SHIP_MODE_ORDER,
)

logger = logging.getLogger("SuperstoreVisualizer")


class SuperstoreVisualizer:
    """
    Generates and exports the 8 required publication-quality figures at 300 DPI.
    """

    def __init__(self, df: pd.DataFrame, output_dir: str | Path = FIGURES_DIR) -> None:
        if df is None or df.empty:
            raise ValueError("SuperstoreVisualizer requires a valid, non-empty DataFrame.")
        self.df: pd.DataFrame = df.copy()
        self.output_dir: Path = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._setup_style()

    def _setup_style(self) -> None:
        """Sets professional corporate styling defaults."""
        sns.set_theme(style="whitegrid", palette="deep")
        plt.rcParams.update({
            "figure.dpi": PLOT_DPI,
            "savefig.dpi": PLOT_DPI,
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans", "Helvetica", "Arial"],
            "axes.titlesize": 14,
            "axes.titleweight": "bold",
            "axes.labelsize": 11,
            "axes.labelweight": "bold",
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "legend.fontsize": 10,
            "legend.title_fontsize": 11,
            "figure.titlesize": 16,
            "figure.titleweight": "bold"
        })

    def plot_correlation_heatmap(self) -> Path:
        """
        Figure 1: Pearson Correlation Heatmap with masked upper triangle.
        """
        cols = [c for c in NUMERICAL_FEATURES if c in self.df.columns]
        numeric_df = self.df[cols].apply(pd.to_numeric, errors="coerce")
        corr = numeric_df.corr(method="pearson")

        mask = np.triu(np.ones_like(corr, dtype=bool))

        fig, ax = plt.subplots(figsize=(9, 7))
        cmap = sns.diverging_palette(230, 20, as_cmap=True)

        sns.heatmap(
            corr,
            mask=mask,
            cmap=cmap,
            vmax=1.0,
            vmin=-1.0,
            center=0,
            annot=True,
            fmt=".2f",
            square=True,
            linewidths=1.2,
            cbar_kws={"shrink": 0.8, "label": "Pearson Correlation Coefficient"},
            ax=ax
        )

        ax.set_title("Figure 1: Pearson Correlation Matrix Across Financial & Operational Metrics", pad=16)
        plt.xticks(rotation=30, ha="right")
        plt.yticks(rotation=0)
        plt.tight_layout()

        out_path = self.output_dir / FIGURE_FILENAMES["fig1"]
        fig.savefig(out_path, dpi=PLOT_DPI, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"Saved Figure 1 to {out_path}")
        return out_path

    def plot_subcategory_performance(self) -> Path:
        """
        Figure 2: Clustered/Dual horizontal bar chart comparing Total Sales and Total Profit
        per Sub-Category, highlighting loss-making categories.
        """
        subcat = self.df.groupby("Sub-Category", observed=True).agg(
            Total_Sales=("Sales", "sum"),
            Total_Profit=("Profit", "sum")
        ).reset_index()

        subcat = subcat.sort_values(by="Total_Sales", ascending=True)

        y_positions = np.arange(len(subcat))
        height = 0.38

        fig, ax = plt.subplots(figsize=(12, 9))

        # Sales bars
        bars_sales = ax.barh(
            y_positions + height/2,
            subcat["Total_Sales"],
            height=height,
            color="#2b5c8f",
            label="Total Sales ($)",
            alpha=0.9
        )

        # Profit bars with color conditioning (green for positive, red for loss)
        profit_colors = ["#e74c3c" if p < 0 else "#27ae60" for p in subcat["Total_Profit"]]
        bars_profit = ax.barh(
            y_positions - height/2,
            subcat["Total_Profit"],
            height=height,
            color=profit_colors,
            label="Total Profit ($) [Red = Loss]",
            alpha=0.9
        )

        ax.axvline(0, color="black", linestyle="--", linewidth=1, alpha=0.7)
        ax.set_yticks(y_positions)
        ax.set_yticklabels(subcat["Sub-Category"])
        ax.xaxis.set_major_formatter(ticker.StrMethodFormatter("${x:,.0f}"))
        ax.set_xlabel("Monetary Value ($ USD)")
        ax.set_title("Figure 2: Total Sales vs. Net Profit Across Product Sub-Categories", pad=16)
        ax.legend(loc="lower right", frameon=True)

        # Annotate loss makers
        for idx, (sales, profit, name) in enumerate(zip(subcat["Total_Sales"], subcat["Total_Profit"], subcat["Sub-Category"])):
            if profit < 0:
                ax.annotate(
                    f" Loss: -${abs(profit):,.0f}",
                    xy=(profit, idx - height/2),
                    xytext=(-65, -3),
                    textcoords="offset points",
                    fontsize=8.5,
                    fontweight="bold",
                    color="#c0392b"
                )

        plt.tight_layout()
        out_path = self.output_dir / FIGURE_FILENAMES["fig2"]
        fig.savefig(out_path, dpi=PLOT_DPI, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"Saved Figure 2 to {out_path}")
        return out_path

    def plot_monthly_trend(self) -> Path:
        """
        Figure 3: Longitudinal Monthly Sales & Profit Trend with annotated peak seasonal periods.
        """
        df_time = self.df.copy()
        df_time["YearMonth"] = df_time["Order Date"].dt.to_period("M").dt.to_timestamp()
        
        monthly = df_time.groupby("YearMonth").agg(
            Monthly_Sales=("Sales", "sum"),
            Monthly_Profit=("Profit", "sum")
        ).reset_index()

        fig, ax1 = plt.subplots(figsize=(14, 6))

        # Plot Sales Line
        line1 = ax1.plot(
            monthly["YearMonth"],
            monthly["Monthly_Sales"],
            color="#2980b9",
            marker="o",
            linewidth=2.2,
            label="Monthly Sales ($)"
        )
        ax1.set_ylabel("Total Sales ($ USD)", color="#2980b9", fontweight="bold")
        ax1.yaxis.set_major_formatter(ticker.StrMethodFormatter("${x:,.0f}"))
        ax1.tick_params(axis="y", labelcolor="#2980b9")

        # Secondary Axis for Profit
        ax2 = ax1.twinx()
        line2 = ax2.plot(
            monthly["YearMonth"],
            monthly["Monthly_Profit"],
            color="#27ae60",
            marker="s",
            linewidth=2.0,
            linestyle="--",
            label="Monthly Profit ($)"
        )
        ax2.set_ylabel("Total Profit ($ USD)", color="#27ae60", fontweight="bold")
        ax2.yaxis.set_major_formatter(ticker.StrMethodFormatter("${x:,.0f}"))
        ax2.tick_params(axis="y", labelcolor="#27ae60")
        ax2.grid(False)

        # Highlight max sales month
        max_sales_idx = monthly["Monthly_Sales"].idxmax()
        max_sales_row = monthly.iloc[max_sales_idx]
        ax1.annotate(
            f"Peak Sales: ${max_sales_row['Monthly_Sales']:,.0f}\n({max_sales_row['YearMonth'].strftime('%b %Y')})",
            xy=(max_sales_row["YearMonth"], max_sales_row["Monthly_Sales"]),
            xytext=(-40, 25),
            textcoords="offset points",
            arrowprops=dict(arrowstyle="->", color="#e74c3c", lw=1.5),
            fontweight="bold",
            color="#c0392b",
            bbox=dict(boxstyle="round,pad=0.3", fc="#fdf2e9", ec="#e74c3c", lw=1)
        )

        # Combine legends
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax1.legend(lines, labels, loc="upper left", frameon=True)

        ax1.set_title("Figure 3: Longitudinal Monthly Sales and Profit Dynamics (Multi-Year)", pad=16)
        ax1.set_xlabel("Order Timeline (Month-Year)")
        plt.tight_layout()

        out_path = self.output_dir / FIGURE_FILENAMES["fig3"]
        fig.savefig(out_path, dpi=PLOT_DPI, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"Saved Figure 3 to {out_path}")
        return out_path

    def plot_discount_impact(self) -> Path:
        """
        Figure 4: Discount vs. Profit Margin with regression trendline and threshold indicator.
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        sample_df = self.df.sample(min(len(self.df), 5000), random_state=42)

        sns.regplot(
            data=sample_df,
            x="Discount",
            y="Profit Margin",
            scatter_kws={"alpha": 0.25, "color": "#34495e", "s": 25},
            line_kws={"color": "#e74c3c", "linewidth": 2.5, "label": "Linear Regression Trend"},
            ax=ax
        )

        # Reference zero profit margin line
        ax.axhline(0, color="#27ae60", linestyle="--", linewidth=1.5, label="Break-Even Threshold (PM = 0)")
        
        # Discount critical threshold line around 20%
        ax.axvline(0.20, color="#d35400", linestyle=":", linewidth=1.8, label="20% Discount Warning Threshold")

        ax.set_title("Figure 4: Impact of Discounting on Profit Margin & Critical Threshold", pad=16)
        ax.set_xlabel("Discount Rate (0.0 = 0%, 0.8 = 80%)")
        ax.set_ylabel("Profit Margin (Profit / Sales)")
        ax.xaxis.set_major_formatter(ticker.PercentFormatter(1.0))
        ax.yaxis.set_major_formatter(ticker.PercentFormatter(1.0))
        ax.set_ylim(-3.0, 1.0)
        ax.legend(loc="lower left", frameon=True)

        ax.annotate(
            "Steep margin erosion beyond 20% discount",
            xy=(0.25, -0.2),
            xytext=(0.40, -1.5),
            arrowprops=dict(arrowstyle="->", color="#c0392b", lw=1.5),
            bbox=dict(boxstyle="round,pad=0.3", fc="#fbeee6", ec="#d35400", lw=1),
            fontweight="bold",
            color="#c0392b"
        )

        plt.tight_layout()
        out_path = self.output_dir / FIGURE_FILENAMES["fig4"]
        fig.savefig(out_path, dpi=PLOT_DPI, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"Saved Figure 4 to {out_path}")
        return out_path

    def plot_shipping_duration(self) -> Path:
        """
        Figure 5: Operational Shipping Duration by Ship Mode (Boxplot).
        """
        order = [m for m in SHIP_MODE_ORDER if m in self.df["Ship Mode"].values]
        
        fig, ax = plt.subplots(figsize=(10, 6))

        sns.boxplot(
            data=self.df,
            x="Ship Mode",
            y="Shipping Duration",
            hue="Ship Mode",
            legend=False,
            order=order,
            palette="Blues_r",
            boxprops=dict(alpha=0.85),
            showmeans=True,
            meanprops=dict(marker="o", markeredgecolor="black", markerfacecolor="#e74c3c", markersize=7),
            ax=ax
        )

        ax.set_title("Figure 5: Operational Shipping Duration Distribution Across Ship Modes", pad=16)
        ax.set_xlabel("Fulfillment / Shipping Mode")
        ax.set_ylabel("Duration in Days (Ship Date - Order Date)")
        
        # Annotate SLA medians
        medians = self.df.groupby("Ship Mode", observed=True)["Shipping Duration"].median()
        for idx, mode in enumerate(order):
            if mode in medians:
                ax.text(
                    idx,
                    medians[mode] + 0.25,
                    f"Median: {int(medians[mode])}d",
                    ha="center",
                    va="bottom",
                    fontweight="bold",
                    fontsize=9.5,
                    color="#1a252f"
                )

        plt.tight_layout()
        out_path = self.output_dir / FIGURE_FILENAMES["fig5"]
        fig.savefig(out_path, dpi=PLOT_DPI, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"Saved Figure 5 to {out_path}")
        return out_path

    def plot_segment_profitability(self) -> Path:
        """
        Figure 6: Profit Margin Distribution Across Customer Segments (KDE Plot).
        """
        fig, ax = plt.subplots(figsize=(10, 6))

        order = [s for s in SEGMENT_ORDER if s in self.df["Segment"].values]

        for seg in order:
            seg_data = self.df[self.df["Segment"] == seg]["Profit Margin"].dropna()
            clipped = seg_data.clip(-1.0, 0.8)
            sns.kdeplot(
                clipped,
                label=f"{seg} (Mean PM: {seg_data.mean():.1%})",
                fill=True,
                alpha=0.35,
                linewidth=2.2,
                color=SEGMENT_PALETTE.get(seg, "#3498db"),
                ax=ax
            )

        ax.axvline(0, color="black", linestyle="--", linewidth=1.2, alpha=0.7, label="Break-Even (PM = 0)")
        ax.set_title("Figure 6: Profit Margin Probability Density Across Customer Segments", pad=16)
        ax.set_xlabel("Profit Margin (Profit / Sales)")
        ax.set_ylabel("Kernel Density Estimate (KDE)")
        ax.xaxis.set_major_formatter(ticker.PercentFormatter(1.0))
        ax.set_xlim(-0.8, 0.7)
        ax.legend(loc="upper left", frameon=True)

        plt.tight_layout()
        out_path = self.output_dir / FIGURE_FILENAMES["fig6"]
        fig.savefig(out_path, dpi=PLOT_DPI, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"Saved Figure 6 to {out_path}")
        return out_path

    def plot_regional_breakdown(self) -> Path:
        """
        Figure 7: Geographic Regional Contribution (Sales, Profit, Average Discount).
        """
        regional = self.df.groupby("Region", observed=True).agg(
            Total_Sales=("Sales", "sum"),
            Total_Profit=("Profit", "sum"),
            Avg_Discount=("Discount", "mean")
        ).reset_index()

        order = [r for r in REGION_ORDER if r in regional["Region"].values]
        regional["Region"] = pd.Categorical(regional["Region"], categories=order, ordered=True)
        regional = regional.sort_values("Region")

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), gridspec_kw={"width_ratios": [1.8, 1]})

        x_pos = np.arange(len(regional))
        width = 0.35

        # Bar 1: Sales and Profit
        bars1 = ax1.bar(x_pos - width/2, regional["Total_Sales"], width=width, label="Total Sales ($)", color="#2980b9", alpha=0.9)
        bars2 = ax1.bar(x_pos + width/2, regional["Total_Profit"], width=width, label="Total Profit ($)", color="#27ae60", alpha=0.9)

        ax1.set_xticks(x_pos)
        ax1.set_xticklabels(regional["Region"], fontweight="bold")
        ax1.yaxis.set_major_formatter(ticker.StrMethodFormatter("${x:,.0f}"))
        ax1.set_title("Total Sales & Profit by Region", fontsize=12, pad=10)
        ax1.set_ylabel("Monetary Value ($ USD)")
        ax1.legend(loc="upper left", frameon=True)

        # Bar 2: Average Discount by Region
        discount_colors = ["#e74c3c" if d > regional["Avg_Discount"].mean() else "#3498db" for d in regional["Avg_Discount"]]
        ax2.bar(regional["Region"], regional["Avg_Discount"], color=discount_colors, width=0.5, alpha=0.85)
        ax2.axhline(regional["Avg_Discount"].mean(), color="black", linestyle="--", linewidth=1.2, label=f"Mean ({regional['Avg_Discount'].mean():.1%})")
        
        ax2.yaxis.set_major_formatter(ticker.PercentFormatter(1.0))
        ax2.set_title("Average Discount Rate by Region", fontsize=12, pad=10)
        ax2.set_ylabel("Discount Rate (%)")
        ax2.legend(loc="upper right", frameon=True)

        fig.suptitle("Figure 7: Multidimensional Geographic Regional Performance Breakdown", fontsize=14, y=1.02)
        plt.tight_layout()

        out_path = self.output_dir / FIGURE_FILENAMES["fig7"]
        fig.savefig(out_path, dpi=PLOT_DPI, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"Saved Figure 7 to {out_path}")
        return out_path

    def plot_sales_performance_tiers(self) -> Path:
        """
        Figure 8: Sales Performance Category Distribution & Share (Donut & Breakdown).
        """
        tier_agg = self.df.groupby("Sales Performance Category", observed=True).agg(
            Order_Count=("Sales", "count"),
            Total_Sales=("Sales", "sum")
        ).reset_index()

        tier_order = [t for t in SALES_TIERS if t in tier_agg["Sales Performance Category"].values]
        tier_agg["Sales Performance Category"] = pd.Categorical(
            tier_agg["Sales Performance Category"], categories=tier_order, ordered=True
        )
        tier_agg = tier_agg.sort_values("Sales Performance Category")

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6))

        palette = ["#aec7e8", "#1f77b4", "#ffbb78", "#2ca02c"]

        # Donut 1: Order Volume Share
        wedges1, texts1, autotexts1 = ax1.pie(
            tier_agg["Order_Count"],
            labels=tier_agg["Sales Performance Category"],
            autopct="%1.1f%%",
            startangle=140,
            colors=palette,
            wedgeprops=dict(width=0.4, edgecolor="white", linewidth=2),
            pctdistance=0.75
        )
        ax1.set_title("Order Volume Share by Tier", fontsize=12, pad=12)

        # Donut 2: Revenue Contribution Share
        wedges2, texts2, autotexts2 = ax2.pie(
            tier_agg["Total_Sales"],
            labels=tier_agg["Sales Performance Category"],
            autopct="%1.1f%%",
            startangle=140,
            colors=palette,
            wedgeprops=dict(width=0.4, edgecolor="white", linewidth=2),
            pctdistance=0.75
        )
        ax2.set_title("Gross Revenue Share by Tier", fontsize=12, pad=12)

        for at in autotexts1 + autotexts2:
            at.set_fontweight("bold")
            at.set_fontsize(9.5)

        fig.suptitle("Figure 8: Sales Performance Quartile Distribution (Volume vs Revenue)", fontsize=14, y=1.02)
        plt.tight_layout()

        out_path = self.output_dir / FIGURE_FILENAMES["fig8"]
        fig.savefig(out_path, dpi=PLOT_DPI, bbox_inches="tight")
        plt.close(fig)
        logger.info(f"Saved Figure 8 to {out_path}")
        return out_path

    def generate_all_plots(self) -> List[Path]:
        """
        Executes and exports all 8 required figures sequentially.
        """
        logger.info("Generating all 8 publication figures...")
        paths = [
            self.plot_correlation_heatmap(),
            self.plot_subcategory_performance(),
            self.plot_monthly_trend(),
            self.plot_discount_impact(),
            self.plot_shipping_duration(),
            self.plot_segment_profitability(),
            self.plot_regional_breakdown(),
            self.plot_sales_performance_tiers()
        ]
        logger.info(f"Successfully generated and exported {len(paths)} figures to {self.output_dir}.")
        return paths

#!/usr/bin/env python3
"""
Create data visualizations from CSV files
Generates various plot types using matplotlib and seaborn

Uses _skill_args injected by skills_tool:
    csv_path: Path to CSV file (required)
    plot_type: Type of plot - histogram, bar, line, scatter, box, heatmap (required)
    column: Column name for single-variable plots (required for histogram, bar)
    x_column: X-axis column for scatter/line plots (optional)
    y_column: Y-axis column for scatter/line plots (optional)
    group_by: Grouping column for bar charts (optional)
    output_path: Path to save plot image (optional, default: /tmp/plot.png)
    title: Custom plot title (optional)
    figsize: Figure size as "width,height" (optional, default: "12,8")
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
import sys

# Set style
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10

def create_histogram(df, column, title=None, output_path='/tmp/plot.png', figsize=(12, 8)):
    """Create histogram for a numeric column"""
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in dataset")

    data = df[column].dropna()

    if len(data) == 0:
        raise ValueError(f"Column '{column}' has no valid data")

    fig, ax = plt.subplots(figsize=figsize)

    # Create histogram with KDE overlay
    ax.hist(data, bins=30, alpha=0.7, color='steelblue', edgecolor='black')

    # Add KDE if enough data points
    if len(data) > 2:
        from scipy import stats
        kde = stats.gaussian_kde(data)
        x_range = np.linspace(data.min(), data.max(), 100)
        ax2 = ax.twinx()
        ax2.plot(x_range, kde(x_range), 'r-', linewidth=2, label='Density')
        ax2.set_ylabel('Density', color='r')
        ax2.tick_params(axis='y', labelcolor='r')
        ax2.legend(loc='upper right')

    ax.set_xlabel(column)
    ax.set_ylabel('Frequency')
    ax.set_title(title or f'Distribution of {column}')

    # Add statistics
    stats_text = f'Mean: {data.mean():.2f}\nMedian: {data.median():.2f}\nStd: {data.std():.2f}'
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Histogram saved to: {output_path}")
    print(f"Statistics for {column}:")
    print(f"  Count: {len(data):,}")
    print(f"  Mean: {data.mean():.2f}")
    print(f"  Median: {data.median():.2f}")
    print(f"  Std Dev: {data.std():.2f}")
    print(f"  Min: {data.min():.2f}")
    print(f"  Max: {data.max():.2f}")

def create_bar_chart(df, column, group_by=None, title=None, output_path='/tmp/plot.png', figsize=(12, 8)):
    """Create bar chart for categorical data or grouped data"""
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in dataset")

    fig, ax = plt.subplots(figsize=figsize)

    if group_by and group_by in df.columns:
        # Grouped bar chart
        grouped = df.groupby(group_by)[column].sum().sort_values(ascending=False)

        # Limit to top 20 categories if too many
        if len(grouped) > 20:
            print(f"Note: Showing top 20 out of {len(grouped)} categories")
            grouped = grouped.head(20)

        colors = plt.cm.viridis(np.linspace(0, 1, len(grouped)))
        bars = ax.bar(range(len(grouped)), grouped.values, color=colors)
        ax.set_xticks(range(len(grouped)))
        ax.set_xticklabels(grouped.index, rotation=45, ha='right')
        ax.set_xlabel(group_by)
        ax.set_ylabel(column)
        ax.set_title(title or f'{column} by {group_by}')

        # Add value labels on bars
        for i, (bar, value) in enumerate(zip(bars, grouped.values)):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{value:,.0f}', ha='center', va='bottom', fontsize=9)

    else:
        # Simple value counts bar chart
        if df[column].dtype in ['object', 'category']:
            counts = df[column].value_counts()
        else:
            # For numeric, create bins
            counts = pd.cut(df[column], bins=10).value_counts().sort_index()

        # Limit to top 20
        if len(counts) > 20:
            print(f"Note: Showing top 20 out of {len(counts)} values")
            counts = counts.head(20)

        colors = plt.cm.plasma(np.linspace(0, 1, len(counts)))
        bars = ax.bar(range(len(counts)), counts.values, color=colors)
        ax.set_xticks(range(len(counts)))
        ax.set_xticklabels([str(x)[:30] for x in counts.index], rotation=45, ha='right')
        ax.set_xlabel(column)
        ax.set_ylabel('Count')
        ax.set_title(title or f'Distribution of {column}')

        # Add count labels
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{int(height):,}', ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Bar chart saved to: {output_path}")

def create_line_chart(df, x_column, y_column, title=None, output_path='/tmp/plot.png', figsize=(12, 8)):
    """Create line chart for time series or continuous data"""
    if x_column not in df.columns or y_column not in df.columns:
        raise ValueError(f"Columns '{x_column}' or '{y_column}' not found")

    # Sort by x_column for proper line plotting
    df_sorted = df[[x_column, y_column]].dropna().sort_values(x_column)

    fig, ax = plt.subplots(figsize=figsize)

    ax.plot(df_sorted[x_column], df_sorted[y_column], marker='o', linewidth=2, markersize=4)
    ax.set_xlabel(x_column)
    ax.set_ylabel(y_column)
    ax.set_title(title or f'{y_column} over {x_column}')

    # Rotate x-axis labels if they're dates or long strings
    plt.xticks(rotation=45, ha='right')

    # Add grid
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Line chart saved to: {output_path}")
    print(f"Data points: {len(df_sorted):,}")

def create_scatter_plot(df, x_column, y_column, title=None, output_path='/tmp/plot.png', figsize=(12, 8)):
    """Create scatter plot to show relationship between two variables"""
    if x_column not in df.columns or y_column not in df.columns:
        raise ValueError(f"Columns '{x_column}' or '{y_column}' not found")

    data = df[[x_column, y_column]].dropna()

    fig, ax = plt.subplots(figsize=figsize)

    ax.scatter(data[x_column], data[y_column], alpha=0.6, s=50, c='steelblue', edgecolors='black', linewidth=0.5)
    ax.set_xlabel(x_column)
    ax.set_ylabel(y_column)
    ax.set_title(title or f'{y_column} vs {x_column}')

    # Add trend line if both are numeric
    if pd.api.types.is_numeric_dtype(data[x_column]) and pd.api.types.is_numeric_dtype(data[y_column]):
        z = np.polyfit(data[x_column], data[y_column], 1)
        p = np.poly1d(z)
        ax.plot(data[x_column], p(data[x_column]), "r--", linewidth=2, alpha=0.8, label='Trend line')

        # Calculate correlation
        correlation = data[x_column].corr(data[y_column])
        ax.text(0.05, 0.95, f'Correlation: {correlation:.3f}',
                transform=ax.transAxes, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

        ax.legend()

    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Scatter plot saved to: {output_path}")
    print(f"Data points: {len(data):,}")

def create_box_plot(df, column, group_by=None, title=None, output_path='/tmp/plot.png', figsize=(12, 8)):
    """Create box plot for distribution analysis"""
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in dataset")

    fig, ax = plt.subplots(figsize=figsize)

    if group_by and group_by in df.columns:
        # Grouped box plot
        data_to_plot = []
        labels = []

        for group in df[group_by].unique():
            if pd.notna(group):
                group_data = df[df[group_by] == group][column].dropna()
                if len(group_data) > 0:
                    data_to_plot.append(group_data)
                    labels.append(str(group)[:30])

        # Limit to 20 groups
        if len(data_to_plot) > 20:
            print(f"Note: Showing first 20 out of {len(data_to_plot)} groups")
            data_to_plot = data_to_plot[:20]
            labels = labels[:20]

        bp = ax.boxplot(data_to_plot, labels=labels, patch_artist=True)

        # Color boxes
        colors = plt.cm.Set3(np.linspace(0, 1, len(data_to_plot)))
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)

        ax.set_xlabel(group_by)
        ax.set_ylabel(column)
        ax.set_title(title or f'Distribution of {column} by {group_by}')
        plt.xticks(rotation=45, ha='right')

    else:
        # Single box plot
        data = df[column].dropna()
        bp = ax.boxplot([data], labels=[column], patch_artist=True)
        bp['boxes'][0].set_facecolor('lightblue')
        ax.set_ylabel(column)
        ax.set_title(title or f'Distribution of {column}')

        # Add statistics
        stats_text = f'Median: {data.median():.2f}\nQ1: {data.quantile(0.25):.2f}\nQ3: {data.quantile(0.75):.2f}\nIQR: {data.quantile(0.75) - data.quantile(0.25):.2f}'
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Box plot saved to: {output_path}")

def create_heatmap(df, title=None, output_path='/tmp/plot.png', figsize=(12, 10)):
    """Create correlation heatmap for numeric columns"""
    numeric_cols = df.select_dtypes(include=['number']).columns

    if len(numeric_cols) < 2:
        raise ValueError("Need at least 2 numeric columns for correlation heatmap")

    corr_matrix = df[numeric_cols].corr()

    fig, ax = plt.subplots(figsize=figsize)

    # Create heatmap
    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', center=0,
                square=True, linewidths=1, cbar_kws={"shrink": 0.8}, ax=ax)

    ax.set_title(title or 'Correlation Heatmap')

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Heatmap saved to: {output_path}")
    print(f"\nCorrelation matrix for {len(numeric_cols)} numeric columns")

def main():
    # Get arguments
    csv_path = _skill_args.get("csv_path")
    plot_type = _skill_args.get("plot_type", "").lower()
    column = _skill_args.get("column")
    x_column = _skill_args.get("x_column")
    y_column = _skill_args.get("y_column")
    group_by = _skill_args.get("group_by")
    output_path = _skill_args.get("output_path", "/tmp/plot.png")
    title = _skill_args.get("title")
    figsize_str = _skill_args.get("figsize", "12,8")

    # Parse figsize
    try:
        width, height = map(float, figsize_str.split(','))
        figsize = (width, height)
    except:
        figsize = (12, 8)

    # Validate arguments
    if not csv_path:
        print("Error: csv_path required in script_args")
        print("\nUsage examples:")
        print('  Histogram: {"csv_path": "data.csv", "plot_type": "histogram", "column": "revenue"}')
        print('  Bar chart: {"csv_path": "data.csv", "plot_type": "bar", "column": "category"}')
        print('  Line chart: {"csv_path": "data.csv", "plot_type": "line", "x_column": "date", "y_column": "sales"}')
        print('  Scatter: {"csv_path": "data.csv", "plot_type": "scatter", "x_column": "price", "y_column": "sales"}')
        print('  Box plot: {"csv_path": "data.csv", "plot_type": "box", "column": "revenue", "group_by": "region"}')
        print('  Heatmap: {"csv_path": "data.csv", "plot_type": "heatmap"}')
        sys.exit(1)

    if not plot_type:
        print("Error: plot_type required (histogram, bar, line, scatter, box, heatmap)")
        sys.exit(1)

    valid_types = ['histogram', 'bar', 'line', 'scatter', 'box', 'heatmap']
    if plot_type not in valid_types:
        print(f"Error: Invalid plot_type '{plot_type}'")
        print(f"Valid types: {', '.join(valid_types)}")
        sys.exit(1)

    try:
        # Load data
        print(f"Loading CSV file: {csv_path}")
        df = pd.read_csv(csv_path)
        print(f"Loaded {len(df):,} rows, {len(df.columns)} columns")

        # Create plot based on type
        if plot_type == 'histogram':
            if not column:
                print("Error: column required for histogram")
                sys.exit(1)
            create_histogram(df, column, title, output_path, figsize)

        elif plot_type == 'bar':
            if not column:
                print("Error: column required for bar chart")
                sys.exit(1)
            create_bar_chart(df, column, group_by, title, output_path, figsize)

        elif plot_type == 'line':
            if not x_column or not y_column:
                print("Error: x_column and y_column required for line chart")
                sys.exit(1)
            create_line_chart(df, x_column, y_column, title, output_path, figsize)

        elif plot_type == 'scatter':
            if not x_column or not y_column:
                print("Error: x_column and y_column required for scatter plot")
                sys.exit(1)
            create_scatter_plot(df, x_column, y_column, title, output_path, figsize)

        elif plot_type == 'box':
            if not column:
                print("Error: column required for box plot")
                sys.exit(1)
            create_box_plot(df, column, group_by, title, output_path, figsize)

        elif plot_type == 'heatmap':
            create_heatmap(df, title, output_path, figsize)

        print("\nVisualization complete!")

    except FileNotFoundError:
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error creating visualization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

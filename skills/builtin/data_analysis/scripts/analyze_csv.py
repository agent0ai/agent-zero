#!/usr/bin/env python3
"""
Analyze CSV data with pandas
Provides comprehensive dataset analysis including statistics, missing values, and grouping

Uses _skill_args injected by skills_tool:
    csv_path: Path to CSV file (required)
    group_by: Column name to group by (optional)
    separator: CSV delimiter (optional, default: ',')
    encoding: File encoding (optional, default: 'utf-8')
"""

import pandas as pd
import numpy as np
import sys
import json

def format_number(num):
    """Format numbers for readable output"""
    if pd.isna(num):
        return 'N/A'
    if abs(num) >= 1e6:
        return f"{num/1e6:.2f}M"
    elif abs(num) >= 1e3:
        return f"{num/1e3:.2f}K"
    else:
        return f"{num:.2f}"

def main():
    # Get arguments injected by skills_tool
    csv_path = _skill_args.get("csv_path")
    group_by = _skill_args.get("group_by", None)
    separator = _skill_args.get("separator", ",")
    encoding = _skill_args.get("encoding", "utf-8")

    if not csv_path:
        print("Error: csv_path required in script_args")
        print("\nUsage:")
        print('{"csv_path": "/path/to/file.csv", "group_by": "optional_column"}')
        sys.exit(1)

    try:
        # Load data
        print(f"Loading CSV file: {csv_path}")
        df = pd.read_csv(csv_path, sep=separator, encoding=encoding)

        print(f"\n{'='*60}")
        print(f"Dataset loaded successfully!")
        print(f"{'='*60}")

        # Basic information
        print(f"\n{'='*60}")
        print("DATASET DIMENSIONS")
        print(f"{'='*60}")
        print(f"Rows: {len(df):,}")
        print(f"Columns: {len(df.columns)}")
        print(f"Total cells: {len(df) * len(df.columns):,}")
        print(f"Memory usage: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")

        # Column information
        print(f"\n{'='*60}")
        print("COLUMN INFORMATION")
        print(f"{'='*60}")
        print(f"\n{'Column':<30} {'Type':<15} {'Non-Null':<12} {'Unique':<10}")
        print("-" * 67)

        for col in df.columns:
            col_type = str(df[col].dtype)
            non_null = df[col].notna().sum()
            unique = df[col].nunique()
            print(f"{col[:29]:<30} {col_type:<15} {non_null:<12,} {unique:<10,}")

        # Data types summary
        print(f"\nData type distribution:")
        type_counts = df.dtypes.value_counts()
        for dtype, count in type_counts.items():
            print(f"  {dtype}: {count} columns")

        # Missing values analysis
        print(f"\n{'='*60}")
        print("MISSING VALUES ANALYSIS")
        print(f"{'='*60}")

        missing = df.isnull().sum()
        missing_pct = (missing / len(df)) * 100

        if missing.sum() == 0:
            print("\nNo missing values found!")
        else:
            print(f"\nTotal missing cells: {missing.sum():,} ({(missing.sum() / (len(df) * len(df.columns)) * 100):.2f}% of all cells)")
            print(f"\n{'Column':<30} {'Missing':<12} {'Percentage'}")
            print("-" * 52)

            missing_df = pd.DataFrame({
                'Missing': missing,
                'Percentage': missing_pct
            }).sort_values('Missing', ascending=False)

            for col, row in missing_df[missing_df['Missing'] > 0].iterrows():
                print(f"{col[:29]:<30} {int(row['Missing']):<12,} {row['Percentage']:.2f}%")

        # Duplicates analysis
        print(f"\n{'='*60}")
        print("DUPLICATE ANALYSIS")
        print(f"{'='*60}")

        duplicates = df.duplicated()
        dup_count = duplicates.sum()

        if dup_count == 0:
            print("\nNo duplicate rows found!")
        else:
            print(f"\nDuplicate rows: {dup_count:,} ({(dup_count / len(df) * 100):.2f}% of total)")

        # Summary statistics for numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns

        if len(numeric_cols) > 0:
            print(f"\n{'='*60}")
            print("SUMMARY STATISTICS (Numeric Columns)")
            print(f"{'='*60}")

            stats = df[numeric_cols].describe()
            print(f"\n{stats.to_string()}")

            # Additional statistics
            print(f"\n{'Statistic':<30} {'Column':<30} {'Value'}")
            print("-" * 70)

            for col in numeric_cols:
                print(f"{'Sum':<30} {col[:29]:<30} {format_number(df[col].sum())}")
                print(f"{'Median':<30} {col[:29]:<30} {format_number(df[col].median())}")
                print(f"{'Mode':<30} {col[:29]:<30} {format_number(df[col].mode()[0] if len(df[col].mode()) > 0 else np.nan)}")
                print(f"{'Variance':<30} {col[:29]:<30} {format_number(df[col].var())}")
                print(f"{'Skewness':<30} {col[:29]:<30} {format_number(df[col].skew())}")
                print(f"{'Kurtosis':<30} {col[:29]:<30} {format_number(df[col].kurtosis())}")
                print()

        # Summary for categorical columns
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns

        if len(categorical_cols) > 0:
            print(f"\n{'='*60}")
            print("CATEGORICAL COLUMNS SUMMARY")
            print(f"{'='*60}")

            for col in categorical_cols[:5]:  # Limit to first 5 to avoid clutter
                print(f"\n{col}:")
                print(f"  Unique values: {df[col].nunique()}")
                print(f"  Most common:")

                value_counts = df[col].value_counts().head(5)
                for val, count in value_counts.items():
                    pct = (count / len(df)) * 100
                    print(f"    {str(val)[:40]}: {count:,} ({pct:.1f}%)")

            if len(categorical_cols) > 5:
                print(f"\n  ... and {len(categorical_cols) - 5} more categorical columns")

        # Correlation analysis for numeric columns
        if len(numeric_cols) > 1:
            print(f"\n{'='*60}")
            print("CORRELATION ANALYSIS")
            print(f"{'='*60}")

            corr_matrix = df[numeric_cols].corr()

            # Find strongest correlations (excluding diagonal)
            correlations = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    col1 = corr_matrix.columns[i]
                    col2 = corr_matrix.columns[j]
                    corr_val = corr_matrix.iloc[i, j]
                    if not pd.isna(corr_val):
                        correlations.append((col1, col2, corr_val))

            if correlations:
                correlations.sort(key=lambda x: abs(x[2]), reverse=True)

                print("\nStrongest correlations:")
                print(f"{'Column 1':<25} {'Column 2':<25} {'Correlation'}")
                print("-" * 60)

                for col1, col2, corr in correlations[:10]:  # Top 10
                    print(f"{col1[:24]:<25} {col2[:24]:<25} {corr:>11.3f}")

        # Group by analysis
        if group_by and group_by in df.columns:
            print(f"\n{'='*60}")
            print(f"GROUPED ANALYSIS BY '{group_by}'")
            print(f"{'='*60}")

            # Check if group_by column has reasonable number of groups
            n_groups = df[group_by].nunique()

            if n_groups > 50:
                print(f"\nWarning: {group_by} has {n_groups} unique values (showing top 20)")
                top_categories = df[group_by].value_counts().head(20).index
                df_grouped = df[df[group_by].isin(top_categories)]
            else:
                df_grouped = df

            if len(numeric_cols) > 0:
                print("\nNumeric aggregations:")

                # Select numeric columns for aggregation
                agg_dict = {}
                for col in numeric_cols:
                    agg_dict[col] = ['count', 'sum', 'mean', 'median', 'std', 'min', 'max']

                grouped = df_grouped.groupby(group_by).agg(agg_dict)

                # Format and print (showing subset to avoid clutter)
                print(f"\n{grouped.to_string()}")

            # Count by category
            print(f"\nCount by {group_by}:")
            counts = df[group_by].value_counts()

            for val, count in counts.head(20).items():
                pct = (count / len(df)) * 100
                print(f"  {str(val)[:40]}: {count:,} ({pct:.1f}%)")

            if len(counts) > 20:
                print(f"  ... and {len(counts) - 20} more categories")

        # Sample data
        print(f"\n{'='*60}")
        print("SAMPLE DATA (First 10 rows)")
        print(f"{'='*60}")
        print(f"\n{df.head(10).to_string()}")

        if len(df) > 10:
            print(f"\n{'='*60}")
            print("SAMPLE DATA (Last 5 rows)")
            print(f"{'='*60}")
            print(f"\n{df.tail(5).to_string()}")

        # Data quality score
        print(f"\n{'='*60}")
        print("DATA QUALITY SCORE")
        print(f"{'='*60}")

        completeness_score = ((1 - (missing.sum() / (len(df) * len(df.columns)))) * 100)
        uniqueness_score = ((1 - (dup_count / len(df))) * 100) if len(df) > 0 else 100
        overall_score = (completeness_score + uniqueness_score) / 2

        print(f"\nCompleteness: {completeness_score:.1f}% (no missing values)")
        print(f"Uniqueness: {uniqueness_score:.1f}% (no duplicates)")
        print(f"Overall Quality Score: {overall_score:.1f}%")

        if overall_score >= 90:
            print("\nData quality: Excellent ✓")
        elif overall_score >= 75:
            print("\nData quality: Good")
        elif overall_score >= 60:
            print("\nData quality: Fair (consider cleaning)")
        else:
            print("\nData quality: Poor (cleaning recommended)")

        print(f"\n{'='*60}")
        print("Analysis complete!")
        print(f"{'='*60}\n")

    except FileNotFoundError:
        print(f"Error: CSV file not found: {csv_path}")
        sys.exit(1)
    except pd.errors.EmptyDataError:
        print("Error: CSV file is empty")
        sys.exit(1)
    except pd.errors.ParserError as e:
        print(f"Error parsing CSV: {e}")
        print(f"\nTry specifying separator: {{'separator': ';'}} or {{'separator': '\\t'}}")
        sys.exit(1)
    except UnicodeDecodeError as e:
        print(f"Error decoding file: {e}")
        print(f"\nTry different encoding: {{'encoding': 'latin-1'}} or {{'encoding': 'cp1252'}}")
        sys.exit(1)
    except Exception as e:
        print(f"Error analyzing CSV: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

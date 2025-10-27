---
name: "data_analysis"
description: "Analyze datasets with pandas, numpy, and matplotlib - statistics, visualization, data cleaning"
version: "1.0.0"
author: "Agent Zero Team"
tags: ["data", "statistics", "analysis", "pandas", "visualization", "csv", "excel", "numpy"]
---

# Data Analysis Skill

This skill provides comprehensive data analysis capabilities for working with structured datasets. It includes procedures for loading, cleaning, analyzing, and visualizing data using industry-standard Python libraries.

## Overview

The data analysis skill enables you to:

- **Load Data**: Import CSV, Excel, JSON, and other common data formats
- **Clean Data**: Handle missing values, duplicates, and outliers
- **Descriptive Statistics**: Calculate mean, median, standard deviation, correlations
- **Data Transformation**: Filter, group, aggregate, and reshape data
- **Visualization Preparation**: Generate summaries suitable for plotting
- **Time Series Analysis**: Work with date/time data and temporal patterns

## Prerequisites

Install required Python packages:

```bash
pip install pandas numpy matplotlib seaborn scipy openpyxl xlrd
```

These are the core data science libraries:
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computing
- **matplotlib**: Plotting and visualization
- **seaborn**: Statistical data visualization
- **scipy**: Scientific computing and statistical tests
- **openpyxl/xlrd**: Excel file support

## Use Cases

### 1. Sales Data Analysis
Analyze sales transactions, customer behavior, revenue trends, and seasonal patterns.

### 2. Scientific Research
Process experimental data, calculate statistics, test hypotheses, visualize results.

### 3. Business Intelligence
Transform raw business data into actionable insights with aggregations and KPIs.

### 4. Quality Control
Monitor process metrics, detect anomalies, track performance over time.

### 5. Financial Analysis
Analyze financial statements, calculate ratios, track portfolio performance.

## Common Workflows

### Workflow 1: Quick Dataset Summary

Use the analyze_csv.py script for instant insights:

```json
{
    "tool_name": "skills_tool",
    "tool_args": {
        "method": "execute_script",
        "skill_name": "data_analysis",
        "script_path": "scripts/analyze_csv.py",
        "script_args": {
            "csv_path": "/path/to/data.csv",
            "group_by": "category"
        }
    }
}
```

### Workflow 2: Custom Analysis

For complex analysis, use code_execution_tool with pandas:

```python
import pandas as pd
import numpy as np

# Load data
df = pd.read_csv('sales.csv')

# Basic exploration
print(df.info())
print(df.describe())

# Calculate metrics
revenue_by_region = df.groupby('region')['revenue'].agg(['sum', 'mean', 'count'])
print(revenue_by_region)

# Correlation analysis
correlation_matrix = df[['revenue', 'units_sold', 'price']].corr()
print(correlation_matrix)
```

### Workflow 3: Data Visualization Preparation

Prepare data summaries for visualization:

```json
{
    "tool_name": "skills_tool",
    "tool_args": {
        "method": "execute_script",
        "skill_name": "data_analysis",
        "script_path": "scripts/visualize_data.py",
        "script_args": {
            "csv_path": "/path/to/data.csv",
            "plot_type": "histogram",
            "column": "revenue",
            "output_path": "/tmp/revenue_hist.png"
        }
    }
}
```

## Step-by-Step Instructions

### Loading Data

**CSV Files:**
```python
import pandas as pd

# Basic load
df = pd.read_csv('data.csv')

# With options
df = pd.read_csv('data.csv',
                 sep=',',           # Delimiter
                 encoding='utf-8',  # Character encoding
                 parse_dates=['date'],  # Parse date columns
                 na_values=['', 'NULL', 'N/A'])  # Missing value indicators
```

**Excel Files:**
```python
# Single sheet
df = pd.read_excel('data.xlsx', sheet_name='Sheet1')

# Multiple sheets
sheets = pd.read_excel('data.xlsx', sheet_name=None)
df1 = sheets['Sheet1']
df2 = sheets['Sheet2']
```

**JSON Files:**
```python
# JSON records
df = pd.read_json('data.json')

# Nested JSON
df = pd.read_json('data.json', orient='records')
```

### Exploring Data

**Basic Information:**
```python
# Dataset shape
print(f"Rows: {len(df)}, Columns: {len(df.columns)}")

# Column names and types
print(df.info())

# First and last rows
print(df.head(10))
print(df.tail(10))

# Column names
print(df.columns.tolist())
```

**Descriptive Statistics:**
```python
# Summary statistics for numeric columns
print(df.describe())

# Include all columns (including non-numeric)
print(df.describe(include='all'))

# Statistics for specific column
print(df['revenue'].describe())

# Custom statistics
print({
    'mean': df['revenue'].mean(),
    'median': df['revenue'].median(),
    'std': df['revenue'].std(),
    'min': df['revenue'].min(),
    'max': df['revenue'].max(),
    'sum': df['revenue'].sum()
})
```

**Value Distributions:**
```python
# Unique values
print(df['category'].unique())
print(f"Unique count: {df['category'].nunique()}")

# Value counts
print(df['category'].value_counts())

# Percentage distribution
print(df['category'].value_counts(normalize=True) * 100)
```

### Handling Missing Data

**Identifying Missing Values:**
```python
# Count missing values per column
missing = df.isnull().sum()
print(missing[missing > 0])

# Percentage missing
missing_pct = (df.isnull().sum() / len(df)) * 100
print(missing_pct[missing_pct > 0])

# Visualize missing data pattern
print(df.isnull().sum().sort_values(ascending=False))
```

**Handling Missing Values:**
```python
# Drop rows with any missing values
df_clean = df.dropna()

# Drop rows where specific column is missing
df_clean = df.dropna(subset=['important_column'])

# Fill missing with specific value
df_filled = df.fillna(0)

# Fill with column mean
df['revenue'] = df['revenue'].fillna(df['revenue'].mean())

# Fill with column median
df['age'] = df['age'].fillna(df['age'].median())

# Forward fill (use previous value)
df_filled = df.fillna(method='ffill')

# Backward fill (use next value)
df_filled = df.fillna(method='bfill')

# Fill with mode for categorical
df['category'] = df['category'].fillna(df['category'].mode()[0])
```

### Data Cleaning

**Remove Duplicates:**
```python
# Find duplicates
duplicates = df.duplicated()
print(f"Duplicate rows: {duplicates.sum()}")

# Remove duplicates
df_unique = df.drop_duplicates()

# Remove duplicates based on specific columns
df_unique = df.drop_duplicates(subset=['id', 'date'])
```

**Handle Outliers:**
```python
# Identify outliers using IQR method
Q1 = df['revenue'].quantile(0.25)
Q3 = df['revenue'].quantile(0.75)
IQR = Q3 - Q1

lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

outliers = df[(df['revenue'] < lower_bound) | (df['revenue'] > upper_bound)]
print(f"Outliers found: {len(outliers)}")

# Remove outliers
df_clean = df[(df['revenue'] >= lower_bound) & (df['revenue'] <= upper_bound)]

# Cap outliers (winsorize)
df['revenue'] = df['revenue'].clip(lower=lower_bound, upper=upper_bound)
```

**Data Type Conversion:**
```python
# Convert to numeric
df['price'] = pd.to_numeric(df['price'], errors='coerce')

# Convert to datetime
df['date'] = pd.to_datetime(df['date'])

# Convert to categorical
df['category'] = df['category'].astype('category')

# String operations
df['name'] = df['name'].str.strip()  # Remove whitespace
df['name'] = df['name'].str.lower()  # Lowercase
df['name'] = df['name'].str.title()  # Title case
```

### Filtering and Selection

**Filter Rows:**
```python
# Single condition
high_revenue = df[df['revenue'] > 1000]

# Multiple conditions (AND)
filtered = df[(df['revenue'] > 1000) & (df['region'] == 'West')]

# Multiple conditions (OR)
filtered = df[(df['revenue'] > 1000) | (df['units'] > 100)]

# String contains
filtered = df[df['product'].str.contains('Premium')]

# Date range
filtered = df[(df['date'] >= '2024-01-01') & (df['date'] <= '2024-12-31')]

# List of values
regions = ['West', 'East']
filtered = df[df['region'].isin(regions)]
```

**Select Columns:**
```python
# Single column
revenue = df['revenue']

# Multiple columns
subset = df[['date', 'product', 'revenue']]

# Columns by type
numeric_df = df.select_dtypes(include=['number'])
categorical_df = df.select_dtypes(include=['object', 'category'])
```

### Grouping and Aggregation

**Basic Grouping:**
```python
# Single aggregation
revenue_by_region = df.groupby('region')['revenue'].sum()

# Multiple aggregations
stats = df.groupby('region')['revenue'].agg(['sum', 'mean', 'count', 'std'])

# Multiple columns, multiple aggregations
agg_dict = {
    'revenue': ['sum', 'mean'],
    'units': ['sum', 'count'],
    'price': 'mean'
}
grouped = df.groupby('region').agg(agg_dict)

# Group by multiple columns
multi_group = df.groupby(['region', 'category'])['revenue'].sum()
```

**Pivot Tables:**
```python
# Basic pivot
pivot = df.pivot_table(
    values='revenue',
    index='region',
    columns='category',
    aggfunc='sum'
)

# Multiple values
pivot = df.pivot_table(
    values=['revenue', 'units'],
    index='region',
    columns='category',
    aggfunc='sum',
    fill_value=0
)

# With margins (totals)
pivot = df.pivot_table(
    values='revenue',
    index='region',
    columns='category',
    aggfunc='sum',
    margins=True
)
```

### Statistical Analysis

See [statistical_methods.md](docs/statistical_methods.md) for detailed statistical analysis procedures.

**Correlations:**
```python
# Correlation matrix
corr_matrix = df[['revenue', 'units', 'price']].corr()
print(corr_matrix)

# Correlation with single variable
correlations = df.corr()['revenue'].sort_values(ascending=False)
print(correlations)

# Scatter matrix for visualization preparation
from pandas.plotting import scatter_matrix
scatter_matrix(df[['revenue', 'units', 'price']])
```

**Distribution Analysis:**
```python
# Quantiles
quantiles = df['revenue'].quantile([0.25, 0.5, 0.75, 0.9, 0.95, 0.99])
print(quantiles)

# Value ranges
print(f"Range: {df['revenue'].max() - df['revenue'].min()}")
print(f"IQR: {df['revenue'].quantile(0.75) - df['revenue'].quantile(0.25)}")

# Skewness and kurtosis
print(f"Skewness: {df['revenue'].skew()}")
print(f"Kurtosis: {df['revenue'].kurtosis()}")
```

### Time Series Analysis

**Time-Based Operations:**
```python
# Set date as index
df['date'] = pd.to_datetime(df['date'])
df.set_index('date', inplace=True)

# Resample to different frequencies
daily = df.resample('D').sum()
weekly = df.resample('W').sum()
monthly = df.resample('M').sum()
quarterly = df.resample('Q').sum()

# Rolling statistics
df['revenue_7d_avg'] = df['revenue'].rolling(window=7).mean()
df['revenue_30d_avg'] = df['revenue'].rolling(window=30).mean()

# Percentage change
df['revenue_pct_change'] = df['revenue'].pct_change()

# Cumulative sum
df['revenue_cumsum'] = df['revenue'].cumsum()
```

**Date Extraction:**
```python
# Extract date components
df['year'] = df['date'].dt.year
df['month'] = df['date'].dt.month
df['day'] = df['date'].dt.day
df['day_of_week'] = df['date'].dt.dayofweek
df['day_name'] = df['date'].dt.day_name()
df['quarter'] = df['date'].dt.quarter
df['week'] = df['date'].dt.isocalendar().week
```

### Data Visualization Preparation

See [visualization_guide.md](docs/visualization_guide.md) for comprehensive visualization best practices.

**Generate Plot-Ready Summaries:**
```python
# For bar charts
bar_data = df.groupby('category')['revenue'].sum().sort_values(ascending=False)

# For line charts (time series)
line_data = df.groupby('date')['revenue'].sum().reset_index()

# For histograms
hist_data = df['revenue'].values

# For box plots
box_data = df.groupby('category')['revenue'].apply(list).to_dict()

# For scatter plots
scatter_data = df[['x_variable', 'y_variable']].dropna()
```

## Scripts Reference

### analyze_csv.py

Comprehensive CSV analysis script that provides:
- Dataset dimensions and column information
- Summary statistics for all numeric columns
- Missing value analysis
- Grouped aggregations (if group_by specified)
- Sample data preview

**Usage:**
```json
{
    "method": "execute_script",
    "skill_name": "data_analysis",
    "script_path": "scripts/analyze_csv.py",
    "script_args": {
        "csv_path": "/path/to/data.csv",
        "group_by": "category_column"
    }
}
```

### visualize_data.py

Generate visualizations from datasets:
- Histograms for distribution analysis
- Bar charts for categorical comparisons
- Line charts for time series
- Scatter plots for relationships
- Box plots for distribution comparisons

**Usage:**
```json
{
    "method": "execute_script",
    "skill_name": "data_analysis",
    "script_path": "scripts/visualize_data.py",
    "script_args": {
        "csv_path": "/path/to/data.csv",
        "plot_type": "histogram",
        "column": "revenue",
        "output_path": "/tmp/plot.png"
    }
}
```

## Common Patterns and Tips

### Pattern 1: Initial Data Exploration
```python
# Quick overview
print(df.shape)
print(df.info())
print(df.describe())
print(df.head())
print(df.isnull().sum())
```

### Pattern 2: Data Quality Check
```python
# Check for issues
print(f"Duplicates: {df.duplicated().sum()}")
print(f"Missing: {df.isnull().sum().sum()}")
print(f"Unique IDs: {df['id'].nunique()}")
print(f"Date range: {df['date'].min()} to {df['date'].max()}")
```

### Pattern 3: Quick Stats by Group
```python
# Summary by category
summary = df.groupby('category').agg({
    'revenue': ['sum', 'mean', 'count'],
    'units': 'sum',
    'price': 'mean'
})
print(summary)
```

### Pattern 4: Time-Based Trends
```python
# Monthly trends
df['month'] = pd.to_datetime(df['date']).dt.to_period('M')
monthly = df.groupby('month')['revenue'].sum()
print(monthly)
```

## Error Handling

**Common Issues:**

1. **File Not Found**
   ```python
   try:
       df = pd.read_csv('data.csv')
   except FileNotFoundError:
       print("Error: File not found")
   ```

2. **Encoding Errors**
   ```python
   # Try different encodings
   df = pd.read_csv('data.csv', encoding='utf-8')
   # or
   df = pd.read_csv('data.csv', encoding='latin-1')
   # or
   df = pd.read_csv('data.csv', encoding='cp1252')
   ```

3. **Memory Errors (Large Files)**
   ```python
   # Read in chunks
   chunk_size = 10000
   chunks = []
   for chunk in pd.read_csv('large_file.csv', chunksize=chunk_size):
       # Process chunk
       processed = chunk[chunk['value'] > 100]
       chunks.append(processed)
   df = pd.concat(chunks)
   ```

4. **Date Parsing Errors**
   ```python
   # Specify date format
   df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d', errors='coerce')
   ```

## Additional Resources

- [docs/statistical_methods.md](docs/statistical_methods.md) - Statistical analysis procedures
- [docs/visualization_guide.md](docs/visualization_guide.md) - Data visualization best practices
- [requirements.txt](requirements.txt) - Required Python packages

## Best Practices

1. **Always Validate Data**: Check for missing values, duplicates, and outliers
2. **Document Assumptions**: Note any data transformations or filtering logic
3. **Save Intermediate Results**: Export cleaned data before complex analysis
4. **Use Appropriate Statistics**: Match statistical methods to data types
5. **Consider Sample Size**: Ensure sufficient data for meaningful analysis
6. **Check Data Types**: Verify columns are correct types before operations
7. **Handle Edge Cases**: Test with small datasets first
8. **Version Your Data**: Track data sources and transformations

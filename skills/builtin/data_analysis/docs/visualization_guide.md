# Data Visualization Guide

Comprehensive guide to data visualization best practices and implementation strategies.

## Table of Contents

1. [Visualization Principles](#visualization-principles)
2. [Chart Selection Guide](#chart-selection-guide)
3. [matplotlib Fundamentals](#matplotlib-fundamentals)
4. [seaborn for Statistical Plots](#seaborn-for-statistical-plots)
5. [Common Plot Types](#common-plot-types)
6. [Customization and Styling](#customization-and-styling)
7. [Best Practices](#best-practices)

## Visualization Principles

### Core Principles

**1. Clarity Over Complexity**
- One main message per visualization
- Remove unnecessary elements (chartjunk)
- Use clear labels and titles
- Ensure readability at target display size

**2. Accurate Representation**
- Start y-axis at zero for bar charts (unless good reason)
- Use appropriate scales (linear vs logarithmic)
- Don't distort aspect ratios
- Show uncertainty when relevant

**3. Effective Use of Color**
- Use color purposefully, not decoratively
- Ensure colorblind-friendly palettes
- Maintain sufficient contrast
- Be consistent across related visualizations

**4. Context and Annotation**
- Provide clear titles and labels
- Include units of measurement
- Add reference lines or ranges
- Annotate key points

### Design Workflow

1. **Understand the Data**: Explore distributions, ranges, relationships
2. **Define the Message**: What insight to communicate?
3. **Choose Chart Type**: Match chart to data and message
4. **Create Draft**: Quick version to validate approach
5. **Refine**: Add labels, colors, annotations
6. **Review**: Check clarity, accuracy, accessibility
7. **Finalize**: Export at appropriate resolution and format

## Chart Selection Guide

### By Data Type

**Single Variable (Univariate)**

| Data Type | Distribution | Comparison | Trend |
|-----------|-------------|------------|-------|
| Continuous | Histogram, Density | Box Plot, Violin | Line Chart |
| Categorical | Bar Chart | Bar Chart | - |
| Count/Frequency | Bar Chart | - | - |

**Two Variables (Bivariate)**

| X Type | Y Type | Chart |
|--------|--------|-------|
| Continuous | Continuous | Scatter, Line |
| Continuous | Categorical | Box Plot, Violin |
| Categorical | Continuous | Bar Chart, Box Plot |
| Categorical | Categorical | Heatmap, Stacked Bar |

**Multiple Variables (Multivariate)**

- **Correlation Matrix**: Heatmap
- **Multiple Time Series**: Line chart with multiple lines
- **3D Relationships**: Bubble chart (size = 3rd variable)
- **Many Variables**: Parallel coordinates, radar chart

### By Purpose

**Show Distribution:**
- Histogram
- Box plot
- Violin plot
- Density plot

**Compare Categories:**
- Bar chart
- Grouped bar chart
- Box plot by group

**Show Relationships:**
- Scatter plot
- Line chart
- Bubble chart
- Heatmap

**Show Composition:**
- Stacked bar chart
- Pie chart (use sparingly)
- Area chart
- Tree map

**Show Trends Over Time:**
- Line chart
- Area chart
- Moving averages

## matplotlib Fundamentals

### Basic Structure

```python
import matplotlib.pyplot as plt
import numpy as np

# Create figure and axis
fig, ax = plt.subplots(figsize=(10, 6))

# Plot data
ax.plot(x, y)

# Customize
ax.set_xlabel('X Label')
ax.set_ylabel('Y Label')
ax.set_title('Plot Title')
ax.grid(True, alpha=0.3)

# Save or show
plt.savefig('plot.png', dpi=300, bbox_inches='tight')
plt.show()
```

### Multiple Subplots

**Grid Layout:**
```python
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# Access individual axes
axes[0, 0].plot(x, y1)
axes[0, 1].scatter(x, y2)
axes[1, 0].bar(categories, values)
axes[1, 1].hist(data, bins=20)

# Set overall title
fig.suptitle('Multiple Subplots', fontsize=16)

plt.tight_layout()
```

**Custom Layout:**
```python
import matplotlib.gridspec as gridspec

fig = plt.figure(figsize=(12, 8))
gs = gridspec.GridSpec(3, 3)

# Different sized subplots
ax1 = fig.add_subplot(gs[0, :])  # Top row, all columns
ax2 = fig.add_subplot(gs[1:, 0])  # Left column, bottom 2 rows
ax3 = fig.add_subplot(gs[1:, 1:])  # Right columns, bottom 2 rows
```

### Color Management

**Color Specification:**
```python
# Named colors
ax.plot(x, y, color='blue')
ax.plot(x, y, color='steelblue')

# Hex codes
ax.plot(x, y, color='#1f77b4')

# RGB tuples
ax.plot(x, y, color=(0.2, 0.4, 0.6))

# RGBA (with transparency)
ax.plot(x, y, color=(0.2, 0.4, 0.6, 0.5))
```

**Colormaps:**
```python
# Sequential: For continuous data
# 'viridis', 'plasma', 'inferno', 'Blues', 'Greens'

# Diverging: For data with meaningful center
# 'RdBu', 'coolwarm', 'seismic'

# Qualitative: For categorical data
# 'Set1', 'Set2', 'Set3', 'tab10', 'Paired'

# Use colormap
colors = plt.cm.viridis(np.linspace(0, 1, len(data)))
for i, (x, y) in enumerate(data):
    ax.scatter(x, y, color=colors[i])

# With colorbar
scatter = ax.scatter(x, y, c=values, cmap='viridis')
plt.colorbar(scatter, ax=ax, label='Value')
```

### Styling

**Set Style:**
```python
# Built-in styles
plt.style.use('seaborn-v0_8-darkgrid')
# Options: 'default', 'classic', 'seaborn-v0_8-*', 'ggplot', 'bmh', 'fivethirtyeight'

# Temporarily use style
with plt.style.context('ggplot'):
    plt.plot(x, y)
```

**Custom RC Parameters:**
```python
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 12
plt.rcParams['axes.labelsize'] = 14
plt.rcParams['axes.titlesize'] = 16
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['figure.titlesize'] = 18
```

## seaborn for Statistical Plots

seaborn is built on matplotlib and provides higher-level interface for statistical visualizations.

### Setup

```python
import seaborn as sns
import matplotlib.pyplot as plt

# Set theme
sns.set_theme(style='whitegrid')
# Styles: 'darkgrid', 'whitegrid', 'dark', 'white', 'ticks'

# Set context (scales elements)
sns.set_context('notebook')
# Contexts: 'paper', 'notebook', 'talk', 'poster'

# Set color palette
sns.set_palette('husl')
# Palettes: 'deep', 'muted', 'pastel', 'bright', 'dark', 'colorblind'
```

### Common seaborn Plots

**Distribution Plots:**
```python
# Histogram with KDE
sns.histplot(data=df, x='column', kde=True)

# KDE plot only
sns.kdeplot(data=df, x='column')

# Multiple distributions
sns.histplot(data=df, x='value', hue='category', multiple='dodge')
```

**Categorical Plots:**
```python
# Bar plot with confidence intervals
sns.barplot(data=df, x='category', y='value')

# Box plot
sns.boxplot(data=df, x='category', y='value')

# Violin plot
sns.violinplot(data=df, x='category', y='value')

# Strip plot (show all points)
sns.stripplot(data=df, x='category', y='value', jitter=True)

# Swarm plot (non-overlapping points)
sns.swarmplot(data=df, x='category', y='value')
```

**Relational Plots:**
```python
# Scatter plot
sns.scatterplot(data=df, x='x_var', y='y_var', hue='category', size='size_var')

# Line plot
sns.lineplot(data=df, x='time', y='value', hue='category')
```

**Regression Plots:**
```python
# Scatter with regression line
sns.regplot(data=df, x='x_var', y='y_var')

# Multiple regression lines by category
sns.lmplot(data=df, x='x_var', y='y_var', hue='category', height=6, aspect=1.5)
```

**Matrix Plots:**
```python
# Correlation heatmap
corr = df.corr()
sns.heatmap(corr, annot=True, cmap='coolwarm', center=0, square=True)

# Clustermap (with hierarchical clustering)
sns.clustermap(df.corr(), annot=True, cmap='coolwarm', center=0)
```

## Common Plot Types

### Histogram

**Purpose**: Show distribution of continuous variable

```python
fig, ax = plt.subplots(figsize=(10, 6))

# Create histogram
ax.hist(df['column'], bins=30, alpha=0.7, color='steelblue', edgecolor='black')

# Add mean and median lines
mean_val = df['column'].mean()
median_val = df['column'].median()
ax.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.2f}')
ax.axvline(median_val, color='green', linestyle='--', linewidth=2, label=f'Median: {median_val:.2f}')

ax.set_xlabel('Value')
ax.set_ylabel('Frequency')
ax.set_title('Distribution of Values')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
```

### Bar Chart

**Purpose**: Compare values across categories

```python
fig, ax = plt.subplots(figsize=(10, 6))

# Aggregate data
data = df.groupby('category')['value'].sum().sort_values(ascending=False)

# Create bar chart
bars = ax.bar(range(len(data)), data.values, color=plt.cm.viridis(np.linspace(0, 1, len(data))))
ax.set_xticks(range(len(data)))
ax.set_xticklabels(data.index, rotation=45, ha='right')

# Add value labels on bars
for i, (bar, value) in enumerate(zip(bars, data.values)):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{value:,.0f}', ha='center', va='bottom', fontsize=10)

ax.set_xlabel('Category')
ax.set_ylabel('Total Value')
ax.set_title('Values by Category')
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
```

### Line Chart

**Purpose**: Show trends over time or continuous variable

```python
fig, ax = plt.subplots(figsize=(12, 6))

# Plot line
ax.plot(df['date'], df['value'], linewidth=2, marker='o', markersize=4, color='steelblue')

# Add shaded area for uncertainty (if available)
if 'lower_bound' in df.columns:
    ax.fill_between(df['date'], df['lower_bound'], df['upper_bound'], alpha=0.3)

# Format x-axis for dates
import matplotlib.dates as mdates
ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
ax.xaxis.set_major_locator(mdates.MonthLocator())
plt.xticks(rotation=45, ha='right')

ax.set_xlabel('Date')
ax.set_ylabel('Value')
ax.set_title('Trend Over Time')
ax.grid(True, alpha=0.3)

plt.tight_layout()
```

### Scatter Plot

**Purpose**: Show relationship between two continuous variables

```python
fig, ax = plt.subplots(figsize=(10, 8))

# Create scatter plot
scatter = ax.scatter(df['x_var'], df['y_var'],
                    c=df['color_var'],  # Color by third variable
                    s=df['size_var'],   # Size by fourth variable
                    alpha=0.6,
                    cmap='viridis',
                    edgecolors='black',
                    linewidth=0.5)

# Add trend line
z = np.polyfit(df['x_var'], df['y_var'], 1)
p = np.poly1d(z)
ax.plot(df['x_var'], p(df['x_var']), "r--", linewidth=2, alpha=0.8, label='Trend')

# Add correlation
correlation = df['x_var'].corr(df['y_var'])
ax.text(0.05, 0.95, f'Correlation: {correlation:.3f}',
        transform=ax.transAxes, verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# Add colorbar
cbar = plt.colorbar(scatter, ax=ax)
cbar.set_label('Color Variable')

ax.set_xlabel('X Variable')
ax.set_ylabel('Y Variable')
ax.set_title('Relationship Between X and Y')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
```

### Box Plot

**Purpose**: Compare distributions across categories

```python
fig, ax = plt.subplots(figsize=(10, 6))

# Create box plot
bp = ax.boxplot([df[df['category'] == cat]['value'] for cat in df['category'].unique()],
                labels=df['category'].unique(),
                patch_artist=True,
                showmeans=True,
                meanprops=dict(marker='D', markerfacecolor='red', markersize=8))

# Color boxes
colors = plt.cm.Set3(np.linspace(0, 1, len(bp['boxes'])))
for patch, color in zip(bp['boxes'], colors):
    patch.set_facecolor(color)

ax.set_xlabel('Category')
ax.set_ylabel('Value')
ax.set_title('Distribution of Values by Category')
ax.grid(True, alpha=0.3, axis='y')

plt.xticks(rotation=45, ha='right')
plt.tight_layout()
```

### Heatmap

**Purpose**: Show patterns in matrix data or correlations

```python
fig, ax = plt.subplots(figsize=(10, 8))

# Create correlation matrix
corr = df[numeric_columns].corr()

# Create heatmap
im = ax.imshow(corr, cmap='coolwarm', vmin=-1, vmax=1, aspect='auto')

# Set ticks
ax.set_xticks(np.arange(len(corr.columns)))
ax.set_yticks(np.arange(len(corr.columns)))
ax.set_xticklabels(corr.columns, rotation=45, ha='right')
ax.set_yticklabels(corr.columns)

# Add correlation values
for i in range(len(corr.columns)):
    for j in range(len(corr.columns)):
        text = ax.text(j, i, f'{corr.iloc[i, j]:.2f}',
                      ha="center", va="center", color="black", fontsize=10)

# Add colorbar
cbar = plt.colorbar(im, ax=ax)
cbar.set_label('Correlation', rotation=270, labelpad=20)

ax.set_title('Correlation Heatmap')
plt.tight_layout()
```

## Customization and Styling

### Axes Customization

**Scale:**
```python
# Logarithmic scale
ax.set_yscale('log')
ax.set_xscale('log')

# Symmetric log (handles zero values)
ax.set_yscale('symlog')

# Custom scale limits
ax.set_xlim(0, 100)
ax.set_ylim(-10, 10)

# Invert axis
ax.invert_yaxis()
```

**Ticks:**
```python
# Custom tick locations
ax.set_xticks([0, 25, 50, 75, 100])
ax.set_xticklabels(['Zero', 'Quarter', 'Half', 'Three-Quarters', 'Full'])

# Tick parameters
ax.tick_params(axis='x', labelsize=12, rotation=45)
ax.tick_params(axis='y', labelsize=12, labelcolor='blue')

# Minor ticks
ax.minorticks_on()
ax.tick_params(which='minor', length=4, color='gray')
```

**Grid:**
```python
# Basic grid
ax.grid(True)

# Customized grid
ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)

# Grid on both axes
ax.grid(True, which='both', axis='both')

# Grid only on y-axis
ax.grid(True, axis='y')
```

### Annotations

**Text Annotations:**
```python
# Basic text
ax.text(x, y, 'Label', fontsize=12, ha='center', va='bottom')

# Text box
ax.text(x, y, 'Important Point',
        bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))

# Arrow annotation
ax.annotate('Key Point',
            xy=(x_point, y_point),  # Point to annotate
            xytext=(x_text, y_text),  # Text location
            arrowprops=dict(arrowstyle='->', color='red', lw=2),
            fontsize=12,
            ha='center')
```

**Reference Lines:**
```python
# Horizontal line
ax.axhline(y=threshold, color='r', linestyle='--', linewidth=2, label='Threshold')

# Vertical line
ax.axvline(x=cutoff, color='g', linestyle='--', linewidth=2, label='Cutoff')

# Shaded region
ax.axhspan(ymin, ymax, alpha=0.3, color='gray', label='Target Range')
ax.axvspan(xmin, xmax, alpha=0.3, color='blue', label='Period of Interest')
```

### Legends

**Basic Legend:**
```python
# Automatic legend from labels
ax.plot(x, y1, label='Series 1')
ax.plot(x, y2, label='Series 2')
ax.legend()

# Custom location
ax.legend(loc='upper right')  # 'upper left', 'lower right', 'center', etc.
ax.legend(loc='best')  # Automatic best location

# Outside plot area
ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')

# Custom frame
ax.legend(frameon=True, fancybox=True, shadow=True)

# Multiple columns
ax.legend(ncol=2)

# Custom title
ax.legend(title='Legend Title', title_fontsize=12)
```

### Fonts and Text

**Font Properties:**
```python
# Set font family
plt.rcParams['font.family'] = 'serif'
# Options: 'serif', 'sans-serif', 'monospace'

# Set specific font
plt.rcParams['font.serif'] = ['Times New Roman']

# Font sizes
plt.rcParams['axes.labelsize'] = 14
plt.rcParams['axes.titlesize'] = 16
plt.rcParams['legend.fontsize'] = 10

# Individual text
ax.set_title('Title', fontsize=16, fontweight='bold', fontfamily='serif')
```

## Best Practices

### Do's

1. **Choose the Right Chart Type**
   - Match visualization to data type and message
   - Use standard chart types when possible

2. **Maximize Data-Ink Ratio**
   - Remove non-essential elements
   - Let data be the focus

3. **Use Color Purposefully**
   - Colorblind-friendly palettes (viridis, colorblind-safe)
   - Consistent color schemes across related plots
   - Use color to highlight, not decorate

4. **Provide Context**
   - Clear, descriptive titles
   - Axis labels with units
   - Legend when needed
   - Data source and date

5. **Make it Accessible**
   - High contrast
   - Large enough fonts (minimum 10pt)
   - Alternative text descriptions
   - Patterns in addition to colors

6. **Export Properly**
   ```python
   # High resolution for print
   plt.savefig('plot.png', dpi=300, bbox_inches='tight')

   # Vector format for scaling
   plt.savefig('plot.pdf', format='pdf', bbox_inches='tight')
   plt.savefig('plot.svg', format='svg', bbox_inches='tight')
   ```

### Don'ts

1. **Don't Use 3D Charts** (unless truly necessary)
   - Distorts perception
   - Makes reading values difficult
   - Use alternative representations

2. **Don't Use Pie Charts** (for most cases)
   - Hard to compare similar values
   - Use bar charts instead
   - Exception: showing part-to-whole with 2-3 categories

3. **Don't Truncate Y-Axis** (for bar charts)
   - Exaggerates differences
   - Misleading comparisons
   - If necessary, clearly indicate

4. **Don't Overload**
   - Too many series on one plot
   - Too much text or annotation
   - Conflicting colors

5. **Don't Use Default Colors Blindly**
   - Check colorblind compatibility
   - Ensure sufficient contrast
   - Test on different displays

### Checklist Before Publishing

- [ ] Clear, descriptive title
- [ ] Axis labels with units
- [ ] Legend (if multiple series)
- [ ] Appropriate scale and limits
- [ ] Readable font sizes
- [ ] High enough resolution
- [ ] Colorblind-friendly palette
- [ ] No chartjunk
- [ ] Data source cited
- [ ] Key points annotated
- [ ] Tested on target display/print

### Common Patterns

**Publication-Ready Plot Template:**
```python
import matplotlib.pyplot as plt
import seaborn as sns

# Set style
sns.set_style("whitegrid")
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['legend.fontsize'] = 10

# Create figure
fig, ax = plt.subplots(figsize=(8, 6))

# Plot data
ax.plot(x, y, linewidth=2, color='steelblue', label='Data')

# Customize
ax.set_xlabel('X Variable (units)', fontsize=12)
ax.set_ylabel('Y Variable (units)', fontsize=12)
ax.set_title('Descriptive Title', fontsize=14, fontweight='bold')
ax.legend(loc='best', frameon=True)
ax.grid(True, alpha=0.3)

# Save
plt.tight_layout()
plt.savefig('publication_plot.pdf', format='pdf', dpi=300, bbox_inches='tight')
plt.savefig('publication_plot.png', format='png', dpi=300, bbox_inches='tight')
```

## Resources

- **matplotlib Documentation**: https://matplotlib.org/stable/contents.html
- **seaborn Gallery**: https://seaborn.pydata.org/examples/index.html
- **ColorBrewer**: https://colorbrewer2.org/ (colorblind-safe palettes)
- **Chart Chooser**: https://www.data-to-viz.com/ (select appropriate chart type)

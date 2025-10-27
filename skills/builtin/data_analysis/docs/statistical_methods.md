# Statistical Methods Guide

Comprehensive guide to statistical analysis procedures for data analysis tasks.

## Table of Contents

1. [Descriptive Statistics](#descriptive-statistics)
2. [Inferential Statistics](#inferential-statistics)
3. [Hypothesis Testing](#hypothesis-testing)
4. [Correlation and Regression](#correlation-and-regression)
5. [Distribution Analysis](#distribution-analysis)
6. [Time Series Statistics](#time-series-statistics)

## Descriptive Statistics

Descriptive statistics summarize and describe the main features of a dataset.

### Central Tendency

Measures that describe the center of a dataset.

**Mean (Average):**
```python
mean = df['column'].mean()
# Trimmed mean (remove outliers)
from scipy import stats
trimmed_mean = stats.trim_mean(df['column'], proportiontocut=0.1)  # Remove 10% from each end
```

**Median (Middle Value):**
```python
median = df['column'].median()
# Weighted median
from scipy.stats import weightedmedian
weighted_med = weightedmedian(df['values'], weights=df['weights'])
```

**Mode (Most Frequent):**
```python
mode = df['column'].mode()[0]
# All modes if multiple
modes = df['column'].mode().tolist()
```

**When to Use:**
- **Mean**: Normal distributions, no extreme outliers
- **Median**: Skewed distributions, presence of outliers
- **Mode**: Categorical data, bimodal distributions

### Dispersion

Measures that describe the spread of data.

**Variance:**
```python
variance = df['column'].var()
# Population variance (ddof=0)
pop_variance = df['column'].var(ddof=0)
```

**Standard Deviation:**
```python
std_dev = df['column'].std()
# Population std dev
pop_std = df['column'].std(ddof=0)
```

**Range:**
```python
data_range = df['column'].max() - df['column'].min()
```

**Interquartile Range (IQR):**
```python
Q1 = df['column'].quantile(0.25)
Q3 = df['column'].quantile(0.75)
IQR = Q3 - Q1
```

**Coefficient of Variation (CV):**
```python
cv = (df['column'].std() / df['column'].mean()) * 100
# Interpretation: CV < 15% = low variation, CV > 30% = high variation
```

### Shape

Measures that describe the distribution shape.

**Skewness:**
```python
skewness = df['column'].skew()
# Interpretation:
# skew < -1 or > 1: Highly skewed
# -1 < skew < -0.5 or 0.5 < skew < 1: Moderately skewed
# -0.5 < skew < 0.5: Approximately symmetric
```

**Kurtosis:**
```python
kurtosis = df['column'].kurtosis()
# Interpretation:
# kurtosis > 0: Heavy tails (leptokurtic)
# kurtosis = 0: Normal distribution (mesokurtic)
# kurtosis < 0: Light tails (platykurtic)
```

### Quantiles and Percentiles

**Quartiles:**
```python
Q1 = df['column'].quantile(0.25)  # 25th percentile
Q2 = df['column'].quantile(0.50)  # 50th percentile (median)
Q3 = df['column'].quantile(0.75)  # 75th percentile
```

**Custom Percentiles:**
```python
# Common percentiles
percentiles = df['column'].quantile([0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99])
print(percentiles)
```

**Deciles:**
```python
deciles = df['column'].quantile([i/10 for i in range(11)])
```

## Inferential Statistics

Draw conclusions about populations from sample data.

### Confidence Intervals

**Mean Confidence Interval:**
```python
from scipy import stats
import numpy as np

data = df['column'].dropna()
confidence = 0.95

mean = np.mean(data)
std_err = stats.sem(data)  # Standard error
ci = stats.t.interval(confidence, len(data)-1, loc=mean, scale=std_err)

print(f"95% CI: [{ci[0]:.2f}, {ci[1]:.2f}]")
```

**Proportion Confidence Interval:**
```python
from statsmodels.stats.proportion import proportion_confint

successes = (df['outcome'] == 'success').sum()
n_trials = len(df)

ci_low, ci_high = proportion_confint(successes, n_trials, alpha=0.05, method='wilson')
print(f"95% CI for proportion: [{ci_low:.3f}, {ci_high:.3f}]")
```

### Sample Size Calculation

**For Mean Estimation:**
```python
from scipy import stats

# Required parameters
confidence = 0.95
margin_of_error = 5
std_dev = 20  # From pilot study or estimate

# Calculate sample size
z_score = stats.norm.ppf((1 + confidence) / 2)
n = ((z_score * std_dev) / margin_of_error) ** 2
print(f"Required sample size: {int(np.ceil(n))}")
```

**For Proportion Estimation:**
```python
# Conservative estimate (p=0.5)
p = 0.5
z_score = 1.96  # 95% confidence
margin = 0.05   # 5% margin of error

n = (z_score**2 * p * (1-p)) / margin**2
print(f"Required sample size: {int(np.ceil(n))}")
```

## Hypothesis Testing

Test statistical hypotheses about data.

### T-Tests

**One-Sample T-Test:**
```python
from scipy import stats

# Test if mean differs from hypothesized value
data = df['column'].dropna()
hypothesized_mean = 100

t_stat, p_value = stats.ttest_1samp(data, hypothesized_mean)

print(f"T-statistic: {t_stat:.3f}")
print(f"P-value: {p_value:.4f}")

if p_value < 0.05:
    print("Reject null hypothesis: Mean differs significantly from", hypothesized_mean)
else:
    print("Fail to reject null hypothesis")
```

**Independent Two-Sample T-Test:**
```python
# Compare means of two independent groups
group1 = df[df['group'] == 'A']['value']
group2 = df[df['group'] == 'B']['value']

# Assuming equal variances
t_stat, p_value = stats.ttest_ind(group1, group2)

# Not assuming equal variances (Welch's t-test)
t_stat, p_value = stats.ttest_ind(group1, group2, equal_var=False)

print(f"T-statistic: {t_stat:.3f}")
print(f"P-value: {p_value:.4f}")
```

**Paired T-Test:**
```python
# Compare means of paired observations (before/after)
before = df['before']
after = df['after']

t_stat, p_value = stats.ttest_rel(before, after)

print(f"T-statistic: {t_stat:.3f}")
print(f"P-value: {p_value:.4f}")
```

### ANOVA (Analysis of Variance)

**One-Way ANOVA:**
```python
from scipy import stats

# Compare means across multiple groups
groups = [group['value'].values for name, group in df.groupby('category')]

f_stat, p_value = stats.f_oneway(*groups)

print(f"F-statistic: {f_stat:.3f}")
print(f"P-value: {p_value:.4f}")

if p_value < 0.05:
    print("At least one group mean differs significantly")
```

**Post-Hoc Tests (after ANOVA):**
```python
from scipy.stats import tukey_hsd

# Tukey's HSD test for pairwise comparisons
res = tukey_hsd(*groups)
print(res)
```

### Chi-Square Tests

**Chi-Square Test of Independence:**
```python
from scipy.stats import chi2_contingency

# Create contingency table
contingency_table = pd.crosstab(df['variable1'], df['variable2'])

chi2, p_value, dof, expected = chi2_contingency(contingency_table)

print(f"Chi-square statistic: {chi2:.3f}")
print(f"P-value: {p_value:.4f}")
print(f"Degrees of freedom: {dof}")

if p_value < 0.05:
    print("Variables are significantly associated")
```

**Chi-Square Goodness of Fit:**
```python
# Test if observed frequencies match expected distribution
observed = df['category'].value_counts().values
expected = [len(df) / len(observed)] * len(observed)  # Uniform distribution

chi2, p_value = stats.chisquare(observed, expected)

print(f"Chi-square statistic: {chi2:.3f}")
print(f"P-value: {p_value:.4f}")
```

### Non-Parametric Tests

**Mann-Whitney U Test (alternative to t-test):**
```python
# When data is not normally distributed
group1 = df[df['group'] == 'A']['value']
group2 = df[df['group'] == 'B']['value']

u_stat, p_value = stats.mannwhitneyu(group1, group2, alternative='two-sided')

print(f"U-statistic: {u_stat:.3f}")
print(f"P-value: {p_value:.4f}")
```

**Wilcoxon Signed-Rank Test (paired alternative):**
```python
# Paired non-parametric test
before = df['before']
after = df['after']

w_stat, p_value = stats.wilcoxon(before, after)

print(f"W-statistic: {w_stat:.3f}")
print(f"P-value: {p_value:.4f}")
```

**Kruskal-Wallis H Test (ANOVA alternative):**
```python
# Non-parametric alternative to one-way ANOVA
groups = [group['value'].values for name, group in df.groupby('category')]

h_stat, p_value = stats.kruskal(*groups)

print(f"H-statistic: {h_stat:.3f}")
print(f"P-value: {p_value:.4f}")
```

## Correlation and Regression

### Correlation Analysis

**Pearson Correlation (linear):**
```python
# Correlation coefficient
correlation = df['x'].corr(df['y'])
print(f"Pearson correlation: {correlation:.3f}")

# With significance test
from scipy.stats import pearsonr
corr, p_value = pearsonr(df['x'], df['y'])
print(f"Correlation: {corr:.3f}, P-value: {p_value:.4f}")

# Interpretation:
# |r| < 0.3: Weak correlation
# 0.3 ≤ |r| < 0.7: Moderate correlation
# |r| ≥ 0.7: Strong correlation
```

**Spearman Correlation (non-linear, monotonic):**
```python
from scipy.stats import spearmanr

corr, p_value = spearmanr(df['x'], df['y'])
print(f"Spearman correlation: {corr:.3f}, P-value: {p_value:.4f}")
```

**Kendall's Tau (ordinal data):**
```python
from scipy.stats import kendalltau

corr, p_value = kendalltau(df['x'], df['y'])
print(f"Kendall's tau: {corr:.3f}, P-value: {p_value:.4f}")
```

**Correlation Matrix:**
```python
# All pairwise correlations
corr_matrix = df[['var1', 'var2', 'var3', 'var4']].corr()
print(corr_matrix)

# Find strongest correlations
def get_strongest_correlations(corr_matrix, n=10):
    # Get upper triangle
    mask = np.triu(np.ones_like(corr_matrix), k=1).astype(bool)
    corr_values = corr_matrix.where(mask)

    # Flatten and sort
    corr_flat = corr_values.stack().sort_values(ascending=False)
    return corr_flat.head(n)

strongest = get_strongest_correlations(corr_matrix)
print(strongest)
```

### Simple Linear Regression

**Using scipy:**
```python
from scipy.stats import linregress

x = df['independent_var']
y = df['dependent_var']

slope, intercept, r_value, p_value, std_err = linregress(x, y)

print(f"Slope: {slope:.3f}")
print(f"Intercept: {intercept:.3f}")
print(f"R-squared: {r_value**2:.3f}")
print(f"P-value: {p_value:.4f}")

# Make predictions
predictions = slope * x + intercept
```

**Using statsmodels (more detailed):**
```python
import statsmodels.api as sm

x = df['independent_var']
y = df['dependent_var']

# Add constant for intercept
X = sm.add_constant(x)

# Fit model
model = sm.OLS(y, X).fit()

# Print summary
print(model.summary())

# Get coefficients
print(f"Intercept: {model.params[0]:.3f}")
print(f"Slope: {model.params[1]:.3f}")
print(f"R-squared: {model.rsquared:.3f}")
```

### Multiple Linear Regression

**Multiple Predictors:**
```python
import statsmodels.api as sm

# Select predictor variables
X = df[['predictor1', 'predictor2', 'predictor3']]
y = df['target']

# Add constant
X = sm.add_constant(X)

# Fit model
model = sm.OLS(y, X).fit()

# Summary with all statistics
print(model.summary())

# Predictions
predictions = model.predict(X)

# Residual analysis
residuals = y - predictions
```

### Regression Diagnostics

**Check Assumptions:**
```python
# 1. Linearity: Plot residuals vs predicted
residuals = model.resid
predicted = model.fittedvalues

# 2. Normality: Q-Q plot data preparation
from scipy import stats
stats.probplot(residuals, dist="norm")

# 3. Homoscedasticity: Residuals vs predicted values
# Should show random scatter

# 4. Independence: Durbin-Watson test
from statsmodels.stats.stattools import durbin_watson
dw = durbin_watson(residuals)
print(f"Durbin-Watson: {dw:.2f}")
# Values between 1.5-2.5 indicate independence

# 5. Multicollinearity: VIF
from statsmodels.stats.outliers_influence import variance_inflation_factor

vif_data = pd.DataFrame()
vif_data["Variable"] = X.columns
vif_data["VIF"] = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
print(vif_data)
# VIF > 10 indicates multicollinearity problem
```

## Distribution Analysis

### Test for Normality

**Shapiro-Wilk Test:**
```python
from scipy.stats import shapiro

stat, p_value = shapiro(df['column'])

print(f"Shapiro-Wilk statistic: {stat:.4f}")
print(f"P-value: {p_value:.4f}")

if p_value > 0.05:
    print("Data appears to be normally distributed")
else:
    print("Data does not appear to be normally distributed")
```

**Kolmogorov-Smirnov Test:**
```python
from scipy.stats import kstest

stat, p_value = kstest(df['column'], 'norm')

print(f"KS statistic: {stat:.4f}")
print(f"P-value: {p_value:.4f}")
```

**Anderson-Darling Test:**
```python
from scipy.stats import anderson

result = anderson(df['column'])

print(f"Anderson-Darling statistic: {result.statistic:.4f}")
print("Critical values:", result.critical_values)
print("Significance levels:", result.significance_level)
```

### Distribution Fitting

**Fit Distribution:**
```python
from scipy import stats

# Fit normal distribution
mu, sigma = stats.norm.fit(df['column'])
print(f"Normal distribution: μ={mu:.2f}, σ={sigma:.2f}")

# Fit other distributions
# Exponential
loc, scale = stats.expon.fit(df['column'])
print(f"Exponential distribution: loc={loc:.2f}, scale={scale:.2f}")

# Gamma
shape, loc, scale = stats.gamma.fit(df['column'])
print(f"Gamma distribution: shape={shape:.2f}, loc={loc:.2f}, scale={scale:.2f}")
```

## Time Series Statistics

### Stationarity Tests

**Augmented Dickey-Fuller Test:**
```python
from statsmodels.tsa.stattools import adfuller

result = adfuller(df['time_series'])

print(f"ADF Statistic: {result[0]:.4f}")
print(f"P-value: {result[1]:.4f}")
print("Critical Values:")
for key, value in result[4].items():
    print(f"  {key}: {value:.4f}")

if result[1] < 0.05:
    print("Series is stationary")
else:
    print("Series is non-stationary")
```

### Autocorrelation

**ACF and PACF:**
```python
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.stattools import acf, pacf

# Calculate ACF
acf_values = acf(df['time_series'], nlags=20)
print("Autocorrelation values:", acf_values)

# Calculate PACF
pacf_values = pacf(df['time_series'], nlags=20)
print("Partial autocorrelation values:", pacf_values)
```

### Trend Analysis

**Moving Average:**
```python
# Simple moving average
df['MA_7'] = df['value'].rolling(window=7).mean()
df['MA_30'] = df['value'].rolling(window=30).mean()

# Exponential moving average
df['EMA'] = df['value'].ewm(span=7, adjust=False).mean()
```

**Decomposition:**
```python
from statsmodels.tsa.seasonal import seasonal_decompose

# Decompose into trend, seasonal, residual
result = seasonal_decompose(df['time_series'], model='additive', period=12)

trend = result.trend
seasonal = result.seasonal
residual = result.resid
```

## Effect Size

### Cohen's d

**For t-tests:**
```python
def cohens_d(group1, group2):
    """Calculate Cohen's d for two groups"""
    n1, n2 = len(group1), len(group2)
    var1, var2 = group1.var(), group2.var()

    # Pooled standard deviation
    pooled_std = np.sqrt(((n1-1)*var1 + (n2-1)*var2) / (n1+n2-2))

    # Cohen's d
    d = (group1.mean() - group2.mean()) / pooled_std
    return d

group1 = df[df['group'] == 'A']['value']
group2 = df[df['group'] == 'B']['value']

d = cohens_d(group1, group2)
print(f"Cohen's d: {d:.3f}")

# Interpretation:
# |d| < 0.2: Small effect
# 0.2 ≤ |d| < 0.8: Medium effect
# |d| ≥ 0.8: Large effect
```

### R-squared

**Coefficient of Determination:**
```python
# For regression models
r_squared = model.rsquared
adjusted_r_squared = model.rsquared_adj

print(f"R-squared: {r_squared:.3f}")
print(f"Adjusted R-squared: {adjusted_r_squared:.3f}")

# Interpretation:
# R² = 0.7 means 70% of variance is explained by the model
```

## Best Practices

1. **Check Assumptions**: Always verify test assumptions before applying
2. **Multiple Testing**: Apply Bonferroni correction when doing multiple tests
3. **Effect Size**: Report effect sizes along with p-values
4. **Sample Size**: Ensure adequate sample size for statistical power
5. **Outliers**: Identify and handle outliers appropriately
6. **Missing Data**: Understand and address missing data patterns
7. **Visualize**: Always visualize data before and after statistical tests
8. **Document**: Record all statistical decisions and rationale

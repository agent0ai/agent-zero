---
source: https://www.stat.cmu.edu/~hseltman/309/Book/Book.pdf
retrieved: 2025-08-09T15:00:28Z
fetch_method: document_query
agent: agent0
original_filename: experimental_design_statistical_analysis_cmu.md
---

# Experimental Design and Analysis

*Source: Howard J. Seltman, Carnegie Mellon University, July 11, 2018*

## Preface

This book is intended as required reading material for Experimental Design for the Behavioral and Social Sciences, a second level statistics course for undergraduate students in the College of Humanities and Social Sciences at Carnegie Mellon University. This course is also cross-listed as a graduate level course for Masters and PhD students (in fields other than Statistics), and supplementary material is included for this level of study.

Over the years the course has grown to include students from dozens of majors beyond Psychology and the Social Sciences and from all of the Colleges of the University. This is appropriate because **Experimental Design is fundamentally the same for all fields**. This book tends towards examples from behavioral and social sciences, but includes a full range of examples.

In truth, a better title for the course is **Experimental Design and Analysis**, and that is the title of this book. **Experimental Design and Statistical Analysis go hand in hand, and neither can be understood without the other.** Only a small fraction of the myriad statistical analytic methods are covered in this book, but my rough guess is that these methods cover 60%-80% of what you will read in the literature and what is needed for analysis of your own experiments.

## Key Learning Principles

### The Importance of Hands-On Experience

One key idea in this course is that **you cannot really learn statistics without doing statistics**. Even if you will never analyze data again, the hands-on experience you will gain from analyzing data in labs, homework and exams will take your understanding of and ability to read about other peoples experiments and data analyses to a whole new level.

### Concept Maps for Learning

I recommend that you create your own "concept maps" as the course progresses. A concept map is usually drawn as a set of ovals with the names of various concepts written inside and with arrows showing relationships among the concepts. Often it helps to label the arrows. **Concept maps are a great learning tool that help almost every student who tries them.** They are particularly useful for a course like this for which the main goal is to learn the relationships among many concepts so that you can learn to carry out specific tasks (design and analysis in this case).

## Chapter 1: The Big Picture

### 1.1 The Importance of Careful Experimental Design

Experimental design is the foundation of all scientific inquiry. Poor design leads to:
- **Invalid conclusions** - Results that don't actually support the claimed findings
- **Wasted resources** - Time, money, and effort spent on studies that can't answer the research question
- **Ethical concerns** - Particularly in human and animal research where poor design wastes participants' contributions

### 1.2 Overview of Statistical Analysis

Statistical analysis serves several critical functions:
1. **Quantifying uncertainty** - Understanding how confident we can be in our results
2. **Separating signal from noise** - Distinguishing real effects from random variation
3. **Making inferences** - Drawing conclusions about populations from sample data
4. **Testing hypotheses** - Formally evaluating research questions

## Chapter 2: Variable Classification

### 2.1 What Makes a "Good" Variable?

A good variable should be:
- **Reliable** - Consistent measurements across time and conditions
- **Valid** - Actually measuring what it claims to measure
- **Sensitive** - Able to detect differences when they exist
- **Practical** - Feasible to measure given resource constraints

### 2.2 Classification by Role

**Explanatory Variables (Independent Variables)**
- Variables that are manipulated or controlled by the researcher
- Used to predict or explain changes in the outcome variable
- Examples: treatment condition, dosage level, training method

**Outcome Variables (Dependent Variables)**
- Variables that are measured to assess the effect of explanatory variables
- The "response" that researchers are trying to understand or predict
- Examples: test scores, reaction time, blood pressure

**Control Variables**
- Variables that are held constant or statistically controlled
- Help isolate the effect of the explanatory variable of interest
- Examples: age, gender, baseline measurements

### 2.3 Classification by Statistical Type

**Categorical Variables**
- **Nominal**: Categories with no natural order (e.g., color, gender, treatment type)
- **Ordinal**: Categories with natural order but unequal intervals (e.g., education level, satisfaction rating)

**Quantitative Variables**
- **Discrete**: Countable values (e.g., number of errors, family size)
- **Continuous**: Measurable on a continuous scale (e.g., height, reaction time, temperature)

## Chapter 3: Review of Probability

### 3.1 Definition(s) of Probability

Probability can be understood in several ways:
- **Classical**: Based on equally likely outcomes (e.g., coin flips)
- **Frequentist**: Long-run relative frequency of events
- **Subjective**: Personal degree of belief in an outcome

### 3.2 Probability Mass Functions and Density Functions

**Probability Mass Function (PMF)**
- Used for discrete random variables
- P(X = x) gives the probability of exactly x
- Sum of all probabilities equals 1

**Probability Density Function (PDF)**
- Used for continuous random variables
- f(x) gives the density at point x
- Area under the curve equals 1
- P(a < X < b) = integral from a to b of f(x)dx

### 3.3 Populations and Samples

**Population**
- The complete set of all individuals or observations of interest
- Usually impossible or impractical to study entirely
- Characterized by parameters (μ, σ, π)

**Sample**
- A subset of the population actually studied
- Used to make inferences about the population
- Characterized by statistics (x̄, s, p̂)

### 3.4 Parameters Describing Distributions

**Central Tendency**
- **Mean (μ)**: Average value, sensitive to outliers
- **Median**: Middle value when ordered, robust to outliers
- **Mode**: Most frequently occurring value

**Spread**
- **Variance (σ²)**: Average squared deviation from the mean
- **Standard Deviation (σ)**: Square root of variance, same units as data
- **Range**: Difference between maximum and minimum values

**Shape**
- **Skewness**: Measure of asymmetry
- **Kurtosis**: Measure of tail heaviness

### 3.5 Central Limit Theorem

One of the most important theorems in statistics:

**Statement**: For sufficiently large sample sizes, the sampling distribution of the sample mean approaches a normal distribution, regardless of the shape of the population distribution.

**Implications**:
- Enables inference about population means using normal distribution
- "Sufficiently large" is often n ≥ 30, but depends on population distribution
- More skewed populations require larger sample sizes

## Chapter 4: Exploratory Data Analysis (EDA)

### 4.1 The Purpose of EDA

Exploratory Data Analysis serves to:
- **Understand the data structure** - What variables exist and how they're distributed
- **Identify patterns** - Relationships, trends, and anomalies
- **Check assumptions** - Verify conditions needed for statistical tests
- **Guide analysis decisions** - Inform choice of appropriate statistical methods

### 4.2 Univariate Analysis

**For Categorical Data**:
- **Frequency tables** - Count and percentage in each category
- **Bar charts** - Visual representation of frequencies
- **Pie charts** - Show proportions of the whole

**For Quantitative Data**:
- **Descriptive statistics** - Mean, median, standard deviation, quartiles
- **Histograms** - Show distribution shape and identify outliers
- **Box plots** - Display median, quartiles, and outliers
- **Stem-and-leaf plots** - Preserve actual data values while showing distribution

### 4.3 Multivariate Analysis

**Relationships Between Variables**:
- **Scatterplots** - Visualize relationships between two quantitative variables
- **Correlation coefficients** - Quantify linear relationships
- **Cross-tabulation** - Examine relationships between categorical variables
- **Side-by-side box plots** - Compare distributions across groups

## Chapter 6: t-tests

### 6.1 The Logic of Statistical Inference

Statistical inference follows a systematic process:

1. **Define the model and parameters** - Specify what we're measuring
2. **State hypotheses** - Null and alternative hypotheses
3. **Choose a test statistic** - A function of the data that measures evidence
4. **Determine the null sampling distribution** - What we'd expect if H₀ is true
5. **Calculate the p-value** - Probability of observing our result or more extreme
6. **Make a decision** - Reject or fail to reject the null hypothesis
7. **Check assumptions** - Verify conditions for valid inference
8. **Draw conclusions** - Interpret results in context

### 6.2 One-Sample t-test

**Purpose**: Test whether a population mean equals a specific value

**Hypotheses**:
- H₀: μ = μ₀
- H₁: μ ≠ μ₀ (two-tailed) or μ > μ₀ or μ < μ₀ (one-tailed)

**Test Statistic**:
t = (x̄ - μ₀) / (s / √n)

**Assumptions**:
- Random sampling
- Normal population distribution (or large sample size)
- Independent observations

### 6.3 Two-Sample t-test

**Purpose**: Compare means between two independent groups

**Equal Variances t-test**:
t = (x̄₁ - x̄₂) / (sp√(1/n₁ + 1/n₂))

where sp is the pooled standard deviation

**Unequal Variances t-test (Welch's t-test)**:
t = (x̄₁ - x̄₂) / √(s₁²/n₁ + s₂²/n₂)

### 6.4 Paired t-test

**Purpose**: Compare means for paired observations (before/after, matched pairs)

**Approach**: Calculate differences for each pair, then perform one-sample t-test on differences

t = d̄ / (sd / √n)

where d̄ is the mean difference and sd is the standard deviation of differences

## Chapter 7: One-Way ANOVA

### 7.1 When to Use ANOVA

Analysis of Variance (ANOVA) is used when:
- Comparing means across **three or more groups**
- You have **one categorical explanatory variable** (factor)
- You have **one quantitative outcome variable**

### 7.2 The Logic of ANOVA

ANOVA works by partitioning total variation into components:

**Total Variation = Between-Group Variation + Within-Group Variation**

- **Between-group variation**: Differences among group means
- **Within-group variation**: Variation within each group (error)

If groups truly differ, between-group variation should be large relative to within-group variation.

### 7.3 The F-statistic

F = (Between-group variance) / (Within-group variance)
= MSB / MSW

where:
- MSB = Mean Square Between groups
- MSW = Mean Square Within groups

**Interpretation**:
- F ≈ 1: Groups don't differ much
- F >> 1: Groups differ substantially

### 7.4 ANOVA Assumptions

1. **Independence**: Observations are independent
2. **Normality**: Outcome variable is normally distributed within each group
3. **Equal variances**: Population variances are equal across groups (homoscedasticity)

### 7.5 Post-hoc Comparisons

When ANOVA is significant, it tells us that **at least one group differs**, but not which specific groups differ. Post-hoc tests address this:

**Common Methods**:
- **Tukey's HSD**: Controls family-wise error rate
- **Bonferroni correction**: Conservative but simple
- **Scheffé's method**: Most conservative, allows complex comparisons

## Chapter 8: Threats to Your Experiment

### 8.1 Internal Validity

**Definition**: The extent to which we can confidently conclude that the explanatory variable caused changes in the outcome variable.

**Common Threats**:
- **History**: External events occurring during the study
- **Maturation**: Natural changes in participants over time
- **Selection bias**: Systematic differences between groups
- **Attrition**: Differential dropout between groups
- **Testing effects**: Changes due to repeated measurement

### 8.2 External Validity

**Definition**: The extent to which results generalize to other populations, settings, and times.

**Considerations**:
- **Population validity**: Do results apply to other groups?
- **Ecological validity**: Do results apply in natural settings?
- **Temporal validity**: Do results persist over time?

### 8.3 Construct Validity

**Definition**: The extent to which variables actually measure what they're supposed to measure.

**Issues**:
- **Operational definitions**: How well do measures capture constructs?
- **Measurement error**: Random and systematic errors in measurement
- **Confounding constructs**: Measures capturing unintended variables

### 8.4 Statistical Conclusion Validity

**Definition**: The extent to which statistical conclusions are correct.

**Threats**:
- **Low power**: Failing to detect real effects
- **Violated assumptions**: Using inappropriate statistical tests
- **Multiple comparisons**: Inflated Type I error rates
- **Fishing expeditions**: Testing many hypotheses without correction

## Chapter 9: Simple Linear Regression

### 9.1 The Regression Model

**Population Model**:
Y = β₀ + β₁X + ε

where:
- Y = outcome variable
- X = explanatory variable
- β₀ = y-intercept (value of Y when X = 0)
- β₁ = slope (change in Y for one-unit increase in X)
- ε = random error term

**Sample Equation**:
ŷ = b₀ + b₁x

where b₀ and b₁ are estimates of β₀ and β₁

### 9.2 Least Squares Estimation

The "best" line minimizes the sum of squared residuals:

SSE = Σ(yi - ŷi)²

**Formulas**:
b₁ = Σ(xi - x̄)(yi - ȳ) / Σ(xi - x̄)²
b₀ = ȳ - b₁x̄

### 9.3 Assessing Model Fit

**R-squared (Coefficient of Determination)**:
R² = SSR / SST = 1 - SSE / SST

where:
- SSR = Sum of Squares Regression
- SSE = Sum of Squares Error
- SST = Sum of Squares Total

**Interpretation**: Proportion of variance in Y explained by X

### 9.4 Regression Assumptions

1. **Linearity**: Relationship between X and Y is linear
2. **Independence**: Observations are independent
3. **Normality**: Residuals are normally distributed
4. **Equal variance**: Residuals have constant variance (homoscedasticity)

### 9.5 Inference in Regression

**Testing the Slope**:
H₀: β₁ = 0 (no linear relationship)
H₁: β₁ ≠ 0 (linear relationship exists)

Test statistic: t = b₁ / SE(b₁)

**Confidence Interval for Slope**:
b₁ ± t(α/2, n-2) × SE(b₁)

## Key Principles for Research Design

### 1. Plan Before You Collect
- **Define research questions clearly**
- **Specify hypotheses in advance**
- **Determine appropriate sample size**
- **Choose valid and reliable measures**

### 2. Control What You Can
- **Random assignment** to reduce confounding
- **Standardize procedures** to reduce error
- **Control extraneous variables** through design
- **Use appropriate comparison groups**

### 3. Measure What Matters
- **Ensure construct validity** of measures
- **Consider multiple measures** of key constructs
- **Pilot test instruments** before main study
- **Document measurement procedures**

### 4. Analyze Appropriately
- **Check assumptions** before analysis
- **Use appropriate statistical tests** for your data
- **Report effect sizes** along with significance tests
- **Consider practical significance** not just statistical significance

### 5. Interpret Cautiously
- **Distinguish correlation from causation**
- **Consider alternative explanations**
- **Acknowledge limitations**
- **Replicate important findings**

## Statistical Power and Sample Size

### Understanding Power

**Statistical Power**: The probability of correctly rejecting a false null hypothesis (detecting a real effect when it exists).

Power = 1 - P(Type II Error) = 1 - β

**Factors Affecting Power**:
1. **Effect size**: Larger effects are easier to detect
2. **Sample size**: Larger samples provide more power
3. **Alpha level**: Higher α increases power but also Type I error risk
4. **Variability**: Less noise makes effects easier to detect

### Sample Size Planning

**Key Questions**:
- What effect size do you want to detect?
- What power level do you want (typically 0.80 or 0.90)?
- What alpha level will you use (typically 0.05)?
- How much variability do you expect?

**General Principles**:
- **Pilot studies** can help estimate effect sizes and variability
- **Power analysis software** (G*Power, R, etc.) can calculate needed sample sizes
- **Consider practical constraints** (time, money, participant availability)
- **Plan for attrition** by recruiting extra participants

## Common Statistical Errors and How to Avoid Them

### 1. Multiple Comparisons Problem

**Problem**: Testing many hypotheses increases the chance of false positives

**Solutions**:
- **Plan comparisons in advance**
- **Use appropriate correction methods** (Bonferroni, FDR)
- **Focus on primary hypotheses**
- **Replicate important findings**

### 2. Assumption Violations

**Problem**: Using statistical tests when their assumptions aren't met

**Solutions**:
- **Check assumptions graphically and statistically**
- **Transform data** when appropriate
- **Use robust or non-parametric alternatives**
- **Report assumption checks** in your results

### 3. Confusing Statistical and Practical Significance

**Problem**: Focusing only on p-values without considering effect sizes

**Solutions**:
- **Always report effect sizes** and confidence intervals
- **Consider practical importance** of findings
- **Use appropriate sample sizes** (not too large or too small)
- **Interpret results in context**

### 4. Data Dredging (p-hacking)

**Problem**: Analyzing data in many ways until finding significant results

**Solutions**:
- **Pre-register analysis plans**
- **Distinguish exploratory from confirmatory analyses**
- **Report all analyses conducted**
- **Use appropriate corrections for multiple testing**

## Conclusion: Integrating Design and Analysis

Effective research requires seamless integration of experimental design and statistical analysis. Key principles:

1. **Design drives analysis** - Choose statistical methods based on your research design
2. **Analysis informs design** - Understanding statistical requirements helps design better studies
3. **Both serve the research question** - Methods should be chosen to best answer your specific questions
4. **Transparency is essential** - Document and report all aspects of design and analysis
5. **Replication builds knowledge** - Single studies, no matter how well-designed, are just the beginning

By following these principles and understanding the fundamental concepts covered in this text, researchers can conduct studies that contribute meaningfully to scientific knowledge and inform evidence-based practice.

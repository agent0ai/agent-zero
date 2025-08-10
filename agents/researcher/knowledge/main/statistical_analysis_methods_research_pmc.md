---
source: https://pmc.ncbi.nlm.nih.gov/articles/PMC10324782/
retrieved: 2025-08-09T15:08:05Z
fetch_method: document_query
agent: agent0
original_filename: statistical_analysis_methods_research_pmc.md
---

# Introduction to Research Statistical Analysis: An Overview of the Basics

*Source: Christian Vandever, HCA Healthcare Journal of Medicine, 2020*

## Abstract

This article covers many statistical ideas essential to research statistical analysis. **Sample size is explained through the concepts of statistical significance level and power.** Variable types and definitions are included to clarify necessities for how the analysis will be interpreted. Categorical and quantitative variable types are defined, as well as response and predictor variables. Statistical tests described include t-tests, ANOVA and chi-square tests. Multiple regression is also explored for both logistic and linear regression. Finally, the most common statistics produced by these methods are explored.

**Keywords:** statistical analysis, sample size, power, t-test, anova, chi-square, regression

## Introduction: The Foundation of Quantitative Research

**Statistical analysis is necessary for any research project seeking to make quantitative conclusions.** The following is a primer for research-based statistical analysis. It is intended to be a high-level overview of appropriate statistical testing, while not diving too deep into any specific methodology.

### Scope and Application

- **Retrospective Projects**: Much of this information is applicable to retrospective projects, where analysis is performed on data that has already been collected
- **General Research**: Most concepts are suitable for any type of research
- **Collaborative Understanding**: This primer helps researchers understand results in coordination with a statistician, not to perform the actual analysis
- **Software Implementation**: Analysis is commonly performed using statistical programming software such as R, SAS or SPSS

### Key Principles

1. **Replication**: Statistical software allows for analysis to be replicated while minimizing the risk for error
2. **Population Relevance**: Results are only relevant to the population that the underlying data represents
3. **Practical Significance**: Statistical significance must be balanced with practical importance
4. **Bias Control**: Proper statistical methods help control for confounding variables and bias

## Fundamental Concepts: Population and Sample Size

### Defining Your Study Population

After developing a hypothesis for a study, including any variables to be used, one of the first steps is to think about the patient population to apply the question. **Results are only relevant to the population that the underlying data represents.**

#### Population Considerations

- **Representativeness**: Since it is impractical to include everyone with a certain condition, a subset of the population of interest should be taken
- **Adequate Size**: This subset should be large enough to have power
- **Statistical Power**: Power means there is enough data to deliver significant results and accurately reflect the study's population

### Statistical Significance and Power: Alpha and Beta

The first statistics of interest are related to significance level and power, alpha and beta.

#### Alpha (α) - Significance Level

**Alpha (α) is the significance level and probability of a type I error**, the rejection of the null hypothesis when it is true.

- **Null Hypothesis**: Generally that there is no difference between the groups compared
- **Type I Error**: Also known as a false positive
- **Example**: An analysis that finds one medication statistically better than another, when in reality there is no difference in efficacy between the two
- **Typical Value**: Alpha is typically set at 0.05, but is commonly reduced to limit the chance of false positives

#### Beta (β) - Type II Error Probability

**Beta (β) is the probability of a type II error**, the failure to reject the null hypothesis when it is actually false.

- **Type II Error**: Also known as a false negative
- **Example**: Analysis finds there is no difference in two medications when in reality one works better than the other
- **Power Relationship**: Power is defined as 1-β

#### Power Calculation and Sample Size

**Power should be calculated prior to running any sort of statistical testing.**

##### Optimal Relationships
- **Alpha**: Should be as small as possible
- **Power**: Should be as large as possible
- **Sample Size**: Power generally increases with larger sample size

##### Trade-offs and Considerations
- **Cost**: Larger sample sizes increase cost
- **Bias Effects**: Larger samples may amplify the effect of any bias in study design
- **Statistical vs. Practical Significance**: As sample size increases, chance for statistically significant results increases, even for small differences that may not matter practically

##### Power Calculators

**Power calculators include the magnitude of the effect to combat potential for exaggeration** and only give significant results that have actual impact.

**Calculator Inputs:**
- Mean values
- Effect size
- Desired power level

**Calculator Output:**
- Required minimum sample size for analysis

**Effect Size Determination:**
- **Available Data**: Effect size calculated using statistical information on variables of interest
- **No Available Data**: Most tests have commonly used values for small, medium, or large effect sizes

## Variable Types and Definitions

When the desired patient population is decided, the next step is to define the variables previously chosen to be included. **Variables come in different types that determine which statistical methods are appropriate and useful.**

### Categorical vs. Quantitative Variables

#### Categorical Variables

**Categorical variables place patients into groups**, such as gender, race and smoking status.

**Characteristics:**
- Categorize patients into discrete groups
- Patient categories are mutually exclusive
- **Examples**: race, smoking status, demographic group

#### Quantitative Variables

**Quantitative variables measure or count some quantity of interest.** Common quantitative variables in research include age and weight.

**Characteristics:**
- Continuous values that measure a variable
- For time-based studies, there would be a new variable for each measurement at each time
- **Examples**: age, weight, heart rate, white blood cell count

#### Variable Type Decision Making

**Important Note**: There can often be a choice for whether to treat a variable as quantitative or categorical.

**Example - Body Mass Index (BMI):**
- **Quantitative Approach**: BMI as discrete numerical values
- **Categorical Approach**: BMI as categories (underweight, normal, overweight, obese)

**Impact**: The decision whether a variable is quantitative or categorical will affect what conclusions can be made when interpreting results from statistical tests.

**Caution**: Since quantitative variables are treated on a continuous scale, it would be inappropriate to transform a variable like "which medication was given" into a quantitative variable with values 1, 2, and 3.

### Response vs. Predictor Variables

Both categorical and quantitative variables can be split into response and predictor variables.

#### Predictor Variables (Independent Variables)

**Predictor variables are explanatory, or independent, variables that help explain changes in a response variable.**

**Characteristics:**
- Explanatory variables
- Should help explain changes in the response variables
- Can be multiple variables that may have an impact on the response variable
- Can be categorical or quantitative

#### Response Variables (Dependent Variables)

**Response variables are outcome, or dependent, variables whose changes can be partially explained by the predictor variables.**

**Characteristics:**
- Outcome variables
- Should be the result of the predictor variables
- One variable per statistical test
- Can be categorical or quantitative

## Statistical Test Selection

**Choosing the correct statistical test depends on the types of variables defined and the question being answered.** The appropriate test is determined by the variables being compared.

### Common Statistical Tests Overview

Some common statistical tests include:
- **T-tests**: Compare quantitative variables between two groups
- **ANOVA**: Compare quantitative variables among three or more groups
- **Chi-square tests**: Examine associations between categorical variables

## T-Tests: Comparing Two Groups

**T-tests compare whether there are differences in a quantitative variable between two values of a categorical variable.**

### Example Application

A t-test could be useful to compare the length of stay for knee replacement surgery patients between those that took apixaban and those that took rivaroxaban.

### T-Test Process

1. **Question**: Is there a statistically significant difference in length of stay between the two groups?
2. **Output**: The t-test will output a p-value
3. **Interpretation**: P-value represents the probability that the two groups could be as different as they are in the data, if they were actually the same

### P-Value Interpretation

**P-value**: A number between zero and one
- **Closer to Zero**: Suggests the difference is more statistically significant
- **Closer to One**: Suggests less statistical significance

### Significance Testing Process

1. **Set Alpha**: Prior to collecting data, set a significance level (alpha)
2. **Compare**: Compare p-value to predetermined alpha level
3. **Decision**: If p-value < alpha, reject null hypothesis (statistically significant difference)

### Example Interpretation

**Scenario**: Alpha set at 0.05
- **P-value = 0.039**: Statistically significant difference in length of stay between apixaban and rivaroxaban patients
- **P-value = 0.91**: No statistical evidence of a difference in length of stay between the two medications

### Post-Hoc Analysis

**Other statistical summaries or methods examine how big of a difference that might be.** These summaries are known as post-hoc analysis since they are performed after the original test to provide additional context to the results.

## ANOVA: Analysis of Variance

**Analysis of variance, or ANOVA, tests can observe mean differences in a quantitative variable between values of a categorical variable, typically with three or more values to distinguish from a t-test.**

### Example Application

ANOVA could add patients given dabigatran to the previous population and evaluate whether the length of stay was significantly different across the three medications.

### ANOVA Process

1. **Null Hypothesis**: Length of stay is the same across all three medications
2. **Test**: Compare means across multiple groups simultaneously
3. **Decision**: If p-value is lower than designated significance level, reject the null hypothesis

### Post-Hoc Testing for ANOVA

**Summaries and post-hoc tests** can be performed to:
- Look at differences between length of stay
- Identify which individual medications may have statistically significant differences from other medications

### Advantages of ANOVA

- **Multiple Comparisons**: Handles multiple groups in single test
- **Type I Error Control**: Reduces risk of inflated Type I error from multiple t-tests
- **Comprehensive Analysis**: Provides overall test plus specific comparisons

## Chi-Square Tests: Categorical Variable Associations

**A chi-square test examines the association between two categorical variables.**

### Example Application

Consider whether the rate of having a post-operative bleed is the same across patients provided with apixaban, rivaroxaban and dabigatran.

### Chi-Square Process

1. **Question**: Are bleeding rates significantly different across medications?
2. **Computation**: Chi-square test computes a p-value
3. **Interpretation**: Determines whether bleeding rates were significantly different or not

### Post-Hoc Analysis for Chi-Square

Post-hoc tests can provide:
- **Bleeding Rate**: For each medication
- **Specific Comparisons**: Which specific medications may have significantly different bleeding rates from each other

### Applications

- **Association Testing**: Determine if two categorical variables are related
- **Independence Testing**: Test if variables are independent
- **Goodness of Fit**: Compare observed vs. expected distributions

## Multiple Regression: Advanced Analysis

**A slightly more advanced way of examining a question can come through multiple regression.** Regression allows more predictor variables to be analyzed and can act as a control when looking at associations between variables.

### Benefits of Regression Analysis

#### Control Variables

**Common control variables** are age, sex and any comorbidities likely to affect the outcome variable that are not closely related to the other explanatory variables.

#### Bias Reduction

**Control variables can be especially important in reducing the effect of bias in a retrospective population.** Since retrospective data was not built with the research question in mind, it is important to eliminate threats to the validity of the analysis.

#### Enhanced Validity

**Testing that controls for confounding variables, such as regression, is often more valuable with retrospective data** because it can ease concerns about validity.

### Types of Regression

The two main types of regression are linear and logistic.

#### Linear Regression

**Linear regression is used to predict differences in a quantitative, continuous response variable**, such as length of stay.

**Characteristics:**
- **Response Variable**: Quantitative/continuous
- **Examples**: Length of stay, blood pressure, weight change
- **Output**: Coefficients showing degree of association

#### Logistic Regression

**Logistic regression predicts differences in a dichotomous, categorical response variable**, such as 90-day readmission.

**Characteristics:**
- **Response Variable**: Dichotomous/categorical
- **Examples**: 90-day readmission (yes/no), mortality (yes/no), treatment success (yes/no)
- **Output**: Odds ratios and probabilities

### Regression Example Applications

**Whether the outcome variable is categorical or quantitative, regression can be appropriate.**

#### Linear Regression Example

**Predictor Variables**: Age, gender, anticoagulant usage
**Response Variable**: Length of stay (quantitative)
**Analysis**: Use predictor variables in linear regression to evaluate their individual effects on length of stay

#### Logistic Regression Example

**Predictor Variables**: Age, gender, anticoagulant usage (same as above)
**Response Variable**: 90-day readmission (dichotomous categorical)
**Analysis**: Use same predictor variables in logistic regression to evaluate their individual effects on whether the patient had a 90-day readmission

### Regression Output and Interpretation

#### P-Values

**Analysis can compute a p-value for each included predictor variable** to determine whether they are significantly associated.

#### Test Statistics

**The statistical tests generate an associated test statistic** which determines the probability the results could be acquired given that there is no association between the compared variables.

#### Coefficients

**Results often come with coefficients** which can give:
- The degree of the association
- The degree to which one variable changes with another

#### Confidence Intervals

**Most tests, including all listed in this article, also have confidence intervals**, which give a range for the correlation with a specified level of confidence.

## Interpreting Non-Significant Results

### Importance of Negative Results

**Even if these tests do not give statistically significant results, the results are still important.** Not reporting statistically insignificant findings creates a bias in research.

### Publication Bias Concerns

**Ideas can be repeated enough times that eventually statistically significant results are reached, even though there is no true significance.** This highlights the importance of:
- Reporting all results, regardless of significance
- Considering effect sizes alongside p-values
- Understanding the difference between statistical and practical significance

### Large Sample Size Considerations

**In some cases with very large sample sizes, p-values will almost always be significant.** In this case:
- **Effect Size is Critical**: Even the smallest, meaningless differences can be found to be statistically significant
- **Practical Significance**: Must evaluate whether statistically significant differences are practically meaningful
- **Clinical Relevance**: Consider whether differences matter in real-world applications

## Advanced Statistical Concepts

### Effect Size

**Effect size** measures the magnitude of the difference between groups, independent of sample size.

#### Types of Effect Size
- **Cohen's d**: For comparing means between groups
- **Eta-squared**: For ANOVA, proportion of variance explained
- **Odds Ratio**: For logistic regression and categorical outcomes
- **R-squared**: For linear regression, proportion of variance explained

#### Interpretation Guidelines
- **Small Effect**: Detectable but minimal practical importance
- **Medium Effect**: Moderate practical significance
- **Large Effect**: Strong practical importance

### Confidence Intervals

**Confidence intervals provide a range of plausible values** for the true population parameter.

#### Interpretation
- **95% Confidence Interval**: If we repeated the study 100 times, 95 of the intervals would contain the true population parameter
- **Width**: Narrower intervals indicate more precision
- **Overlap**: Non-overlapping confidence intervals suggest significant differences

#### Advantages over P-Values
- Provide information about effect size
- Show precision of estimates
- More informative than simple significance testing

### Multiple Comparisons

**When conducting multiple statistical tests, the risk of Type I error increases.**

#### Problem
- Each test has α probability of Type I error
- Multiple tests increase overall Type I error rate
- Family-wise error rate can become unacceptably high

#### Solutions
- **Bonferroni Correction**: Divide α by number of comparisons
- **False Discovery Rate**: Control proportion of false discoveries
- **Planned Comparisons**: Pre-specify important comparisons

## Data Assumptions and Validation

### Assumptions for Common Tests

#### T-Test Assumptions
1. **Normality**: Data should be approximately normally distributed
2. **Independence**: Observations should be independent
3. **Equal Variances**: Groups should have similar variances (for two-sample t-test)

#### ANOVA Assumptions
1. **Normality**: Residuals should be normally distributed
2. **Independence**: Observations should be independent
3. **Homogeneity of Variance**: Groups should have equal variances

#### Chi-Square Assumptions
1. **Independence**: Observations should be independent
2. **Expected Frequencies**: Expected cell counts should be ≥5
3. **Categorical Data**: Variables should be truly categorical

#### Regression Assumptions
1. **Linearity**: Relationship between variables should be linear
2. **Independence**: Residuals should be independent
3. **Homoscedasticity**: Constant variance of residuals
4. **Normality**: Residuals should be normally distributed

### Assumption Checking

#### Graphical Methods
- **Histograms**: Check normality of distributions
- **Q-Q Plots**: Compare data to normal distribution
- **Scatter Plots**: Check linearity and homoscedasticity
- **Residual Plots**: Examine regression assumptions

#### Statistical Tests
- **Shapiro-Wilk Test**: Test for normality
- **Levene's Test**: Test for equal variances
- **Durbin-Watson Test**: Test for independence of residuals

### Handling Assumption Violations

#### Transformation
- **Log Transformation**: For right-skewed data
- **Square Root**: For count data
- **Box-Cox**: General power transformations

#### Non-Parametric Alternatives
- **Mann-Whitney U**: Alternative to t-test
- **Kruskal-Wallis**: Alternative to ANOVA
- **Spearman Correlation**: Alternative to Pearson correlation

## Sample Size and Power Analysis

### Components of Power Analysis

#### Required Information
1. **Effect Size**: Expected magnitude of difference
2. **Alpha Level**: Acceptable Type I error rate
3. **Power**: Desired probability of detecting true effect
4. **Variability**: Expected standard deviation or variance

#### Types of Power Analysis
- **Prospective**: Calculate required sample size
- **Post-hoc**: Calculate achieved power with given sample
- **Sensitivity**: Determine detectable effect size

### Factors Affecting Power

#### Increase Power
- Larger effect sizes
- Larger sample sizes
- Lower variability
- Higher alpha levels
- One-tailed vs. two-tailed tests

#### Decrease Power
- Smaller effect sizes
- Smaller sample sizes
- Higher variability
- Lower alpha levels
- Missing data

### Practical Considerations

#### Resource Constraints
- **Budget**: Cost per participant
- **Time**: Duration of data collection
- **Personnel**: Available research staff
- **Equipment**: Measurement capabilities

#### Ethical Considerations
- **Minimum Sample**: Avoid underpowered studies
- **Maximum Sample**: Don't expose unnecessary participants to risk
- **Interim Analysis**: Plan for early stopping rules

## Data Management and Quality Control

### Data Collection

#### Standardization
- **Protocols**: Standardized data collection procedures
- **Training**: Consistent training for data collectors
- **Documentation**: Clear variable definitions and coding

#### Quality Assurance
- **Double Entry**: Independent data entry verification
- **Range Checks**: Identify impossible or unlikely values
- **Logic Checks**: Verify consistency across variables

### Missing Data

#### Types of Missing Data
1. **Missing Completely at Random (MCAR)**: Missing data unrelated to any variables
2. **Missing at Random (MAR)**: Missing data related to observed variables
3. **Missing Not at Random (MNAR)**: Missing data related to unobserved variables

#### Handling Missing Data
- **Complete Case Analysis**: Exclude cases with missing data
- **Imputation**: Replace missing values with estimated values
- **Multiple Imputation**: Create multiple datasets with different imputations
- **Maximum Likelihood**: Use all available data in analysis

### Data Cleaning

#### Outlier Detection
- **Statistical Methods**: Z-scores, IQR method
- **Graphical Methods**: Box plots, scatter plots
- **Domain Knowledge**: Clinical or practical impossibility

#### Outlier Handling
- **Investigation**: Determine if outliers are errors or valid extreme values
- **Correction**: Fix data entry errors
- **Transformation**: Reduce impact through data transformation
- **Robust Methods**: Use statistical methods less sensitive to outliers

## Reporting Statistical Results

### Essential Elements

#### Descriptive Statistics
- **Sample Size**: Number of participants/observations
- **Central Tendency**: Means, medians
- **Variability**: Standard deviations, ranges
- **Distributions**: Frequencies, percentages

#### Inferential Statistics
- **Test Statistics**: t-values, F-values, chi-square values
- **P-Values**: Exact values when possible
- **Effect Sizes**: Magnitude of differences
- **Confidence Intervals**: Precision of estimates

### Best Practices

#### Transparency
- **Methods**: Clear description of statistical procedures
- **Assumptions**: Report assumption checking and violations
- **Software**: Specify statistical software and versions used

#### Interpretation
- **Statistical vs. Practical Significance**: Distinguish between the two
- **Limitations**: Acknowledge study limitations
- **Generalizability**: Discuss applicability to other populations

## Common Statistical Errors

### Design Errors

#### Inadequate Sample Size
- **Problem**: Insufficient power to detect meaningful effects
- **Solution**: Conduct proper power analysis before data collection

#### Multiple Comparisons
- **Problem**: Inflated Type I error rate
- **Solution**: Adjust significance levels or use planned comparisons

#### Confounding Variables
- **Problem**: Alternative explanations for observed effects
- **Solution**: Include relevant control variables in analysis

### Analysis Errors

#### Assumption Violations
- **Problem**: Invalid statistical inferences
- **Solution**: Check assumptions and use appropriate alternatives

#### Data Dredging
- **Problem**: Finding spurious significant results through multiple testing
- **Solution**: Pre-specify hypotheses and analysis plans

#### Correlation vs. Causation
- **Problem**: Inferring causation from correlation
- **Solution**: Use appropriate study designs and careful interpretation

### Interpretation Errors

#### P-Hacking
- **Problem**: Manipulating analysis to achieve significant p-values
- **Solution**: Pre-register analysis plans and report all analyses

#### Overinterpretation
- **Problem**: Drawing conclusions beyond what data support
- **Solution**: Conservative interpretation and acknowledgment of limitations

## Conclusion: Ensuring Appropriate Statistical Analysis

**These variables and tests are just some things to keep in mind before, during and after the analysis process in order to make sure that the statistical reports are supporting the questions being answered.**

### Key Considerations

1. **Patient Population**: Carefully define and consider the target population
2. **Variable Types**: Understand categorical vs. quantitative and response vs. predictor variables
3. **Statistical Tests**: Choose appropriate tests based on variable types and research questions
4. **Result Validity**: Any results are only as useful as the process used to obtain them

### Implementation Guidelines

**This primer can be used as a reference to help ensure appropriate statistical analysis** by:

- Planning analysis before data collection
- Choosing appropriate statistical methods
- Checking assumptions and handling violations
- Interpreting results in context
- Reporting findings transparently

### Final Recommendations

1. **Collaborate**: Work with statisticians when possible
2. **Plan Ahead**: Consider statistical analysis during study design
3. **Document Everything**: Maintain clear records of all analytical decisions
4. **Stay Current**: Keep up with evolving statistical best practices
5. **Be Transparent**: Report methods and limitations honestly

**The goal is to ensure that statistical analysis supports valid, reliable, and meaningful conclusions that advance scientific knowledge and inform evidence-based decision making.**

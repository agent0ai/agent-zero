<!-- Source: https://aph-qualityhandbook.org/set-up-conduct/process-analyze-data/3-2-quantitative-research/3-2-2-data-analysis/data-analysis-documentation/ -->

Data analysis documentation | APH Quality Handbook

[xml version="1.0" encoding="UTF-8" ?

1-logo/default/en](https://www.amsterdamumc.org/research/institutes/amsterdam-public-health.htm "Amsterdam Public Health")

Menu

Search

* [1-icon/ui/arrow\_right

  Amsterdam Public Health](https://www.amsterdamumc.org/research/institutes/amsterdam-public-health.htm)
* [1-icon/ui/arrow\_right

  Home](/home/)
* [1-icon/ui/arrow\_right

  Research Lifecycle](/research-lifecycle/)

#### More APH...

* [1-icon/ui/arrow\_right

  About](https://www.amsterdamumc.org/research/institutes/amsterdam-public-health/about.htm)
* [1-icon/ui/arrow\_right

  News](https://www.amsterdamumc.org/research/institutes/amsterdam-public-health/news.htm)
* [1-icon/ui/arrow\_right

  Events](https://www.amsterdamumc.org/research/institutes/amsterdam-public-health/events.htm)
* [1-icon/ui/arrow\_right

  Research information](https://www.amsterdamumc.org/research/institutes/amsterdam-public-health/information.htm)
* [1-icon/ui/arrow\_right

  Our strenghts](Our strenghts)

* [Amsterdam UMC Research](#)
  + [Amsterdam Public Health](https://www.amsterdamumc.org/research/institutes/amsterdam-public-health.htm)
  + [Home](/home/)
  + [Research Lifecycle](/research-lifecycle/)
  + #### More APH...
  + [About](https://www.amsterdamumc.org/research/institutes/amsterdam-public-health/about.htm)
  + [News](https://www.amsterdamumc.org/research/institutes/amsterdam-public-health/news.htm)
  + [Events](https://www.amsterdamumc.org/research/institutes/amsterdam-public-health/events.htm)
  + [Research information](https://www.amsterdamumc.org/research/institutes/amsterdam-public-health/information.htm)
  + <Our strenghts>
* [Menu](#)
  + [Home](/home/)
  + [Design, Plan & Propose](/design-plan-propose/)
    - [Ideas](/design-plan-propose/ideas/)
    - [Partners](/design-plan-propose/partners/)
    - [Proposal Writing](/design-plan-propose/proposal-writing/)
  + [Set-up & Conduct](/set-up-conduct/)
    - [Study Preparation](/set-up-conduct/study-preparation/)
    - [Methods & Data Collection](/set-up-conduct/methods-data-collection/)
    - [Process & Analyze Data](/set-up-conduct/process-analyze-data/)
  + [Reporting, Review & Knowledge Utilization](/reporting-review-knowledge-utilization/)
    - [Writing & Publication](/reporting-review-knowledge-utilization/writing-publication/)
    - [Archiving & Open Data](/reporting-review-knowledge-utilization/archiving-open-data/)
    - [Knowledge Utilization](/reporting-review-knowledge-utilization/knowledge-utilization/)
  + [Compliance, Training & Supervision](/compliance-training-supervision/)
    - [Compliance](/compliance-training-supervision/compliance/)
    - [Training](/compliance-training-supervision/training/)
    - [Supervision](/compliance-training-supervision/supervision/)

Search

# Data analysis documentation

* [Home](/home/)
* [Design, Plan & Propose](/design-plan-propose/)
  + [Ideas](/design-plan-propose/ideas/)
  + [Partners](/design-plan-propose/partners/)
  + [Proposal Writing](/design-plan-propose/proposal-writing/)
* [Set-up & Conduct](/set-up-conduct/)
  + [Study Preparation](/set-up-conduct/study-preparation/)
  + [Methods & Data Collection](/set-up-conduct/methods-data-collection/)
  + [Process & Analyze Data](/set-up-conduct/process-analyze-data/)
* [Reporting, Review & Knowledge Utilization](/reporting-review-knowledge-utilization/)
  + [Writing & Publication](/reporting-review-knowledge-utilization/writing-publication/)
  + [Archiving & Open Data](/reporting-review-knowledge-utilization/archiving-open-data/)
  + [Knowledge Utilization](/reporting-review-knowledge-utilization/knowledge-utilization/)
* [Compliance, Training & Supervision](/compliance-training-supervision/)
  + [Compliance](/compliance-training-supervision/compliance/)
  + [Training](/compliance-training-supervision/training/)
  + [Supervision](/compliance-training-supervision/supervision/)

* [Set-up & Conduct](/set-up-conduct/)
* [Process & Analyze Data](/set-up-conduct/process-analyze-data/)
* [Quantitative research](/set-up-conduct/process-analyze-data/3-2-quantitative-research/)
* [Data analysis](/set-up-conduct/process-analyze-data/3-2-quantitative-research/3-2-2-data-analysis/)
* Data analysis documentation

#### Data analysis

---

* [Analysis plan](/set-up-conduct/process-analyze-data/3-2-quantitative-research/3-2-2-data-analysis/analysis-plan/)
* [Initial data analysis](/set-up-conduct/process-analyze-data/3-2-quantitative-research/3-2-2-data-analysis/initial-data-analysis/)
* [Post-hoc & sensitivity analyses](/set-up-conduct/process-analyze-data/3-2-quantitative-research/3-2-2-data-analysis/post-hoc-sensitivity-analyses/)
* [Data analysis documentation](/set-up-conduct/process-analyze-data/3-2-quantitative-research/3-2-2-data-analysis/data-analysis-documentation/)
* [Handling missing data](/set-up-conduct/process-analyze-data/3-2-quantitative-research/3-2-2-data-analysis/handling-missing-data/)

##### Aim

To ensure that the analyses can be properly reproduced

##### Requirements

Clear documentation of the data analysis in a log file (for example SPSS syntax, Do file in STATA, R script or Word file), to be able to reproduce the relevant data analyses.

##### Documentation

Log file including:

* Specific research questions or purpose of the analysis;
* Databases which are used for the analyses (For example ‘get file’ statement in SPSS syntax);
* All statistical analyses which are executed.
* Add a ‘README’ tab in your data files and/or separate descriptive document to ensure you can reproduce the results when needed (e.g. in case of audit or inspection, or journal review) and to promote interoperability of your data files.

##### Responsibilities

* Executing researcher: To document all steps that are taken throughout the data analysis in a log file.
* Project leaders: To regularly check and discuss the data analysis, by using the documentation in a log file.
* Research assistant: N.a.

##### How To

It is important in respect of reproducibility and efficiency of data analysis that clear documentation of the data analysis takes place. This may be undertaken by creating a log file for all the relevant analyses. This file needs to start off with the research question to be answered and the date of the analysis, and should end with a(n) (provisional) answer to the question.

A lof file (e.g. SPSS syntax) can be used to document your analyses (e.g. for an article) to allow you and others to easily retrieve and reproduce everything. Don’t forget to always include the name and location of the datafile (e.g. ‘get file’ in SPSS), so you know which file is related to your analysis (and where they are stored). Log files should include the code for all statistical tests conducted, to serve as an analysis logbook. Place your code in a logical order and distinguish between variable definitions and analyses (e.g. firstly all variable definitions, than the analyses for table 1, then table 2, etc.). A Dutch example of this can be found here.

Tip: annotate your log files (e.g. by using \* followed by text in SPSS syntax). Annotations are an important part of documentation of your data analyses and facilitate reproduction of your results end recycling of your code.

### References

* 1. Swaen et al: Responsible Epidemiologic Research Practice: a guideline developed by a working group of the Netherlands Epidemiological Society. J Clin Epidemiol. 2018 Aug;100:111-119.

### Tags

[Quantitative research](https://aph-qualityhandbook.org/search/?q=tag%3aQuantitative+research)

[Documentation](https://aph-qualityhandbook.org/search/?q=tag%3aDocumentation)

[Data management](https://aph-qualityhandbook.org/search/?q=tag%3aData+management)

[Data analysis](https://aph-qualityhandbook.org/search/?q=tag%3aData+analysis)

### Download

---

[##### Data Anlysis Documentation](/media/wgvds2bh/data-anlysis-documentation.pdf)

PDF - 139.9Kb

### Related

[#### Handling missing data](/set-up-conduct/process-analyze-data/3-2-quantitative-research/3-2-2-data-analysis/handling-missing-data/)

[#### Initial data analysis](/set-up-conduct/process-analyze-data/3-2-quantitative-research/3-2-2-data-analysis/initial-data-analysis/)

[#### Post-hoc & sensitivity analyses](/set-up-conduct/process-analyze-data/3-2-quantitative-research/3-2-2-data-analysis/post-hoc-sensitivity-analyses/)

* [##### Version history](#)

  **Version 4.0** - Revision - 08 DEC 2021 - Dr. Marieke Blom, Laura van Dongen, Elize Vlainic

  ---

  **Version 3.0 -**Revision guideline - 26 OCT 2016 - EMGO

  ---

  **Version 2.0 -**Revision format - 12 MAY 2015 - EMGO

  ---

  **Version 1.1 -** English translation - 01 JAN 2010 - EMGO

  ---

  **Version 1.0 -**Title modified: Documentation instead of Report. Adding details with example of documented syntax - 21 APR 2004 - EMGO

logo\_UvA\_Vu

[xml version="1.0" encoding="UTF-8" ?

1-logo/default/en](https://www.amsterdamumc.org/research/institutes/amsterdam-public-health.htm "Amsterdam Public Health")

* [Home](/home/)
* [Research Lifecycle](/research-lifecycle/)
* [Scientific Quality](/scientific-quality/)

* [Amsterdam Public Health](https://www.amsterdamumc.org/research/institutes/amsterdam-public-health.htm)
* [Advice and support](/compliance-training-supervision/training/advice-and-support/)
* [Tags](/tags/)

* [Disclaimer](/disclaimer/)
* [Credits](/credits/)
* [Contact us](/contact-us/)
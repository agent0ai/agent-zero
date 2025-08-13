<!-- Source: https://ibm.github.io/data-science-best-practices/ -->

Introduction | IBM Data Science Best Practices                [Skip to main content](#main-content)   Link      Menu      Expand       (external link)    Document      Search       Copy       Copied      

[IBM Data Science Best Practices](/data-science-best-practices/)

* [Introduction](/data-science-best-practices/)
* [Project Team](/data-science-best-practices/project_team.html)
  + [Project Roles](/data-science-best-practices/project_roles.html)
* [Architecture](/data-science-best-practices/architecture.html)
  + [Interfaces](/data-science-best-practices/interfaces.html)
* [Source Code](/data-science-best-practices/source_code.html)
* [Documentation](/data-science-best-practices/documentation.html)
* [Versioning](/data-science-best-practices/versioning.html)
* [Data Management](/data-science-best-practices/data_management.html)
* [Dependency Management](/data-science-best-practices/dependency_management.html)
* [Configuration Management](/data-science-best-practices/configuration_management.html)
* [Testing](/data-science-best-practices/testing.html)
* [Quality Measurements](/data-science-best-practices/quality_measurements.html)
* [Model Training](/data-science-best-practices/model_training.html)
* [Distribution](/data-science-best-practices/distribution.html)
* [Cloud Deployment](/data-science-best-practices/cloud_deployment.html)
* [Edge Deployment](/data-science-best-practices/edge_deployment.html)
* [Monitoring](/data-science-best-practices/monitoring.html)
* [Automation](/data-science-best-practices/automation.html)
* [Scaling](/data-science-best-practices/scaling.html)
* [Sizing](/data-science-best-practices/sizing.html)
* [Security](/data-science-best-practices/security.html)
* [Usage Recommendations](/data-science-best-practices/recommendation.html)
* [License & Contributing](/data-science-best-practices/license.html)
  This site uses [Just the Docs](https://github.com/just-the-docs/just-the-docs), a documentation theme for Jekyll.

# IBM Data Science - Best Practices

## Introduction

[![](https://imgs.xkcd.com/comics/machine_learning.png)](https://xkcd.com/1838/)   
 "[Machine Learning](https://xkcd.com/1838/)" by Randall Munroe is licensed under [CC BY-NC 2.5](https://creativecommons.org/licenses/by-nc/2.5/).

The goal of this document is to enable you as a data scientist to develop a data science use case in a semi-professional setting to make it ready for production use. This means focusing on the versioning, scalability, monitoring and engineering of the solution.

### Prerequisites

#### Required Skills

* Python programming - Intermediate Level
* Data Science - Intermediate Level
* Shell, Terminal or CMD (command-line) - Beginner Level
* Git - Beginner Level

#### Tools

* [Python 3](https://www.python.org/downloads/) - Python 3.10
* IDE (Integrated Development Environment) - Our recommendations: [Visual Studio Code](https://code.visualstudio.com/) or [PyCharm Community Edition](https://www.jetbrains.com/pycharm/)

> **Q: Can I use Jupyter Notebooks as my IDE?** A: No, since this is not an IDE. Also we feel that it tends to encourage bad coding practice, especially with beginners. For further details: [I don’t like Notebooks - Joel Grus (YouTube)](https://www.youtube.com/watch?v=7jiPeIFXb6U)

> **Q: Can I use a plain text editor?** A: Yes, if you feel that this is the best for you, then go for it. Just make sure that it is a plain text editor and not a rich-text editor.

> **Q: Can I use Anaconda?** A: No, Anaconda Free Version is only permitted for ‘individual hobbyists, academics, non-profits, and small businesses’ ([more details](https://www.anaconda.com/blog/anaconda-commercial-edition-faq)); You require commercial licensing to use Anaconda in a large enterprise.

#### ‘IBM Consulting for AI at Scale’ Offering

![AI at Scale Overview](./res/img/AI_Scale.png)   
 © IBM

‘IBM Consulting for AI at Scale’ is an IBM Consulting offering, which aims at scaling current AI engagements and applications towards an enterprise setup. It consists of multiple pillars, which are building up the overall offering:

* **Vision:** Addresses the AI and data strategy of a company and a potential transformation roadmap to make AI a key component of the company’s offering.
* **Operating Model:** When the journey and the plan is fixed, it is essential to define the how to execute and operate
* **Data and Technology:** In order to scale AI applications and environments, it is also key to incorporate a strong management and eco system for the existing data.
* **Engineering and Operations:** This addresses the questions of engineering, deploying and monitoring the AI solution. It is the most technical part of the offering and is the focus of this playbook.
* **Change Management:** The process to transform and change existing AI structures is addressed in this pillar.
* **People and Enablement:** To achieve maturity and scalability in AI it is essential to also cover the right skill set, roles and team setup in the AI organization.

### The Role of Machine Learning in a Real World AI System

![Real World AI System](/data-science-best-practices/res/img/RealWorldAISystem.png)

As outlined in the paper “[Hidden Technical Debt in Machine Learning Systems](https://papers.nips.cc/paper/2015/file/86df7dcfd896fcaf2674f757a2463eba-Paper.pdf)” AI systems can become very quickly very complex. Machine Learning itself is just a tiny portion of the overall AI system. Understanding the surrounding factors is the first step is managing the complexity and keeping the technical debt of such systems at bay. The aim of these Data Science Best Practices is to guide and help understand these factors.

## Need Help

Reach us at on Slack [#datascience-best-practices](https://slack.com/app_redirect?channel=CUZGJN43V) (IBM Internal)
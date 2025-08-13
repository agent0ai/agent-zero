<!-- Source: https://developers.redhat.com/articles/2022/10/20/ultimate-cicd-resource-guide -->

The ultimate CI/CD resource guide | Red Hat Developer

[Skip to main content](#main-content)

[![Redhat Developers  Logo](/themes/custom/rhdp_fe/images/branding/2023_RHDLogo_reverse.svg)](/)

* Products

  ### Platforms

  + [Red Hat Enterprise Linux](/products/rhel/overview)

    ![Red Hat Enterprise Linux Icon](/sites/default/files/2023-10/RHEL-2.png "Red Hat Enterprise Linux")
  + [Red Hat AI](https://developers.redhat.com/products/red-hat-ai)

    ![Red Hat AI](/sites/default/files/2025-08/red-hat-ai.png "Red Hat AI")
  + [Red Hat OpenShift](/products/openshift/overview)

    ![Openshift icon](/sites/default/files/Red%20Hat%20OS%402x.png "Openshift icon")
  + [Red Hat Ansible Automation Platform](/products/ansible/overview)

    ![Ansible icon](/sites/default/files/ICO%20-%20Ansible%20Platform%20Learning%20Resources.png "Ansible icon")
  + [View All Red Hat Products](/products)

  ### Featured

  + [Red Hat build of OpenJDK](/products/openjdk/overview)
  + [Red Hat Developer Hub](/products/developer-hub/overview)
  + [Red Hat JBoss Enterprise Application Platform](/products/eap/overview)
  + [Red Hat OpenShift Dev Spaces](/products/openshift-dev-spaces/overview)
  + [Red Hat OpenShift Local](/products/openshift-local/overview)

  + ### Red Hat Developer Sandbox

    Try Red Hat products and technologies without setup or configuration fees for 30 days with this shared Openshift and Kubernetes cluster.
  + [Try at no cost](/developer-sandbox)
* Technologies

  ### Featured

  + [AI/ML](https://developers.redhat.com/topics/ai-ml)

    ![AI/ML Icon](/sites/default/files/2024-05/ai-ml_featured.png "AI/ML Icon")
  + [Linux](/topics/linux)

    ![Linux Icon](/sites/default/files/Red%20Hat%20OS%20Platform%402x.png "Linux Icon")
  + [Kubernetes](https://developers.redhat.com/topics/kubernetes)

    ![Cloud icon](/sites/default/files/Cloud-native%20app%20server%20on%20OpenShift.png "Cloud icon")
  + [Automation](/topics/automation)

    ![Automation Icon showing arrows moving in a circle around a gear](/sites/default/files/2023-10/Automation-2.png "Automation")
  + [View All Technologies](/topics)

  + ### Programming Languages & Frameworks

    - [Java](/java)
    - [Python](/topics/python)
    - [JavaScript](/topics/javascript)
  + ### System Design & Architecture

    - [Red Hat architecture and design patterns](/topics/red-hat-architecture-and-design-patterns)
    - [Microservices](/topics/microservices)
    - [Event-Driven Architecture](/topics/event-driven)
    - [Databases](https://developers.redhat.com/topics/databases)

  + ### Developer Productivity

    - [Developer productivity](https://developers.redhat.com/topics/developer-productivity)
    - [Developer Tools](https://developers.redhat.com/topics/developer-tools)
    - [GitOps](/topics/gitops)
  + ### Automated Data Processing

    - [AI/ML](https://developers.redhat.com/aiml)
    - [Data Science](/topics/data-science)
    - [Apache Kafka on Kubernetes](/topics/kafka-kubernetes)

  + ### Platform Engineering

    - [DevOps](/topics/devops)
    - [DevSecOps](/topics/devsecops)
    - [Ansible automation for applications and services](/topics/ansible-automation-applications-and-services)
  + ### Secure Development & Architectures

    - [Security](/topics/security)
    - [Secure coding](/topics/secure-coding)
* Learn

  ### Featured

  + [Kubernetes & Cloud Native](/learn/openshift)

    ![Openshift icon](/sites/default/files/Red%20Hat%20OS%402x.png "Openshift icon")
  + [Linux](/learn/rhel)

    ![Rhel icon](/sites/default/files/Red%20Hat%20OS%20Platform%402x.png "Rhel icon")
  + [Automation](/learn/ansible)

    ![Ansible cloud icon](/sites/default/files/ICO%20-%20Download%20Ansible%20Automation%20Platform.png "Ansible cloud icon")
  + [AI/ML](/learn/openshift-ai)

    ![AI/ML Icon](/sites/default/files/2023-10/ai-ml.png "AI/ML Icon")
  + [View All Learning Resources](/learn)

  ### E-Books

  + [GitOps Cookbook](/e-books/gitops-cookbook)
  + [Podman in Action](/e-books/podman-action)
  + [Kubernetes Operators](/e-books/kubernetes-operators)
  + [The Path to GitOps](https://developers.redhat.com/e-books/path-gitops)
  + [View All E-books](/e-books)

  ### Cheat Sheets

  + [Linux Commands](/cheat-sheets/linux-commands-cheat-sheet-old)
  + [Bash Commands](/cheat-sheets/bash-shell-cheat-sheet)
  + [Git](/cheat-sheets/git-cheat-sheet)
  + [systemd Commands](/cheat-sheets/systemd-commands-cheat-sheet)
  + [View All Cheat Sheets](/cheat-sheets)

  ### Documentation

  + [Product Documentation](https://docs.redhat.com)
  + [API Catalog](/api-catalog/)
  + [Legacy Documentation](https://console.redhat.com/docs/api)
* Developer Sandbox

  ### Developer Sandbox

  + Access Red Hat’s products and technologies without setup or configuration, and start developing quicker than ever before with our new, no-cost sandbox environments.
  + [Explore Developer Sandbox](https://developers.redhat.com/developer-sandbox)

  ### Featured Developer Sandbox activities

  + [Get started with your Developer Sandbox](/developer-sandbox/activities)
  + [OpenShift virtualization and application modernization using the Developer Sandbox](/learn/openshift/openshift-virtualization-and-application-modernization-using-developer-sandbox)
  + [Explore all Developer Sandbox activities](/developer-sandbox/activities)

  ### Ready to start developing apps?

  + [Try at no cost](https://developers.redhat.com/content-gateway/link/3886857)
* [Blog](/blog)
* [Events](/events)
* [Videos](/videos)

Search

Search

All Red Hat

# The ultimate CI/CD resource guide

October 20, 2022

[Heiker Medina](/author/heiker-medina)

Related topics:
:   [CI/CD](/topics/ci-cd/all)[GitOps](/topics/gitops/all)[Operators](/topics/kubernetes/operators)

Related products:
:   [Red Hat OpenShift Container Platform](https://developers.redhat.com/products/openshift/overview)

### Share:

Table of contents:

You've found the right place for content on [continuous integration/continuous deployment (CI/CD)](/topics/ci-cd). We've gathered our highest-performing articles from the past year on this topic on Red Hat Developer. This article will introduce you to all things related to CI/CD.

## What is CI/CD and why is it important for developers?

Continuous integration (CI) and continuous deployment (CD) are development processes making use of automated tools to produce high-quality software.

CI ensures that any code submitted by each developer works together with all other code in the project. Typically, CI works by running regression tests.

CD involves further automation to make sure that the latest accepted versions of a project enter production, and that all the pieces deployed together are compatible.

Numerous tools, such as integrated development environments and version control systems, help you build software. But when it comes to creating software that customers trust—and even love—you need to pay attention to the details. A good CI/CD environment ensures that testing, integration, and deployment are fast, easy, and accurate. CI/CD allows you to iterate faster, build more reliable code, and deliver better customer experiences.

## Recent articles to explore about CI/CD

Here are eight great Red Hat Developer articles on this topic:

* **[Deploy Helm charts with Jenkins CI/CD](/articles/2021/05/24/deploy-helm-charts-jenkins-cicd-red-hat-openshift-4):** Learn how to use Jenkins's CI/CD capabilities to deploy a Helm chart using a [Red Hat OpenShift](/openshift) 4 cluster. Helm is a package manager for Kubernetes that uses a packaging format called *charts*. These charts have all of the Kubernetes resources required to deploy an application, such as deployments and services.
* **[A developer's guide to CI/CD and GitOps with Jenkins Pipelines](/articles/2022/01/13/developers-guide-cicd-and-gitops-jenkins-pipelines):** [GitOps](/topics/gitops) and CI/CD have a lot to offer each other. This article guides you through the use of a Jenkinsfile to create deployments that combine CI/CD and GitOps.
* **[Containerize .NET applications without writing Dockerfiles](/articles/2022/08/01/containerize-net-applications-without-writing-dockerfiles):** Discover how to use a tool named dotnet build-image to create Dockerfiles and containerized images from [.NET](/topics/dotnet) applications. You will also learn how to use this tool in a GitHub workflow to create an image from a .NET application and push it to a repository.
* **[Automate CI/CD on pull requests with Argo CD ApplicationSets](/articles/2022/04/05/automate-cicd-pull-requests-argo-cd-applicationsets#):** The quest to further automate building, testing, and deployment is inspiring new features in Argo CD, [Kubernetes](/topics/kubernetes), and other tools. This article shows how to improve feature testing by automating builds and the creation of Kubernetes environments. ApplicationSets in Argo CD, together with Tekton, create a CI/CD system that includes feature branch testing on OpenShift.
* **[How to create a better front-end developer experience](/articles/2021/06/01/how-create-better-front-end-developer-experience):** Explore common pain points that can complicate the development process, and learn how to address them to foster better developer experiences. Take developing a form using React, for example. If developers can develop the form without difficulty, it will likely be a positive experience for the customer as well.
* **[OpenShift support for GitOps processes](/articles/2022/02/09/gitops-using-red-hat-openshift-console-49-and-410#):** This article explains how [OpenShift's GitOps Operator](https://www.redhat.com/en/technologies/cloud-computing/openshift/gitops) works and highlights improvements in OpenShift 4.9 and 4.10. The article includes a video showing how to use the developer console to manage cluster configurations and deploy cloud-native applications using OpenShift. Follow up this article by trying out a [learning path about GitOps](/learn/openshift/develop-gitops).
* **[Integrate ISO 20022 payments messaging with CI/CD](/articles/2022/01/20/integrate-iso-20022-payments-messaging-cicd):** An increasing number of financial institutions are embracing ISO 20022 standards for payments and securities transactions. This article shows how to use the message conversion platform from Trace Financial (a Red Hat ISV) and Red Hat Fuse to convert messages between the SWIFT MT and MX formats for financial data. Key benefits of the MX message set include the ability to capture richer data, flexibility, and a machine-readable format.
* **[Tools and practices for remote development teams](/articles/2021/10/12/tools-and-practices-remote-development-teams):** This article explores a few tools and practices that can help you work from home. Ideas include shared IDEs to facilitate collaboration, a repository of self-service and single-click workspaces for IDE consistency, and triggering CI/CD pipelines from source control systems to automate manual operations tasks.

## The Developer Sandbox is a great place to start

Interested in developing your first application at no cost? Test out the [Developer Sandbox on Red Hat OpenShift](/developer-sandbox) and learn by doing.

*Last updated:
December 27, 2023*

## Recent Posts

* ### [Windows image-building service for OpenShift Virtualization](/articles/2025/08/12/windows-image-building-service-openshift-virtualization)
* ### [Build your first Software Template for Backstage](/articles/2025/08/12/build-your-first-software-template-backstage)
* ### [How to build a simple agentic AI server with MCP](/articles/2025/08/12/how-build-simple-agentic-ai-server-mcp)
* ### [Boost AI efficiency with GPU autoscaling on OpenShift](/articles/2025/08/12/boost-ai-efficiency-gpu-autoscaling-openshift)
* ### [What's new in Red Hat OpenShift GitOps 1.17](/blog/2025/08/11/whats-new-red-hat-openshift-gitops-117)

## What’s up next?

[![Getting GitOps e-book card](/sites/default/files/styles/article_floated/public/GettingGitOps-card-image%20%281%29.png?itok=sON87uld)](/sites/default/files/GettingGitOps-card-image%20%281%29.png)

Learn how to navigate the complex world of modern container-based software development and distribution with *Getting GitOps: A Practical Platform with OpenShift, Argo CD, and Tekton*.

[Get the e-book](https://developers.redhat.com/e-books/getting-gitops-practical-platform-openshift-argo-cd-and-tekton)

[![Red Hat Developers logo](/themes/custom/rhdp_fe/images/branding/2023_RHDLogo_reverse.svg)](/)

[LinkedIn](https://www.linkedin.com/showcase/red-hat-developer)

[YouTube](https://www.youtube.com/channel/UC7noUdfWp-ukXUlAsJnSm-Q)

[Twitter](https://twitter.com/rhdevelopers)

[Facebook](https://www.facebook.com/redhatinc)

### Products

* [Red Hat Enterprise Linux](https://developers.redhat.com/products/rhel/overview)
* [Red Hat OpenShift](https://developers.redhat.com/products/openshift/overview)
* [Red Hat Ansible Automation Platform](https://developers.redhat.com/products/ansible/overview)

### Build

* [Developer Sandbox](https://developers.redhat.com/developer-sandbox)
* [Developer Tools](/topics/developer-tools)
* [Interactive Tutorials](https://developers.redhat.com/learn#assembly-id-70181)
* [API Catalog](https://developers.redhat.com/api-catalog/)

### Quicklinks

* [Learning Resources](/learn)
* [E-books](/e-books)
* [Cheat Sheets](/cheat-sheets)
* [Blog](/blog)
* [Events](/events)
* [Newsletter](/newsletter)

### Communicate

* [About us](https://developers.redhat.com/about)
* [Contact sales](https://developers.redhat.com/contact-sales)
* [Find a partner](https://catalog.redhat.com/partners/)
* [Report a website issue](/report_a_website_issue)
* [Site Status Dashboard](https://status.redhat.com/)
* [Report a security problem](https://access.redhat.com/security/team/contact/?extIdCarryOver=true&sc_cid=701f2000001OH6pAAG)

### RED HAT DEVELOPER

Build here. Go anywhere.

We serve the builders. The problem solvers who create careers with code.

Join us if you’re a developer, software engineer, web designer, front-end designer, UX designer, computer scientist, architect, tester, product manager, project manager or team lead.

[Sign me up](/register "Create a Red Hat Developer account")

### Red Hat legal and privacy links

* [About Red Hat](https://redhat.com/en/about/company)
* [Jobs](https://redhat.com/en/jobs)
* [Events](https://redhat.com/en/events)
* [Locations](https://redhat.com/en/about/office-locations)
* [Contact Red Hat](https://redhat.com/en/contact)
* [Red Hat Blog](https://redhat.com/en/blog)
* [Inclusion at Red Hat](https://www.redhat.com/en/about/our-culture/diversity-equity-inclusion)
* [Cool Stuff Store](https://coolstuff.redhat.com/)
* [Red Hat Summit](https://www.redhat.com/en/summit)

© 2025 Red Hat

### Red Hat legal and privacy links

* [Privacy statement](https://redhat.com/en/about/privacy-policy)
* [Terms of use](https://redhat.com/en/about/terms-use)
* [All policies and guidelines](https://redhat.com/en/about/all-policies-guidelines)
* [Digital accessibility](https://redhat.com/en/about/digital-accessibility)

## Report a website issue

Your name

Your e-mail address

Subject

Message

Type of request/issue

Download Issue - Logged in User can't get file
Content is wrong or missing from site
Learning Path trouble : Broken Instruqt
Learning Path trouble : Missing Content
Product Issue
Trouble registering for an event
I cannot log in
I cannot renew my subscription
I cannot sign up to the Red Hat Developer Program
Other

Problem Page URL

Country/Territory

-Please choose-
Canada
China
India
United States

American Samoa
Australia
Bangladesh
Bhutan
Brunei Darussalam
Cambodia
Christmas Island
Cocos (Keeling) Islands
Cook Islands
Fiji
Guam
Heard Island and McDonald Islands
Hong Kong
Indonesia
Japan
Kiribati
Korea, Republic of
Lao People's Democratic Republic
Macao
Malaysia
Maldives
Mongolia
Marshall Islands
Myanmar
Nauru
Nepal
New Zealand
Niue
Norfolk Island
Northern Mariana Islands
Palau
Papua New Guinea
Philippines
Samoa
Singapore
Solomon Islands
Sri Lanka
Thailand
Timor-Leste
Tokelau
Tonga
Tuvalu
Taiwan
Vanuatu
Viet Nam

Afghanistan
Aland Islands
Albania
Algeria
Andorra
Angola
Armenia
Aruba
Austria
Azerbaijan
Bahrain
Belarus
Belgium
Benin
Bermuda
Bosnia and Herzegovina
Botswana
Bouvet Island
British Indian Ocean Territory
Bulgaria
Burkina Faso
Burundi
Cameroon
Cape Verde
Central African Republic
Chad
Comoros
Congo
Congo, The Democratic Republic of the
Cote d'Ivoire
Croatia
Curacao
Cyprus
Czech Republic
Denmark
Djibouti
Egypt
Equatorial Guinea
Eritrea
Estonia
Ethiopia
Faroe Islands
Finland
France
French Polynesia
French Southern Territories
Gabon
Gambia
Georgia
Germany
Ghana
Gibraltar
Greece
Greenland
Guadeloupe
Guernsey
Guinea
Guinea-Bissau
Holy See (Vatican City State)
Hungary
Iceland
Iran, Islamic Republic of
Iraq
Ireland
Isle of Man
Israel
Italy
Jersey
Jordan
Kazakhstan
Kenya
Kuwait
Kyrgyzstan
Latvia
Lebanon
Lesotho
Liberia
Libyan Arab Jamahiriya
Liechtenstein
Lithuania
Luxembourg
Macedonia, The Former Yugoslav Republic of
Madagascar
Malawi
Mali
Malta
Martinique
Mauritania
Mauritius
Mayotte
Moldova, Republic of
Monaco
Montenegro
Morocco
Mozambique
Namibia
Netherlands
Netherlands Antilles
New Caledonia
Niger
Nigeria
Norway
Oman
Pakistan
Palestinian Territory, Occupied
Pitcairn
Poland
Portugal
Qatar
Reunion
Romania
Russian Federation
Rwanda
Saint Barthelemy
Saint Helena
Saint Martin (French part)
Saint Pierre and Miquelon
San Marino
Sao Tome and Principe
Saudi Arabia
Senegal
Serbia
Serbia and Montenegro
Seychelles
Sierra Leone
Sint Maarten
Slovakia
Slovenia
Somalia
South Africa
South Georgia and the South Sandwich Islands
South Sudan
Spain
Sudan
Svalbard and Jan Mayen
Swaziland
Sweden
Switzerland
Syrian Arab Republic
Tajikistan
Tanzania, United Republic of
Togo
Tunisia
Turkey
Turkmenistan
Uganda
Ukraine
United Arab Emirates
United Kingdom
Uzbekistan
Wallis and Futuna
Western Sahara
Yemen
Zaire
Zambia
Zimbabwe

Anguilla
Antigua and Barbuda
Argentina
Bahamas
Barbados
Belize
Bolivia
Brazil
Cayman Islands
Chile
Colombia
Costa Rica
Cuba
Dominica
Dominican Republic
Ecuador
El Salvador
Falkland Islands (Malvinas)
French Guiana
Grenada
Guatemala
Guyana
Haiti
Honduras
Jamaica
Mexico
Micronesia, Federated States of
Montserrat
Nicaragua
Panama
Paraguay
Peru
Puerto Rico
Saint Kitts and Nevis
Saint Lucia
Saint Vincent and the Grenadines
Suriname
Trinidad and Tobago
Turks and Caicos Islands
United States Minor Outlying Islands
Uruguay
Venezuela
Virgin Islands, British
Virgin Islands, U.S.

Red Hat Account Number

Red Hat Username
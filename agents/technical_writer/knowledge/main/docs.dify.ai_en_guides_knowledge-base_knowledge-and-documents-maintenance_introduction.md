<!-- Source: https://docs.dify.ai/en/guides/knowledge-base/knowledge-and-documents-maintenance/introduction -->

Manage Knowledge - Dify Docs

[Dify Docs home page![light logo](https://assets-docs.dify.ai/2025/05/d05cfc6ebe48f725d171dc71c64a5d16.svg)![dark logo](https://assets-docs.dify.ai/2025/05/c51f1cda47c1d9a4a162d7736f6e4c53.svg)](/)

English

Search...

⌘KAsk AI

* [Blog](https://dify.ai/blog)
* [Dify](https://cloud.dify.ai)
* [Dify](https://cloud.dify.ai)

Search...

Navigation

Manage Knowledge

Manage Knowledge

[Documentation](/en/introduction)[Plugin Development](/plugin-dev-en/0111-getting-started-dify-plugin)[API Access](/api-reference/chat/send-chat-message)[Resources](/en/resources/termbase)

##### Getting Started

* Welcome to Dify
* Dify Community
* [Dify Cloud](/en/getting-started/cloud)
* [Dify Premium on AWS](/en/getting-started/dify-premium)
* [Dify for Education](/en/getting-started/dify-for-education)
* [API Access](/en/openapi-api-access-readme)

##### Guide

* Model Configuration
* Application Orchestration
* Workflow
* Knowledge

  + [Knowledge](/en/guides/knowledge-base/readme)
  + Create Knowledge
  + Manage Knowledge

    - [Manage Knowledge](/en/guides/knowledge-base/knowledge-and-documents-maintenance/introduction)
    - [Maintain Documents](/en/guides/knowledge-base/knowledge-and-documents-maintenance/maintain-knowledge-documents)
    - [Maintain Knowledge via API](/en/guides/knowledge-base/knowledge-and-documents-maintenance/maintain-dataset-via-api)
  + [Metadata](/en/guides/knowledge-base/metadata)
  + [Integrate Knowledge Base within Application](/en/guides/knowledge-base/integrate-knowledge-within-application)
  + [Retrieval Test / Citation and Attributions](/en/guides/knowledge-base/retrieval-test-and-citation)
  + [Knowledge Request Rate Limit](/en/guides/knowledge-base/knowledge-request-rate-limit)
  + [Connect External Knowledge](/en/guides/knowledge-base/connect-external-knowledge-base)
  + [External Knowledge API](/en/guides/knowledge-base/external-knowledge-api)
* Publishing
* Annotation
* Monitoring
* Tools
* Collaboration
* Management

##### Workshop

* [Introduction](/en/workshop/README)
* Basic
* Intermediate

##### Community

* [Seek Support](/en/community/support)
* [Become a Contributor](/en/community/contribution)
* [Contributing to Dify Documentation](/en/community/docs-contribution)

##### Plugins

* [Introduction](/en/plugins/introduction)
* Quick Start
* [Manage Plugins](/en/plugins/manage-plugins)
* Schema Specification
* Best Practice
* Publish Plugins
* [FAQ](/en/plugins/faq)

##### Development

* Backend
* Models Integration
* Migration

##### Learn More

* Use Cases
* Extended Reading
* FAQ

##### Policies

* [License](/en/policies/open-source)
* User Agreement

On this page

* [View Linked Applications in the Knowledge Base](#view-linked-applications-in-the-knowledge-base)
* [Maintain Knowledge Documents](#maintain-knowledge-documents)
* [Maintain Knowledge Base Via API](#maintain-knowledge-base-via-api)

Manage Knowledge

# Manage Knowledge

Copy page

Copy page

The knowledge page is accessible only to the team owner, team administrators, and users with editor permissions.

Click the **Knowledge** button at the top of the Dify platform and select the knowledge you want to manage. Navigate to Settings in the left sidebar to configure it.
Here, you can modify the knowledge base’s name, description, permissions, indexing method, embedding model and retrieval settings.
![Knowledge base settings](https://assets-docs.dify.ai/2024/12/20fc93428f8f20f7acfce665c4ed4ddf.png)

* **Knowledge Name**: Used to distinguish among different knowledge bases.
* **Knowledge Description**: Used to describe the information represented by the documents in the knowledge base.
* **Permission**: Defines access control for the knowledge base with three levels:
  + **“Only Me”**: Restricts access to the knowledge base owner.
  + **“All team members”**: Grants access to every member of the team.
  + **“Partial team members”**: Allows selective access to specific team members.
    Users without appropriate permissions cannot access the knowledge base. When granting access to team members (Options 2 or 3), authorized users are granted full permissions, including the ability to view, edit, and delete knowledge base content.
* **Indexing Mode**: For detailed explanations, please refer to the [documentation](/en/guides/knowledge-base/create-knowledge-and-upload-documents/setting-indexing-methods).
* **Embedding Model**: Allows you to modify the embedding model for the knowledge base. Changing the embedding model will re-embed all documents in the knowledge base, and the original embeddings will be deleted.
* **Retrieval Settings**: For detailed explanations, please refer to the [documentation](/en/learn-more/extended-reading/retrieval-augment/retrieval).

---

## [​](#view-linked-applications-in-the-knowledge-base) View Linked Applications in the Knowledge Base

On the left side of the knowledge base, you can see all linked Apps. Hover over the circular icon to view the list of all linked apps. Click the jump button on the right to quickly browser them.
![Viewing the Linked Apps](https://assets-docs.dify.ai/2024/12/28899b9b0eba8996f364fb74e5b94c7f.png)
You can manage your knowledge base documents either through a web interface or via an API.

## [​](#maintain-knowledge-documents) Maintain Knowledge Documents

You can administer all documents and their corresponding chunks directly in the knowledge base. For more details, refer to the following documentation:
[## Maintain Knowledge Documents

Learn how to maintain knowledge documents](/en/guides/knowledge-base/knowledge-and-documents-maintenance/maintain-knowledge-documents)

## [​](#maintain-knowledge-base-via-api) Maintain Knowledge Base Via API

Dify Knowledge Base provides a comprehensive set of standard APIs. Developers can use these APIs to perform routine management and maintenance tasks, such as adding, deleting, updating, and retrieving documents and chunks. For more details, refer to the following documentation:
[## Maintain Knowledge Base via API

Learn how to maintain knowledge base via API](/en/guides/knowledge-base/knowledge-and-documents-maintenance/maintain-dataset-via-api)
![Knowledge base API management](https://assets-docs.dify.ai/dify-enterprise-mintlify/en/guides/knowledge-base/02cf8bc06990606ff1d60b73ce7a82c8.png)

---

[Edit this page](https://github.com/langgenius/dify-docs/edit/main/en/guides/knowledge-base/knowledge-and-documents-maintenance/introduction.mdx) | [Report an issue](https://github.com/langgenius/dify-docs/issues/new?template=docs.yml)

Was this page helpful?

YesNo

[3. Select the Indexing Method and Retrieval Setting](/en/guides/knowledge-base/create-knowledge-and-upload-documents/setting-indexing-methods)[Maintain Documents](/en/guides/knowledge-base/knowledge-and-documents-maintenance/maintain-knowledge-documents)

[x](https://x.com/dify_ai)[github](https://github.com/langgenius/dify-docs)[linkedin](https://www.linkedin.com/company/langgenius)

[Powered by Mintlify](https://mintlify.com/preview-request?utm_campaign=poweredBy&utm_medium=referral&utm_source=dify-6c0370d8)

Assistant

Responses are generated using AI and may contain mistakes.
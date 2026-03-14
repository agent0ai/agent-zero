# Business Workflow Templates

This document outlines the common business workflow templates added to Agent Jumbo's Workflow Engine. These templates are stored in the SQLite database and include best-practice stages and example prompts for the agent.

## 1. Strategic Content Marketing

**Type:** `marketing` | **Version:** `1.0.0`
Efficiently manage the content lifecycle from research to multi-channel distribution.

### Stages & Tasks

- **Strategy & Ideation**
  - *Topic & Keyword Research*: [Example Prompt] Perform keyword research for 'Enterprise AI Security' and identify top 5 trending sub-topics for Q1 2026.
  - *Create Content Brief*: [Example Prompt] Create a detailed content brief for a whitepaper on 'Zero Trust AI' including target persona, key message, and outline.
- **Content Production**
  - *Draft Core Content*: [Example Prompt] Draft a 2000-word deep-dive article based on the provided content brief.
  - *Generate Visual Assets*: [Example Prompt] Generate 3 DALL-E prompts to create isometric illustrations.
- **Distribution & Promotion**
  - *Social Media Repurposing*: [Example Prompt] Convert the core article into a 10-slide LinkedIn carousel and X posts.

---

## 2. Employee Onboarding (Standard)

**Type:** `hr` | **Version:** `1.1.0`
A structured approach to integrating new hires.

### Stages & Tasks

- **Pre-Arrival Logistics**
  - *IT & Access Setup*: [Example Prompt] Generate a checklist for setting up Git, Slack, and AWS access.
  - *Welcome Kit*: [Example Prompt] Draft a personalized welcome email for the new hire.
- **Orientation & Integration**
  - *Company Overview*: [Example Prompt] Present the company mission and 2026 roadmap.

---

## 3. Customer Support Escalation

**Type:** `support` | **Version:** `1.0.0`
Streamlined handling of complex technical issues.

### Stages & Tasks

- **Triage & Documentation**
  - *Issue Summary*: [Example Prompt] Summarize the customer's technical issue from the last 3 tickets.
- **Engineering Collaboration**
  - *Bug Report*: [Example Prompt] Draft a GitHub issue with clear reproduction steps and logs.

---

## 4. Monthly Financial Close

**Type:** `finance` | **Version:** `1.0.0`
Maintain accounting accuracy and regular executive reporting.

### Stages & Tasks

- **Account Reconciliation**
  - *Bank Statement Match*: [Example Prompt] Identify discrepancies between records and PDF statements.
- **Executive Reporting**
  - *P&L Analysis*: [Example Prompt] Analyze the P&L compared to the same month last year.

---
*Note: These templates are versioned and can be updated via the `workflow_engine` instrument.*

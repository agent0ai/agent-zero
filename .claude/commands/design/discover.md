---
description: Interactive customer discovery workflow - gather pain points, map workflows, and define requirements
argument-hint: "[customer-name] [--resume session-id] [--export pdf|json]"
allowed-tools:
  - Bash
  - Read
  - Write
---

# Design Discovery - Interactive Customer Discovery Workflow

**Estimated Time**: 30-45 minutes
**Purpose**: Comprehensive customer discovery to identify pain points, map workflows, and define requirements
**Output**: Structured discovery document ready for prototype generation

---

## EXECUTION PROTOCOL

This is an interactive session. I will guide you through 6 phases:

1. **Customer Information** - Basic project details
2. **Pain Point Elicitation** - Deep dive into problems
3. **Workflow Mapping** - Current vs. desired state
4. **Requirements Gathering** - Functional and non-functional needs
5. **Success Metrics** - Define measurable outcomes
6. **Summary & Approval** - Review and finalize

**Navigation Options**:

- Type "next" to proceed to next section
- Type "back" to return to previous section
- Type "skip" to skip a section (can return later)
- Type "save" to save draft and resume later
- Type "review" to see what's been captured so far

---

## SESSION MANAGEMENT

**Starting New Session**:

```bash
/design:discover "Acme Corp"
```

**Resuming Previous Session**:

```bash
/design:discover --resume acme-corp-2024-12-06
```

**Exporting Discovery**:

```bash
/design:discover --export pdf
/design:discover --export json
```

---

# PHASE 1: CUSTOMER INFORMATION

Let me gather basic information about this discovery session.

## Customer Details

**Question 1**: What is the customer's full company name?

- Example: "Acme Corporation" or "Acme Corp"
- This will be used for all documentation

**Question 2**: What is the project/initiative name?

- Example: "Lead Scoring System", "Customer Portal", "Internal Dashboard"
- Keep it descriptive but concise

**Question 3**: Primary contact information?

```
Name: [Full name of primary stakeholder]
Title: [Role/position]
Email: [Contact email]
Phone: [Optional]
```

**Question 4**: Who are the key stakeholders for this project?

- List names and roles of anyone who should be involved in decisions
- Examples: CEO, CTO, Head of Sales, Product Manager

```
1. [Name] - [Role] - [Department]
2. [Name] - [Role] - [Department]
3. [Name] - [Role] - [Department]
```

**Question 5**: What is your target timeline for this project?

- [ ] Urgent (< 1 month)
- [ ] Fast track (1-3 months)
- [ ] Standard (3-6 months)
- [ ] Long-term (6+ months)
- [ ] Flexible/TBD

**Question 6**: What is your estimated budget range?

- [ ] Under $10k
- [ ] $10k - $50k
- [ ] $50k - $100k
- [ ] $100k - $250k
- [ ] $250k+
- [ ] TBD/Flexible

---

### PHASE 1 SUMMARY

```
✓ Customer Information Captured

Company: [Customer Name]
Project: [Project Name]
Primary Contact: [Name] ([Title])
Stakeholders: [Count] identified
Timeline: [Selected timeline]
Budget: [Selected range]
```

**Ready to proceed to Phase 2: Pain Point Elicitation?**

- Type "next" to continue
- Type "edit" to modify any information

---

# PHASE 2: PAIN POINT ELICITATION

This is the most critical phase. I'll help you uncover the real problems that need solving.

## Core Pain Points Discovery

**Question 1**: What are the top 3 problems or challenges you're facing right now?

Please describe each problem in detail:

**Problem #1**:

```
Problem Title: [Short name]
Description: [What's happening? Why is it a problem?]
Who's Affected: [Which team/role/department?]
Frequency: [How often does this occur?]
  - Daily
  - Weekly
  - Monthly
  - Quarterly
  - Ad-hoc
```

**Problem #2**:

```
Problem Title: [Short name]
Description: [What's happening? Why is it a problem?]
Who's Affected: [Which team/role/department?]
Frequency: [How often does this occur?]
```

**Problem #3**:

```
Problem Title: [Short name]
Description: [What's happening? Why is it a problem?]
Who's Affected: [Which team/role/department?]
Frequency: [How often does this occur?]
```

---

## Quantifying Impact

For each problem identified, let's quantify the impact:

### Problem #1: [Title]

**Question 2a**: How much time does this problem cost you?

```
Time per incident: [X hours/minutes]
Frequency: [Y times per week/month]
People affected: [Z team members]

Total monthly time cost: [Calculated]
Annual time cost: [Calculated]
```

**Question 2b**: How much money does this problem cost you?

- Direct costs (lost revenue, wasted spend, etc.)
- Indirect costs (opportunity cost, delayed decisions, etc.)

```
Direct monthly cost: $[Amount]
Indirect monthly cost: $[Amount]
Total annual cost: $[Amount]
```

**Question 2c**: What's the impact on customer satisfaction/business outcomes?

- [ ] Critical - Losing customers/revenue
- [ ] High - Damaging customer relationships
- [ ] Medium - Creating friction/delays
- [ ] Low - Minor inconvenience

---

### Problem #2: [Title]

**Question 3a**: How much time does this problem cost you?

```
Time per incident: [X hours/minutes]
Frequency: [Y times per week/month]
People affected: [Z team members]

Total monthly time cost: [Calculated]
Annual time cost: [Calculated]
```

**Question 3b**: How much money does this problem cost you?

```
Direct monthly cost: $[Amount]
Indirect monthly cost: $[Amount]
Total annual cost: $[Amount]
```

**Question 3c**: What's the impact on customer satisfaction/business outcomes?

- [ ] Critical - Losing customers/revenue
- [ ] High - Damaging customer relationships
- [ ] Medium - Creating friction/delays
- [ ] Low - Minor inconvenience

---

### Problem #3: [Title]

**Question 4a**: How much time does this problem cost you?

```
Time per incident: [X hours/minutes]
Frequency: [Y times per week/month]
People affected: [Z team members]

Total monthly time cost: [Calculated]
Annual time cost: [Calculated]
```

**Question 4b**: How much money does this problem cost you?

```
Direct monthly cost: $[Amount]
Indirect monthly cost: $[Amount]
Total annual cost: $[Amount]
```

**Question 4c**: What's the impact on customer satisfaction/business outcomes?

- [ ] Critical - Losing customers/revenue
- [ ] High - Damaging customer relationships
- [ ] Medium - Creating friction/delays
- [ ] Low - Minor inconvenience

---

## Previous Solutions Attempted

**Question 5**: For each problem, what have you already tried to solve it?

### Problem #1: [Title]

```
Solutions Attempted:
1. [What did you try?]
   - Result: [What happened?]
   - Why it didn't work: [Root cause]

2. [What did you try?]
   - Result: [What happened?]
   - Why it didn't work: [Root cause]

Current Workaround:
[How are you managing this today?]
```

### Problem #2: [Title]

```
Solutions Attempted:
1. [What did you try?]
   - Result: [What happened?]
   - Why it didn't work: [Root cause]

Current Workaround:
[How are you managing this today?]
```

### Problem #3: [Title]

```
Solutions Attempted:
1. [What did you try?]
   - Result: [What happened?]
   - Why it didn't work: [Root cause]

Current Workaround:
[How are you managing this today?]
```

---

## Ideal Outcomes

**Question 6**: For each problem, what would the ideal outcome look like?

### Problem #1: [Title]

```
Ideal State:
[Describe the perfect solution - what happens? How does it feel? What changes?]

Success Looks Like:
- [Specific outcome 1]
- [Specific outcome 2]
- [Specific outcome 3]

Must-Have Features:
- [ ] [Feature 1]
- [ ] [Feature 2]
- [ ] [Feature 3]
```

### Problem #2: [Title]

```
Ideal State:
[Describe the perfect solution]

Success Looks Like:
- [Specific outcome 1]
- [Specific outcome 2]
- [Specific outcome 3]

Must-Have Features:
- [ ] [Feature 1]
- [ ] [Feature 2]
- [ ] [Feature 3]
```

### Problem #3: [Title]

```
Ideal State:
[Describe the perfect solution]

Success Looks Like:
- [Specific outcome 1]
- [Specific outcome 2]
- [Specific outcome 3]

Must-Have Features:
- [ ] [Feature 1]
- [ ] [Feature 2]
- [ ] [Feature 3]
```

---

## Additional Pain Points

**Question 7**: Are there any other problems worth mentioning?

- Type "yes" to add more problems (Problem #4, #5, etc.)
- Type "no" to proceed to summary

---

### PHASE 2 SUMMARY

```
✓ Pain Points Captured

Total Problems Identified: [Count]

Priority Ranking (by impact):
1. [Problem Title] - Annual Cost: $[X], Time: [Y hours]
2. [Problem Title] - Annual Cost: $[X], Time: [Y hours]
3. [Problem Title] - Annual Cost: $[X], Time: [Y hours]

Total Annual Cost of Problems: $[Sum]
Total Annual Time Lost: [Sum] hours

Solutions Previously Attempted: [Count]
Clear Ideal Outcomes Defined: [Yes/No for each]
```

**Ready to proceed to Phase 3: Workflow Mapping?**

- Type "next" to continue
- Type "edit" to modify pain points
- Type "review" to see full capture

---

# PHASE 3: WORKFLOW MAPPING

Now let's map the key workflows that are affected by these problems.

## Identifying Key Workflows

**Question 1**: What are the 3-5 most important workflows/processes in your business that relate to these pain points?

Examples:

- Lead qualification process
- Customer onboarding
- Invoice generation and payment
- Support ticket resolution
- Reporting and analytics

```
Workflow #1: [Name]
Workflow #2: [Name]
Workflow #3: [Name]
Workflow #4: [Name] (optional)
Workflow #5: [Name] (optional)
```

---

## Workflow Deep Dive

For each workflow, I'll ask about:

- Current state (how it works today)
- Desired state (how it should work)
- Bottlenecks (where the pain is)
- Time/cost savings potential

---

### Workflow #1: [Name]

**Current State Analysis**

**Question 2a**: How does this workflow work today? (Step-by-step)

```
Step 1: [Action] - Performed by: [Role] - Tools: [System/manual]
Step 2: [Action] - Performed by: [Role] - Tools: [System/manual]
Step 3: [Action] - Performed by: [Role] - Tools: [System/manual]
Step 4: [Action] - Performed by: [Role] - Tools: [System/manual]
Step 5: [Action] - Performed by: [Role] - Tools: [System/manual]
...
```

**Question 2b**: How many people are involved in this workflow?

```
Roles Involved:
- [Role 1]: [% of time spent on this workflow]
- [Role 2]: [% of time spent on this workflow]
- [Role 3]: [% of time spent on this workflow]
```

**Question 2c**: How long does this workflow take from start to finish?

```
Average Duration: [X hours/days]
Minimum Duration: [X hours/days]
Maximum Duration: [X hours/days]
Volume: [How many times per week/month?]
```

**Question 2d**: What are the bottlenecks in this workflow?

```
Bottleneck #1:
- Location: [Which step?]
- Cause: [Why does it slow down here?]
- Impact: [How much delay does this add?]

Bottleneck #2:
- Location: [Which step?]
- Cause: [Why does it slow down here?]
- Impact: [How much delay does this add?]
```

---

**Desired State Vision**

**Question 2e**: How should this workflow work in an ideal world?

```
Ideal Workflow:
Step 1: [Action] - Automation level: [Manual/Semi-auto/Fully auto]
Step 2: [Action] - Automation level: [Manual/Semi-auto/Fully auto]
Step 3: [Action] - Automation level: [Manual/Semi-auto/Fully auto]
...

Key Improvements:
- [What's different?]
- [What's eliminated?]
- [What's automated?]
```

**Question 2f**: What could be eliminated, automated, or streamlined?

```
Eliminate:
- [ ] [Step/task that adds no value]
- [ ] [Step/task that adds no value]

Automate:
- [ ] [Repetitive manual task]
- [ ] [Data entry/transfer]
- [ ] [Notifications/alerts]

Streamline:
- [ ] [Combine steps X and Y]
- [ ] [Reduce approval layers]
- [ ] [Integrate tools]
```

---

**Impact Quantification**

**Question 2g**: How much time could you save with the ideal workflow?

```
Current Time: [X hours/days per instance]
Ideal Time: [Y hours/days per instance]
Time Saved: [X - Y]

Volume: [Z instances per month]
Monthly Time Savings: [(X - Y) * Z]
Annual Time Savings: [Monthly * 12]

Cost of Time Saved: $[Annual hours * avg hourly rate]
```

**Question 2h**: What other benefits would the ideal workflow provide?

- [ ] Faster customer response times
- [ ] Reduced errors/rework
- [ ] Better data quality
- [ ] Improved compliance
- [ ] Increased capacity (can handle more volume)
- [ ] Better customer satisfaction
- [ ] Other: [Specify]

---

### Workflow #2: [Name]

**Current State Analysis**

**Question 3a**: How does this workflow work today? (Step-by-step)

```
Step 1: [Action] - Performed by: [Role] - Tools: [System/manual]
Step 2: [Action] - Performed by: [Role] - Tools: [System/manual]
...
```

**Question 3b**: How many people are involved?

```
Roles Involved:
- [Role]: [% of time]
...
```

**Question 3c**: Duration and volume?

```
Average Duration: [X]
Volume: [Y per month]
```

**Question 3d**: Bottlenecks?

```
Bottleneck #1: [Location] - [Cause] - [Impact]
Bottleneck #2: [Location] - [Cause] - [Impact]
```

**Desired State Vision**

**Question 3e**: Ideal workflow?

```
Ideal Workflow:
Step 1: [Action] - [Automation level]
Step 2: [Action] - [Automation level]
...
```

**Question 3f**: Improvements?

```
Eliminate: [List]
Automate: [List]
Streamline: [List]
```

**Impact Quantification**

**Question 3g**: Time savings?

```
Time Saved Per Instance: [X]
Annual Time Savings: [Y hours]
Cost Savings: $[Z]
```

**Question 3h**: Other benefits?

- [ ] [Benefit 1]
- [ ] [Benefit 2]
...

---

### Workflow #3: [Name]

**Current State Analysis**

**Question 4a**: How does this workflow work today?

```
[Step-by-step breakdown]
```

**Question 4b**: People involved?

```
[Roles and time %]
```

**Question 4c**: Duration/volume?

```
[Timing metrics]
```

**Question 4d**: Bottlenecks?

```
[Identified bottlenecks]
```

**Desired State Vision**

**Question 4e**: Ideal workflow?

```
[Ideal process]
```

**Question 4f**: Improvements?

```
[Eliminate/Automate/Streamline]
```

**Impact Quantification**

**Question 4g**: Time savings?

```
[Savings calculations]
```

**Question 4h**: Other benefits?

```
[Additional benefits]
```

---

### Workflow #4: [Name] (Optional)

[Repeat same question structure if applicable]

---

### Workflow #5: [Name] (Optional)

[Repeat same question structure if applicable]

---

### PHASE 3 SUMMARY

```
✓ Workflows Mapped

Total Workflows Analyzed: [Count]

Workflow Overview:
1. [Workflow Name]
   - Current Duration: [X]
   - Ideal Duration: [Y]
   - Time Savings: [Z hours/year]
   - Cost Savings: $[Amount]
   - Bottlenecks: [Count]

2. [Workflow Name]
   - Current Duration: [X]
   - Ideal Duration: [Y]
   - Time Savings: [Z hours/year]
   - Cost Savings: $[Amount]
   - Bottlenecks: [Count]

3. [Workflow Name]
   - Current Duration: [X]
   - Ideal Duration: [Y]
   - Time Savings: [Z hours/year]
   - Cost Savings: $[Amount]
   - Bottlenecks: [Count]

Total Annual Time Savings: [Sum] hours
Total Annual Cost Savings: $[Sum]

Automation Opportunities Identified: [Count]
Steps to Eliminate: [Count]
Steps to Streamline: [Count]
```

**Ready to proceed to Phase 4: Requirements Gathering?**

- Type "next" to continue
- Type "edit" to modify workflows
- Type "review" to see full capture

---

# PHASE 4: REQUIREMENTS GATHERING

Now let's translate pain points and workflows into specific requirements.

## Part A: Functional Requirements

These are the features and capabilities the solution must have.

**Question 1**: Let's create user stories for the key features needed.

I'll guide you through creating user stories in the format:
**"As a [role], I want [action] so that [benefit]"**

---

### User Story Template

For each pain point and workflow bottleneck, we'll create user stories:

**User Story #1**:

```
As a: [Role - who will use this feature?]
I want: [Action - what should the system do?]
So that: [Benefit - why is this valuable?]

Acceptance Criteria:
- [ ] [Specific condition that must be met]
- [ ] [Specific condition that must be met]
- [ ] [Specific condition that must be met]

Priority: [Must Have / Should Have / Nice to Have]

Related to:
- Pain Point: [Which problem does this solve?]
- Workflow: [Which workflow does this improve?]
```

---

**Let me suggest user stories based on your pain points...**

[System generates suggested user stories based on Phase 2 & 3 responses]

**Suggested User Story #1**:

```
As a: [Inferred role]
I want: [Inferred need from pain points]
So that: [Inferred benefit]

Acceptance Criteria:
- [ ] [Suggested criterion 1]
- [ ] [Suggested criterion 2]
- [ ] [Suggested criterion 3]

Priority: [Suggested - Must Have]
```

**Is this user story accurate?**

- Type "yes" to accept
- Type "edit" to modify
- Type "skip" to remove

---

**Question 2**: Let's categorize requirements by feature area.

Which feature areas are most important for this project?

**Core Feature Areas**:

- [ ] Dashboard & Reporting (data visualization, KPIs, analytics)
- [ ] Data Management (CRUD operations, import/export, bulk actions)
- [ ] Workflow Automation (triggered actions, notifications, approvals)
- [ ] User Management (roles, permissions, authentication)
- [ ] Integration (API, third-party tools, data sync)
- [ ] Communication (email, SMS, notifications, alerts)
- [ ] Configuration (settings, customization, preferences)
- [ ] Mobile Access (responsive design, mobile app, offline)
- [ ] Search & Filtering (advanced search, saved filters, faceted search)
- [ ] Collaboration (comments, sharing, team features)
- [ ] Other: [Specify]

---

### Feature Area: Dashboard & Reporting

**Question 3a**: What data needs to be visualized on the dashboard?

```
KPI Cards (key metrics displayed prominently):
1. [Metric Name] - [Format: number/currency/percentage/trend]
   - Source: [Where does this data come from?]
   - Update Frequency: [Real-time/hourly/daily/weekly]

2. [Metric Name] - [Format]
   - Source: [Data source]
   - Update Frequency: [Frequency]

3. [Metric Name] - [Format]
   - Source: [Data source]
   - Update Frequency: [Frequency]

Charts/Graphs Needed:
1. [Chart Type: line/bar/pie/scatter] - [What data?]
   - Time Range: [Last 7/30/90 days, YTD, custom]
   - Drill-down: [Can users click for details?]

2. [Chart Type] - [What data?]
   - Time Range: [Range]
   - Drill-down: [Yes/No]

Data Tables:
1. [Table Name] - [What records?]
   - Columns: [List key columns]
   - Sortable: [Yes/No]
   - Filterable: [Yes/No]
   - Actions: [What can users do? View/Edit/Delete/Export]
```

**Question 3b**: Who needs access to the dashboard?

```
Role: [Sales Manager]
- Can see: [Which KPIs/charts?]
- Can do: [View only / Export / Configure widgets]

Role: [Individual Contributor]
- Can see: [Which KPIs/charts?]
- Can do: [View only / Export / Configure widgets]

Role: [Executive]
- Can see: [Which KPIs/charts?]
- Can do: [View only / Export / Configure widgets]
```

**Question 3c**: What reports need to be generated?

```
Report #1: [Report Name]
- Format: [PDF/Excel/CSV]
- Frequency: [On-demand/Daily/Weekly/Monthly]
- Recipients: [Who receives it?]
- Data Included: [What's in the report?]

Report #2: [Report Name]
- Format: [PDF/Excel/CSV]
- Frequency: [On-demand/Daily/Weekly/Monthly]
- Recipients: [Who receives it?]
- Data Included: [What's in the report?]
```

---

### Feature Area: Data Management

**Question 4a**: What data entities need to be managed?

```
Entity #1: [Name - e.g., "Leads", "Customers", "Orders"]
- Fields: [List all fields needed]
  - [Field Name]: [Type: text/number/date/dropdown/etc.] - [Required/Optional]
  - [Field Name]: [Type] - [Required/Optional]

- Relationships: [How does this connect to other entities?]
  - Related to [Entity Name]: [One-to-many/Many-to-many]

- Business Rules:
  - [Rule 1: e.g., "Email must be unique"]
  - [Rule 2: e.g., "Status can't go from 'Closed' to 'Open'"]

Entity #2: [Name]
- Fields: [List]
- Relationships: [Connections]
- Business Rules: [Rules]

Entity #3: [Name]
- Fields: [List]
- Relationships: [Connections]
- Business Rules: [Rules]
```

**Question 4b**: What actions can users perform on this data?

```
For Entity: [Name]

Create:
- Who can create: [Roles]
- Required fields: [List]
- Validation rules: [What must be checked?]
- Triggers: [What happens after creation? Notifications? Workflows?]

Read/View:
- Who can view: [Roles]
- Default view: [List/Grid/Cards]
- Filters available: [What can users filter by?]
- Search: [What fields are searchable?]

Update:
- Who can update: [Roles]
- Which fields are editable: [List or "all except..."]
- Validation rules: [What must be checked?]
- Triggers: [What happens after update?]

Delete:
- Who can delete: [Roles]
- Soft delete or hard delete: [Which?]
- What happens to related data: [Cascade delete? Block delete?]
- Confirmation required: [Yes/No]

Bulk Actions:
- [ ] Bulk create (import from CSV/Excel)
- [ ] Bulk update (select multiple and update field)
- [ ] Bulk delete
- [ ] Bulk export
- [ ] Other: [Specify]
```

**Question 4c**: What import/export capabilities are needed?

```
Import:
- File formats: [CSV/Excel/JSON/API]
- Mapping: [Auto-map fields or manual mapping?]
- Duplicate handling: [Skip/Update/Create new]
- Validation: [What checks before import?]
- Volume: [How many records at once?]

Export:
- File formats: [CSV/Excel/PDF/JSON]
- Filters: [Can users export filtered data?]
- Scheduling: [One-time or recurring exports?]
- Delivery: [Download or email or cloud storage?]
```

---

### Feature Area: Workflow Automation

**Question 5a**: What workflows should be automated?

```
Automated Workflow #1: [Name]
Trigger: [What starts this workflow?]
  - [ ] Record created
  - [ ] Record updated (specific field changes)
  - [ ] Time-based (daily at 9am, weekly on Monday, etc.)
  - [ ] Manual trigger (button click)
  - [ ] External event (API webhook, email received, etc.)

Conditions: [When should this workflow run?]
  - IF [Field] [equals/contains/greater than] [Value]
  - AND/OR [Another condition]

Actions: [What should happen?]
  1. [Action: Update field, Send email, Create record, Call API, etc.]
  2. [Action]
  3. [Action]

Notifications: [Who should be notified?]
  - [Role/Person]: [Via email/SMS/in-app] when [Event]

Error Handling: [What if an action fails?]
  - [ ] Retry [X] times
  - [ ] Alert admin
  - [ ] Log error and continue
  - [ ] Stop workflow

Automated Workflow #2: [Name]
Trigger: [What starts it?]
Conditions: [When to run?]
Actions: [What happens?]
Notifications: [Who to notify?]
Error Handling: [How to handle failures?]
```

**Question 5b**: What approval workflows are needed?

```
Approval Workflow #1: [Name]
Triggered by: [What action requires approval?]

Approval Chain:
1. [Role/Person] - [Can approve/reject/send back]
   - Auto-approve if: [Condition, e.g., "amount < $1000"]
   - Timeout: [What happens if no response in X days?]

2. [Role/Person] - [Can approve/reject/send back]
   - Required if: [Condition]
   - Timeout: [Action]

Approval Actions:
- If approved: [What happens? Record updated, workflow continues, etc.]
- If rejected: [What happens? Notify requester, mark as rejected, etc.]
- If sent back: [Requester can revise and resubmit]

Notifications:
- Approval request: [Email/SMS/In-app to approver]
- Approved: [Notify requester and stakeholders]
- Rejected: [Notify requester with reason]
```

---

### Feature Area: User Management

**Question 6a**: What roles and permissions are needed?

```
Role #1: [Role Name - e.g., "Admin"]
Permissions:
  Dashboard & Reporting:
    - [ ] View dashboard
    - [ ] Configure dashboard
    - [ ] Export reports
    - [ ] Schedule reports

  Data Management:
    - [ ] Create [Entity Name]
    - [ ] View [Entity Name]
    - [ ] Update [Entity Name]
    - [ ] Delete [Entity Name]
    - [ ] Bulk import/export

  Workflow Automation:
    - [ ] Create workflows
    - [ ] Edit workflows
    - [ ] Enable/disable workflows

  User Management:
    - [ ] Create users
    - [ ] Edit users
    - [ ] Deactivate users
    - [ ] Assign roles

  System Settings:
    - [ ] Configure settings
    - [ ] Manage integrations
    - [ ] View audit logs

Role #2: [Role Name - e.g., "Manager"]
Permissions:
  [List permissions]

Role #3: [Role Name - e.g., "User"]
Permissions:
  [List permissions]
```

**Question 6b**: What authentication/security features are needed?

```
Authentication:
- [ ] Email/password login
- [ ] Single Sign-On (SSO) via [Google/Microsoft/Okta]
- [ ] Multi-factor authentication (MFA)
- [ ] Social login [Google/LinkedIn/GitHub]

Password Policy:
- Minimum length: [8/10/12 characters]
- Complexity: [Require uppercase/lowercase/numbers/symbols]
- Expiration: [Never/30/60/90 days]
- History: [Can't reuse last X passwords]

Session Management:
- Session timeout: [15/30/60 minutes of inactivity]
- Maximum concurrent sessions: [1/3/unlimited]
- Force logout on password change: [Yes/No]

Security Features:
- [ ] IP whitelisting
- [ ] Audit log (track all user actions)
- [ ] Data encryption at rest
- [ ] Data encryption in transit (HTTPS)
- [ ] GDPR compliance (data export, right to be forgotten)
- [ ] SOC 2 compliance
- [ ] HIPAA compliance
```

---

### Feature Area: Integration

**Question 7a**: What external systems need to integrate?

```
Integration #1: [System Name - e.g., "Zoho CRM"]
Direction: [One-way or Two-way sync]
Data Synced: [What data flows between systems?]
Frequency: [Real-time/Every 15 min/Hourly/Daily]
Mapping: [How do fields map between systems?]
Conflict Resolution: [If data differs, which system wins?]

Integration #2: [System Name]
Direction: [One-way/Two-way]
Data Synced: [What data?]
Frequency: [How often?]
Mapping: [Field mapping]
Conflict Resolution: [Resolution strategy]
```

**Question 7b**: What API capabilities are needed?

```
API Type: [REST/GraphQL/SOAP]

Endpoints Needed:
- [ ] GET /api/[entity] - List all records
- [ ] GET /api/[entity]/:id - Get single record
- [ ] POST /api/[entity] - Create record
- [ ] PUT /api/[entity]/:id - Update record
- [ ] DELETE /api/[entity]/:id - Delete record
- [ ] POST /api/[entity]/bulk - Bulk operations
- [ ] GET /api/[entity]/export - Export data
- [ ] POST /api/[entity]/import - Import data
- [ ] POST /api/workflows/:id/trigger - Trigger workflow

Authentication: [API Key/OAuth 2.0/JWT]
Rate Limiting: [X requests per minute/hour]
Webhooks: [Which events should trigger webhooks?]
  - [ ] Record created
  - [ ] Record updated
  - [ ] Record deleted
  - [ ] Workflow completed
```

---

### Feature Area: Communication

**Question 8a**: What communication features are needed?

```
Email:
- Send from: [System email or user email?]
- Templates: [List email templates needed]
  1. [Template Name] - [When sent?] - [To whom?]
  2. [Template Name] - [When sent?] - [To whom?]
- Personalization: [Merge fields needed]
- Tracking: [Track opens/clicks?]
- Scheduling: [Send immediately or schedule?]
- Attachments: [What files can be attached?]

SMS:
- Provider: [Zoho/Twilio/MessageBird]
- Templates: [List SMS templates needed]
- Character limit handling: [Truncate/Multiple messages]
- Opt-out handling: [How to handle unsubscribes?]
- Cost limit: [Cap spending at $X per month]

In-App Notifications:
- Types:
  - [ ] Success messages (record saved, workflow completed)
  - [ ] Error messages (validation failed, permission denied)
  - [ ] Warnings (approaching limit, action required)
  - [ ] Info (new feature, system maintenance)
- Persistence: [Dismiss/Stay until clicked/Auto-dismiss after X seconds]
- Notification center: [Can users view history?]

Push Notifications (Mobile):
- Events: [What triggers push notifications?]
- Frequency limits: [Max X per day to avoid spam]
```

---

## Part B: Non-Functional Requirements

These are the quality attributes and constraints the solution must meet.

**Question 9**: Performance Requirements

```
Response Time:
- Page load: [< 2 seconds / < 3 seconds / < 5 seconds]
- API response: [< 500ms / < 1 second / < 2 seconds]
- Search results: [< 1 second / < 2 seconds]
- Report generation: [< 10 seconds / < 30 seconds / < 1 minute]

Throughput:
- Concurrent users: [50 / 100 / 500 / 1000+]
- Transactions per second: [10 / 100 / 1000+]
- API requests per minute: [100 / 1000 / 10000+]

Data Volume:
- Total records: [10k / 100k / 1M / 10M+]
- Growth rate: [X new records per month]
- File upload size limit: [10MB / 50MB / 100MB / 500MB]

Uptime:
- Target availability: [99% / 99.9% / 99.99%]
- Acceptable downtime: [< 1 hour per month / < 4 hours per month]
- Maintenance window: [When can system be down for updates?]
```

**Question 10**: Security Requirements

```
Data Protection:
- [ ] Encryption at rest (database, file storage)
- [ ] Encryption in transit (HTTPS/TLS)
- [ ] Backup encryption
- [ ] Field-level encryption for sensitive data [specify fields]

Access Control:
- [ ] Role-based access control (RBAC)
- [ ] Row-level security (users only see their data)
- [ ] Column-level security (hide sensitive fields by role)
- [ ] IP whitelisting
- [ ] MFA for admin access
- [ ] MFA for all users

Compliance:
- [ ] GDPR (EU data privacy)
- [ ] HIPAA (healthcare data)
- [ ] PCI DSS (payment card data)
- [ ] SOC 2 (security audit)
- [ ] ISO 27001
- [ ] Other: [Specify]

Audit & Monitoring:
- [ ] Log all data access
- [ ] Log all data changes (who/what/when)
- [ ] Log all login attempts
- [ ] Log all admin actions
- [ ] Real-time security alerts
- [ ] Anomaly detection
- [ ] Log retention: [90 days / 1 year / 7 years]

Data Retention:
- Active data: [Keep for X years]
- Deleted data: [Soft delete, keep for X days]
- Backup retention: [Daily for 30 days, monthly for 1 year]
```

**Question 11**: Scalability Requirements

```
Growth Projection:
- Users in Year 1: [X]
- Users in Year 3: [Y]
- Data volume in Year 1: [X records]
- Data volume in Year 3: [Y records]

Scaling Strategy:
- [ ] Vertical scaling (bigger servers)
- [ ] Horizontal scaling (more servers, load balancing)
- [ ] Database sharding (split data across multiple databases)
- [ ] Caching layer (Redis, Memcached)
- [ ] CDN for static assets

Resource Limits:
- Max database size: [100GB / 500GB / 1TB / unlimited]
- Max file storage: [100GB / 1TB / 10TB / unlimited]
- Max API calls per account: [10k/day / 100k/day / unlimited]
```

**Question 12**: Reliability Requirements

```
Backup & Recovery:
- Backup frequency: [Hourly / Daily / Weekly]
- Backup retention: [30 days / 90 days / 1 year]
- Recovery Time Objective (RTO): [How quickly can we restore? 1 hour / 4 hours / 24 hours]
- Recovery Point Objective (RPO): [How much data can we lose? 15 min / 1 hour / 24 hours]
- Backup testing: [Test recovery monthly / quarterly]

Disaster Recovery:
- [ ] Multi-region deployment (failover to different geographic region)
- [ ] Automated failover
- [ ] Manual failover
- [ ] Disaster recovery plan documented
- [ ] DR drills quarterly

Error Handling:
- [ ] Graceful degradation (system still works with reduced functionality)
- [ ] User-friendly error messages
- [ ] Automatic retry for transient failures
- [ ] Error logging and alerting
- [ ] Rollback capability for failed deployments
```

**Question 13**: Usability Requirements

```
User Experience:
- [ ] Responsive design (works on mobile, tablet, desktop)
- [ ] Mobile-first design
- [ ] Native mobile app (iOS/Android)
- [ ] Progressive Web App (PWA)
- [ ] Offline capability
- [ ] Accessibility (WCAG 2.1 Level AA compliance)
- [ ] Multi-language support [List languages needed]
- [ ] Dark mode
- [ ] Customizable UI (themes, branding)

Learning Curve:
- Target time to productivity: [< 1 hour / < 1 day / < 1 week]
- Training required: [None / Video tutorials / Live training]
- Documentation: [In-app help / Knowledge base / User manual]

Help & Support:
- [ ] In-app contextual help
- [ ] Tooltips and guided tours
- [ ] Video tutorials
- [ ] Knowledge base / FAQ
- [ ] Live chat support
- [ ] Email support
- [ ] Phone support
- [ ] Community forum
```

**Question 14**: Maintainability Requirements

```
Code Quality:
- [ ] Code documentation
- [ ] Automated testing (unit, integration, E2E)
- [ ] Test coverage minimum: [70% / 80% / 90%]
- [ ] Code review required for all changes
- [ ] Linting and formatting standards
- [ ] Security scanning (SAST, DAST)

Deployment:
- [ ] Continuous Integration (CI)
- [ ] Continuous Deployment (CD)
- [ ] Automated rollback on failure
- [ ] Blue-green deployment
- [ ] Canary deployment
- [ ] Feature flags
- [ ] Zero-downtime deployments

Monitoring:
- [ ] Application performance monitoring (APM)
- [ ] Error tracking (Sentry, Rollbar)
- [ ] Log aggregation (ELK, Splunk)
- [ ] Uptime monitoring
- [ ] Real user monitoring (RUM)
- [ ] Synthetic monitoring
- [ ] Alerts for performance degradation
- [ ] Alerts for error spikes
```

---

### FUNCTIONAL REQUIREMENTS SUMMARY

```
✓ Functional Requirements Captured

User Stories Created: [Count]
  - Must Have: [Count]
  - Should Have: [Count]
  - Nice to Have: [Count]

Feature Areas Defined:
  ✓ Dashboard & Reporting: [Count] requirements
  ✓ Data Management: [Count] entities, [Count] actions
  ✓ Workflow Automation: [Count] automated workflows
  ✓ User Management: [Count] roles defined
  ✓ Integration: [Count] external systems
  ✓ Communication: [Count] templates
  ✓ [Other areas]: [Count] requirements

Total Functional Requirements: [Count]
```

---

### NON-FUNCTIONAL REQUIREMENTS SUMMARY

```
✓ Non-Functional Requirements Captured

Performance:
  - Page load: [< X seconds]
  - Concurrent users: [Y users]
  - Uptime target: [Z%]

Security:
  - Compliance: [GDPR/HIPAA/PCI/SOC2/None]
  - Encryption: [At rest/In transit/Both]
  - MFA: [Required/Optional/Not needed]
  - Audit logging: [Yes/No]

Scalability:
  - Year 1: [X users, Y records]
  - Year 3: [X users, Y records]
  - Scaling strategy: [Vertical/Horizontal/Both]

Reliability:
  - Backup frequency: [X]
  - RTO: [Y hours]
  - RPO: [Z hours]
  - Disaster recovery: [Yes/No]

Usability:
  - Responsive design: [Yes/No]
  - Mobile app: [Yes/No]
  - Accessibility: [WCAG level]
  - Multi-language: [Languages]

Maintainability:
  - Test coverage: [X%]
  - CI/CD: [Yes/No]
  - Monitoring: [Tools listed]
```

**Ready to proceed to Phase 5: Success Metrics?**

- Type "next" to continue
- Type "edit" to modify requirements
- Type "review" to see full capture

---

# PHASE 5: SUCCESS METRICS

Let's define how we'll measure the success of this project.

## SMART Goals

For each pain point and workflow improvement, let's create SMART goals:

- **S**pecific: What exactly will be achieved?
- **M**easurable: How will we know we've achieved it?
- **A**chievable: Is it realistic given constraints?
- **R**elevant: Does it align with business objectives?
- **T**ime-bound: When will it be achieved?

---

### Goal #1: [Related to Pain Point #1]

**Question 1a**: What is the specific goal?

```
Specific Goal: [e.g., "Reduce lead qualification time by 50%"]
```

**Question 1b**: How will we measure success?

```
Measurable Metrics:
- Metric 1: [e.g., "Average time to qualify a lead"]
  - Current baseline: [X hours]
  - Target: [Y hours]
  - Measurement method: [How to track?]

- Metric 2: [e.g., "Number of leads qualified per week"]
  - Current baseline: [X leads]
  - Target: [Y leads]
  - Measurement method: [How to track?]

- Metric 3: [Optional additional metric]
  - Current baseline: [X]
  - Target: [Y]
  - Measurement method: [How to track?]
```

**Question 1c**: Is this achievable?

```
Achievable because:
- [Reason 1: e.g., "Automation will eliminate 3 manual steps"]
- [Reason 2: e.g., "Similar companies have achieved this"]
- [Reason 3: e.g., "Team has capacity to adopt new process"]

Risks to achieving:
- [Risk 1: e.g., "User adoption may be slow"]
  - Mitigation: [How to address?]
- [Risk 2]
  - Mitigation: [How to address?]
```

**Question 1d**: Why is this relevant to the business?

```
Business Impact:
- [ ] Increases revenue by $[X]
- [ ] Reduces costs by $[X]
- [ ] Improves customer satisfaction (NPS +[X] points)
- [ ] Increases market share by [X%]
- [ ] Enables growth (handle [X%] more volume)
- [ ] Reduces risk/compliance issues
- [ ] Other: [Specify]

Strategic alignment:
[How does this support company strategy/vision?]
```

**Question 1e**: When will this be achieved?

```
Timeline:
- Phase 1 (MVP): [Date] - [What's included?]
  - Success criteria: [Metric target for MVP]

- Phase 2 (Full rollout): [Date] - [What's included?]
  - Success criteria: [Metric target for full rollout]

- Phase 3 (Optimization): [Date] - [What's included?]
  - Success criteria: [Final target metrics]

Checkpoints:
- 30 days after launch: [What to measure?]
- 60 days after launch: [What to measure?]
- 90 days after launch: [What to measure?]
```

---

### Goal #2: [Related to Pain Point #2]

**Question 2a**: Specific goal?

```
[Goal statement]
```

**Question 2b**: Measurable metrics?

```
Metric 1: [Name] - Current: [X], Target: [Y]
Metric 2: [Name] - Current: [X], Target: [Y]
Metric 3: [Name] - Current: [X], Target: [Y]
```

**Question 2c**: Achievable?

```
Achievable because: [Reasons]
Risks: [List and mitigations]
```

**Question 2d**: Relevance?

```
Business Impact: [How it helps]
Strategic alignment: [Why it matters]
```

**Question 2e**: Timeline?

```
Phase 1: [Date] - [Criteria]
Phase 2: [Date] - [Criteria]
Phase 3: [Date] - [Criteria]
```

---

### Goal #3: [Related to Pain Point #3]

[Repeat SMART goal structure]

---

## Leading vs. Lagging Indicators

**Question 3**: What are the leading indicators we can track?

Leading indicators predict future success (early warning signals):

```
Leading Indicator #1: [e.g., "Daily active users"]
- Why it matters: [Predicts long-term adoption]
- Target: [X users per day]
- Review frequency: [Daily/Weekly]

Leading Indicator #2: [e.g., "Feature usage rate"]
- Why it matters: [Shows value realization]
- Target: [X% of users using key features]
- Review frequency: [Weekly]

Leading Indicator #3: [e.g., "User feedback score"]
- Why it matters: [Early signal of satisfaction]
- Target: [4.5/5 or higher]
- Review frequency: [Weekly]
```

**Question 4**: What are the lagging indicators we'll measure?

Lagging indicators show results after the fact (outcome metrics):

```
Lagging Indicator #1: [e.g., "Total time saved per month"]
- Target: [X hours saved]
- Review frequency: [Monthly]

Lagging Indicator #2: [e.g., "Cost savings"]
- Target: $[X] saved per month
- Review frequency: [Monthly]

Lagging Indicator #3: [e.g., "Customer satisfaction (NPS)"]
- Target: [Score]
- Review frequency: [Quarterly]
```

---

## Acceptance Criteria

**Question 5**: What must be true for the project to be considered successful?

```
Go-Live Acceptance Criteria:
(Must be met before project can launch)

Technical Criteria:
- [ ] All must-have features implemented and tested
- [ ] Performance meets targets (page load < X seconds)
- [ ] Security audit passed
- [ ] Data migration completed (if applicable)
- [ ] Integration testing passed
- [ ] User acceptance testing (UAT) passed
- [ ] Load testing passed ([X] concurrent users)
- [ ] Backup and recovery tested
- [ ] Monitoring and alerts configured
- [ ] Documentation complete

Business Criteria:
- [ ] [X]% of users trained
- [ ] Executive sponsor approval
- [ ] Budget approved for ongoing operations
- [ ] Support team ready
- [ ] Communication plan executed
- [ ] Change management plan executed

Post-Launch Success Criteria:
(Must be met within 90 days of launch)

Adoption:
- [ ] [X]% of target users actively using system
- [ ] [X]% of key workflows migrated to new system
- [ ] Legacy system decommissioned (if applicable)

Performance:
- [ ] [Metric 1] meets or exceeds target
- [ ] [Metric 2] meets or exceeds target
- [ ] [Metric 3] meets or exceeds target

Satisfaction:
- [ ] User satisfaction score > [X]
- [ ] Support ticket volume < [Y] per week
- [ ] No critical bugs open for > 24 hours
```

---

## Dashboard & Reporting

**Question 6**: How will we track and report on these metrics?

```
Success Dashboard:
- Location: [Where will stakeholders view this?]
- Update frequency: [Real-time/Daily/Weekly]
- Access: [Who can view?]

KPIs on Dashboard:
1. [KPI Name]
   - Visualization: [Number/Chart/Gauge/Trend]
   - Target line: [Show goal]
   - Current value: [Live data]

2. [KPI Name]
   - Visualization: [Type]
   - Target line: [Show goal]
   - Current value: [Live data]

3. [KPI Name]
   - Visualization: [Type]
   - Target line: [Show goal]
   - Current value: [Live data]

Regular Reports:
- Weekly: [What's included? Who receives?]
- Monthly: [What's included? Who receives?]
- Quarterly: [What's included? Who receives?]

Stakeholder Communication:
- Executive summary: [When? To whom?]
- Team updates: [When? To whom?]
- All-hands presentation: [When?]
```

---

### PHASE 5 SUMMARY

```
✓ Success Metrics Defined

SMART Goals Created: [Count]
  Goal 1: [Name] - Target: [Metric]
  Goal 2: [Name] - Target: [Metric]
  Goal 3: [Name] - Target: [Metric]

Leading Indicators: [Count]
  - [Indicator 1]: [Target]
  - [Indicator 2]: [Target]
  - [Indicator 3]: [Target]

Lagging Indicators: [Count]
  - [Indicator 1]: [Target]
  - [Indicator 2]: [Target]
  - [Indicator 3]: [Target]

Go-Live Acceptance Criteria: [Count] items
Post-Launch Success Criteria: [Count] items

Projected ROI:
  - Annual time savings: [X hours]
  - Annual cost savings: $[Y]
  - Implementation cost: $[Z]
  - Payback period: [W months]
  - 3-year ROI: [%]
```

**Ready to proceed to Phase 6: Summary & Approval?**

- Type "next" to continue
- Type "edit" to modify success metrics
- Type "review" to see full capture

---

# PHASE 6: SUMMARY & APPROVAL

Let me compile everything we've captured into a comprehensive discovery summary.

---

## COMPLETE DISCOVERY SUMMARY

### Project Overview

```
Customer: [Company Name]
Project: [Project Name]
Primary Contact: [Name] ([Title])
Discovery Date: [Date]
Session Duration: [X minutes]

Key Stakeholders:
1. [Name] - [Role]
2. [Name] - [Role]
3. [Name] - [Role]

Timeline: [Selected timeline]
Budget: [Selected range]
```

---

### Executive Summary

```
PROBLEM STATEMENT:
[Company Name] is facing [X] critical business challenges that are costing
$[Y] annually and consuming [Z] hours of productivity. The primary pain points are:
1. [Pain Point 1] - Annual cost: $[X]
2. [Pain Point 2] - Annual cost: $[X]
3. [Pain Point 3] - Annual cost: $[X]

PROPOSED SOLUTION:
Implement a comprehensive [solution type] that will:
- [Key capability 1]
- [Key capability 2]
- [Key capability 3]

EXPECTED OUTCOMES:
- Reduce [metric] by [X%]
- Save $[Y] annually
- Improve [metric] by [X%]
- Enable growth of [X%]

ROI PROJECTION:
- Implementation cost: $[X]
- Annual savings: $[Y]
- Payback period: [Z] months
- 3-year ROI: [%]
```

---

### Pain Points Summary

```
Total Pain Points Identified: [Count]

#1: [Pain Point Title]
- Impact: [Critical/High/Medium/Low]
- Annual Cost: $[X]
- Annual Time Lost: [Y] hours
- Affected Teams: [Departments/roles]
- Current Workaround: [Description]
- Ideal Outcome: [Description]

#2: [Pain Point Title]
- Impact: [Level]
- Annual Cost: $[X]
- Annual Time Lost: [Y] hours
- Affected Teams: [Departments/roles]
- Current Workaround: [Description]
- Ideal Outcome: [Description]

#3: [Pain Point Title]
- Impact: [Level]
- Annual Cost: $[X]
- Annual Time Lost: [Y] hours
- Affected Teams: [Departments/roles]
- Current Workaround: [Description]
- Ideal Outcome: [Description]

TOTAL ANNUAL COST OF PROBLEMS: $[Sum]
TOTAL ANNUAL TIME LOST: [Sum] hours
```

---

### Workflow Analysis

```
Workflows Mapped: [Count]

Workflow #1: [Name]
- Current Duration: [X hours/days]
- Ideal Duration: [Y hours/days]
- Time Savings: [Z%]
- Bottlenecks: [Count]
- Annual Hours Saved: [X]
- Annual Cost Saved: $[Y]

Workflow #2: [Name]
- Current Duration: [X hours/days]
- Ideal Duration: [Y hours/days]
- Time Savings: [Z%]
- Bottlenecks: [Count]
- Annual Hours Saved: [X]
- Annual Cost Saved: $[Y]

Workflow #3: [Name]
- Current Duration: [X hours/days]
- Ideal Duration: [Y hours/days]
- Time Savings: [Z%]
- Bottlenecks: [Count]
- Annual Hours Saved: [X]
- Annual Cost Saved: $[Y]

TOTAL WORKFLOW IMPROVEMENTS:
- Total time saved annually: [X] hours
- Total cost saved annually: $[Y]
- Automation opportunities: [Count]
- Steps to eliminate: [Count]
```

---

### Requirements Summary

```
FUNCTIONAL REQUIREMENTS: [Total Count]

Must Have (Critical): [Count]
- [Requirement 1]
- [Requirement 2]
- [Requirement 3]
... (top 10 shown)

Should Have (Important): [Count]
- [Requirement 1]
- [Requirement 2]
... (top 5 shown)

Nice to Have (Desired): [Count]
- [Requirement 1]
- [Requirement 2]
... (top 3 shown)

Feature Areas:
✓ Dashboard & Reporting: [Count] requirements
✓ Data Management: [Count] entities, [Count] actions
✓ Workflow Automation: [Count] workflows
✓ User Management: [Count] roles
✓ Integration: [Count] external systems
✓ Communication: [Count] templates

NON-FUNCTIONAL REQUIREMENTS:

Performance:
- Page load: [< X seconds]
- Concurrent users: [Y]
- Uptime target: [Z%]

Security:
- Compliance: [GDPR/HIPAA/PCI/SOC2/None]
- Encryption: [Yes/No]
- MFA: [Yes/No]
- Audit logging: [Yes/No]

Scalability:
- Year 1: [X users, Y records]
- Year 3: [X users, Y records]

Reliability:
- Backup: [Frequency]
- RTO: [X hours]
- RPO: [Y hours]
```

---

### Success Metrics

```
SMART GOALS: [Count]

Goal #1: [Description]
- Metric: [Name]
- Current: [X]
- Target: [Y]
- Timeline: [Date]

Goal #2: [Description]
- Metric: [Name]
- Current: [X]
- Target: [Y]
- Timeline: [Date]

Goal #3: [Description]
- Metric: [Name]
- Current: [X]
- Target: [Y]
- Timeline: [Date]

ACCEPTANCE CRITERIA:
- Go-Live: [Count] items must be met
- Post-Launch (90 days): [Count] items must be met

ROI PROJECTION:
- Annual time savings: [X] hours ($[Y] value)
- Annual cost savings: $[Z]
- Total annual benefit: $[Y + Z]
- Implementation cost: $[A]
- Payback period: [B] months
- 3-year ROI: [C]%
```

---

## DISCOVERY COMPLETENESS CHECK

```
✓ Phase 1: Customer Information - [100%] complete
  ✓ Company details
  ✓ Stakeholders identified
  ✓ Timeline and budget discussed

✓ Phase 2: Pain Point Elicitation - [100%] complete
  ✓ [X] pain points identified
  ✓ Impact quantified (time and cost)
  ✓ Previous solutions documented
  ✓ Ideal outcomes defined

✓ Phase 3: Workflow Mapping - [100%] complete
  ✓ [X] workflows analyzed
  ✓ Current state documented
  ✓ Desired state defined
  ✓ Bottlenecks identified
  ✓ Savings calculated

✓ Phase 4: Requirements Gathering - [100%] complete
  ✓ [X] functional requirements
  ✓ [Y] non-functional requirements
  ✓ Priorities assigned
  ✓ Acceptance criteria defined

✓ Phase 5: Success Metrics - [100%] complete
  ✓ [X] SMART goals defined
  ✓ Leading indicators identified
  ✓ Lagging indicators identified
  ✓ ROI calculated

OVERALL COMPLETENESS: [100%]
```

---

## NEXT STEPS

```
1. Customer Review
   - Please review this discovery summary
   - Identify any corrections or additions needed
   - Confirm accuracy of all captured information

2. Stakeholder Approval
   - Share with key stakeholders: [List names]
   - Obtain sign-off from: [Primary decision maker]
   - Address any questions or concerns

3. Discovery Sign-Off
   - Formal approval required to proceed
   - Signature: [Name], [Title], [Date]
   - Approved budget: $[Amount]

4. Proceed to Prototype
   - Once approved, we'll create interactive prototypes
   - Prototypes will visualize the proposed solution
   - Demo data will simulate real-world usage
   - Command: /design:prototype [discovery-id]

5. Technical Design
   - After prototype approval, we'll create technical specs
   - Architecture, database design, API design
   - Development plan and timeline
```

---

## APPROVAL WORKFLOW

**Question 1**: Is this discovery summary accurate and complete?

- Type "yes" to approve
- Type "edit [section]" to make changes
- Type "review [section]" to re-read a specific section

**Question 2**: Do you have any questions or concerns?
[Open field for customer feedback]

**Question 3**: Are you ready to proceed to sign-off?

- Type "yes" to proceed to sign-off
- Type "no" to save as draft and return later

---

## FINAL SIGN-OFF

```
DISCOVERY APPROVAL

I, [Name], [Title] at [Company], hereby approve this discovery summary
and authorize proceeding to the prototype phase.

I confirm that:
✓ All pain points have been accurately captured
✓ All workflows have been correctly mapped
✓ All requirements reflect our needs
✓ Success metrics are aligned with business goals
✓ Budget and timeline are acceptable

Approved by: [Name]
Title: [Title]
Company: [Company Name]
Date: [Date]
Signature: [Digital signature]

Discovery ID: [auto-generated-id]
Next Step: Prototype Generation
Command: /design:prototype [discovery-id]
```

---

## SAVING DISCOVERY TO DATABASE

**Calling API**: POST /api/discovery

```json
{
  "customer": {
    "company_name": "[Company Name]",
    "project_name": "[Project Name]",
    "primary_contact": {
      "name": "[Name]",
      "title": "[Title]",
      "email": "[Email]",
      "phone": "[Phone]"
    },
    "stakeholders": [
      {"name": "[Name]", "role": "[Role]", "department": "[Dept]"}
    ],
    "timeline": "[Timeline]",
    "budget": "[Budget Range]"
  },
  "pain_points": [
    {
      "title": "[Title]",
      "description": "[Description]",
      "impact_level": "[Critical/High/Medium/Low]",
      "annual_cost": 0,
      "annual_time_lost_hours": 0,
      "affected_teams": ["[Team]"],
      "current_workaround": "[Description]",
      "ideal_outcome": "[Description]",
      "previous_solutions": ["[Solution]"]
    }
  ],
  "workflows": [
    {
      "name": "[Workflow Name]",
      "current_duration_hours": 0,
      "ideal_duration_hours": 0,
      "time_savings_percent": 0,
      "bottlenecks": [
        {"location": "[Step]", "cause": "[Cause]", "impact": "[Impact]"}
      ],
      "annual_hours_saved": 0,
      "annual_cost_saved": 0,
      "current_steps": ["[Step]"],
      "ideal_steps": ["[Step]"],
      "automation_opportunities": ["[Opportunity]"]
    }
  ],
  "requirements": {
    "functional": [
      {
        "user_story": "As a [role], I want [action] so that [benefit]",
        "acceptance_criteria": ["[Criterion]"],
        "priority": "must_have|should_have|nice_to_have",
        "feature_area": "[Area]"
      }
    ],
    "non_functional": {
      "performance": {
        "page_load_seconds": 0,
        "concurrent_users": 0,
        "uptime_percent": 0
      },
      "security": {
        "compliance": ["[GDPR/HIPAA/PCI/SOC2]"],
        "encryption": true,
        "mfa": true,
        "audit_logging": true
      },
      "scalability": {
        "year1_users": 0,
        "year3_users": 0,
        "year1_records": 0,
        "year3_records": 0
      },
      "reliability": {
        "backup_frequency": "[Frequency]",
        "rto_hours": 0,
        "rpo_hours": 0
      }
    }
  },
  "success_metrics": {
    "smart_goals": [
      {
        "description": "[Goal]",
        "metric_name": "[Metric]",
        "current_value": 0,
        "target_value": 0,
        "timeline": "[Date]",
        "business_impact": "[Impact]"
      }
    ],
    "leading_indicators": [
      {"name": "[Name]", "target": "[Target]", "frequency": "[Frequency]"}
    ],
    "lagging_indicators": [
      {"name": "[Name]", "target": "[Target]", "frequency": "[Frequency]"}
    ],
    "acceptance_criteria": {
      "go_live": ["[Criterion]"],
      "post_launch": ["[Criterion]"]
    }
  },
  "roi": {
    "annual_time_savings_hours": 0,
    "annual_cost_savings": 0,
    "implementation_cost": 0,
    "payback_period_months": 0,
    "three_year_roi_percent": 0
  },
  "approval": {
    "approved_by": "[Name]",
    "title": "[Title]",
    "date": "[Date]",
    "status": "approved"
  },
  "created_at": "[ISO DateTime]",
  "updated_at": "[ISO DateTime]"
}
```

---

## SUCCESS MESSAGE

```
✅ Discovery Complete and Saved!

Discovery ID: [generated-id]
Customer: [Company Name]
Project: [Project Name]

Summary:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pain Points Identified: [X]
Workflows Mapped: [Y]
Requirements Captured: [Z]
  - Functional: [A] (Must Have: [B], Should Have: [C], Nice to Have: [D])
  - Non-Functional: [E]

Success Metrics:
  - SMART Goals: [F]
  - Leading Indicators: [G]
  - Lagging Indicators: [H]

ROI Projection:
  - Annual Savings: $[X]
  - Implementation Cost: $[Y]
  - Payback Period: [Z] months
  - 3-Year ROI: [A]%

Status: ✅ APPROVED
Approved By: [Name] on [Date]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Next Steps:
1. Generate Prototype
   Command: /design:prototype [discovery-id]

2. View Discovery
   URL: /discoveries/[discovery-id]

3. Export Discovery
   PDF: /downloads/discovery-[discovery-id].pdf
   JSON: /downloads/discovery-[discovery-id].json

🎉 Ready to create your prototype!
```

---

## SESSION MANAGEMENT

**Save Draft** (if not yet approved):

```bash
# Session saved to: .claude/discovery-drafts/[discovery-id].json
# Resume with: /design:discover --resume [discovery-id]
```

**Export Options**:

```bash
# Export to PDF
/design:discover --export pdf [discovery-id]
# Output: /downloads/discovery-[discovery-id].pdf

# Export to JSON
/design:discover --export json [discovery-id]
# Output: /downloads/discovery-[discovery-id].json
```

---

## END OF DISCOVERY WORKFLOW

This discovery session is complete. The data has been saved and is ready for prototype generation.

**What would you like to do next?**

- Generate prototype: `/design:prototype [discovery-id]`
- View all discoveries: `/design:list-discoveries`
- Export discovery: `/design:discover --export pdf [discovery-id]`
- Create new discovery: `/design:discover "[New Customer Name]"`

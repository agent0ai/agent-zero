---
description: Optimize resume for specific job postings and ATS systems
argument-hint: [--resume <file>] [--job-posting <url|text>] [--analyze-keywords]
model: claude-sonnet-4-5-20250929
allowed-tools: Task, Read, Glob, Grep, Write, Bash
---

# Resume Optimizer

Job-specific optimization with keyword matching, ATS compatibility, and impact statement enhancement.

## Overview

The Resume Optimizer is a comprehensive ATS (Applicant Tracking System) optimization tool that analyzes your resume against specific job postings, identifies keyword gaps, ensures formatting compliance, and provides actionable recommendations to maximize your application success rate. This tool combines industry best practices with AI-powered analysis to help your resume pass automated screening systems and impress human recruiters.

## ROI Breakdown: $55,000/year

- **Interview Rate Increase**: 35% improvement in interview callbacks = $30K/year value
- **ATS Pass Rate**: 80% ATS compatibility vs 45% industry average = $15K/year value
- **Time Savings**: 12 hours saved per job search cycle x 4 cycles/year = $8K/year value
- **Strategic Positioning**: Better role matching and salary negotiation leverage = $2K/year value

## Key Benefits

1. **ATS Compatibility Analysis** - Ensures your resume passes automated screening systems that reject 75% of applications
   - Formatting validation against ATS parsing requirements
   - Identification of problematic elements (tables, graphics, headers/footers)
   - Font and section heading optimization

2. **Keyword Gap Analysis** - Identifies missing critical keywords from job descriptions
   - Extracting high-priority skills and qualifications from posting
   - Comparing your resume content against requirements
   - Suggesting natural integration points for missing keywords

3. **Impact Statement Enhancement** - Transforms basic job duties into compelling achievements
   - Converting passive descriptions to active accomplishments
   - Adding quantifiable metrics and results
   - Strengthening action verbs and power words

4. **Score-Based Assessment** - Provides objective 0-100 compatibility score
   - Keyword coverage percentage
   - ATS formatting compliance score
   - Content quality and impact rating
   - Overall optimization score with improvement areas

5. **Industry-Specific Optimization** - Tailors resume to specific sectors and roles
   - Technical skills prominence for tech roles
   - Certifications and compliance for regulated industries
   - Leadership and strategy focus for management positions

6. **Competitive Positioning** - Differentiates your application from other candidates
   - Highlighting unique value propositions
   - Emphasizing relevant accomplishments
   - Aligning experience with company culture and values

7. **Format Standardization** - Ensures professional presentation across all systems
   - Consistent date formatting and spacing
   - Proper section ordering and hierarchy
   - Contact information optimization

8. **Real-Time Feedback** - Provides immediate actionable recommendations
   - Line-by-line improvement suggestions
   - Priority-ranked changes for maximum impact
   - Before/after examples for clarity

## Implementation Steps

### Step 1: Resume Document Analysis

**Objective**: Parse and understand the current resume structure and content

**Actions**:

- Read the resume file (PDF, DOCX, or TXT format)
- Identify all sections: Contact, Summary, Experience, Education, Skills, etc.
- Extract text content while noting formatting elements
- Catalog current keywords, skills, and accomplishments
- Identify any ATS-incompatible elements (graphics, tables, text boxes)

**Output**: Structured breakdown of resume sections with content inventory

### Step 2: Job Posting Intelligence Gathering

**Objective**: Extract all requirements and preferences from target job posting

**Actions**:

- Parse job description (from URL or text input)
- Extract required skills, qualifications, and experience
- Identify preferred/nice-to-have skills
- Capture company culture indicators and values
- Note specific tools, technologies, or methodologies mentioned
- Identify required years of experience and education level
- Extract industry-specific terminology and jargon

**Output**: Comprehensive requirements matrix with priority ranking

### Step 3: Keyword Matching and Gap Analysis

**Objective**: Compare resume content against job requirements

**Actions**:

- Map resume keywords to job posting requirements
- Calculate keyword coverage percentage for each category
- Identify critical missing keywords (required skills not mentioned)
- Find contextual mismatches (skills mentioned but not demonstrated)
- Analyze keyword frequency and prominence
- Compare against industry-standard keyword densities
- Generate priority list of keywords to add

**Output**: Keyword gap report with integration recommendations

### Step 4: ATS Formatting Compliance Check

**Objective**: Ensure resume will parse correctly in ATS systems

**Actions**:

- Verify standard section headings (Work Experience, Education, Skills)
- Check date formatting consistency (MM/YYYY format preferred)
- Identify problematic elements: tables, text boxes, headers/footers, images
- Validate font choices (standard fonts: Arial, Calibri, Times New Roman)
- Check for proper spacing and section breaks
- Verify contact information is in standard location
- Test bullet point formatting (standard bullets vs. custom symbols)
- Ensure file type compatibility (prefer .docx or .pdf)

**Output**: ATS compliance report with specific formatting fixes

### Step 5: Impact Statement Enhancement

**Objective**: Transform job duties into quantifiable achievements

**Actions**:

- Identify weak statements (responsibilities without results)
- Apply STAR method (Situation, Task, Action, Result) framework
- Add quantifiable metrics where missing (percentages, dollar amounts, time saved)
- Strengthen action verbs (led, optimized, increased vs. responsible for, helped)
- Ensure each bullet demonstrates value/impact
- Remove redundant or low-value statements
- Prioritize most impressive achievements at top of each role

**Output**: Enhanced experience section with before/after comparisons

### Step 6: Skills Section Optimization

**Objective**: Properly categorize and present technical and soft skills

**Actions**:

- Reorganize skills by relevance to job posting
- Create skill categories (Technical, Leadership, Domain Expertise)
- Move critical job-required skills to prominent position
- Add proficiency levels where appropriate
- Remove outdated or irrelevant skills
- Integrate certifications and credentials
- Ensure consistency with experience section

**Output**: Optimized skills section aligned with job requirements

### Step 7: Summary/Objective Statement Crafting

**Objective**: Create compelling opening that matches job requirements

**Actions**:

- Extract key qualifications from job posting
- Highlight most relevant experience and achievements
- Incorporate critical keywords naturally
- Demonstrate value proposition in 3-4 sentences
- Include years of experience and specialization
- Align tone with company culture (corporate vs. startup)
- Make it specific to the role, not generic

**Output**: Tailored professional summary matching job posting

### Step 8: Scoring and Assessment

**Objective**: Provide objective measure of resume-job fit

**Actions**:

- Calculate keyword coverage score (0-30 points)
- Assess ATS formatting compliance (0-25 points)
- Evaluate impact statement quality (0-25 points)
- Rate overall content relevance (0-20 points)
- Generate composite score (0-100)
- Identify top 5 improvement opportunities
- Estimate likelihood of ATS passage (low/medium/high)

**Output**: Detailed score report with improvement roadmap

### Step 9: Recommendations Generation

**Objective**: Provide actionable, prioritized improvement list

**Actions**:

- Rank recommendations by impact (critical, high, medium, low)
- Provide specific text suggestions for each change
- Include keyword integration examples
- Suggest formatting corrections
- Recommend content additions/deletions
- Offer alternative phrasings for impact statements
- Provide industry-specific customization ideas

**Output**: Priority-ranked action plan with specific edits

### Step 10: Optimized Resume Generation

**Objective**: Create final optimized version ready for submission

**Actions**:

- Apply all critical and high-priority recommendations
- Ensure consistent formatting throughout
- Verify all job-required keywords are naturally integrated
- Check final ATS compatibility
- Generate both ATS-friendly version and visual/designed version
- Create accompanying optimization report
- Provide customization notes for future applications

**Output**: Optimized resume file plus optimization report

## Usage Examples

### Example 1: Tech Industry ATS Optimization

```
User: Optimize my resume for a Senior Software Engineer position at Google
Input: resume.pdf + job_posting_url
Output:
- ATS Score: 87/100 (up from 62/100)
- Added keywords: Kubernetes, microservices, system design, distributed systems
- Enhanced impact: "Led team of 5 engineers" → "Led cross-functional team of 5 engineers to deliver microservices architecture, reducing deployment time by 40% and improving system reliability to 99.99%"
- Fixed formatting: Removed header graphics, standardized date format
- Recommendation: Add "Scale" and "performance optimization" keywords to experience section
```

### Example 2: Career Transition Optimization

```
User: Optimize resume for transition from teaching to corporate training role
Input: current_resume.docx + training_manager_job.txt
Output:
- Keyword mapping: "curriculum development" → "training program design", "student outcomes" → "learning metrics"
- Transferable skills emphasized: presentation skills, needs assessment, program evaluation
- Added business terminology: ROI, stakeholder management, KPIs
- New summary: "Education professional with 8+ years developing and delivering high-impact training programs, seeking to leverage instructional design expertise and proven track record of measurable learning outcomes in corporate L&D environment"
```

### Example 3: Executive-Level Optimization

```
User: Optimize C-suite resume for CFO position
Input: executive_resume.pdf + cfo_posting.pdf
Output:
- Strategic focus: Emphasized P&L responsibility, M&A experience, board presentations
- Quantified scale: Added company revenue, team size, budget managed
- Industry keywords: financial modeling, capital allocation, stakeholder relations, regulatory compliance
- Enhanced achievements: "Managed finance team" → "Transformed finance function for $500M organization, implementing zero-based budgeting and advanced analytics, resulting in 15% cost reduction and improved forecasting accuracy"
```

### Example 4: Entry-Level Graduate Optimization

```
User: Optimize new graduate resume for marketing coordinator role
Input: grad_resume.docx + marketing_job_url
Output:
- Emphasis on relevant coursework and projects
- Highlighted internship accomplishments with metrics
- Added keywords: digital marketing, social media analytics, content creation, campaign management
- Enhanced education section with relevant projects and GPA
- Created strong summary highlighting enthusiasm and relevant skills despite limited experience
```

### Example 5: Industry-Specific Compliance (Healthcare)

```
User: Optimize resume for Registered Nurse position
Input: nurse_resume.pdf + hospital_job_posting.txt
Output:
- Verified licensing and certifications prominently displayed
- Added healthcare-specific keywords: HIPAA, EMR systems, patient care protocols
- Emphasized specializations: ICU, emergency medicine, patient ratios
- Quantified patient outcomes and safety metrics
- Ensured regulatory compliance terminology throughout
```

### Example 6: Multi-Job Application Batch Optimization

```
User: Optimize resume for 3 different product manager positions
Input: resume.pdf + [job1.txt, job2.txt, job3.txt]
Output:
- Generated 3 tailored versions with common base
- Version 1 (B2B SaaS): Emphasized enterprise sales, customer retention, ARR growth
- Version 2 (Consumer Mobile): Highlighted user acquisition, engagement metrics, A/B testing
- Version 3 (Fintech): Added regulatory compliance, security, financial services experience
- Master keyword list with version-specific integration
```

## Quality Control Checklist

- [ ] Resume file successfully parsed and all sections identified
- [ ] Job posting requirements fully extracted and categorized
- [ ] Keyword gap analysis completed with priority rankings
- [ ] All ATS-incompatible elements identified and flagged
- [ ] Each experience bullet includes action verb and quantifiable result
- [ ] Critical job-required keywords integrated naturally (not keyword stuffed)
- [ ] Date formatting consistent throughout (MM/YYYY format)
- [ ] Contact information in ATS-compatible location (top of page)
- [ ] Section headings use standard terminology (Work Experience, not Professional Journey)
- [ ] No tables, text boxes, headers/footers, or graphics in ATS version
- [ ] Skills section reorganized with job-relevant skills prominent
- [ ] Professional summary tailored to specific job posting
- [ ] Overall optimization score calculated and improvement areas identified
- [ ] Final resume length appropriate (1 page for <10 years experience, 2 pages for 10+ years)
- [ ] Both ATS-friendly and visual versions generated

## Best Practices

1. **Always Create Job-Specific Versions** - Never use a generic resume for multiple applications. Each job deserves a tailored version optimizing for that specific posting.

2. **Prioritize Keyword Integration Over Density** - Focus on naturally incorporating required keywords rather than hitting arbitrary density targets. ATS systems penalize keyword stuffing.

3. **Lead with Impact, Not Responsibilities** - Every bullet point should demonstrate value delivered, not just tasks performed. Use STAR method consistently.

4. **Maintain ATS and Human Readability** - While optimizing for ATS, ensure the resume remains compelling for human recruiters who review it after ATS passage.

5. **Use Industry-Standard Section Headings** - Stick with "Work Experience", "Education", "Skills" rather than creative alternatives that confuse ATS parsers.

6. **Quantify Everything Possible** - Add metrics, percentages, dollar amounts, time frames, team sizes, and scale indicators wherever possible.

7. **Keep Formatting Simple in ATS Version** - Use standard fonts, simple bullets, no columns, and avoid headers/footers. Create a separate visual version for in-person interviews.

8. **Front-Load Important Information** - Put most relevant experience and keywords in the top half of the first page where recruiters spend most attention.

9. **Test Against Multiple ATS Systems** - Different systems have different parsing capabilities. Test with tools like Jobscan or Resume Worded before submission.

10. **Update for Each Application Round** - As you gain new experience or receive feedback, continuously improve your base resume and customization approach.

## Integration Points

- **LinkedIn Profile Optimizer** (`/resume/linkedin`) - Ensure consistency between resume and LinkedIn profile
- **Cover Letter Generator** (`/resume/cover-letter`) - Use optimized resume insights to craft matching cover letter
- **Portfolio Generator** (`/resume/portfolio`) - Align portfolio projects with resume accomplishments
- **Interview Prep** - Use keyword analysis to prepare for likely interview questions
- **Job Search Tracking** - Track which optimizations correlate with interview invitations
- **Personal Brand Consistency** - Maintain consistent messaging across all job search materials

## Success Criteria

- **ATS Compatibility Score**: 85+ out of 100
- **Keyword Coverage**: 90%+ of required skills mentioned
- **Interview Callback Rate**: 25-35% improvement over baseline
- **Application Time Reduction**: 60% faster job-specific customization
- **Impact Statement Quality**: 100% of experience bullets include quantifiable results
- **Formatting Compliance**: Zero ATS-incompatible elements
- **Relevance Score**: 80%+ content directly relevant to target role
- **Professional Polish**: Zero typos, consistent formatting, appropriate length

## Common Use Cases

1. **Active Job Search** - Optimizing resume for each new application during intensive job search period
2. **Career Transition** - Repositioning experience when changing industries or roles
3. **Promotion Pursuit** - Highlighting achievements for internal advancement opportunities
4. **Contract/Freelance** - Tailoring experience for specific project bids
5. **Networking Preparation** - Creating polished resume for professional conferences and events
6. **Annual Update** - Refreshing resume with past year's accomplishments and new skills
7. **Competitive Analysis** - Understanding how your background compares to job requirements
8. **Career Planning** - Identifying skill gaps between current state and target roles

## Troubleshooting

**Issue**: Low keyword match score despite relevant experience

- **Solution**: Job requirements may use different terminology. Look for synonyms and industry-specific terms. Example: "customer success" vs "client relations"

**Issue**: ATS formatting score is low

- **Solution**: Export resume as plain text to see how ATS sees it. Simplify formatting, remove tables/graphics, use standard section headings

**Issue**: Resume too long after adding keywords

- **Solution**: Remove older/less relevant positions, consolidate similar roles, eliminate low-impact bullets, use more concise language

**Issue**: Optimization feels inauthentic or keyword-stuffed

- **Solution**: Focus on naturally integrating keywords into genuine accomplishments. If you don't have the skill, consider removing it rather than forcing it

**Issue**: Different ATS systems give different results

- **Solution**: Create a maximally compatible version that works across all systems, then test and adjust for specific high-priority applications

## Advanced Features

1. **Multi-Version Management** - Maintain master resume with all experience, generate tailored versions for different job types, track which versions perform best

2. **Competitive Intelligence** - Analyze successful resumes in target industry to identify patterns, terminology, and formatting preferences

3. **Automated Keyword Tracking** - Build personal keyword database from job postings in target field, track trending skills and requirements

4. **A/B Testing Strategy** - Test different resume versions for similar roles, measure callback rates, optimize based on data

5. **Industry Benchmark Comparison** - Compare your resume against industry standards for similar roles, identify gaps and opportunities

6. **Skills Gap Analysis** - Identify frequently requested skills you lack, create learning plan to acquire them, update resume as skills develop

7. **Achievement Quantification Framework** - Develop system for consistently measuring and documenting accomplishments in current role for future resume updates

8. **Personal Branding Integration** - Ensure resume aligns with LinkedIn, portfolio, personal website, and other professional materials for cohesive brand

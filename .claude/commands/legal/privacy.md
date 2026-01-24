---
description: Create privacy policies compliant with GDPR, CCPA, PIPEDA
argument-hint: [--regions <gdpr|ccpa|pipeda|all>] [--business-type <saas|ecommerce|mobile-app|website>] [--export <html|pdf|markdown>]
model: claude-sonnet-4-5-20250929
allowed-tools: Write, Read, Glob, Grep, AskUserQuestion, Bash, WebSearch
---

# Privacy Policy Generator

Generate comprehensive, legally compliant privacy policies for GDPR (EU), CCPA (California), PIPEDA (Canada), and other jurisdictions.

## LEGAL DISCLAIMER

**IMPORTANT**: This tool generates privacy policy TEMPLATES based on common legal requirements. It is NOT legal advice and does NOT guarantee compliance with all applicable laws. Privacy laws are complex and vary by jurisdiction, business type, and data practices. You MUST have your privacy policy reviewed and approved by a qualified privacy attorney or data protection officer (DPO) before publication. Non-compliance with privacy laws can result in substantial fines (up to 4% of global revenue for GDPR violations).

## What This Command Does

Generates privacy policies that address major global privacy regulations:

### Regulatory Coverage

- **GDPR (EU)**: General Data Protection Regulation (27 EU member states + EEA)
- **CCPA (California)**: California Consumer Privacy Act + CPRA amendments
- **PIPEDA (Canada)**: Personal Information Protection and Electronic Documents Act
- **UK GDPR**: Post-Brexit UK data protection law
- **LGPD (Brazil)**: Lei Geral de Proteção de Dados
- **APPI (Japan)**: Act on Protection of Personal Information
- **PDPA (Singapore)**: Personal Data Protection Act
- **State Privacy Laws**: Virginia, Colorado, Connecticut, Utah privacy acts

### Policy Sections Generated

1. **What Information We Collect**
   - Personal identifiers (name, email, phone)
   - Device and usage data (IP, cookies, analytics)
   - Payment information (if applicable)
   - Sensitive personal information (if applicable)

2. **How We Use Your Information**
   - Service provision and operation
   - Communication and customer support
   - Marketing and advertising (with opt-out rights)
   - Legal compliance and fraud prevention

3. **How We Share Your Information**
   - Service providers and processors
   - Business transfers (M&A)
   - Legal obligations and law enforcement
   - Third-party disclosure transparency

4. **Your Rights and Choices**
   - **GDPR**: Access, rectification, erasure, portability, object, restrict
   - **CCPA**: Know, delete, opt-out of sale, non-discrimination
   - **PIPEDA**: Access, correction, complaint rights

5. **Data Security and Retention**
   - Security measures implemented
   - Data breach notification procedures
   - Retention periods and deletion policies

6. **International Transfers**
   - Cross-border data transfer mechanisms
   - Standard Contractual Clauses (SCCs)
   - Privacy Shield alternatives (post-Schrems II)

7. **Children's Privacy**
   - COPPA compliance (US, under 13)
   - Age verification mechanisms
   - Parental consent procedures

8. **Cookies and Tracking**
   - Cookie types and purposes
   - Third-party cookies and analytics
   - Cookie consent management
   - Do Not Track (DNT) signals

9. **Changes to Privacy Policy**
   - Update notification process
   - Effective date tracking
   - Version history

10. **Contact Information**
    - Data controller/business contact
    - Data Protection Officer (DPO) if required
    - Supervisory authority information (EU)

## Usage Examples

### Generate GDPR-Compliant Privacy Policy (SaaS)

```bash
/legal:privacy --regions gdpr --business-type saas --export html
```

**Key Features**:

- Legal basis for processing (consent, contract, legitimate interest)
- Data subject rights (access, erasure, portability, object)
- DPO contact information (if required)
- EU representative details (if outside EU)
- International transfer mechanisms (SCCs, BCRs)
- Data breach notification within 72 hours
- Right to lodge complaint with supervisory authority

### Generate CCPA-Compliant Privacy Policy (E-commerce)

```bash
/legal:privacy --regions ccpa --business-type ecommerce --export pdf
```

**Key Features**:

- "Do Not Sell My Personal Information" link requirement
- 12-month disclosure of data collection and sales
- Consumer rights notice (know, delete, opt-out)
- Non-discrimination policy
- Authorized agent submission process
- Verifiable consumer request procedures
- Categories of personal information collected and sold

### Generate Multi-Jurisdiction Policy (Mobile App)

```bash
/legal:privacy --regions all --business-type mobile-app --export markdown
```

**Covers**:

- GDPR (EU users)
- CCPA (California users)
- PIPEDA (Canadian users)
- UK GDPR (UK users)
- App store privacy nutrition labels (Apple App Store requirements)
- Mobile-specific data collection (location, camera, microphone, contacts)
- Push notification consent
- In-app analytics and advertising IDs

### Generate Website Privacy Policy (Small Business)

```bash
/legal:privacy --regions gdpr,ccpa --business-type website --export html
```

**Streamlined Policy for**:

- Contact forms and email collection
- Google Analytics or similar
- Cookie consent banner integration
- Mailchimp or email marketing platform
- Social media plugins
- Third-party embedded content

## Business Value / ROI

### Compliance and Risk Mitigation

- **GDPR fines avoided**: Up to €20M or 4% of global annual revenue (whichever is higher)
- **CCPA penalties avoided**: $2,500 per unintentional violation, $7,500 per intentional violation
- **Privacy attorney fees**: $5,000-$25,000 for custom privacy policy drafting
- **Annual compliance costs**: $50,000-$500,000 for ongoing privacy program management

### Real-World GDPR Fines (Examples)

- **Amazon (2021)**: €746 million ($887M) - targeted advertising practices
- **WhatsApp (2021)**: €225 million ($267M) - transparency and information failures
- **Google (2019)**: €50 million ($57M) - lack of transparency and valid consent
- **British Airways (2020)**: £20 million ($26M) - data breach affecting 400,000 customers

### Business Benefits

- **Customer trust**: 81% of consumers concerned about data privacy (Cisco, 2023)
- **Competitive advantage**: Privacy-conscious brands gain market share
- **Partnership requirements**: Many B2B partners require privacy compliance
- **App store requirements**: Apple/Google require privacy policies for app listing
- **Payment processors**: Stripe, PayPal require compliant privacy policies
- **Ad platforms**: Google Ads, Facebook Ads require privacy policy links

### Time and Cost Savings

- **DIY compliance**: 100+ hours of research and drafting (opportunity cost: $10,000-$50,000)
- **Attorney review only**: $2,000-$5,000 (vs. $25,000 for full drafting)
- **Faster time to market**: Launch products/features without privacy bottlenecks
- **Template reuse**: Generate policies for multiple products/brands

### Quantified ROI Example

**E-commerce Startup (Pre-Series A)**:

- Privacy attorney drafting: $15,000
- Ongoing compliance consulting: $5,000/year
- **AI-generated policy cost**: $0 (+ $2,000 attorney review)
- **Savings Year 1**: $13,000
- **Risk mitigation value**: Priceless (avoid catastrophic fines)
- **Investor confidence**: Privacy compliance required for due diligence

## Success Metrics

### Legal Compliance

- [ ] All required disclosures present for target jurisdictions
- [ ] Data subject rights clearly explained
- [ ] Contact information for privacy inquiries provided
- [ ] DPO appointed and listed (if required under GDPR)
- [ ] Cookie consent mechanism implemented
- [ ] Privacy policy reviewed by qualified attorney
- [ ] Policy published and easily accessible (footer link, dedicated page)

### User Experience

- [ ] Plain language explanations (avoid excessive legal jargon)
- [ ] Clear table of contents or sections
- [ ] Mobile-responsive formatting
- [ ] Easy-to-find contact information
- [ ] Last updated date displayed prominently
- [ ] Downloadable PDF version available
- [ ] Translation for non-English markets (if applicable)

### Technical Implementation

- [ ] Privacy policy URL: `/privacy` or `/privacy-policy`
- [ ] Linked from website footer and signup flows
- [ ] Version control and change tracking
- [ ] Cookie consent banner integrated
- [ ] Data subject request (DSR) portal implemented
- [ ] Privacy policy acceptance checkboxes in forms
- [ ] Email notification system for policy updates

### Regulatory Readiness

- [ ] Data inventory and mapping completed
- [ ] Records of Processing Activities (ROPA) maintained
- [ ] Data Processing Agreements (DPAs) with vendors
- [ ] Data breach response plan documented
- [ ] Annual privacy training for employees
- [ ] Privacy impact assessments (PIAs) for high-risk processing
- [ ] Third-party audit or certification (optional: ISO 27701, SOC 2)

## Privacy Law Comparison

| Requirement | GDPR (EU) | CCPA (CA) | PIPEDA (CA) | UK GDPR |
|-------------|-----------|-----------|-------------|---------|
| **Scope** | EU residents | CA residents | Canadian businesses | UK residents |
| **Consent** | Explicit, granular | Not required (opt-out model) | Meaningful consent | Explicit, granular |
| **Age of consent** | 16 (or 13-16 by member state) | 13 (via COPPA) | Provincial (13-18) | 13 |
| **DPO required** | Some organizations | No | No | Some organizations |
| **Fines** | €20M or 4% revenue | $7,500 per violation | CAD $100,000 | £17.5M or 4% revenue |
| **Data portability** | Yes | Yes (limited) | Yes (access right) | Yes |
| **Right to erasure** | Yes | Yes | Limited | Yes |
| **Breach notification** | 72 hours | None (private right of action) | ASAP (material breaches) | 72 hours |

## Business Type Considerations

### SaaS/Software

- **Data collected**: User accounts, usage analytics, payment info, support tickets
- **Key concerns**: Subprocessors/vendors, international transfers, data retention
- **Special requirements**: DPA with customers, SOC 2 certification often required

### E-commerce

- **Data collected**: Orders, payment info, shipping addresses, browsing history
- **Key concerns**: Payment card data (PCI-DSS), marketing opt-ins, abandoned carts
- **Special requirements**: CCPA "Do Not Sell" prominent, cookie consent for tracking

### Mobile Apps

- **Data collected**: Device IDs, location, camera/mic, contacts, push tokens
- **Key concerns**: App permissions, children's apps (COPPA), app store requirements
- **Special requirements**: Apple Privacy Nutrition Label, runtime permissions (iOS/Android)

### Healthcare/Wellness

- **Data collected**: Health information, biometric data, medical records
- **Key concerns**: HIPAA (US), special category data (GDPR Article 9), consent requirements
- **Special requirements**: Business Associate Agreement (BAA), heightened security standards

### Marketing/Advertising

- **Data collected**: Behavioral data, cookies, advertising IDs, cross-site tracking
- **Key concerns**: Targeting and profiling, data sales/sharing, third-party pixels
- **Special requirements**: Cookie consent banners, opt-out mechanisms, transparency

## Integration with Other Commands

**Compliance Workflow**:

```bash
/legal:privacy --regions all --business-type saas  # Generate privacy policy
/legal:terms                                        # Generate terms of service
/legal:gdpr                                         # GDPR compliance checklist
/security/audit                                     # Security posture assessment
```

**Website Launch**:

```bash
/legal:privacy --regions gdpr,ccpa  # Privacy policy
/legal:terms                         # Terms of service
/landing/create                      # Landing page with legal links
```

**Product Compliance**:

```bash
/legal:privacy --business-type mobile-app  # App privacy policy
/legal:gdpr --deep-dive                    # GDPR compliance documentation
/security/scan                             # Security vulnerability scan
```

## Regulatory Resources

### GDPR (EU)

- **Official text**: <https://gdpr-info.eu/>
- **Supervisory authorities**: <https://edpb.europa.eu/about-edpb/about-edpb/members_en>
- **Guidance**: EDPB guidelines and recommendations
- **Key articles**: Art. 6 (lawful basis), Art. 15-22 (data subject rights), Art. 33-34 (breach notification)

### CCPA/CPRA (California)

- **Official text**: <https://oag.ca.gov/privacy/ccpa>
- **Enforcement**: California Attorney General, California Privacy Protection Agency (CPRA)
- **Requirements**: Annual privacy policy updates, "Do Not Sell" link, consumer request portal
- **Effective dates**: CCPA (Jan 2020), CPRA (Jan 2023)

### PIPEDA (Canada)

- **Official text**: <https://www.priv.gc.ca/en/privacy-topics/privacy-laws-in-canada/the-personal-information-protection-and-electronic-documents-act-pipeda/>
- **Enforcement**: Office of the Privacy Commissioner of Canada
- **Principles**: 10 Fair Information Principles
- **Provincial laws**: Quebec (Law 25), BC (PIPA), Alberta (PIPA)

### UK GDPR

- **Official text**: <https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/>
- **Enforcement**: Information Commissioner's Office (ICO)
- **Post-Brexit**: Substantially similar to EU GDPR with minor divergences
- **International transfers**: UK Adequacy Decisions required

## Attorney Review Checklist

Before publishing your AI-generated privacy policy, ensure attorney review covers:

- [ ] **Accuracy**: Policy reflects actual data practices (no overclaiming or underclaiming)
- [ ] **Completeness**: All required disclosures present for target jurisdictions
- [ ] **Consistency**: Policy aligns with terms of service, DPAs, and other legal docs
- [ ] **Compliance**: Meets specific requirements of GDPR, CCPA, PIPEDA, etc.
- [ ] **Third parties**: All vendors, partners, and data processors disclosed
- [ ] **Data flows**: International transfers properly explained and legally supported
- [ ] **Rights mechanisms**: Procedures for data subject requests actually implemented
- [ ] **Updates**: Process for notifying users of material changes
- [ ] **Contact info**: Correct company name, legal entity, contact details, DPO (if required)
- [ ] **Effective date**: Accurate and reflects current version

**Recommended attorney review cost**: $2,000-$5,000 (vs. $15,000-$25,000 for full drafting)

## Commands

**`/legal:privacy`** - Generate comprehensive privacy policy
**`/legal:terms`** - Generate terms of service
**`/legal:gdpr`** - GDPR compliance checklist and documentation
**`/legal:contract nda`** - Generate business contracts
**`/security/audit`** - Security audit for privacy compliance

---
**REMEMBER**: This is a template requiring attorney review. Not legal advice. Privacy compliance is an ongoing obligation, not a one-time task.
**Related**: /legal/terms, /legal/gdpr, /security/audit, /landing/create

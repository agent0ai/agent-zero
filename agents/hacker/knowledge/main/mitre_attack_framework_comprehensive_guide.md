# MITRE ATT&CK Framework: Comprehensive Adversary Tactics and Techniques Guide

## Document Overview

**Source**: MITRE Corporation - Official ATT&CK Framework
**URL**: https://attack.mitre.org/
**Classification**: Globally-accessible knowledge base of adversary tactics and techniques
**Scope**: Enterprise, Mobile, and Industrial Control Systems (ICS)
**Purpose**: Foundation for threat modeling, adversary emulation, and cybersecurity defense

### Validation & Quality Assurance
- **Source Authority**: MITRE Corporation - federally funded research and development center
- **Industry Standard**: Globally recognized framework used by government and private sector
- **Continuous Updates**: Regularly updated based on real-world observations and threat intelligence
- **Community Validation**: Extensive peer review and industry collaboration
- **Verification**: Cross-referenced with NIST cybersecurity frameworks and industry best practices

## Executive Summary

MITRE ATT&CK® (Adversarial Tactics, Techniques, and Common Knowledge) represents the definitive knowledge base of adversary behaviors based on real-world observations. This framework provides a comprehensive taxonomy of how threat actors operate across the entire attack lifecycle, from initial reconnaissance through final impact.

The framework serves as the foundation for:
- **Threat Modeling**: Understanding adversary capabilities and attack patterns
- **Adversary Emulation**: Simulating real-world attack scenarios for testing
- **Detection Engineering**: Building security controls based on known techniques
- **Threat Intelligence**: Categorizing and analyzing threat actor behaviors
- **Red Team Operations**: Structured approach to penetration testing and security assessment

## Framework Architecture

### Core Components

#### Tactics (14 Categories)
Tactics represent the "why" of an attack - the adversary's tactical goals during an attack.

1. **Reconnaissance (TA0043)** - Information gathering for attack planning
2. **Resource Development (TA0042)** - Establishing resources to support operations
3. **Initial Access (TA0001)** - Gaining foothold within target network
4. **Execution (TA0002)** - Running malicious code on target systems
5. **Persistence (TA0003)** - Maintaining access across system restarts
6. **Privilege Escalation (TA0004)** - Gaining higher-level permissions
7. **Defense Evasion (TA0005)** - Avoiding detection by security controls
8. **Credential Access (TA0006)** - Stealing account credentials
9. **Discovery (TA0007)** - Learning about system and network environment
10. **Lateral Movement (TA0008)** - Moving through the network
11. **Collection (TA0009)** - Gathering data of interest
12. **Command and Control (TA0011)** - Communicating with compromised systems
13. **Exfiltration (TA0010)** - Stealing data from the network
14. **Impact (TA0040)** - Manipulating, interrupting, or destroying systems

#### Techniques (200+ Methods)
Techniques describe "how" an adversary achieves a tactical goal by performing an action.

#### Sub-Techniques (400+ Variations)
Sub-techniques provide more specific descriptions of adversarial behavior used to achieve techniques.

#### Procedures
Procedures are the specific implementation details of techniques by threat actors.

## Detailed Tactical Analysis

### Reconnaissance (TA0043)
**Objective**: Gather information to plan future attack operations

**Key Techniques**:
- **Active Scanning (T1595)**: Direct interaction with target infrastructure
  - IP Block Scanning (T1595.001)
  - Vulnerability Scanning (T1595.002)
  - Wordlist Scanning (T1595.003)

- **Gather Victim Information (T1589-T1592)**: Collecting target intelligence
  - Identity Information (T1589): Credentials, email addresses, employee names
  - Network Information (T1590): Domain properties, DNS, network topology
  - Organization Information (T1591): Physical locations, business relationships
  - Host Information (T1592): Hardware, software, firmware details

- **Search Techniques (T1593-T1598)**: Open source intelligence gathering
  - Open Websites/Domains (T1593): Social media, search engines, code repositories
  - Technical Databases (T1596): DNS/Passive DNS, WHOIS, digital certificates
  - Phishing for Information (T1598): Spearphishing for intelligence collection

### Resource Development (TA0042)
**Objective**: Establish resources to support attack operations

**Key Techniques**:
- **Acquire Infrastructure (T1583)**: Obtaining attack infrastructure
  - Domains (T1583.001)
  - DNS Servers (T1583.002)
  - Virtual Private Servers (T1583.003)
  - Botnets (T1583.005)

- **Develop Capabilities (T1587)**: Creating attack tools and resources
  - Malware (T1587.001)
  - Code Signing Certificates (T1587.002)
  - Exploits (T1587.004)

- **Obtain Capabilities (T1588)**: Acquiring existing attack tools
  - Malware (T1588.001)
  - Tools (T1588.002)
  - Vulnerabilities (T1588.006)

### Initial Access (TA0001)
**Objective**: Gain initial foothold within target network

**Key Techniques**:
- **Phishing (T1566)**: Social engineering via electronic communications
  - Spearphishing Attachment (T1566.001)
  - Spearphishing Link (T1566.002)
  - Spearphishing via Service (T1566.003)

- **Exploit Public-Facing Application (T1190)**: Taking advantage of weaknesses in internet-facing systems

- **External Remote Services (T1133)**: Leveraging legitimate remote access services

- **Supply Chain Compromise (T1195)**: Manipulating products or delivery mechanisms
  - Software Dependencies (T1195.001)
  - Software Supply Chain (T1195.002)
  - Hardware Supply Chain (T1195.003)

### Execution (TA0002)
**Objective**: Run malicious code on target systems

**Key Techniques**:
- **Command and Scripting Interpreter (T1059)**: Abuse of command-line interfaces
  - PowerShell (T1059.001)
  - Windows Command Shell (T1059.003)
  - Unix Shell (T1059.004)
  - Python (T1059.006)
  - JavaScript (T1059.007)

- **User Execution (T1204)**: Relying on user actions to execute code
  - Malicious Link (T1204.001)
  - Malicious File (T1204.002)

- **Scheduled Task/Job (T1053)**: Abuse of task scheduling functionality
  - Cron (T1053.003)
  - Scheduled Task (T1053.005)

### Persistence (TA0003)
**Objective**: Maintain access across system restarts and credential changes

**Key Techniques**:
- **Boot or Logon Autostart Execution (T1547)**: Automatic execution during system startup
  - Registry Run Keys (T1547.001)
  - Authentication Package (T1547.002)
  - Kernel Modules and Extensions (T1547.006)

- **Create or Modify System Process (T1543)**: Creating or modifying system-level processes
  - Windows Service (T1543.003)
  - Launch Daemon (T1543.004)

- **Event Triggered Execution (T1546)**: Establishing persistence through event triggers
  - Windows Management Instrumentation Event Subscription (T1546.003)
  - Application Shimming (T1546.011)

### Privilege Escalation (TA0004)
**Objective**: Gain higher-level permissions on systems or networks

**Key Techniques**:
- **Abuse Elevation Control Mechanism (T1548)**: Circumventing access controls
  - Bypass User Account Control (T1548.002)
  - Sudo and Sudo Caching (T1548.003)

- **Access Token Manipulation (T1134)**: Manipulating access tokens to escalate privileges
  - Token Impersonation/Theft (T1134.001)
  - Create Process with Token (T1134.002)

- **Exploitation for Privilege Escalation (T1068)**: Exploiting software vulnerabilities

### Defense Evasion (TA0005)
**Objective**: Avoid detection throughout the attack lifecycle

**Key Techniques**:
- **Obfuscated Files or Information (T1027)**: Making detection more difficult
  - Software Packing (T1027.002)
  - Steganography (T1027.003)
  - Command Obfuscation (T1027.010)

- **Process Injection (T1055)**: Injecting code into legitimate processes
  - Dynamic-link Library Injection (T1055.001)
  - Process Hollowing (T1055.012)

- **Masquerading (T1036)**: Manipulating features to avoid detection
  - Invalid Code Signature (T1036.001)
  - Rename Legitimate Utilities (T1036.003)

- **Impair Defenses (T1562)**: Reducing effectiveness of security controls
  - Disable or Modify Tools (T1562.001)
  - Disable Windows Event Logging (T1562.002)

### Credential Access (TA0006)
**Objective**: Steal account names and passwords

**Key Techniques**:
- **OS Credential Dumping (T1003)**: Obtaining credentials from operating systems
  - LSASS Memory (T1003.001)
  - Security Account Manager (T1003.002)
  - NTDS (T1003.003)

- **Brute Force (T1110)**: Attempting to guess credentials
  - Password Guessing (T1110.001)
  - Password Cracking (T1110.002)
  - Password Spraying (T1110.003)

- **Credentials from Password Stores (T1555)**: Obtaining stored credentials
  - Credentials from Web Browsers (T1555.003)
  - Windows Credential Manager (T1555.004)

### Discovery (TA0007)
**Objective**: Learn about the system and internal network

**Key Techniques**:
- **System Information Discovery (T1082)**: Gathering system configuration information

- **Account Discovery (T1087)**: Identifying user and service accounts
  - Local Account (T1087.001)
  - Domain Account (T1087.002)

- **Network Service Discovery (T1046)**: Identifying network services

- **Remote System Discovery (T1018)**: Identifying other systems on the network

### Lateral Movement (TA0008)
**Objective**: Move through the network to reach objectives

**Key Techniques**:
- **Remote Services (T1021)**: Using legitimate remote access methods
  - Remote Desktop Protocol (T1021.001)
  - SMB/Windows Admin Shares (T1021.002)
  - SSH (T1021.004)

- **Exploitation of Remote Services (T1210)**: Exploiting remote service vulnerabilities

- **Use Alternate Authentication Material (T1550)**: Using stolen credentials
  - Pass the Hash (T1550.002)
  - Pass the Ticket (T1550.003)

### Collection (TA0009)
**Objective**: Gather data of interest to achieve objectives

**Key Techniques**:
- **Data from Local System (T1005)**: Collecting data from local storage

- **Email Collection (T1114)**: Accessing email repositories
  - Local Email Collection (T1114.001)
  - Remote Email Collection (T1114.002)

- **Archive Collected Data (T1560)**: Compressing data for exfiltration
  - Archive via Utility (T1560.001)
  - Archive via Library (T1560.002)

### Command and Control (TA0011)
**Objective**: Communicate with compromised systems

**Key Techniques**:
- **Application Layer Protocol (T1071)**: Using standard application protocols
  - Web Protocols (T1071.001)
  - File Transfer Protocols (T1071.002)
  - DNS (T1071.004)

- **Encrypted Channel (T1573)**: Using encryption to hide communications
  - Symmetric Cryptography (T1573.001)
  - Asymmetric Cryptography (T1573.002)

- **Proxy (T1090)**: Using intermediary systems for communication
  - Internal Proxy (T1090.001)
  - External Proxy (T1090.002)

### Exfiltration (TA0010)
**Objective**: Steal data from the network

**Key Techniques**:
- **Exfiltration Over C2 Channel (T1041)**: Using existing command and control channels

- **Exfiltration Over Web Service (T1567)**: Using web services for data theft
  - Exfiltration to Cloud Storage (T1567.002)
  - Exfiltration to Code Repository (T1567.001)

- **Exfiltration Over Alternative Protocol (T1048)**: Using non-standard protocols

### Impact (TA0040)
**Objective**: Manipulate, interrupt, or destroy systems and data

**Key Techniques**:
- **Data Encrypted for Impact (T1486)**: Encrypting data to disrupt operations (ransomware)

- **Data Destruction (T1485)**: Destroying data to disrupt operations

- **Service Stop (T1489)**: Stopping critical services

- **Resource Hijacking (T1496)**: Using compromised resources for unauthorized purposes
  - Compute Hijacking (T1496.001)
  - Bandwidth Hijacking (T1496.002)

## Threat Actor Groups and Software

### Advanced Persistent Threat (APT) Groups
The framework catalogs hundreds of threat actor groups with their associated techniques:

- **APT1 (Comment Crew)**: Chinese military unit known for intellectual property theft
- **APT28 (Fancy Bear)**: Russian military intelligence group
- **APT29 (Cozy Bear)**: Russian foreign intelligence service
- **Lazarus Group**: North Korean state-sponsored group
- **Carbanak**: Financial crime syndicate

### Malware Families
Extensive catalog of malware with mapped techniques:

- **Cobalt Strike**: Commercial penetration testing tool often used by threat actors
- **Mimikatz**: Credential extraction tool
- **PowerShell Empire**: Post-exploitation framework
- **Metasploit**: Penetration testing framework

## Practical Applications

### Adversary Emulation
**Purple Team Operations**: Combining red and blue team activities
- Use ATT&CK techniques to design realistic attack scenarios
- Test detection capabilities against known adversary behaviors
- Validate security control effectiveness

**Red Team Exercises**: Structured attack simulations
- Plan attack paths using ATT&CK tactics and techniques
- Document techniques used during engagements
- Provide actionable feedback to blue teams

### Threat Intelligence
**Campaign Analysis**: Understanding threat actor operations
- Map observed behaviors to ATT&CK techniques
- Identify patterns and trends in adversary tactics
- Predict future attack vectors

**Threat Hunting**: Proactive search for threats
- Develop hunting hypotheses based on ATT&CK techniques
- Create detection rules for specific adversary behaviors
- Prioritize hunting activities based on threat landscape

### Security Architecture
**Detection Engineering**: Building effective security controls
- Map security tools to ATT&CK techniques they can detect
- Identify coverage gaps in security architecture
- Prioritize security investments based on threat modeling

**Incident Response**: Structured approach to threat analysis
- Categorize observed behaviors using ATT&CK framework
- Understand attack progression and predict next steps
- Develop containment strategies based on technique analysis

## Integration with Security Tools

### SIEM and Analytics Platforms
- **Splunk**: ATT&CK App for mapping security events to techniques
- **Elastic Security**: Built-in ATT&CK technique mapping
- **IBM QRadar**: ATT&CK-based threat hunting and detection

### Threat Intelligence Platforms
- **MISP**: Threat intelligence sharing with ATT&CK tagging
- **ThreatConnect**: ATT&CK technique correlation and analysis
- **Anomali**: Threat intelligence enrichment with ATT&CK context

### Security Orchestration
- **Phantom/SOAR**: Automated response based on ATT&CK techniques
- **Demisto**: Playbook development using ATT&CK framework
- **TheHive**: Case management with ATT&CK technique tracking

## Advanced Concepts

### ATT&CK Navigator
**Visualization Tool**: Interactive matrix for technique analysis
- Create custom views of relevant techniques
- Overlay threat intelligence on the matrix
- Compare different threat actor capabilities
- Export visualizations for reporting and analysis

### ATT&CK Data Sources
**Detection Data Model**: Mapping techniques to data sources
- Identify required data sources for technique detection
- Understand data collection requirements
- Optimize log collection and retention strategies

### Mitigations Framework
**Defensive Measures**: Countermeasures for ATT&CK techniques
- Map security controls to techniques they mitigate
- Prioritize defensive investments
- Validate mitigation effectiveness

## Implementation Methodology

### Phase 1: Assessment
1. **Current State Analysis**: Map existing security controls to ATT&CK techniques
2. **Gap Analysis**: Identify uncovered techniques and tactics
3. **Threat Modeling**: Prioritize techniques based on threat landscape

### Phase 2: Enhancement
1. **Detection Development**: Create rules for high-priority techniques
2. **Tool Integration**: Implement ATT&CK mapping in security tools
3. **Process Integration**: Incorporate ATT&CK into security workflows

### Phase 3: Operationalization
1. **Team Training**: Educate security teams on ATT&CK usage
2. **Continuous Improvement**: Regular updates based on new techniques
3. **Metrics and Reporting**: Track coverage and effectiveness metrics

## Best Practices

### Framework Adoption
- **Start Small**: Begin with high-priority techniques relevant to your environment
- **Iterative Approach**: Gradually expand coverage and sophistication
- **Community Engagement**: Participate in ATT&CK community discussions

### Quality Assurance
- **Regular Updates**: Stay current with framework updates and new techniques
- **Validation Testing**: Regularly test detection capabilities
- **Documentation**: Maintain clear mapping between tools and techniques

### Organizational Integration
- **Cross-Team Collaboration**: Involve red, blue, and purple teams
- **Executive Communication**: Translate technical details to business impact
- **Vendor Engagement**: Require ATT&CK support from security vendors

## Future Developments

### Emerging Domains
- **Cloud Security**: Enhanced coverage of cloud-specific techniques
- **Container Security**: Kubernetes and container-focused techniques
- **IoT and OT**: Industrial control systems and IoT device techniques

### Advanced Analytics
- **Machine Learning**: AI-powered technique prediction and detection
- **Behavioral Analysis**: User and entity behavior analytics integration
- **Threat Modeling**: Automated threat model generation

## Conclusion

The MITRE ATT&CK framework represents the gold standard for understanding adversary behavior and building effective cybersecurity defenses. Its comprehensive taxonomy of tactics, techniques, and procedures provides organizations with:

- **Common Language**: Standardized terminology for describing threats
- **Actionable Intelligence**: Practical guidance for security improvements
- **Measurable Outcomes**: Metrics for assessing security effectiveness
- **Community Knowledge**: Shared understanding of threat landscape

By implementing ATT&CK-based approaches to threat modeling, detection engineering, and adversary emulation, organizations can significantly improve their security posture and resilience against sophisticated threats.

### Strategic Value
The framework enables organizations to move from reactive security to proactive threat-informed defense, focusing resources on the techniques most likely to be used by relevant threat actors.

### Operational Excellence
ATT&CK provides the foundation for building mature security operations that can effectively detect, respond to, and recover from advanced threats while continuously improving defensive capabilities.

### Industry Leadership
Organizations that effectively implement ATT&CK-based security programs position themselves as industry leaders in cybersecurity maturity and threat resilience.

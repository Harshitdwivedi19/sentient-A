# Privacy & Data Ethics Policy for Sentient Trajectory

**Last Updated:** October 25, 2026  
**Effective Date:** October 25, 2026  

Sentient Trajectory ("the Application", "we", "our", or "us") provides explainable conversation sentiment analysis and emotional trajectory modeling. We believe personal conversations and messages are deeply confidential. This Policy sets forth our comprehensive commitment to data privacy, global cyber laws, ethical artificial intelligence, and transparent ad-supported monetization.

---

### 1. Global Legal Compliance Framework

This Policy complies with international cyber laws, data protection regulations, and digital consumer rights statutes, including:
- **European Union General Data Protection Regulation (GDPR - EU 2016/679)**
- **California Consumer Privacy Act (CCPA) as amended by the California Privacy Rights Act (CPRA)**
- **Digital Personal Data Protection Act, 2023 (DPDP Act - India)**
- **Children's Online Privacy Protection Act (COPPA - 15 U.S.C. §§ 6501–6506)**
- **Google Play Developer Program Policies & Families Policy**

---

### 2. The Core Privacy Principle: 100% Local On-Device Processing

- **No Remote Message Transmission:** All natural language processing, sentiment classification, context aggregation, turning-point detection, and trajectory modeling occur **exclusively inside your device memory (RAM)**.
- **Zero Cloud Storage:** Your dialogue messages, WhatsApp export `.txt` files, speaker names, timestamps, and emotional trajectory scores are **never uploaded, synced, or backed up to any external cloud server or remote database**.
- **Ephemeral Session Data:** Closing the application or refreshing the workspace immediately purges active dialogue data from system RAM.

---

### 3. Advertising & Monetization Disclosures

To provide Sentient Trajectory as a free service, we display third-party advertisements (such as Google AdMob) within the application.

#### A. Strict Data Separation (Privacy Firewall)
- **Advertisers and ad networks NEVER receive your conversation text, chat logs, speaker identities, sentiment scores, or turning-point analysis.**
- There is a strict, impenetrable separation between our local AI analysis engine and third-party advertising SDKs.

#### B. Information Collected by Ad Partners
Third-party ad networks (e.g. Google LLC) may automatically collect standard device-level technical signals for the sole purpose of ad delivery, frequency capping, fraud prevention, and performance reporting:
- Mobile Advertising Identifiers (Google Advertising ID / GAID / IDFA)
- Device model, operating system version, and general hardware configuration
- IP address (used solely to determine coarse, non-precise city/region location and language preferences)
- Non-identifying ad interaction metrics (impressions, clicks, and load diagnostics)

#### C. User Ad Choices & Personalization Opt-Out
You maintain complete control over advertising personalization under GDPR, CCPA, and DPDP:
- **Android Device Settings:** Navigate to **Settings > Google > Ads** (or **Settings > Privacy > Ads**) to toggle *"Opt out of Ads Personalization"* or *"Reset Advertising ID"*.
- **EU/EEA & UK Consent:** Users within the European Economic Area are presented with a consent banner permitting the selection of Non-Personalized Ads (NPA).
- **California "Do Not Sell or Share":** Under the CCPA/CPRA, we confirm that **we do not sell or share user personal data or conversation content**.

---

### 4. User Rights Under Global Cyber Laws

Regardless of your geographic location, we respect and enforce the highest international data rights standards:

| Legal Right | Applicable Statutes | How Sentient Trajectory Complies |
| :--- | :--- | :--- |
| **Right to Access & Portability** | GDPR Art. 15/20, CCPA § 1798.100, DPDP Sec. 11 | You can export your full analysis records at any time via CSV, Markdown report, or JSON directly to your device storage. |
| **Right to Erasure ("Be Forgotten")** | GDPR Art. 17, CCPA § 1798.105, DPDP Sec. 12 | Because processing is 100% local, clearing your session or deleting exported files permanently erases all trace of your data. |
| **Right to Rectification** | GDPR Art. 16, CCPA § 1798.106 | You can freely edit, rename speakers, or modify message turns before running inference. |
| **Right to Non-Discrimination** | CCPA § 1798.125 | All core analysis features remain fully functional regardless of ad personalization choices. |
| **Right to Grievance Redressal** | DPDP Act Sec. 13 | Users may submit privacy inquiries or grievances directly to our Data Protection Contact. |

---

### 5. Children's Privacy (COPPA & DPDP Compliance)

- Sentient Trajectory is intended for general audiences aged 13 and above.
- In strict adherence to COPPA and Section 9 of the India DPDP Act 2023, we **do not knowingly collect personal data from children under 13**, nor do we permit behavioral profiling or targeted advertising directed at minors.
- If a parent or guardian discovers that an ad network has collected device signals from a minor without consent, please contact us for immediate remedial assistance.

---

### 6. AI Ethics, Explainability & Responsible Use

Sentient Trajectory follows internationally recognized principles of Responsible AI:
1. **Non-Causal Statistical Observations:** Model-predicted sentiment polarities ($s_t$) and turning-point shifts denote mathematical patterns in expressed written language. They **do not** constitute psychiatric evaluations, medical diagnoses, or biological measurements of emotional state.
2. **Defensive Cyber Security (Risk #87 Mitigation):** To protect users against CSV formula-injection exploits (DDE command execution), our export engine defensively sanitizes cells starting with `=`, `+`, `-`, or `@` by prepending an apostrophe (`'`).
3. **Algorithmic Transparency:** All inference models, context aggregation windows ($k$), and sensitivity thresholds ($\tau$) are user-configurable and open to audit.

---

### 7. Data Retention & Security Safeguards

- **Local Storage:** The Application does not maintain background tracking databases. Imported `.txt` chat files are read transiently.
- **Device Security:** We recommend keeping your mobile OS updated and protecting your device with biometrics or a PIN to safeguard locally exported CSV/Markdown files.

---

### 8. Changes to This Policy

We may update this Policy periodically to reflect technological advancements, legal developments, or ad network specifications. Any updates will be published with a revised "Last Updated" date.

---

### 9. Privacy & Grievance Contact

For questions regarding this Policy, exercise of legal data rights, or cyber ethics inquiries:
- **Email:** `dharshit095@gmail.com`
- **Data Protection & Grievance Officer:** Harshit Dwivedi
- **Public Repository:** [github.com](https://github.com)

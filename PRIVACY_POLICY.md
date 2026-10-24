# Privacy Policy for Sentient Trajectory

**Last updated:** October 24, 2026

Sentient Trajectory ("the Application", "we", "our") is designed as an explainable, research-grade natural language processing tool for analyzing conversation sentiment trajectories. We believe your conversations are deeply personal. This Privacy Policy outlines our strict commitment to user privacy and data security.

---

### 1. 100% On-Device Local Processing

- **No Remote Transmission:** All natural language processing, sentiment classification, context-window aggregation, and turning-point calculations occur **entirely on your local device**.
- **No Cloud Server Dependency:** The Application operates independently without transmitting conversation text, messages, speaker names, timestamps, or analysis results to any external server or third-party cloud service.

---

### 2. Information We Do NOT Collect

We do **not** collect, store, monetize, or transmit:
- Personal Identifiable Information (PII) such as your name, phone number, email address, or device ID.
- The content of your pasted messages or imported WhatsApp `.txt` chat files.
- Sentiment prediction records, emotional volatility metrics, or turning-point analysis outputs.
- Location data, contacts, or browsing history.

---

### 3. File Access & WhatsApp Import

When you import an exported WhatsApp chat file (`.txt`) or export analysis results:
- The file is read strictly within device memory (RAM) to parse turns and speaker tags.
- No files are uploaded to any external server.
- The Application does not modify, delete, or inspect any other files on your device.

---

### 4. Third-Party Analytics & Tracking

- The Application contains **zero third-party trackers, ad SDKs, telemetry libraries, or user-profiling scripts**.
- We do not display advertisements.

---

### 5. Data Security (Formula-Injection Defenses)

When exporting analytical records to CSV, the Application incorporates defensive sanitization (Risk #87) by prepending dangerous formula prefixes (`=`, `+`, `-`, `@`) with an apostrophe (`'`) to protect you from spreadsheet code execution vulnerabilities.

---

### 6. Children's Privacy

The Application does not collect information from anyone, including children under the age of 13.

---

### 7. Changes to This Privacy Policy

If we update this Privacy Policy, the revised version will be published at this URL with an updated revision date.

---

### 8. Contact Us

If you have questions regarding this Privacy Policy or the scientific methodology of Sentient Trajectory, please open an issue on our public project repository.

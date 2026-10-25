# Google Play Store Release & Submission Guide

This guide contains everything required to publish **Sentient Trajectory** on the Google Play Store for free.

---

## 1. Generated Release Package & Assets

All release assets are generated and stored in your project directory:

| Asset | Path | Purpose |
| :--- | :--- | :--- |
| **Android App Bundle (.aab)** | `dist/SentimentTrajectory.aab` | **Upload this file to Google Play Console** |
| **Production Release Keystore** | `dist/release.keystore` | Permanent cryptographic signature key (**Keep safe!**) |
| **Release APK (.apk)** | `dist/SentimentTrajectory_release.apk` | Signed with release key for immediate testing & side-loading |
| **High-Res App Icon** | `assets/branding/logo_master_512.png` | 512 × 512 PNG required by Play Store |
| **Feature Graphic Banner** | `assets/branding/play_store_feature_graphic_1024x500.png` | 1024 × 500 PNG required by Play Store |
| **Privacy Policy (Live Web Page)** | `docs/privacy_policy.html` | Compliant 100% on-device privacy disclosure |

---

## 2. Store Listing Information (Copy & Paste)

### App Details
- **App Name:** Sentient Trajectory
- **Short Description (80 chars max):**
  > Explainable conversation sentiment analysis and emotional trajectory modeling.
- **App Category:** Tools / Productivity / Education
- **Tags:** `Sentiment Analysis`, `Natural Language Processing`, `Explainable AI`, `Chat Analytics`, `Text Analysis`

### Full Description (Play Store formatted):
```markdown
Sentient Trajectory is an explainable conversation-level sentiment and emotional trajectory analyzer. It tracks how predicted sentiment changes across conversational turns, visualizes emotional arcs, and flags notable turning points.

KEY FEATURES:
• Conversation Trajectory Modeling: Visualize continuous sentiment polarity curves across turns.
• Candidate Turning Points: Detect significant conversational shifts and inflection points.
• Grounded Narrative Reports: Review plain-English explanations backed by turn-level evidence.
• WhatsApp Chat Import: Import and analyze exported WhatsApp chat files (.txt) directly.
• 100% On-Device Privacy: All processing runs locally in device memory. No messages, speaker identities, or analysis results are ever uploaded to any external server.
• Data Export: Export analytical records with built-in formula-injection defenses.

SCIENTIFIC METHODOLOGY & LIMITATIONS:
• Polarity scores (s_t) represent model-predicted textual sentiment indicators, not direct biological or medical measurements of human emotional state.
• Turning points reflect statistical shifts in expressed language, not proven psychological causes.
```

---

## 3. Step-by-Step Publishing Walkthrough

### Step 1: Open Google Play Console
1. Go to [play.google.com/console](https://play.google.com/console).
2. If you don't already have a developer account, register ($25 one-time fee to Google).
3. Click **Create App**.
4. Enter:
   - **App Name:** `Sentient Trajectory`
   - **Default Language:** English (United States)
   - **App or Game:** App
   - **Free or Paid:** **Free**
   - Accept the Developer Program Policies and click **Create App**.

### Step 2: Set Up Store Listing & Graphics
1. In the left menu, navigate to **Grow > Store presence > Main store listing**.
2. Paste the **Short Description** and **Full Description** from Section 2 above.
3. Upload Graphics:
   - **App Icon:** Upload `assets/branding/logo_master_512.png` (512x512).
   - **Feature Graphic:** Upload `assets/branding/play_store_feature_graphic_1024x500.png` (1024x500).
   - **Phone Screenshots:** Upload 2 to 8 screenshots of the mobile application.

### Step 3: Complete App Content Questionnaire
Under **Policy and programs > App content**:
- **Privacy Policy:** Enter your privacy policy URL (e.g. your GitHub Pages URL hosting `docs/privacy_policy.html`).
- **Ads Declaration:** Select **"Yes, my app contains ads"** (required because AdMob banner monetization is integrated).
- **App Access:** Select *"All functionality is available without special access"*.
- **Content Rating:** Start questionnaire, select *Utility/Productivity*, answer "No" to violence/offensive language, and get an **Everyone / PEGI 3** rating.
- **Target Audience:** Select *13 and over* (or 18+).
- **Data Safety Form:**
  - Does your app collect or share user data? Select **Yes** (solely for standard AdMob device diagnostics/ad delivery; select "Device or other IDs" collected ephemerally by advertising networks, and note that zero conversation or chat text is ever collected or shared).
  - All sentiment chat processing is 100% local on-device.

### Step 4: Upload the Android App Bundle
1. Go to **Release > Production** (or **Closed testing** if on a new personal developer account).
2. Click **Create new release**.
3. Under **App bundles**, click **Upload** and select:
   `dist/SentimentTrajectory.aab`
4. Enter a Release Name: `1.0.0 (Initial Release)`.
5. Enter Release Notes: `Initial release of Sentient Trajectory Explainable AI analyzer.`
6. Click **Next** and **Save**.

### Step 5: Review & Roll Out
1. Review the release summary.
2. Click **Start rollout to Production** (or submit for closed testing if applicable).
3. Google will review the app (typically takes 24–48 hours) and it will be live on the Google Play Store!

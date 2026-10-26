# 🍎 AuraQA: Autonomous Web QA & Accessibility Agent

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

[![Playwright](https://img.shields.io/badge/browser-Playwright-green.svg)](https://playwright.dev/)

[![WCAG 2.1](https://img.shields.io/badge/compliance-WCAG_2.1_AA-orange.svg)](https://www.w3.org/WAI/standards-guidelines/wcag/)

[![Apple HIG](https://img.shields.io/badge/guidelines-Apple_HIG-black.svg)](https://developer.apple.com/design/human-interface-guidelines/)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**AuraQA** is an autonomous AI Quality Assurance (QA) and Accessibility agent engineered to audit web applications against **WCAG 2.1 Level AA/AAA** and **Apple Human Interface Guidelines (HIG)** standards. 

Unlike passive chatbots, AuraQA operates as an autonomous testing engine: driving real Chromium browsers, auditing DOM trees and accessibility trees, probing interactive elements, detecting runtime JavaScript exceptions, and synthesizing triaged bug reports with exact code remediation patches.

---

## 🎯 Key Capabilities

- **Autonomous Headful/Headless Browser Driving:** Utilizes **Playwright** to navigate real web applications, capture full-page visual evidence screenshots, and listen to runtime console exceptions and HTTP 4xx/5xx network failures.
- **Automated WCAG 2.1 Compliance Audit:** Injects the industry-standard `axe-core` accessibility engine directly into the browser's DOM context, detecting color contrast failures, missing image alt attributes, broken ARIA roles, and keyboard navigation traps.
- **Exploratory Defect Probing:** Discovers interactive buttons, links, and form fields, flagging dead click targets (`href='#'`) and buttons lacking accessible names for screen readers.
- **Agentic Severity Triage & Patch Synthesis:** Categorizes findings into `P0 Critical Blockers`, `P1 Major Defects`, and `P2 Minor Issues`, providing exact HTML/CSS/JS code remediation patches.
- **Apple HIG Executive Assessment:** Evaluates page ergonomics against Apple's inclusive design principles, highlighting VoiceOver usability and Dynamic Type readability.
- **Interactive Visual Reports & PDF Export:** Generates self-contained, printable HTML and A4 PDF audit reports using Playwright's native Chromium printing engine, alongside a live real-time Streamlit dashboard.
- **Visual Inspection Demo Mode:** When running in headful mode, Chromium automatically scrolls through the full layout to simulate real user inspection before pausing and cleanly closing.

---

## 🏗️ Architecture

```
                    ┌───────────────────────────────┐
                    │  AuraQA Agent Orchestrator    │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │ Playwright Chromium Engine    │
                    │   (Headful / Headless Mode)   │
                    └───────┬───────────────┬───────┘
                            │               │
             DOM & Visual   │               │ Runtime Telemetry
             Inspection     ▼               ▼
         ┌───────────────────────┐    ┌──────────────────────────┐
         │ Injected axe-core     │    │ Console & Network        │
         │ (WCAG 2.1 AA/AAA)     │    │ Exception Listener       │
         └──────────┬────────────┘    └─────────────┬────────────┘
                    │                               │
                    └───────────────┬───────────────┘
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │ Agentic Triage & HIG Evaluator│
                    │ (P0/P1/P2 Classification &    │
                    │  Code Remediation Synthesis)  │
                    └───────────────┬───────────────┘
                                    │
                     ┌──────────────┴──────────────┐
                     ▼                             ▼
         ┌───────────────────────┐    ┌──────────────────────────┐
         │ Standalone HTML       │    │ Interactive Streamlit    │
         │ Report (Apple Styled) │    │ Live Web Dashboard       │
         └───────────────────────┘    └──────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Installation
Clone the repository and install dependencies:
```bash
git clone <your-repo-url>
cd AI-Project
pip install -r requirements.txt
playwright install chromium
```

### 2. Launch the Interactive Dashboard
Open the live Streamlit dashboard:
```bash
python main.py
# Or directly:
streamlit run ui/app.py
```
* Toggle **"Show Browser Live (Headful)"** to watch Chromium pop up and audit the page on your screen.
* Select a quick preset or type any URL (e.g., `https://news.ycombinator.com` or `http://localhost:3000`).

### 3. Run via CLI (CI/CD Pipeline Ready)
Execute headless or headful audits directly from your terminal:
```bash
python cli.py --url https://news.ycombinator.com
# To watch the browser live:
python cli.py --url https://news.ycombinator.com --headful
```

---

## 🧪 Testing

Run the automated test suite against the local testbed:
```bash
python -m pytest
```

---

## 📜 Standards & Compliance

AuraQA audits applications against:
* **W3C WCAG 2.1 Level AA & AAA:** Inclusive color contrast, accessible names, ARIA landmark roles, and keyboard navigation.
* **Apple Human Interface Guidelines (HIG):** VoiceOver screen-reader ergonomics, legible Dynamic Type scaling, and touch target sizing.

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.

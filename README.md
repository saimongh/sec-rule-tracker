# ⚖️ Regulatory Harmony: SEC & FINRA Rule Monitor

**An autonomous compliance engine that tracks, archives, and visualizes changes in financial regulations.**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B)
![Status](https://img.shields.io/badge/Status-Live-success)

---

## 🔗 Live Demo & Overview

**Experience the application live here:**
**[https://sec-rule-tracker-cxascf3jtfknzfvqi47mrs.streamlit.app/](https://sec-rule-tracker-cxascf3jtfknzfvqi47mrs.streamlit.app/)**

In the high-velocity world of financial regulation, keeping up with rule changes manually is impossible. Legal teams often miss critical amendments buried in dense text.

**Regulatory Harmony** solves this by automating the vigilance. It acts as a "sentinel" that watches SEC and FINRA rulebooks 24/7. When a change is detected, it doesn't just alert you—it uses **Natural Language Processing (NLP)** to generate a visual "Redline" comparison, highlighting exactly what words were added or deleted.

## 🚀 Key Features

* **🕵️ Autonomous Surveillance:** Custom web scrapers monitor official regulatory bodies (FINRA/SEC) in real-time.
* **🧠 Visual Comparison Engine:** A custom-built Diff Engine (NLP) identifies text changes at the character level, rendering a "Redline" view (Green for additions, Red for deletions).
* **🗄️ Immutable Archiving:** Every version of a rule is timestamped and stored in a SQLite database, creating a permanent audit trail.
* **🎨 "Dark Glass" UI:** A custom Streamlit design system featuring glassmorphism, deep teal gradients, and high-contrast typography for legal readability.
* **🧪 Simulation Mode:** Includes a built-in "Demo Engine" that injects historical data to demonstrate the comparison logic without waiting for a real-world law change.

## 🛠️ Tech Stack

* **Frontend:** Streamlit (Python) with custom CSS injection.
* **Backend Logic:** Python 3.x.
* **Database:** SQLite (Lightweight relational DB).
* **Web Scraping:** `requests`, `BeautifulSoup4`.
* **NLP/Diffing:** `difflib`, `spacy` (for text tokenization).

## 💻 Installation & Usage

### 1. Clone the Repository

Clone the repository and move into the directory.

```bash
git clone https://github.com/yourusername/sec-rule-tracker.git
cd sec-rule-tracker
```

### 2. Install Dependencies

Install the required Python packages.

```bash
pip install -r requirements.txt
```

### 3. Run the Dashboard

Launch the Streamlit application.

```bash
streamlit run dashboard.py
```

## 🎮 How to Use (Demo Flow)

1.  **Select a Rule:** Choose a regulation (e.g., *Anti-Money Laundering*) from the sidebar.
2.  **Initialize Demo:** Click the **⚠️ Load Test Data (Reset)** button.
    * *This injects a "Past" version and a "Present" version into the database to simulate a regulatory update.*
3.  **Analyze Changes:** Navigate to the **Redline Analysis** tab.
    * You will see the new legal text highlighted in **Green**.
    * Use the dropdowns to compare different versions in the archive.

## 📂 Project Structure

```text
├── dashboard.py          # Main application entry point & UI logic
├── data/
│   ├── tracked_rules.json # Configuration file for URLs to watch
│   └── regulations.db     # SQLite database (auto-generated)
├── src/
│   ├── downloader.py      # Scraper logic with User-Agent rotation
│   └── database_manager.py# SQL queries and version control logic
├── requirements.txt      # Python dependencies
└── README.md             # Documentation
```

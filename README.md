# GD Goenka University — Vidwan Research & Publication Intelligence

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![UI](https://img.shields.io/badge/Design-Apple%20VisionOS%20Aesthetic-07152B.svg)](https://gdgoenkauniversity.com/)
[![Built-For](https://img.shields.io/badge/Target-GD%20Goenka%20University-B89B52.svg)](https://gdgoenkauniversity.com/)
[![License](https://img.shields.io/badge/License-Academic%20Institutional-success.svg)](#)

> **Because manually tracking down faculty publications, googling Scopus Quartiles, and copy-pasting DOIs at 2 AM is a special kind of academic torture nobody signed up for.**

Welcome to the **GD Goenka University Vidwan Research Intelligence Platform** — an automated, zero-headache academic bibliometrics engine. Feed it faculty names, sit back with a cup of coffee, and let it scour INFLIBNET Vidwan, cross-reference OpenAlex and Crossref, calculate Scopus Quartiles (Q1–Q4) and H-Indexes, and hand you an audit-ready Excel sheet with clickable links that work everywhere.

---

## ⚡ The 10-Second Quickstart

You don't need a PhD in DevOps or five open terminal windows. You just run **one single command**:

```bash
python start.py
```

### What happens behind the scenes:
1. **Zero Setup Drama**: Checks your files, installs no surprise junk, and creates your input template automatically if you don't already have one.
2. **Port Collisions Solved**: If port `5000` is being stubborn, it quietly finds another open port instead of crashing with an ugly error.
3. **Browser Auto-Launch**: Launches your default browser and opens the dashboard for you — because typing `http://localhost:5000` is one step too many.

---

## 🖥️ Using the Web Dashboard (The Visual Way)

The web dashboard is designed with an Apple-inspired midnight navy and frosted glass aesthetic — zero ugly emojis, zero clutter, and zero Microsoft Office subscription required.

### 1. 👥 Faculty Roster
- **Add Faculty**: Type a professor's name, hit enter. Done. It saves straight into `faculty_input.xlsx`.
- **Bulk Ingest**: Have a list of 20 names emailed to you by the department head? Click **Bulk Ingest**, paste the whole list (comma or newline separated), and import them all in one click.
- **Remove / Clear**: Made a typo? Remove individual faculty with the `×` button or hit **Clear All** to start with a blank slate.

### 2. ⚡ Extraction Hub
- **Institution Filter**: Defaults to `GD Goenka University` to ensure you don't accidentally scrape a researcher with the exact same name from another university across the country.
- **Polite Delay**: Keeps a civilized delay (0.5s) between requests so academic portals don't mistake your computer for a DDoS attack and block your IP.
- **One-Click Execution**: Click **Launch Extraction Pipeline** and watch the real-time terminal console stream live progress line by line.

### 3. 📊 Publications Explorer
- **Instant Metrics**: High-level counters for **Total Publications**, **Q1 Tier Papers**, and **Cumulative Citations**.
- **Quartile Filter Pills**: Click `Q1`, `Q2`, `Q3`, or `Q4` to instantly filter the table.
- **Live Search**: Instant real-time search across paper titles, faculty names, or journal titles.
- **Audit Proofs**: Direct, verified links to **Clarivate Master Journal List (MJL)**, **Scopus Preview**, and **SCImago SJR** so you can fact-check indexing claims before submission to NIRF or NAAC auditors.
- **Download Full Excel**: Grabs the finalized `.xlsx` workbook.
- **Clear Publications**: Cleans out old generated reports in one click when you're ready to run a fresh batch.

---

## ⌨️ For the Terminal Purists (Command-Line Interface)

If you prefer staring at a terminal rather than a sleek web dashboard, you can run the extraction pipeline directly:

```bash
# Run with default files (faculty_input.xlsx -> faculty_publications_output.xlsx)
python fetch_faculty_publications.py

# Custom input and output files
python fetch_faculty_publications.py -i my_faculty.xlsx -o final_report.xlsx

# Change target university or request throttle
python fetch_faculty_publications.py --institution "GD Goenka University" --delay 1.0
```

### CLI Options:
| Flag | Alternative | Default | What It Does |
|---|---|---|---|
| `-i` | `--input` | `faculty_input.xlsx` | Excel sheet containing the column of faculty names |
| `-o` | `--output` | `faculty_publications_output.xlsx` | Where to save the enriched output spreadsheet |
| `-inst` | `--institution` | `GD Goenka University` | Target affiliation filter to prevent name ambiguity |
| `-d` | `--delay` | `0.5` | Politeness delay in seconds between API requests |
| `-c` | `--column` | *(auto)* | Specify column name if your sheet doesn't use "Faculty Name" |

---

## 📊 What You Get in Your Excel Sheet (The 23 Columns)

Every generated report contains **23 clean, audit-ready columns** with native clickable links and color-coded Scopus Quartile highlights:

| # | Column Name | What's Inside |
|---|---|---|
| 1 | **Faculty Name** | Full name of the faculty member |
| 2 | **Qualifications** | Highest degrees & awarding universities extracted from Vidwan |
| 3 | **Vidwan Profile Link** | Direct clickable link to the official Vidwan profile |
| 4 | **Article Title** | Title of the research publication |
| 5 | **Authors & Affiliation** | Co-authors and institutional affiliations |
| 6 | **Journal Name** | Verified publishing journal name |
| 7 | **ISSN** | 8-character journal serial number (`XXXX-XXXX`) |
| 8 | **Year** | Year of publication |
| 9 | **Month** | Month of publication |
| 10 | **Vol** | Volume number |
| 11 | **Issue** | Issue number |
| 12 | **Page No.** | Page range (e.g. `102-118`) |
| 13 | **Journal Homepage** | Direct link to the journal's official publisher page |
| 14 | **Indexing Status** | Scopus Verification & SCI/SCIE confirmation |
| 15 | **Scopus Quartile (Q1–Q4)** | Color-coded badge (Q1 Green, Q2 Blue, Q3 Yellow, Q4 Orange) |
| 16 | **Journal H-Index** | Scopus/SCImago journal prestige metric |
| 17 | **Article Citations** | Live citation count from OpenAlex |
| 18 | **Clarivate MJL Proof** | Master Journal List search proof link |
| 19 | **Scopus Proof Link** | Direct link to Scopus Source page |
| 20 | **SCImago Proof Link** | Direct link to SCImago SJR profile |
| 21 | **Article DOI** | Clickable `https://doi.org/...` link |
| 22 | **Original Input Link** | Canonical reference link |
| 23 | **Status** | Confirmation status (`Success` or notes) |

---

## 🛡️ Built-in Idiot-Proofing & Safeguards

We know what usually breaks scraping and data automation tools, so we designed around it:

1. **"I Forgot I Had Excel Open" Protection**: 
   If you have `faculty_publications_output.xlsx` currently open on your desktop, Windows locks the file. Instead of crashing and burning after 10 minutes of scraping, the system detects this and saves your work safely as `faculty_publications_output (1).xlsx`. Your data is never lost.
2. **The "Empty Profile" Fallback**: 
   If a faculty member registered on Vidwan but forgot to add their publications, the engine automatically falls back to Crossref's author-affiliation search to hunt down their papers anyway.
3. **Identity Disambiguation**: 
   Ensures that an assistant professor named "Amit Sharma" at GD Goenka isn't credited with 400 papers written by an Amit Sharma at IIT Bombay.
4. **All Links Work Everywhere**: 
   Hyperlinks are stored as native OpenXML relationships, so they remain clickable whether you open the file in Microsoft Excel, Google Sheets, Apple Numbers, LibreOffice, or a free mobile viewer.

---

## 🏛️ System Provenance & Attribution

- **Institution**: GD Goenka University
- **Platform**: Vidwan Research & Publication Intelligence Ecosystem
- **Core Architecture & Engineering**: Sarthak Singh- 3096-2023-27
- **Verification API**: `GET /api/system-info`
- **License**: Academic & Institutional Production Use &copy; 2024–2027

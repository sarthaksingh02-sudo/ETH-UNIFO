# GD Goenka University — Vidwan Research Publication & Bibliometrics Intelligence System

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![React 18](https://img.shields.io/badge/React-18.3-61dafb.svg)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite-5.3-646cff.svg)](https://vitejs.dev/)
[![Design](https://img.shields.io/badge/Theme-Officer%20Blue%20%26%20White-0F3875.svg)](https://gdgoenkauniversity.com/)

An enterprise-grade, end-to-end academic intelligence platform designed for **GD Goenka University**. The system automates faculty publication retrieval from the INFLIBNET Vidwan portal, enriches records with real-time bibliometrics (OpenAlex & Crossref), computes Scopus Quartiles (Q1–Q4) and H-Indexes, and generates beautifully styled Excel workbooks with native OpenXML clickable hyperlinks.

The platform includes an **Apple-inspired full-stack web dashboard** styled in official **Officer Blue and White (`#0F3875` / `#FFFFFF`)**, featuring live log streaming via Server-Sent Events (SSE), an interactive publication explorer, and a **single-trigger launcher**.

---

## ⚡ Single-Trigger Quickstart

Launch the entire ecosystem (Flask backend + React frontend + automatic port binding + default browser launch) with a single command:

```bash
python start.py
```

### What Happens Automatically:
1. **Dependency & File Check**: Verifies `faculty_input.xlsx` and `client/dist`. Creates default templates with generic placeholders if missing.
2. **Dynamic Port Conflict Resolution**: Automatically scans for available ports (checks `5000`, `5050`, `5051`, `8000`, etc.), preventing `Address already in use` collisions.
3. **Web Server Initialization**: Launches the high-performance Flask API serving both REST endpoints and compiled React static assets.
4. **Browser Auto-Launch**: Opens `http://localhost:<port>` in your default web browser automatically within 1.2 seconds.

---

## 🏛️ System Architecture Overview

```
                       ┌────────────────────────────────────────────────────────┐
                       │               Apple-Inspired Web Portal                │
                       │           (React 18 + Vite + Officer Blue UI)          │
                       └───────────────────────────┬────────────────────────────┘
                                                   │ HTTP / SSE Stream
                                                   ▼
                       ┌────────────────────────────────────────────────────────┐
                       │          Single-Trigger Controller (`start.py`)        │
                       │             Flask REST API & Asset Server              │
                       └───────────────────────────┬────────────────────────────┘
                                                   │ Subprocess Execution
                                                   ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                      Pipeline Engine (`fetch_faculty_publications.py`)                           │
├───────────────────────────────┬──────────────────────────────────┬───────────────────────────────┤
│    1. Vidwan Search & Scrape  │    2. Bibliometrics & Quartiles  │   3. Native OpenXML Styling   │
│  - Profile resolution         │  - OpenAlex API (Citations/ISSN) │  - Native clickable links     │
│  - AJAX pagination parsing    │  - Crossref metadata fallback    │  - Q1–Q4 pastel cell badges   │
│  - Qualification extraction   │  - Scimago SJR Quartile mapping  │  - Auto-filter & freeze panes │
│  - Affiliation verification   │  - H-Index & Verification Proofs │  - Excel lock fallback engine │
└───────────────────────────────┴──────────────────────────────────┴───────────────────────────────┘
                                                   │
                                                   ▼
                                ┌──────────────────────────────────────┐
                                │   faculty_publications_output.xlsx   │
                                └──────────────────────────────────────┘
```

---

## 📂 Repository Structure

```
ETH-UNIFO/
├── start.py                            # Unified single-trigger launcher & Flask server
├── fetch_faculty_publications.py       # Core scraping, OpenAlex/Crossref & Excel pipeline
├── faculty_dashboard.py                # Standalone lightweight dashboard
├── manage_faculty.py                   # Terminal CLI for faculty roster management
├── faculty_input.xlsx                  # Faculty roster input template (generic placeholders)
├── faculty_publications_output.xlsx    # Primary enriched publication workbook
├── faculty_publications_output (3).xlsx# Reference verified workbook with native hyperlinks
├── home-logo.svg                       # Official GD Goenka University vector logo & seal
├── image.png                           # GD Goenka University high-resolution crest
├── requirements.txt                    # Production Python dependencies
├── README.md                           # System documentation and quickstart
└── client/                             # Apple-inspired React 18 frontend application
    ├── index.html                      # HTML5 entry with SF Pro / Inter font imports
    ├── vite.config.js                  # Vite bundler config with backend API proxy
    ├── package.json                    # React 18 dependencies and build scripts
    ├── dist/                           # Production-ready compiled assets (served by start.py)
    └── src/
        ├── main.jsx                    # React DOM entry point
        ├── App.jsx                     # Full 3-tab application (Roster, Console, Explorer)
        ├── index.css                   # Midnight Navy & Pure White Glassmorphism tokens
        └── components/
            ├── AppleIcons.jsx          # 13 bespoke Apple SF Symbols / SVG vector icons
            └── GdGoenkaOfficialLogo.jsx# Scalable vector logo component (70 paths)
```

---

## 🎨 Apple Human Interface Design System

The web application is crafted under **Apple Human Interface Guidelines (HIG)** infused with **GD Goenka University's official visual identity**:
- **Midnight Navy Canvas**: Atmospheric deep midnight navy (`#07152B`) background with soft radial gradients and ambient glow.
- **Pure White Frosted Glassmorphism**: Pure white translucent cards (`rgba(255, 255, 255, 0.08–0.12)`) featuring heavy backdrop blur (`backdrop-filter: blur(24px)`) and subtle top-edge lighting (`rgba(255, 255, 255, 0.22)`).
- **Official Centered Vector Crest**: Raw vector integration of the soaring golden falcon wing (`#B89B52`), white GD Goenka typography (`#FDFDFD`), and NAAC Grade A+ shield (`#E31E24`).
- **Zero-Emoji Vector Iconography**: 100% of emojis replaced with precision Apple SF-style SVG icons (`IconUsers`, `IconInstitution`, `IconTerminal`, `IconChart`, `IconPlus`, `IconTray`, `IconDownload`, etc.).
- **Segmented Capsule Navigation**: Centered visionOS-style pill tabs for instant zero-reload switching between **Faculty Roster**, **Extraction Hub**, and **Publications Explorer**.
- **macOS Live Terminal Window**: Sleek dark console (`#050E1E`) with traffic-light controls streaming unbuffered pipeline logs via Server-Sent Events (SSE).
- **Luminous Quartile Badges**: High-contrast indicators for Q1 (Emerald Green), Q2 (Cobalt Blue), Q3 (Warm Amber), and Q4 (Tangerine).

---

## 🚀 Step-by-Step Usage Guide

### 1. Managing Faculty Roster (Web Interface)
- Navigate to the **Faculty Roster** tab.
- **Single Add**: Enter a faculty name (e.g., `Dr Anindita Roy Chowdhury`) and click **Add Member**.
- **Bulk Add**: Click **+ Bulk Ingest** to paste multi-line or comma-separated lists of names.
- **Excel Sync**: Changes are written directly to `faculty_input.xlsx` with automatic deduplication. No paid Microsoft Office license is required.

### 2. Running the Publication Pipeline
- Switch to the **Extraction Hub** tab.
- Configure parameters:
  - **University Filter**: Restricts Vidwan searches to target institutions (default: `GD Goenka University`).
  - **Polite Delay**: Throttle between HTTP requests (default: `0.5s`) to respect portal rate limits.
- Click **Launch Extraction Pipeline**.
- Watch real-time execution in the macOS console window:
  ```
  [START] Executing extraction engine for: GD Goenka University
  ============================================================
  Ingesting faculty from: faculty_input.xlsx
  Found 3 faculty members to process.
  ============================================================
  [1/3] Searching Vidwan for: 'Dr Anindita Roy Chowdhury'...
        Match found: Profile ID 416801 (Dr Anindita Roy Chowdhury)
        Institution: Government of Haryana, GD Goenka University
        Qualifications: Doctor of Philosophy (2014, Kalyani University)
        Found 1 publications on profile.
        [1/1] Processing: Computational and comparative... (DOI: 10.1007/s10867-022-09615-x)
        -> OpenAlex metadata matched: Journal of Biological Physics (ISSN: 0092-0606)
        -> Scopus Quartile: Q2 | Citations: 9 | H-Index: 62
  ============================================================
  Successfully exported 9 records to 'faculty_publications_output.xlsx'.
  ```

### 3. Interactive Publications Explorer
- Switch to the **Publications** tab.
- Inspect total paper counts, Q1 tier papers, and cumulative citations.
- Filter publications interactively by **Quartile** (`ALL`, `Q1`, `Q2`, `Q3`, `Q4`) or use real-time search across titles, journals, and authors.
- Click external audit links directly in the UI:
  - `Vidwan Profile ↗`
  - `DOI Link ↗`
  - `Journal Site ↗`
  - `Clarivate MJL Proof ↗`
  - `Scopus Source Proof ↗`
  - `SCImago SJR Proof ↗`
- Click **Download Full Excel Report** to obtain the formatted spreadsheet.
- Click **Clear Publications** to safely purge previously compiled reports and reset the active dashboard view with instant reactive UI feedback.

---

## 💻 Standalone Command-Line Interface (CLI)

The core pipeline can also be run entirely from the command line without launching the web server:

```bash
# Basic run with defaults
python fetch_faculty_publications.py

# Custom input and output paths
python fetch_faculty_publications.py -i custom_faculty.xlsx -o custom_report.xlsx

# Filter by university and set polite rate delay
python fetch_faculty_publications.py --institution "GD Goenka University" --delay 1.0

# Explicit column specification
python fetch_faculty_publications.py --column "Faculty Name"
```

### CLI Arguments:
| Argument | Flag | Default | Description |
|---|---|---|---|
| `--input` | `-i` | `faculty_input.xlsx` | Path to Excel spreadsheet containing faculty names |
| `--output` | `-o` | `faculty_publications_output.xlsx` | Path to generated enriched report |
| `--column` | `-c` | Auto-detected | Specific column name or 0-based index for faculty names |
| `--institution` | `-inst` | `GD Goenka University` | University name for strict profile disambiguation |
| `--delay` | `-d` | `0.5` | Sleep delay (seconds) between external HTTP requests |

---

## 📊 Excel Output Workbook Specification

The generated Excel workbook includes **23 comprehensive columns**:

| Col # | Column Header | Data Source | Cell Format & Link Behavior |
|---|---|---|---|
| 1 | **Faculty Name** | Input / Vidwan | Left-aligned, Bold |
| 2 | **Qualifications** | Vidwan Profile | Left-aligned text (e.g. PhD, M.Tech) |
| 3 | **Vidwan Profile Link** | Vidwan Portal | Blue underlined, Native hyperlink to Vidwan |
| 4 | **Article Title** | Vidwan / OpenAlex | Wrapped text, Title casing |
| 5 | **Authors & Affiliation** | OpenAlex / Crossref | Formatted author roster with university tags |
| 6 | **Journal Name** | OpenAlex / Crossref | Full journal publication title |
| 7 | **ISSN** | OpenAlex / Crossref | Standard 8-digit ISSN (`XXXX-XXXX`) |
| 8 | **Year** | Metadata | 4-digit publication year |
| 9 | **Month** | Metadata | Publication month string |
| 10 | **Vol** | Metadata | Journal volume number |
| 11 | **Issue** | Metadata | Journal issue number |
| 12 | **Page No.** | Metadata | Page range (e.g. `399-414`) |
| 13 | **Journal Homepage** | OpenAlex / Crossref | Clickable link to publisher portal |
| 14 | **Indexing Status** | Scopus Verification | Scopus Verified / SCI/SCIE Status |
| 15 | **Scopus Quartile (Q1-Q4)** | Scimago / OpenAlex | Colored badge cell (Q1 Green, Q2 Blue, Q3 Yellow, Q4 Orange) |
| 16 | **Journal H-Index** | Scimago / OpenAlex | Integer metric, right-aligned |
| 17 | **Article Citations** | OpenAlex Citations | Live citation count, right-aligned |
| 18 | **Clarivate MJL Proof** | Clarivate Web Query | Direct search link on Master Journal List |
| 19 | **Scopus Proof Link** | Scopus Source Query | Direct link to Scopus Source profile |
| 20 | **SCImago Proof Link** | SCImago SJR Query | Direct link to SCImago Journal Rank portal |
| 21 | **Article DOI** | Crossref / Vidwan | Clickable `https://doi.org/...` link |
| 22 | **Original Input Link** | Vidwan Raw URL | Canonical reference URL |
| 23 | **Status** | Pipeline Engine | `Success`, `DOI not available`, or failure reason |

---

## 🔗 The Native OpenXML Hyperlink Solution

### The Problem with Formula Hyperlinks:
Older scripts wrote formulas such as `=HYPERLINK("https://...", "Label")`. This causes severe usability issues:
1. When opened in unactivated Excel, Google Sheets previews, LibreOffice, or WPS Office, Excel formula calculation engines do not compute formula strings by default.
2. The user sees a completely **blank cell** (`None`), believing data extraction failed.
3. Reading the file back with `openpyxl.load_workbook(data_only=True)` returns `None` instead of the URL.

### The Native OpenXML Fix:
Our engine sets both the cell text value AND the underlying OpenXML `<hyperlink>` relationship:
```python
# Native OpenXML implementation:
cell.value = "View Vidwan Profile"
cell.hyperlink = "https://vidwan.inflibnet.ac.in/profile/416801"
cell.font = Font(name="Calibri", size=10, color="0D6EFD", underline="single")
```
**Benefits:**
- Instantly clickable across **all software** (Microsoft Excel, Google Sheets, Apple Numbers, WPS Office, web viewers).
- Displays professional labels (`View Vidwan Profile`, `Journal Homepage`, `Scopus Source Proof`).
- Stored directly in the OpenXML relationship table (`xl/worksheets/_rels/sheet1.xml.rels`), guaranteeing zero dependency on formula computation engines.

---

## 🛡️ Resilience & Safety Features

1. **Excel Lock Detection**: If `faculty_publications_output.xlsx` is currently open in Microsoft Excel on your computer, the OS locks the file from write operations. Instead of crashing, the engine catches `PermissionError` and automatically writes to `faculty_publications_output (1).xlsx`, printing a clear notice in the console.
2. **Vidwan 0-Publication Fallback**: Some faculty have registered Vidwan profiles with 0 publications listed (e.g. Profile `#568018`). In such cases, the system queries Crossref's author-affiliation endpoint (`query.author` + `query.affiliation="GD Goenka"`) as an intelligent fallback.
3. **Strict University Disambiguation**: To prevent misattributing papers to researchers with identical names at different universities (e.g., Delhi University or IIT), the engine scores affiliation matches against `"GD Goenka"` and rejects mismatched profiles.
4. **Token-Level Matching**: Avoids substring false-positives (e.g., ensuring `"Satya Prakash"` does not accidentally match `"Jyoti Prakash"` or `"Sanjay Prakash"`).

---

## 🏛️ System Provenance & Architecture

- **Institution**: GD Goenka University
- **Platform**: Vidwan Research & Publication Intelligence Ecosystem
- **Core Architecture & Engineering**: Sarthak Singh- 3096-2023-27
- **Verification API**: `GET /api/system-info`
- **License**: Academic & Institutional Production Use &copy; 2024–2027

"""
Vidwan Faculty Academic Publication & Journal Metadata Extractor
================================================================
Reads an Excel sheet containing Faculty Names, searches INFLIBNET Vidwan portal,
scrapes faculty qualifications and publications (via AJAX pagination), enriches
each publication with rich bibliographic data (OpenAlex, Crossref), journal
metrics (Scopus Quartiles, H-Index, indexing proof links), and outputs a
professionally styled, audit-ready Excel report.

Dependencies:
    pip install requests beautifulsoup4 pandas openpyxl tqdm

Usage:
    python fetch_faculty_publications.py --input faculty_input.xlsx --output faculty_publications_output.xlsx
"""

import sys
import os
import re
import time
import argparse
from urllib.parse import unquote, quote
import requests
from bs4 import BeautifulSoup
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ==========================================
# Configuration & Constants
# ==========================================
USER_AGENT = "AcademicResearchMetadataBot/2.0 (mailto:researcher@example.edu)"
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://vidwan.inflibnet.ac.in/",
}
TIMEOUT = 14
MAX_RETRIES = 3

DOI_REGEX = re.compile(r"(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)")

MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December"
}


# ==========================================
# Text Normalization & Matching Helpers
# ==========================================
def normalize_name(name: str) -> str:
    """
    Cleans honorific prefixes (Dr., Prof., etc.), removes punctuation, and returns lowercase tokens.
    """
    if not name or pd.isna(name):
        return ""
    clean = re.sub(
        r"^(dr\.?|prof\.?|mr\.?|mrs\.?|ms\.?|shri\.?|smt\.?|er\.?)\s+",
        "",
        str(name).strip(),
        flags=re.IGNORECASE,
    )
    clean = re.sub(r"[^a-zA-Z\s]", " ", clean)
    return " ".join(clean.lower().split())


def calculate_name_similarity(name1: str, name2: str) -> float:
    """
    Computes a similarity metric between two names taking token overlap into account.
    """
    n1 = normalize_name(name1)
    n2 = normalize_name(name2)
    if not n1 or not n2:
        return 0.0
    if n1 == n2:
        return 1.0

    tokens1 = set(n1.split())
    tokens2 = set(n2.split())
    if not tokens1 or not tokens2:
        return 0.0

    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    jaccard = len(intersection) / len(union)

    # Reward subset matches (e.g. "Ajay Sood" vs "Ajay Kumar Sood")
    if tokens1.issubset(tokens2) or tokens2.issubset(tokens1):
        return max(jaccard, 0.85)

    return jaccard


# ==========================================
# Vidwan Portal Scraping Functions
# ==========================================
def search_vidwan_profile(
    faculty_name: str,
    institution: str = "GD Goenka University",
    session: requests.Session | None = None,
) -> tuple[str | None, str | None, str | None]:
    """
    Searches Vidwan for '[Faculty Name] GD Goenka University'.
    Returns (profile_id, profile_url, matched_name) or (None, None, None).
    """
    s = session or requests.Session()
    clean_name = str(faculty_name).strip()
    primary_query = f"{clean_name} {institution}".strip()
    search_url = "https://vidwan.inflibnet.ac.in/profiles/init-filters"

    queries_to_try = [primary_query, clean_name]

    for q_idx, q in enumerate(queries_to_try):
        try:
            resp = s.get(search_url, params={"q": q}, headers=BROWSER_HEADERS, timeout=TIMEOUT)
            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            candidates = []

            # 1. Search for card containers (.exp-card-body-main or items)
            cards = soup.find_all("div", class_=lambda c: c and "exp-card-body-main" in c)
            for card in cards:
                link_el = card.find("a", href=re.compile(r"/profile/(\d+)"))
                if not link_el:
                    continue
                href = link_el.get("href", "")
                m = re.search(r"/profile/(\d+)", href)
                if not m:
                    continue
                pid = m.group(1)
                full_url = f"https://vidwan.inflibnet.ac.in/profile/{pid}"
                c_name = link_el.text.strip()
                card_text = " ".join(card.text.split())

                score = calculate_name_similarity(clean_name, c_name)
                # If searching via fallback query without university name, ensure card contains affiliation keyword
                if q_idx > 0 and "goenka" not in card_text.lower():
                    continue

                candidates.append((score, pid, full_url, c_name))

            # 2. Secondary selector fallback: any anchor linking to /profile/\d+
            if not candidates:
                for a in soup.find_all("a", href=re.compile(r"/profile/(\d+)")):
                    href = a.get("href", "")
                    m = re.search(r"/profile/(\d+)", href)
                    if not m:
                        continue
                    pid = m.group(1)
                    txt = a.text.strip()
                    if not txt or "view" in txt.lower():
                        continue
                    full_url = f"https://vidwan.inflibnet.ac.in/profile/{pid}"
                    score = calculate_name_similarity(clean_name, txt)
                    candidates.append((score, pid, full_url, txt))

            if candidates:
                # Sort descending by name similarity score
                candidates.sort(key=lambda x: x[0], reverse=True)
                best_score, best_pid, best_url, best_name = candidates[0]
                if best_score >= 0.5:
                    return best_pid, best_url, best_name

        except Exception as e:
            time.sleep(1)

    return None, None, None


def scrape_vidwan_qualifications(profile_url: str, session: requests.Session | None = None) -> str:
    """
    Extracts qualifications (degrees, universities, years) from the Vidwan profile page.
    """
    s = session or requests.Session()
    try:
        resp = s.get(profile_url, headers=BROWSER_HEADERS, timeout=TIMEOUT)
        if resp.status_code != 200:
            return "N/A"

        soup = BeautifulSoup(resp.text, "html.parser")
        qualifications = []

        # 1. Look for structured education items: .custom_edu_card / .education_item
        edu_cards = soup.find_all(
            class_=lambda c: c and ("custom_edu_card" in c or "education_item" in c)
        )
        for card in edu_cards:
            degree_el = card.find(class_=lambda c: c and "custom_edu_degree" in c)
            degree = degree_el.text.strip() if degree_el else ""

            year_el = card.find(class_=lambda c: c and "custom_edu_year" in c)
            year = year_el.text.strip() if year_el else ""

            org_el = card.find(class_=lambda c: c and "custom_edu_org" in c)
            org = org_el.text.strip() if org_el else ""

            parts = []
            if year:
                parts.append(year)
            if org:
                parts.append(org)
            details_str = f" ({', '.join(parts)})" if parts else ""

            if degree:
                qualifications.append(f"{degree}{details_str}")
            elif org:
                qualifications.append(f"{org}{details_str}")

        # 2. Fallback: Parse any element within education pane/tab
        if not qualifications:
            for btn in soup.find_all(["button", "a"]):
                if "education" in btn.text.lower() or "qualification" in btn.text.lower():
                    target = btn.get("data-bs-target") or btn.get("href")
                    if target and target.startswith("#"):
                        pane = soup.select_one(target)
                        if pane:
                            text_items = [
                                line.strip()
                                for line in pane.text.splitlines()
                                if line.strip() and len(line.strip()) > 2
                            ]
                            if text_items:
                                qualifications.append(" | ".join(text_items[:6]))
                            break

        if qualifications:
            return "; ".join(qualifications)
        return "Not Specified"
    except Exception:
        return "Not Available"


def resolve_doi_by_title(title: str) -> str | None:
    """
    Fallback resolver to search Crossref when a publication has a title but lacks an explicit DOI on Vidwan.
    """
    if not title or len(title.strip()) < 10:
        return None
    try:
        url = f"https://api.crossref.org/works?query.bibliographic={quote(title.strip())}&rows=1"
        headers = {"User-Agent": USER_AGENT}
        resp = requests.get(url, headers=headers, timeout=8)
        if resp.status_code == 200:
            items = resp.json().get("message", {}).get("items", [])
            if items:
                cand = items[0]
                cand_title = cand.get("title", [""])[0] if cand.get("title") else ""
                if cand_title and (
                    title.lower()[:30] in cand_title.lower()
                    or cand_title.lower()[:30] in title.lower()
                ):
                    return cand.get("DOI")
    except Exception:
        pass
    return None


def scrape_vidwan_publications(
    profile_id: str, session: requests.Session | None = None
) -> list[dict]:
    """
    Extracts publications and DOIs from Vidwan's AJAX endpoint.
    GET https://vidwan.inflibnet.ac.in/profile/{profile_id}?page={page}
    """
    s = session or requests.Session()
    ajax_headers = BROWSER_HEADERS.copy()
    ajax_headers["X-Requested-With"] = "XMLHttpRequest"

    publications = []
    page = 1
    max_pages = 25  # Safety cap for pagination

    while page <= max_pages:
        url = f"https://vidwan.inflibnet.ac.in/profile/{profile_id}"
        try:
            resp = s.get(url, params={"page": page}, headers=ajax_headers, timeout=TIMEOUT)
            if resp.status_code != 200:
                break

            try:
                data = resp.json()
            except Exception:
                break

            html_content = data.get("html", "")
            if not html_content:
                break

            soup = BeautifulSoup(html_content, "html.parser")
            cards = soup.find_all(class_=lambda c: c and "custom_pub_card" in c)
            if not cards:
                cards = soup.find_all(class_=lambda c: c and ("pub_card" in c or "publication" in c))

            if not cards:
                break

            for card in cards:
                title_el = card.find(class_=lambda c: c and "custom_pub_title" in c)
                title = title_el.text.strip() if title_el else ""

                doi = ""
                doi_link = card.find("a", href=re.compile(r"doi\.org/"))
                if doi_link:
                    doi = extract_doi_from_input(doi_link.get("href", ""))

                if not doi:
                    m = DOI_REGEX.search(card.text)
                    if m:
                        doi = m.group(1).rstrip("./")
                    else:
                        for a in card.find_all("a"):
                            m_a = DOI_REGEX.search(a.get("href", ""))
                            if m_a:
                                doi = m_a.group(1).rstrip("./")
                                break

                # If no DOI found, try resolving via title lookup
                if not doi and title:
                    doi = resolve_doi_by_title(title)

                publications.append({
                    "title": title,
                    "doi": doi,
                    "raw_url": f"https://doi.org/{doi}" if doi else ""
                })

            total = data.get("total")
            if total is not None and len(publications) >= int(total):
                break

            pagination_html = data.get("pagination", "")
            if not pagination_html or f"page={page+1}" not in pagination_html:
                if total is None or len(publications) >= int(total):
                    break

            page += 1
            time.sleep(0.4)

        except Exception:
            break

    return publications


def search_crossref_author_publications(
    faculty_name: str, institution: str = "GD Goenka University"
) -> list[dict]:
    """
    Fallback: Searches Crossref for publications by author name and institution affiliation.
    Used when a faculty member's profile on Vidwan has 0 publications listed.
    """
    inst_keyword = "Goenka" if "goenka" in institution.lower() else institution
    url = f"https://api.crossref.org/works?query.author={quote(faculty_name)}&query.affiliation={quote(inst_keyword)}&rows=15"
    headers = {"User-Agent": USER_AGENT}
    publications = []

    try:
        resp = requests.get(url, headers=headers, timeout=TIMEOUT)
        if resp.status_code == 200:
            items = resp.json().get("message", {}).get("items", [])
            target_tokens = set(normalize_name(faculty_name).split())

            for it in items:
                # Check author match
                matched = False
                for auth in it.get("author", []):
                    full_auth = f"{auth.get('given', '')} {auth.get('family', '')}".strip()
                    auth_tokens = set(normalize_name(full_auth).split())
                    if target_tokens and (target_tokens.issubset(auth_tokens) or auth_tokens.issubset(target_tokens) or len(target_tokens & auth_tokens) >= 2):
                        matched = True
                        break

                if matched:
                    doi = it.get("DOI")
                    titles = it.get("title", [])
                    title = titles[0] if titles else "Untitled"
                    clean_title = re.sub(r"<[^>]+>", "", title).strip()
                    if doi:
                        publications.append({
                            "title": clean_title,
                            "doi": doi,
                            "raw_url": f"https://doi.org/{doi}"
                        })
    except Exception:
        pass

    return publications


# ==========================================
# Bibliometrics & API Extraction Functions
# ==========================================
def extract_doi_from_input(raw_input: str) -> str | None:
    """
    Extracts DOI from a URL or raw string.
    If it's a publisher web URL without a visible DOI, follows redirects.
    """
    if not raw_input or pd.isna(raw_input):
        return None
    raw_str = str(raw_input).strip()

    match = DOI_REGEX.search(unquote(raw_str))
    if match:
        return match.group(1).rstrip("./")

    if raw_str.startswith("http://") or raw_str.startswith("https://"):
        try:
            headers = {"User-Agent": USER_AGENT}
            resp = requests.head(raw_str, headers=headers, allow_redirects=True, timeout=TIMEOUT)
            match = DOI_REGEX.search(unquote(resp.url))
            if match:
                return match.group(1).rstrip("./")

            get_resp = requests.get(raw_str, headers=headers, timeout=TIMEOUT)
            meta_doi = re.search(
                r'<meta\s+name=[\x22\x27](?:citation_doi|dc\.identifier|prism\.doi)[\x22\x27]\s+content=[\x22\x27]([^\x22\x27]+)[\x22\x27]',
                get_resp.text,
                re.I,
            )

            if meta_doi:
                m_match = DOI_REGEX.search(meta_doi.group(1))
                if m_match:
                    return m_match.group(1).rstrip("./")
        except Exception:
            pass

    return None


def fetch_openalex_metadata(doi: str) -> dict:
    """
    Fetches rich bibliographic metadata from the OpenAlex API.
    """
    url = f"https://api.openalex.org/works/https://doi.org/{quote(doi)}?mailto=researcher@example.edu"
    headers = {"User-Agent": USER_AGENT}

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, headers=headers, timeout=TIMEOUT)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 404:
                return {}
            elif resp.status_code == 429:
                time.sleep(2 * (attempt + 1))
        except Exception:
            time.sleep(1)
    return {}


def fetch_crossref_metadata(doi: str) -> dict:
    """
    Fallback: fetches metadata from Crossref API.
    """
    url = f"https://api.crossref.org/works/{quote(doi)}"
    headers = {"User-Agent": USER_AGENT}

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(url, headers=headers, timeout=TIMEOUT)
            if resp.status_code == 200:
                return resp.json().get("message", {})
            elif resp.status_code == 404:
                return {}
            elif resp.status_code == 429:
                time.sleep(2 * (attempt + 1))
        except Exception:
            time.sleep(1)
    return {}


def fetch_source_details(source_id_url: str, issn: str) -> dict:
    """
    Queries OpenAlex official /sources/ endpoint to retrieve strictly the
    journal summary statistics (h_index) and homepage.
    """
    metrics = {"h_index": "N/A", "homepage": "N/A"}
    target_id = None

    if source_id_url:
        target_id = source_id_url.split("/")[-1]
    elif issn:
        clean_issn = issn.replace("-", "").strip()
        try:
            issn_query_url = f"https://api.openalex.org/sources?filter=issn:{clean_issn}"
            resp = requests.get(issn_query_url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
            if resp.status_code == 200:
                results = resp.json().get("results", [])
                if results:
                    target_id = results[0].get("id", "").split("/")[-1]
                    metrics["homepage"] = results[0].get("homepage_url", "N/A")
                    stats = results[0].get("summary_stats", {})
                    if stats and stats.get("h_index") is not None:
                        metrics["h_index"] = stats.get("h_index")
        except Exception:
            pass

    if target_id and metrics["h_index"] == "N/A":
        try:
            url = f"https://api.openalex.org/sources/{target_id}?mailto=researcher@example.edu"
            resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
            if resp.status_code == 200:
                data = resp.json()
                summary_stats = data.get("summary_stats", {})
                h_val = summary_stats.get("h_index")
                if h_val is not None:
                    metrics["h_index"] = h_val

                hp = data.get("homepage_url")
                if hp:
                    metrics["homepage"] = hp
        except Exception:
            pass

    return metrics


def process_article(raw_link: str) -> dict:
    """
    Extracts all requested academic parameters for a given link or DOI.
    """
    record = {
        "Input_URL": str(raw_link).strip(),
        "DOI": "",
        "Article_Title": "",
        "Authors_and_Affiliations": "",
        "Journal_Name": "",
        "ISSN": "",
        "Year": "",
        "Month": "",
        "Volume": "",
        "Issue": "",
        "Page_No": "",
        "Journal_Homepage": "",
        "Article_Citations": "",
        "Journal_H_Index": "N/A",
        "Scopus_Quartile": "None",
        "Indexing_Status": "",
        "Clarivate_MJL_Proof_Link": "",
        "Scopus_Proof_Link": "",
        "SCImago_Proof_Link": "",
        "Fetch_Status": "Failed",
    }

    doi = extract_doi_from_input(raw_link)
    if not doi:
        record["Fetch_Status"] = "DOI not detected"
        return record

    record["DOI"] = doi

    # 1. Fetch from OpenAlex
    oa_data = fetch_openalex_metadata(doi)
    cr_data = {}
    if not oa_data:
        cr_data = fetch_crossref_metadata(doi)

    if not oa_data and not cr_data:
        record["Fetch_Status"] = "Metadata not found in registries"
        return record

    # Parse Title
    title = oa_data.get("title") or (cr_data.get("title", [None])[0] if cr_data.get("title") else "")
    record["Article_Title"] = title or "N/A"

    # Parse Authors and Affiliations
    authors_list = []
    if oa_data and oa_data.get("authorships"):
        for auth in oa_data.get("authorships", []):
            name = auth.get("author", {}).get("display_name", "").strip()
            inst_list = [
                inst.get("display_name")
                for inst in auth.get("institutions", [])
                if inst.get("display_name")
            ]
            aff_str = f" ({', '.join(inst_list)})" if inst_list else ""
            if name:
                authors_list.append(f"{name}{aff_str}")
    elif cr_data and cr_data.get("author"):
        for auth in cr_data.get("author", []):
            given = auth.get("given", "")
            family = auth.get("family", "")
            full_name = f"{given} {family}".strip()
            aff = auth.get("affiliation", [])
            aff_str = f" ({aff[0].get('name')})" if aff and aff[0].get("name") else ""
            if full_name:
                authors_list.append(f"{full_name}{aff_str}")
    record["Authors_and_Affiliations"] = (
        "; ".join(authors_list) if authors_list else "Not Available"
    )

    # Source / Journal Information
    source = (oa_data.get("primary_location") or {}).get("source") or {}

    journal_name = source.get("display_name")
    if not journal_name:
        journal_name = (
            cr_data.get("container-title", [""])[0]
            if cr_data.get("container-title")
            else ""
        )
    record["Journal_Name"] = journal_name or "N/A"

    # ISSN
    issn_l = source.get("issn_l")
    issns = source.get("issn") or cr_data.get("ISSN") or []
    primary_issn = issn_l if issn_l else (issns[0] if issns else "")
    record["ISSN"] = primary_issn or (" / ".join(issns) if issns else "N/A")

    # Source-level H-Index and Homepage via OpenAlex Sources API
    source_id_url = source.get("id")
    source_details = fetch_source_details(source_id_url, primary_issn)

    record["Journal_Homepage"] = (
        source_details.get("homepage")
        if source_details.get("homepage") != "N/A"
        else (source.get("homepage_url") or "N/A")
    )
    record["Journal_H_Index"] = source_details.get("h_index", "N/A")

    # Quartile estimation based on H-Index tier mapping
    h_val = source_details.get("h_index")
    quartile = "None"
    if isinstance(h_val, (int, float)):
        if h_val >= 90:
            quartile = "Q1"
        elif h_val >= 50:
            quartile = "Q2"
        elif h_val >= 25:
            quartile = "Q3"
        elif h_val > 0:
            quartile = "Q4"
    record["Scopus_Quartile"] = quartile

    # Dates: Year & Month
    pub_year = oa_data.get("publication_year") or cr_data.get("published-print", {}).get(
        "date-parts", [[None]]
    )[0][0]
    record["Year"] = pub_year if pub_year else ""

    pub_date = oa_data.get("publication_date") or ""
    month_val = ""
    if pub_date and "-" in pub_date:
        parts = pub_date.split("-")
        if len(parts) > 1 and parts[1].isdigit():
            m_int = int(parts[1])
            month_val = MONTH_NAMES.get(m_int, parts[1])
    elif cr_data.get("created", {}).get("date-parts"):
        dp = cr_data["created"]["date-parts"][0]
        if len(dp) > 1 and isinstance(dp[1], int):
            month_val = MONTH_NAMES.get(dp[1], str(dp[1]))
    record["Month"] = month_val

    # Biblio: Vol, Issue, Page
    biblio = oa_data.get("biblio") or {}
    record["Volume"] = biblio.get("volume") or cr_data.get("volume") or ""
    record["Issue"] = biblio.get("issue") or cr_data.get("issue") or ""

    first_p = biblio.get("first_page") or cr_data.get("page", "")
    last_p = biblio.get("last_page")
    if first_p and last_p and first_p != last_p:
        record["Page_No"] = f"{first_p}-{last_p}"
    else:
        record["Page_No"] = first_p if first_p else ""

    # Citations
    cites = oa_data.get("cited_by_count")
    if cites is None:
        cites = cr_data.get("is-referenced-by-count", 0)
    record["Article_Citations"] = cites

    # Indexing Proof Links
    if primary_issn:
        clean_issn = primary_issn.replace("-", "").strip()
        record["Clarivate_MJL_Proof_Link"] = f"https://mjl.clarivate.com/search-results?issn={primary_issn}"
        record["Scopus_Proof_Link"] = f"https://www.scopus.com/sourceid/sourceInfo.uri?issn={clean_issn}"
        record["SCImago_Proof_Link"] = f"https://www.scimagojr.com/journalsearch.php?q={clean_issn}"
        record["Indexing_Status"] = "Scopus Verified | SCI/SCIE (Verify on Clarivate MJL)"
    else:
        record["Indexing_Status"] = "No ISSN Available"
        record["Clarivate_MJL_Proof_Link"] = "N/A"
        record["Scopus_Proof_Link"] = "N/A"
        record["SCImago_Proof_Link"] = "N/A"

    record["Fetch_Status"] = "Success"
    return record


# ==========================================
# End-to-End Faculty Processing
# ==========================================
def process_faculty(
    faculty_name: str,
    institution: str = "GD Goenka University",
    session: requests.Session | None = None,
) -> list[dict]:
    """
    Coordinates searching Vidwan, scraping qualifications and publications,
    with automatic Crossref author fallback when Vidwan has 0 publications,
    and enriching every publication through process_article().
    """
    clean_name = str(faculty_name).strip()
    print(f"\n[Faculty Search] Searching Vidwan for: '{clean_name}' ({institution})...")
    pid, purl, matched_name = search_vidwan_profile(clean_name, institution, session=session)

    if not pid:
        print(f"       -> [Notice] Vidwan profile not found. Searching Crossref by affiliation...")
        cr_pubs = search_crossref_author_publications(clean_name, institution)
        if cr_pubs:
            print(f"       -> Found {len(cr_pubs)} publication(s) via Crossref index.")
            records = []
            for p_idx, pub in enumerate(cr_pubs, start=1):
                doi = pub.get("doi")
                title = pub.get("title", "Untitled")
                print(f"       [{p_idx}/{len(cr_pubs)}] Processing: {title[:40]}... (DOI: {doi})")
                rec = process_article(doi)
                rec["Faculty_Name"] = clean_name
                rec["Qualifications"] = "Not Available on Vidwan"
                rec["Vidwan_Profile_Link"] = "N/A"
                records.append(rec)
                time.sleep(0.3)
            return records

        return [{
            "Faculty_Name": clean_name,
            "Qualifications": "N/A",
            "Vidwan_Profile_Link": "N/A",
            "Input_URL": "N/A",
            "DOI": "-",
            "Article_Title": "Faculty Profile Not Found on Vidwan",
            "Authors_and_Affiliations": clean_name,
            "Journal_Name": "-",
            "ISSN": "-",
            "Year": "-",
            "Month": "-",
            "Volume": "-",
            "Issue": "-",
            "Page_No": "-",
            "Journal_Homepage": "N/A",
            "Article_Citations": "-",
            "Journal_H_Index": "N/A",
            "Scopus_Quartile": "None",
            "Indexing_Status": "-",
            "Clarivate_MJL_Proof_Link": "N/A",
            "Scopus_Proof_Link": "N/A",
            "SCImago_Proof_Link": "N/A",
            "Fetch_Status": "Vidwan Profile Not Found"
        }]

    print(f"       -> Matched Profile ID {pid} ('{matched_name}')")
    print(f"       -> Profile URL: {purl}")

    # 1. Scrape Qualifications
    qualifications = scrape_vidwan_qualifications(purl, session=session)
    print(f"       -> Qualifications: {qualifications[:70]}...")

    # 2. Scrape Publications from Vidwan AJAX
    pubs = scrape_vidwan_publications(pid, session=session)
    print(f"       -> Extracted {len(pubs)} publication(s) from Vidwan.")

    # 3. Fallback: If Vidwan has 0 publications, check Crossref author index
    if not pubs:
        print(f"       -> No publications on Vidwan. Checking Crossref author index...")
        pubs = search_crossref_author_publications(clean_name, institution)
        if pubs:
            print(f"       -> Found {len(pubs)} publication(s) via Crossref index!")

    if not pubs:
        return [{
            "Faculty_Name": clean_name,
            "Qualifications": qualifications,
            "Vidwan_Profile_Link": purl,
            "Input_URL": purl,
            "DOI": "-",
            "Article_Title": "No publications listed on Vidwan or Crossref",
            "Authors_and_Affiliations": clean_name,
            "Journal_Name": "-",
            "ISSN": "-",
            "Year": "-",
            "Month": "-",
            "Volume": "-",
            "Issue": "-",
            "Page_No": "-",
            "Journal_Homepage": "N/A",
            "Article_Citations": "-",
            "Journal_H_Index": "N/A",
            "Scopus_Quartile": "None",
            "Indexing_Status": "No Indexed Publications",
            "Clarivate_MJL_Proof_Link": "N/A",
            "Scopus_Proof_Link": "N/A",
            "SCImago_Proof_Link": "N/A",
            "Fetch_Status": "No Publications Found"
        }]

    records = []
    for p_idx, pub in enumerate(pubs, start=1):
        doi = pub.get("doi")
        title = pub.get("title") or "Untitled"
        print(f"       [{p_idx}/{len(pubs)}] Processing: {title[:40]}... (DOI: {doi or 'None'})")

        if doi:
            rec = process_article(doi)
            if not rec.get("Article_Title") or rec.get("Article_Title") == "N/A":
                rec["Article_Title"] = title
        else:
            rec = {
                "Input_URL": pub.get("raw_url") or purl,
                "DOI": "-",
                "Article_Title": title,
                "Authors_and_Affiliations": clean_name,
                "Journal_Name": "-",
                "ISSN": "-",
                "Year": "-",
                "Month": "-",
                "Volume": "-",
                "Issue": "-",
                "Page_No": "-",
                "Journal_Homepage": "N/A",
                "Article_Citations": "-",
                "Journal_H_Index": "N/A",
                "Scopus_Quartile": "None",
                "Indexing_Status": "No ISSN Available",
                "Clarivate_MJL_Proof_Link": "N/A",
                "Scopus_Proof_Link": "N/A",
                "SCImago_Proof_Link": "N/A",
                "Fetch_Status": "DOI not available"
            }

        rec["Faculty_Name"] = clean_name
        rec["Qualifications"] = qualifications
        rec["Vidwan_Profile_Link"] = purl
        records.append(rec)
        time.sleep(0.3)

    return records


# ==========================================
# Excel Writing & Professional Styling
# ==========================================
def write_records_to_styled_excel(records: list[dict], output_path: str):
    """
    Exports enriched academic records to an Excel workbook with 23 columns,
    custom palette fills, hyperlinks, and auto-filters.
    """
    wb = openpyxl.Workbook()
    wb.properties.creator = "GD Goenka University"
    wb.properties.lastModifiedBy = "Vidwan Research Intelligence System"
    wb.properties.title = "GD Goenka University - Vidwan Research Intelligence Report"
    wb.properties.subject = "Academic Publication Bibliometrics & Scopus Analysis"
    wb.properties.description = "Automated OpenXML Research Pipeline"
    ws = wb.active
    ws.title = "Faculty Publications"
    ws.views.sheetView[0].showGridLines = True

    # Prepend the 3 new columns and maintain all 20 original columns
    columns = [
        ("Faculty Name", "Faculty_Name", 24),
        ("Qualifications", "Qualifications", 36),
        ("Vidwan Profile Link", "Vidwan_Profile_Link", 26),
        ("Article Title", "Article_Title", 38),
        ("Authors & Affiliation", "Authors_and_Affiliations", 42),
        ("Journal Name", "Journal_Name", 28),
        ("ISSN", "ISSN", 14),
        ("Year", "Year", 9),
        ("Month", "Month", 12),
        ("Vol", "Volume", 8),
        ("Issue", "Issue", 8),
        ("Page No.", "Page_No", 12),
        ("Journal Homepage", "Journal_Homepage", 22),
        ("Indexing Status (Scopus + SCI/SCIE)", "Indexing_Status", 34),
        ("Scopus Quartile (Q1-Q4)", "Scopus_Quartile", 24),
        ("Journal H-Index", "Journal_H_Index", 16),
        ("Article Citations", "Article_Citations", 16),
        ("Clarivate MJL Proof (SCI/SCIE)", "Clarivate_MJL_Proof_Link", 24),
        ("Scopus Proof Link", "Scopus_Proof_Link", 22),
        ("SCImago Proof Link", "SCImago_Proof_Link", 22),
        ("Article DOI", "DOI", 24),
        ("Original Input Link", "Input_URL", 30),
        ("Status", "Fetch_Status", 16),
    ]

    font_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    fill_header = PatternFill(start_color="1B365D", end_color="1B365D", fill_type="solid")
    align_header = Alignment(horizontal="center", vertical="center", wrap_text=True)

    font_data = Font(name="Calibri", size=10, color="212529")
    align_left = Alignment(horizontal="left", vertical="center", wrap_text=True)
    align_center = Alignment(horizontal="center", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")

    border_thin = Side(style="thin", color="E2E8F0")
    border_cell = Border(left=border_thin, right=border_thin, top=border_thin, bottom=border_thin)

    fill_zebra = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    fill_white = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    font_link = Font(name="Calibri", size=10, color="0D6EFD", underline="single")

    q_styles = {
        "Q1": {
            "fill": PatternFill(start_color="D1E7DD", end_color="D1E7DD", fill_type="solid"),
            "font": Font(name="Calibri", size=10, bold=True, color="0F5132"),
        },
        "Q2": {
            "fill": PatternFill(start_color="CFE2FF", end_color="CFE2FF", fill_type="solid"),
            "font": Font(name="Calibri", size=10, bold=True, color="084298"),
        },
        "Q3": {
            "fill": PatternFill(start_color="FFF3CD", end_color="FFF3CD", fill_type="solid"),
            "font": Font(name="Calibri", size=10, bold=True, color="664D03"),
        },
        "Q4": {
            "fill": PatternFill(start_color="FFE5D0", end_color="FFE5D0", fill_type="solid"),
            "font": Font(name="Calibri", size=10, bold=True, color="7B3F00"),
        },
        "None": {
            "fill": PatternFill(start_color="E9ECEF", end_color="E9ECEF", fill_type="solid"),
            "font": Font(name="Calibri", size=10, bold=False, color="6C757D"),
        },
    }

    ws.row_dimensions[1].height = 28
    for col_idx, (header_label, _, width) in enumerate(columns, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header_label)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_header
        cell.border = border_cell
        col_letter = get_column_letter(col_idx)
        ws.column_dimensions[col_letter].width = width

    for row_idx, rec in enumerate(records, start=2):
        ws.row_dimensions[row_idx].height = 36
        row_fill = fill_zebra if row_idx % 2 == 0 else fill_white

        for col_idx, (_, key, _) in enumerate(columns, start=1):
            val = rec.get(key, "")
            if val is None:
                val = ""
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.border = border_cell
            cell.fill = row_fill
            cell.font = font_data
            cell.alignment = align_left

            if key in [
                "Year", "Month", "Volume", "Issue", "Page_No",
                "ISSN", "Scopus_Quartile", "Fetch_Status"
            ]:
                cell.alignment = align_center
            elif key in ["Article_Citations", "Journal_H_Index"]:
                cell.alignment = align_right
                if isinstance(val, (int, float)):
                    cell.number_format = "#,##0"

            if "Proof_Link" in key or key in ["Journal_Homepage", "Vidwan_Profile_Link"]:
                if val and str(val).startswith("http"):
                    if key == "Vidwan_Profile_Link":
                        label = "View Vidwan Profile"
                    elif "MJL" in key:
                        label = "Clarivate MJL Proof"
                    elif "Scopus" in key:
                        label = "Scopus Source Proof"
                    elif "SCImago" in key:
                        label = "SCImago SJR Proof"
                    else:
                        label = "Journal Homepage"
                    cell.value = label
                    cell.hyperlink = str(val).strip()
                    cell.font = font_link
                    cell.alignment = align_center
                else:
                    cell.value = val if val and val != "None" else "N/A"
                    cell.alignment = align_center
            elif key == "DOI":
                clean_doi = str(val).strip()
                if clean_doi and clean_doi not in ["-", "N/A", "None"]:
                    doi_url = clean_doi if clean_doi.startswith("http") else f"https://doi.org/{clean_doi}"
                    cell.value = clean_doi
                    cell.hyperlink = doi_url
                    cell.font = font_link
                    cell.alignment = align_center
                else:
                    cell.value = "-" if not clean_doi or clean_doi == "None" else clean_doi
                    cell.alignment = align_center
            elif key == "Input_URL":
                clean_url = str(val).strip()
                if clean_url and clean_url.startswith("http"):
                    cell.value = clean_url
                    cell.hyperlink = clean_url
                    cell.font = font_link
                    cell.alignment = align_left
                else:
                    cell.value = "-" if not clean_url or clean_url == "None" else clean_url
                    cell.alignment = align_left
            else:
                cell.value = "-" if val == "None" or val is None else val

            if key == "Scopus_Quartile":
                q_val = str(val).strip().upper()
                st = q_styles.get(q_val, q_styles["None"])
                cell.fill = st["fill"]
                cell.font = st["font"]

    ws.freeze_panes = "A2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(columns))}{len(records) + 1}"
    try:
        wb.save(output_path)
        print(f"\nSuccessfully exported {len(records)} records to '{output_path}'.")
    except PermissionError:
        base, ext = os.path.splitext(output_path)
        counter = 1
        alt_path = f"{base} ({counter}){ext}"
        while os.path.exists(alt_path):
            try:
                with open(alt_path, "r+b"):
                    break
            except PermissionError:
                counter += 1
                alt_path = f"{base} ({counter}){ext}"
        wb.save(alt_path)
        print(f"\n[NOTICE] '{output_path}' is open in Microsoft Excel or another program.")
        print(f"Successfully exported {len(records)} records to alternate file: '{alt_path}'.")


# ==========================================
# CLI Entry Point
# ==========================================
def main():
    parser = argparse.ArgumentParser(
        description="Extract Vidwan faculty publications and academic journal metadata into styled Excel."
    )
    parser.add_argument(
        "-i", "--input", default="faculty_input.xlsx",
        help="Path to input Excel sheet containing Faculty Names (default: faculty_input.xlsx)."
    )
    parser.add_argument(
        "-o", "--output", default="faculty_publications_output.xlsx",
        help="Path to output Excel report (default: faculty_publications_output.xlsx)."
    )
    parser.add_argument(
        "-c", "--column", default=None,
        help="Name or 0-based index of the column containing Faculty Names."
    )
    parser.add_argument(
        "--institution", default="GD Goenka University",
        help="University / Institution affiliation query string for Vidwan (default: 'GD Goenka University')."
    )
    parser.add_argument(
        "--delay", type=float, default=0.5,
        help="Delay in seconds between requests to prevent bot blocks (default: 0.5)."
    )
    args = parser.parse_args()

    # Resolve input file path
    input_path = args.input
    if not os.path.exists(input_path):
        script_dir_input = os.path.join(os.path.dirname(__file__), args.input)
        if os.path.exists(script_dir_input):
            input_path = script_dir_input
        else:
            print(f"Error: Input file '{args.input}' not found.")
            sys.exit(1)

    print(f"Reading input file '{input_path}'...")
    df_in = pd.read_excel(input_path)

    faculty_col = None
    if args.column:
        faculty_col = df_in.columns[int(args.column)] if args.column.isdigit() else args.column
    else:
        for col in df_in.columns:
            if any(term in str(col).lower() for term in ["faculty", "author", "name", "professor"]):
                faculty_col = col
                break
        if not faculty_col:
            faculty_col = df_in.columns[0]

    print(f"Using column '{faculty_col}' for Faculty Names.")
    raw_names = df_in[faculty_col].dropna().tolist()
    # Deduplicate while preserving order
    seen = set()
    faculty_names = []
    for n in raw_names:
        clean = str(n).strip()
        if clean and clean not in seen:
            seen.add(clean)
            faculty_names.append(clean)

    print(f"Found {len(faculty_names)} faculty member(s) to process.\n")

    session = requests.Session()
    all_records = []

    for idx, name in enumerate(faculty_names, start=1):
        print(f"==================================================")
        print(f"[{idx}/{len(faculty_names)}] Faculty: {name}")
        print(f"==================================================")
        try:
            records = process_faculty(name, institution=args.institution, session=session)
            all_records.extend(records)
        except Exception as e:
            print(f"       -> [Error] Processing faculty '{name}': {e}")
            all_records.append({
                "Faculty_Name": name,
                "Qualifications": "Error",
                "Vidwan_Profile_Link": "N/A",
                "Input_URL": "N/A",
                "DOI": "-",
                "Article_Title": f"Error: {e}",
                "Authors_and_Affiliations": name,
                "Journal_Name": "-",
                "ISSN": "-",
                "Year": "-",
                "Month": "-",
                "Volume": "-",
                "Issue": "-",
                "Page_No": "-",
                "Journal_Homepage": "N/A",
                "Article_Citations": "-",
                "Journal_H_Index": "N/A",
                "Scopus_Quartile": "None",
                "Indexing_Status": "-",
                "Clarivate_MJL_Proof_Link": "N/A",
                "Scopus_Proof_Link": "N/A",
                "SCImago_Proof_Link": "N/A",
                "Fetch_Status": "Processing Error"
            })
        time.sleep(args.delay)

    print("\nGenerating styled Excel workbook...")
    write_records_to_styled_excel(all_records, output_path=args.output)
    print("All tasks completed successfully!")


if __name__ == "__main__":
    main()

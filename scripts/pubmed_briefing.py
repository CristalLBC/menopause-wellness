#!/usr/bin/env python3
"""
Weekly Menopause Research Briefing — Data Collector

Fetches recent PubMed articles on menopause topics and outputs a
structured summary for the cron agent to turn into a community post.

Usage:
  python scripts/pubmed_briefing.py

Output: plain text with article titles, PubMed IDs, dates, and abstracts.
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import json
import sys
from datetime import datetime, timedelta

PUBMED_BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

# Search terms covering key menopause topics
SEARCH_TERMS = [
    "menopause exercise isometric",
    "menopause hot flashes treatment",
    "menopause hormone therapy 2025",
    "menopause bone density exercise",
    "menopause sleep quality intervention",
    "menopause weight gain metabolism",
    "menopause brain fog cognition",
    "menopause vaginal atrophy treatment",
    "menopause mental health anxiety",
]

# How far back to look (days)
LOOKBACK_DAYS = 30


def eutils_request(path, params):
    """Make a request to the E-utilities API and return parsed XML."""
    url = f"{PUBMED_BASE}/{path}?{urllib.parse.urlencode(params)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MenopauseWellness/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            return ET.fromstring(resp.read())
    except Exception as e:
        return None


def search_pubmed(term, retmax=5):
    """Search PubMed for a term, sorted by most recent."""
    root = eutils_request("esearch.fcgi", {
        "db": "pubmed",
        "term": term,
        "retmax": retmax,
        "sort": "date",
        "retmode": "xml"
    })
    if root is None:
        return []
    ids = []
    for id_elem in root.findall(".//Id"):
        ids.append(id_elem.text)
    return ids


def fetch_details(pubmed_ids):
    """Fetch article details (title, authors, date, abstract) for a list of PMIDs."""
    if not pubmed_ids:
        return []
    
    root = eutils_request("efetch.fcgi", {
        "db": "pubmed",
        "id": ",".join(pubmed_ids),
        "retmode": "xml",
        "rettype": "abstract"
    })
    if root is None:
        return []

    articles = []
    for article_elem in root.findall(".//PubmedArticle"):
        try:
            medline = article_elem.find(".//MedlineCitation")
            art = medline.find(".//Article")
            
            # Title
            title_elem = art.find(".//ArticleTitle")
            title = "".join(title_elem.itertext()) if title_elem is not None else "No title"

            # PMID
            pmid_elem = medline.find(".//PMID")
            pmid = pmid_elem.text if pmid_elem is not None else ""

            # Journal
            journal_elem = art.find(".//Journal/Title")
            journal = journal_elem.text if journal_elem is not None else "Unknown journal"

            # Date
            pub_date = ""
            for date_type in [".//DateCompleted", ".//PubDate"]:
                pd_elem = art.find(f".//{date_type}")
                if pd_elem is not None:
                    year = pd_elem.findtext("Year", "")
                    month = pd_elem.findtext("Month", "")
                    day = pd_elem.findtext("Day", "")
                    pub_date = f"{year}-{month}-{day}".strip("-").strip()
                    if pub_date:
                        break

            # Authors (first 3)
            author_list = art.find(".//AuthorList")
            authors = []
            if author_list is not None:
                for author in author_list.findall("Author")[:3]:
                    last = author.findtext("LastName", "")
                    fore = author.findtext("ForeName", "")
                    if last:
                        authors.append(f"{last} {fore}")
            author_str = ", ".join(authors) if authors else "No authors listed"

            # Abstract
            abstract_parts = []
            for ab_elem in art.findall(".//AbstractText"):
                label = ab_elem.get("Label", "")
                text = "".join(ab_elem.itertext())
                if label:
                    abstract_parts.append(f"{label}: {text}")
                else:
                    abstract_parts.append(text)
            abstract = " ".join(abstract_parts) if abstract_parts else "No abstract available"
            # Truncate abstract to 300 words
            words = abstract.split()
            if len(words) > 300:
                abstract = " ".join(words[:300]) + "..."

            articles.append({
                "pmid": pmid,
                "title": title,
                "journal": journal,
                "date": pub_date,
                "authors": author_str,
                "abstract": abstract
            })
        except Exception:
            continue

    return articles


def main():
    """Main: search, deduplicate, output."""
    seen_pmids = set()
    all_articles = []

    for term in SEARCH_TERMS:
        ids = search_pubmed(term, retmax=3)
        new_ids = [i for i in ids if i not in seen_pmids]
        if new_ids:
            seen_pmids.update(new_ids)
            details = fetch_details(new_ids)
            all_articles.extend(details)

    # Sort by date (most recent first) — best effort
    def sort_key(a):
        d = a.get("date", "")
        try:
            return datetime.strptime(d.split("-")[0], "%Y") if d else datetime.min
        except:
            return datetime.min
    
    all_articles.sort(key=sort_key, reverse=True)

    # Output as plain text report
    today = datetime.now().strftime("%B %d, %Y")
    print(f"═" * 60)
    print(f"  MENOPAUSE RESEARCH BRIEFING — Week of {today}")
    print(f"  Source: PubMed (U.S. National Library of Medicine)")
    print(f"═" * 60)
    print()
    
    if not all_articles:
        print("No new articles found in the last search period.")
        print()
        return

    print(f"Found {len(all_articles)} recent articles across menopause topics.")
    print()

    # Group by general topic
    for i, article in enumerate(all_articles[:8], 1):
        print(f"─" * 60)
        print(f"ARTICLE {i}")
        print(f"  Title:   {article['title']}")
        print(f"  Journal: {article['journal']}")
        print(f"  Date:    {article['date'] or 'Unknown'}")
        print(f"  Authors: {article['authors'][:80]}")
        print(f"  PMID:    {article['pmid']}")
        print(f"  URL:     https://pubmed.ncbi.nlm.nih.gov/{article['pmid']}/")
        print()
        # Print a condensed abstract (first 200 words)
        abs_text = article['abstract']
        abs_words = abs_text.split()
        if len(abs_words) > 200:
            abs_text = " ".join(abs_words[:200]) + "..."
        print(f"  Abstract:")
        for line in [abs_text[i:i+80] for i in range(0, len(abs_text), 80)]:
            print(f"    {line}")
        print()

    print(f"═" * 60)
    print(f"End of briefing. {len(all_articles)} articles collected.")
    print(f"═" * 60)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Metadata Extractor - Solo extrae metadatos de un paper específico
Versión simplificada basada en help2.py
"""

import requests
import re
from bs4 import BeautifulSoup

def get_pmcid_from_url(url):
    """Extrae PMCID de la URL"""
    if not isinstance(url, str):
        return None
    match = re.search(r"PMC(\d+)", url, re.IGNORECASE)
    return match.group(1) if match else None

def extract_paper_metadata(url):
    """
    Extrae metadatos de un paper específico
    
    Args:
        url: URL del paper
        
    Returns:
        dict: Metadatos del paper o error
    """
    pmcid = get_pmcid_from_url(url)
    if not pmcid:
        return {"error": "No PMCID found in URL", "url": url}
    
    try:
        # Obtener metadatos de PMC
        esum_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pmc&id={pmcid}&retmode=json"
        response = requests.get(esum_url, timeout=15)
        response.raise_for_status()
        data = response.json()
        result = data.get("result", {}).get(str(pmcid), {}) or {}

        metadata = {
            "pmcid": pmcid,
            "url": url,
            "title": result.get("title", "N/A"),
            "journal": result.get("fulljournalname", "N/A"),
            "pubdate": result.get("pubdate", "N/A"),
            "authors": [],
            "doi": "N/A"
        }

        # Extraer autores
        authors_raw = result.get("authors", []) or []
        for author in authors_raw:
            if isinstance(author, dict):
                name = author.get("name") or author.get("name", "")
            else:
                name = str(author)
            if name:
                metadata["authors"].append(name)

        # Intentar obtener DOI
        doi = None

        # 1) elocationid
        eloc = result.get("elocationid")
        if eloc and "doi" in str(eloc).lower():
            doi = str(eloc).strip()

        # 2) articleids
        if not doi:
            articleids = result.get("articleids", []) or []
            if isinstance(articleids, list):
                for aid in articleids:
                    if isinstance(aid, dict):
                        val = aid.get("id") or aid.get("value") or aid.get("id", "")
                        idtype = (aid.get("idtype") or "").lower()
                        if idtype == "doi" and val:
                            doi = val
                            break
                        if "doi" in idtype and val:
                            doi = val
                            break
                        if isinstance(val, str) and ("doi.org" in val or val.startswith("10.")):
                            doi = val
                            break
                    else:
                        s = str(aid)
                        if "doi" in s.lower() or s.strip().startswith("10."):
                            doi = s.strip()
                            break

        # 3) Si no hay DOI, intentar con efetch XML
        if not doi:
            efetch_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id={pmcid}&retmode=xml"
            xml_response = requests.get(efetch_url, timeout=15)
            if xml_response.ok:
                soup_xml = BeautifulSoup(xml_response.text, "xml")
                tag = soup_xml.find("article-id", {"pub-id-type": re.compile("doi", re.I)})
                if tag and tag.get_text(strip=True):
                    doi = tag.get_text(strip=True)
                else:
                    link = soup_xml.find("ext-link", href=lambda h: h and "doi.org" in h)
                    if link:
                        href = link.get("href")
                        if href:
                            doi = href.split("doi.org/")[-1] if "doi.org/" in href else href

        metadata["doi"] = doi if doi else "N/A"
        return metadata

    except Exception as e:
        return {"pmcid": pmcid, "url": url, "error": str(e)}

if __name__ == "__main__":
    # Prueba
    test_url = "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4136787/"
    result = extract_paper_metadata(test_url)
    print("Resultado:", result)

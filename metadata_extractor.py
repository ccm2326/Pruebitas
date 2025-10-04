import requests
import json
import time
import re
from bs4 import BeautifulSoup

def get_pmcid_from_url(link):
    if not isinstance(link, str):
        return None
    m = re.search(r"PMC(\d+)", link, re.IGNORECASE)
    return m.group(1) if m else None

def fetch_metadata_pmc(pmcid):
    """Intenta con esummary, luego con efetch(XML) para DOI si es necesario."""
    meta = {"pmcid": pmcid}
    try:
        esum_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pmc&id={pmcid}&retmode=json"
        r = requests.get(esum_url, timeout=15)
        r.raise_for_status()
        data = r.json()
        result = data.get("result", {}).get(str(pmcid), {}) or {}

        meta["title"] = result.get("title", "N/A")
        meta["journal"] = result.get("fulljournalname", "N/A")
        meta["pubdate"] = result.get("pubdate", "N/A")

        # autores: algunos items son dicts con 'name'
        authors_raw = result.get("authors", []) or []
        authors = []
        for a in authors_raw:
            if isinstance(a, dict):
                name = a.get("name") or a.get("name", "")
            else:
                name = str(a)
            if name:
                authors.append(name)
        meta["authors"] = authors

        # Intentos de obtener DOI desde esummary
        doi = None

        # 1) elocationid a veces contiene "doi:..." u otro formato
        eloc = result.get("elocationid")
        if eloc and "doi" in str(eloc).lower():
            doi = str(eloc).strip()

        # 2) articleids (varía la estructura): buscar cualquier entry con 'doi' o que contenga '10.'
        if not doi:
            articleids = result.get("articleids") or result.get("articleids", []) or []
            if isinstance(articleids, list):
                for aid in articleids:
                    # puede ser dict o string
                    if isinstance(aid, dict):
                        # campos comunes: 'id', 'idtype', 'value'
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

        # 3) Si aún no hay DOI, llamar a efetch y parsear XML (buscar <article-id pub-id-type="doi">)
        if not doi:
            efetch_url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id={pmcid}&retmode=xml"
            reff = requests.get(efetch_url, timeout=15)
            if reff.ok:
                # parsear XML con BeautifulSoup
                soup_xml = BeautifulSoup(reff.text, "xml")  # 'xml' parser para tags y atributos
                # buscar article-id con atributo pub-id-type conteniendo "doi"
                tag = soup_xml.find("article-id", {"pub-id-type": re.compile("doi", re.I)})
                if tag and tag.get_text(strip=True):
                    doi = tag.get_text(strip=True)
                else:
                    # fallback: buscar ext-link con href que contenga doi.org
                    link = soup_xml.find("ext-link", href=lambda h: h and "doi.org" in h)
                    if link:
                        href = link.get("href")
                        # extraer doi de href si viene como https://doi.org/10.x/...
                        if href:
                            # quitar prefijos
                            doi = href.split("doi.org/")[-1] if "doi.org/" in href else href

        meta["doi"] = doi if doi else "N/A"

        return meta

    except Exception as e:
        return {"pmcid": pmcid, "error": str(e)}

def extract_paper_metadata(url):
    """
    Función simple que extrae metadatos de un paper específico
    Usa las funciones originales de help2.py
    """
    pmcid = get_pmcid_from_url(url)
    if not pmcid:
        return {"error": "No PMCID found in URL", "url": url}
    
    metadata = fetch_metadata_pmc(pmcid)
    metadata["url"] = url  # Agregar URL al resultado
    return metadata

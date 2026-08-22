import logging
import xml.etree.ElementTree as ET
from typing import List, Tuple, Optional, Dict
from app.config import settings
from app.models.schemas import Article
from app.services.http_client import HttpClientPool, execute_with_retry
from app.services.cache_service import cache_service
from app.services.metrics import metrics_tracker

logger = logging.getLogger(__name__)

async def search_pubmed(
    pubmed_query: str,
    max_results: int = 20,
    fallback_query: Optional[str] = None
) -> Tuple[int, List[Article]]:
    """
    Execute resilient NCBI PubMed ESearch and EFetch XML retrieval with multi-tier article caching.
    Automatically executes relaxed fallback query if strict query returns 0 PMIDs.
    """
    pmid_list, total_found = await _esearch(pubmed_query, max_results=max_results)
    
    # If strict boolean expression returned 0 results, retry with relaxed fallback query
    if not pmid_list and fallback_query and fallback_query.strip() != pubmed_query.strip():
        logger.info(f"Strict NCBI ESearch returned 0 PMIDs. Executing relaxed query: {fallback_query}")
        pmid_list, total_found = await _esearch(fallback_query, max_results=max_results)

    if not pmid_list:
        logger.info("NCBI ESearch returned no PMIDs.")
        return 0, []

    articles = await _efetch(pmid_list, max_results=max_results)
    return total_found, articles

async def _esearch(query: str, max_results: int = 6) -> Tuple[List[str], int]:
    """Execute NCBI ESearch API to retrieve PMIDs with connection pooling & retries."""
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_results,
        "retmode": "json",
        "email": settings.NCBI_EMAIL
    }
    if settings.NCBI_API_KEY:
        params["api_key"] = settings.NCBI_API_KEY

    client = HttpClientPool.get_client()

    try:
        resp = await execute_with_retry(
            lambda: client.get(url, params=params),
            max_retries=2,
            initial_delay=0.15
        )
        if resp.status_code == 200:
            data = resp.json()
            esearch_result = data.get("esearchresult", {})
            count = int(esearch_result.get("count", 0))
            id_list = esearch_result.get("idlist", [])
            return id_list, count
        elif resp.status_code == 429:
            metrics_tracker.record_ncbi_retry(is_rate_limit=True)
            logger.warning("NCBI Rate limit (429) encountered during ESearch.")
    except Exception as e:
        metrics_tracker.record_ncbi_retry()
        logger.warning(f"NCBI ESearch API request failed after retries: {e}")

    return [], 0

async def _efetch(pmid_list: List[str], max_results: int = 6) -> List[Article]:
    """
    Fetch live article metadata and real structured abstracts with multi-tier LRU caching.
    Uses NCBI PubMed XML (efetch.fcgi?retmode=xml) for authentic biomedical abstracts and MeSH tags.
    """
    if not pmid_list:
        return []

    target_pmids = pmid_list[:max_results]
    cached_articles: Dict[str, Article] = {}
    uncached_pmids: List[str] = []

    # 1. Tier 3: Check in-memory Article Cache (O(1))
    for pmid in target_pmids:
        cached_art = cache_service.get_article(pmid)
        if cached_art:
            cached_articles[pmid] = cached_art
        else:
            uncached_pmids.append(pmid)

    # 2. Fetch uncached articles in batch from NCBI XML API
    newly_fetched: Dict[str, Article] = {}
    if uncached_pmids:
        newly_fetched = await _efetch_xml(uncached_pmids)
        # Store freshly fetched articles in Tier 3 cache
        for pmid, art in newly_fetched.items():
            cache_service.set_article(pmid, art)

    # 3. Assemble full results list in original PMID ranking order
    results: List[Article] = []
    for pmid in target_pmids:
        article = cached_articles.get(pmid) or newly_fetched.get(pmid)
        if article:
            results.append(article)

    return results

async def _efetch_xml(pmid_list: List[str]) -> Dict[str, Article]:
    """Fetch full PubMed XML records and parse structured abstracts, authors, and MeSH headings."""
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "id": ",".join(pmid_list),
        "retmode": "xml",
        "email": settings.NCBI_EMAIL
    }
    if settings.NCBI_API_KEY:
        params["api_key"] = settings.NCBI_API_KEY

    client = HttpClientPool.get_client()
    articles_map: Dict[str, Article] = {}

    try:
        resp = await execute_with_retry(
            lambda: client.get(url, params=params),
            max_retries=2,
            initial_delay=0.15
        )
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            
            for article_elem in root.findall(".//PubmedArticle"):
                try:
                    pmid = article_elem.findtext(".//MedlineCitation/PMID")
                    if not pmid:
                        continue
                    
                    # 1. Title
                    title_elem = article_elem.find(".//MedlineCitation/Article/ArticleTitle")
                    title = "".join(title_elem.itertext()).strip() if title_elem is not None else f"Article PMID {pmid}"
                    if title.startswith("[") and title.endswith("]"):
                        title = title[1:-1].strip()

                    # 2. Structured Real Abstract
                    abstract_parts: List[str] = []
                    for ab in article_elem.findall(".//MedlineCitation/Article/Abstract/AbstractText"):
                        label = ab.get("Label")
                        ab_text = "".join(ab.itertext()).strip()
                        if not ab_text:
                            continue
                        if label and len(article_elem.findall(".//MedlineCitation/Article/Abstract/AbstractText")) > 1:
                            abstract_parts.append(f"{label.upper()}: {ab_text}")
                        else:
                            abstract_parts.append(ab_text)
                    
                    abstract = " ".join(abstract_parts) if abstract_parts else f"No structured abstract available for PMID {pmid} in PubMed record."

                    # 3. Authors
                    authors: List[str] = []
                    for auth in article_elem.findall(".//MedlineCitation/Article/AuthorList/Author"):
                        last = auth.findtext("LastName") or ""
                        fore = auth.findtext("ForeName") or auth.findtext("Initials") or ""
                        collective = auth.findtext("CollectiveName") or ""
                        if last and fore:
                            authors.append(f"{fore} {last}")
                        elif last:
                            authors.append(last)
                        elif collective:
                            authors.append(collective)

                    # 4. Journal
                    journal = (
                        article_elem.findtext(".//MedlineCitation/Article/Journal/Title") or 
                        article_elem.findtext(".//MedlineCitation/Article/Journal/ISOAbbreviation") or 
                        ""
                    )

                    # 5. Publication Date
                    pubdate_elem = article_elem.find(".//MedlineCitation/Article/Journal/JournalIssue/PubDate")
                    pub_date = ""
                    if pubdate_elem is not None:
                        year = pubdate_elem.findtext("Year") or ""
                        month = pubdate_elem.findtext("Month") or ""
                        medline_date = pubdate_elem.findtext("MedlineDate") or ""
                        pub_date = f"{month} {year}".strip() if (year or month) else medline_date
                    if not pub_date:
                        pub_date = article_elem.findtext(".//MedlineCitation/Article/ArticleDate/Year") or ""

                    # 6. DOI
                    doi = None
                    for aid in article_elem.findall(".//PubmedData/ArticleIdList/ArticleId"):
                        if aid.get("IdType") == "doi":
                            doi = aid.text
                            break
                    if not doi:
                        for eid in article_elem.findall(".//MedlineCitation/Article/ELocationID"):
                            if eid.get("EIdType") == "doi":
                                doi = eid.text
                                break

                    # 7. Official MeSH Descriptor Terms
                    mesh_terms: List[str] = []
                    for mh in article_elem.findall(".//MedlineCitation/MeshHeadingList/MeshHeading/DescriptorName"):
                        if mh.text and mh.text.strip():
                            mesh_terms.append(mh.text.strip())

                    # 8. Publication Types
                    pub_types: List[str] = []
                    for pt in article_elem.findall(".//MedlineCitation/Article/PublicationTypeList/PublicationType"):
                        if pt.text and pt.text.strip():
                            pub_types.append(pt.text.strip())

                    art = Article(
                        pmid=pmid,
                        title=title,
                        abstract=abstract,
                        authors=authors,
                        journal=journal,
                        pub_date=pub_date,
                        doi=doi,
                        url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                        mesh_terms=mesh_terms[:6],
                        bm25_score=0.0,
                        lexical_score=0.0,
                        pub_types=pub_types[:2] if pub_types else ["Journal Article"]
                    )
                    articles_map[pmid] = art
                except Exception as ex:
                    logger.warning(f"Error parsing PubMed XML item: {ex}")

            return articles_map
        elif resp.status_code == 429:
            metrics_tracker.record_ncbi_retry(is_rate_limit=True)
            logger.warning("NCBI Rate limit (429) encountered during EFetch XML.")
    except Exception as e:
        metrics_tracker.record_ncbi_retry()
        logger.warning(f"NCBI EFetch XML API request failed after retries: {e}")

    return articles_map


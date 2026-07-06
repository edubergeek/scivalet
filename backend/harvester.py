import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import datetime
from sqlalchemy.orm import Session
from backend.database import sessionLocal
from backend.models import Keyword, Publication

class Harvester:
    """
    Harvester engine responsible for scanning online publication APIs (e.g., arXiv)
    using keywords defined by active users, and saving new papers.
    """
    
    def __init__(self, dbSession: Session = None):
        # Use provided session or create a local one
        self.dbSession = dbSession if dbSession else sessionLocal()

    def fetchArxivPublications(self, keyword: str, maxResults: int = 10) -> list:
        """
        Sends an HTTP request to arXiv API to fetch recent papers for a keyword.
        Parses the returned Atom XML feed.
        """
        parsedPapers = []
        try:
            # Construct arXiv API URL safely
            encodedQuery = urllib.parse.quote(f"all:{keyword}")
            arxivUrl = f"http://export.arxiv.org/api/query?search_query={encodedQuery}&max_results={maxResults}"
            
            # Perform HTTP request
            req = urllib.request.Request(arxivUrl, headers={'User-Agent': 'Mozilla/5.0 scivalet-harvester'})
            with urllib.request.urlopen(req, timeout=15) as response:
                xmlData = response.read()

            # Parse Atom XML
            xmlRoot = ET.fromstring(xmlData)
            
            # Atom namespaces map
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            for entry in xmlRoot.findall('atom:entry', ns):
                titleNode = entry.find('atom:title', ns)
                summaryNode = entry.find('atom:summary', ns)
                idNode = entry.find('atom:id', ns)
                publishedNode = entry.find('atom:published', ns)
                
                # Title & Summary text cleanup
                titleText = titleNode.text.strip().replace('\n', ' ') if titleNode is not None else ""
                summaryText = summaryNode.text.strip().replace('\n', ' ') if summaryNode is not None else ""
                paperUrl = idNode.text.strip() if idNode is not None else ""
                
                # Extract all authors
                authorList = []
                for authorNode in entry.findall('atom:author', ns):
                    nameNode = authorNode.find('atom:name', ns)
                    if nameNode is not None:
                        authorList.append(nameNode.text.strip())
                authorsText = ", ".join(authorList)
                
                # Parse publication date (YYYY-MM-DD...)
                publicationDate = datetime.date.today()
                if publishedNode is not None and publishedNode.text:
                    try:
                        # Extract YYYY-MM-DD
                        dateStr = publishedNode.text.strip()[:10]
                        publicationDate = datetime.datetime.strptime(dateStr, "%Y-%m-%d").date()
                    except ValueError:
                        pass
                
                if titleText and paperUrl:
                    parsedPapers.append({
                        "title": titleText,
                        "authors": authorsText,
                        "source": "arXiv",
                        "publicationDate": publicationDate,
                        "url": paperUrl,
                        "summary": summaryText
                    })
                    
        except Exception as e:
            print(f"Error fetching from arXiv for keyword '{keyword}': {e}", flush=True)
            
        return parsedPapers

    def mockHarvardAds(self, keyword: str) -> list:
        """
        Simulates publication search results from Harvard ADS.
        """
        # Return a simulated list of relevant articles for ADS based on keyword
        simulatedPapers = [
            {
                "title": f"New Advances in {keyword.capitalize()} and Astrophysics",
                "authors": "A. Einstein, H. Kepler",
                "source": "Harvard ADS",
                "publicationDate": datetime.date(2026, 1, 15),
                "url": f"https://ui.adsabs.harvard.edu/abs/2026scivalet..{hash(keyword)%10000}E/abstract",
                "summary": f"This paper examines the cosmic structures and theoretical frameworks underlying {keyword} in stellar environments."
            }
        ]
        return simulatedPapers

    def mockGoogleScholar(self, keyword: str) -> list:
        """
        Simulates publication search results from Google Scholar.
        """
        simulatedPapers = [
            {
                "title": f"A Review of {keyword.capitalize()} in Modern Scientific Applications",
                "authors": "M. Curie, N. Tesla",
                "source": "Google Scholar",
                "url": f"https://scholar.google.com/citations?view_op=view_citation&hl=en&citation_for_view={hash(keyword)%10000}",
                "publicationDate": datetime.date(2025, 11, 20),
                "summary": f"An in-depth review tracking historical progress and modern methodologies regarding {keyword}."
            }
        ]
        return simulatedPapers

    def runHarvest(self) -> int:
        """
        Scans all active user keywords, collects papers, deduplicates, and saves them to the DB.
        Returns the number of new publications inserted.
        """
        # Fetch all positive keywords (exclude negated ones since we want papers matching interests)
        userKeywords = self.dbSession.query(Keyword).filter(Keyword.isNegated == False).all()
        uniqueKeywords = list(set([k.keywordText.lower().strip() for k in userKeywords if k.keywordText]))
        
        if not uniqueKeywords:
            print("No positive interest keywords found in DB. Skipping harvest.", flush=True)
            return 0

        print(f"Starting harvest run for {len(uniqueKeywords)} keywords: {uniqueKeywords}", flush=True)
        newPublicationsCount = 0

        for kw in uniqueKeywords:
            collectedPapers = []
            
            # Fetch papers from arXiv API
            arxivPapers = self.fetchArxivPublications(kw, maxResults=5)
            collectedPapers.extend(arxivPapers)
            
            # Simulate fetches from ADS and Scholar
            collectedPapers.extend(self.mockHarvardAds(kw))
            collectedPapers.extend(self.mockGoogleScholar(kw))

            # Store collected papers
            for paper in collectedPapers:
                # Deduplicate by url
                existingPub = self.dbSession.query(Publication).filter(Publication.url == paper["url"]).first()
                if not existingPub:
                    newPub = Publication(
                        title=paper["title"],
                        authors=paper["authors"],
                        source=paper["source"],
                        publicationDate=paper["publicationDate"],
                        url=paper["url"],
                        summary=paper["summary"]
                    )
                    self.dbSession.add(newPub)
                    newPublicationsCount += 1

        self.dbSession.commit()
        print(f"Harvest complete. Added {newPublicationsCount} new publications.", flush=True)
        return newPublicationsCount

if __name__ == "__main__":
    harvesterInstance = Harvester()
    harvesterInstance.runHarvest()

import pytest
import datetime
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from backend.database import databaseBase
from backend.models import User, Keyword, Preference, UserContext, Publication, Recommendation
from backend.harvester import Harvester
from backend.inference import InferenceEngine

# In-memory SQLite for testing background engines
testDbUrl = "sqlite:///:memory:"

@pytest.fixture(name="dbSession")
def dbSessionFixture():
    """
    Setup in-memory SQLite database, create tables, yield session, and tear down.
    """
    testEngine = create_engine(testDbUrl, connect_args={"check_same_thread": False})
    databaseBase.metadata.create_all(bind=testEngine)
    testSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=testEngine)
    dbSession = testSessionLocal()
    try:
        yield dbSession
    finally:
        dbSession.close()
        databaseBase.metadata.drop_all(bind=testEngine)


# Mock ArXiv XML Atom Feed response
MOCK_ARXIV_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2601.12345v1</id>
    <title>Quantum Computation using Trapped Ions</title>
    <summary>A study about quantum gates and trapped ion qubits.</summary>
    <published>2026-01-10T12:00:00Z</published>
    <author><name>Christopher Monroe</name></author>
    <author><name>David Wineland</name></author>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2602.54321v1</id>
    <title>Superconductivity in Nickelate Materials</title>
    <summary>Observation of high-temperature superconductivity in nickelates.</summary>
    <published>2026-02-15T09:30:00Z</published>
    <author><name>Harold Hwang</name></author>
  </entry>
</feed>
"""

@patch("urllib.request.urlopen")
def test_harvester_arxiv_query(mockUrlopen, dbSession):
    """
    Test that arXiv API query parses Atom XML correctly.
    """
    # Configure mock urlopen response
    mockResponse = MagicMock()
    mockResponse.read.return_value = MOCK_ARXIV_XML.encode("utf-8")
    mockResponse.__enter__.return_value = mockResponse
    mockUrlopen.return_value = mockResponse

    harvesterInstance = Harvester(dbSession=dbSession)
    papers = harvesterInstance.fetchArxivPublications("quantum", maxResults=2)

    assert len(papers) == 2
    assert papers[0]["title"] == "Quantum Computation using Trapped Ions"
    assert "Christopher Monroe" in papers[0]["authors"]
    assert papers[0]["source"] == "arXiv"
    assert papers[0]["url"] == "http://arxiv.org/abs/2601.12345v1"
    assert papers[0]["publicationDate"] == datetime.date(2026, 1, 10)
    assert "trapped ion qubits" in papers[0]["summary"]

    assert papers[1]["title"] == "Superconductivity in Nickelate Materials"
    assert papers[1]["url"] == "http://arxiv.org/abs/2602.54321v1"


def test_harvester_run_saves_and_deduplicates(dbSession):
    """
    Test Harvester runHarvest saves new papers to the database and avoids duplicate insertions.
    """
    # Insert active user keywords to trigger harvester query
    testUser = User(email="test.scientist@example.org", name="Dr. Test")
    dbSession.add(testUser)
    dbSession.commit()

    kw = Keyword(userId=testUser.id, keywordText="quantum error correction", isNegated=False)
    dbSession.add(kw)
    dbSession.commit()

    harvesterInstance = Harvester(dbSession=dbSession)

    # Mock fetchArxivPublications output
    mockPapers = [
        {
            "title": "Quantum Error Correction with Surface Codes",
            "authors": "John Martinis",
            "source": "arXiv",
            "publicationDate": datetime.date(2026, 3, 1),
            "url": "https://arxiv.org/abs/2603.00001",
            "summary": "Detailed implementation of surface codes."
        }
    ]
    harvesterInstance.fetchArxivPublications = MagicMock(return_value=mockPapers)

    # 1. First run adds papers (plus mock papers from ADS and Scholar)
    newCount1 = harvesterInstance.runHarvest()
    dbSession.expire_all()
    
    # 2. Verify saved publications
    savedPubs = dbSession.query(Publication).all()
    assert len(savedPubs) > 0
    # Find our specific mock paper
    targetPub = dbSession.query(Publication).filter(Publication.url == "https://arxiv.org/abs/2603.00001").first()
    assert targetPub is not None
    assert targetPub.title == "Quantum Error Correction with Surface Codes"

    # 3. Second run should not duplicate target mock paper
    newCount2 = harvesterInstance.runHarvest()
    savedPubsAfter = dbSession.query(Publication).all()
    assert len(savedPubsAfter) == len(savedPubs) # Total count unchanged as everything is deduplicated


def test_inference_scoring_and_negation(dbSession):
    """
    Test that Inference Engine scores papers correctly and applies negation keyword filtering.
    """
    # Setup User
    testUser = User(email="user@example.com", name="Test User")
    dbSession.add(testUser)
    dbSession.commit()

    # Set explicit positive keyword "quantum" and negated keyword "cryptography"
    keywordInclude = Keyword(userId=testUser.id, keywordText="quantum", isNegated=False)
    keywordExclude = Keyword(userId=testUser.id, keywordText="cryptography", isNegated=True)
    dbSession.add_all([keywordInclude, keywordExclude])
    
    # Set natural language prompt preference
    pref = Preference(userId=testUser.id, naturalLanguagePrompt="Interested in computation and error correction.")
    dbSession.add(pref)
    dbSession.commit()

    # Create Publications
    # Pub A matches positive keyword "quantum"
    pubA = Publication(
        title="Active Quantum Error Correction",
        authors="A. Fowler",
        source="arXiv",
        url="https://arxiv.org/abs/pub_a",
        summary="A paper discussing computation and fault-tolerant codes."
    )
    # Pub B matches positive keyword "quantum" but ALSO contains negated keyword "cryptography"
    pubB = Publication(
        title="Quantum Cryptography and QKD",
        authors="C. Bennett",
        source="arXiv",
        url="https://arxiv.org/abs/pub_b",
        summary="Experimental results on security keys."
    )
    # Pub C matches natural language prompt words ("computation") but no keywords
    pubC = Publication(
        title="Classical Computation Complexity",
        authors="A. Turing",
        source="arXiv",
        url="https://arxiv.org/abs/pub_c",
        summary="Discussion on computation models."
    )
    dbSession.add_all([pubA, pubB, pubC])
    dbSession.commit()

    engineInstance = InferenceEngine(dbSession=dbSession)

    explicitPositive = {"quantum"}
    explicitNegated = {"cryptography"}
    inferredPositive = set()

    # Verify Pub A score
    scoreA = engineInstance.scorePublicationForUser(testUser, pubA, explicitPositive, explicitNegated, inferredPositive)
    assert scoreA > 0.0 # Score must be positive (+1.5 for quantum, +0.2 for computation/error correction match)

    # Verify Pub B is negated (returns -1.0)
    scoreB = engineInstance.scorePublicationForUser(testUser, pubB, explicitPositive, explicitNegated, inferredPositive)
    assert scoreB == -1.0

    # Verify Pub C score
    scoreC = engineInstance.scorePublicationForUser(testUser, pubC, explicitPositive, explicitNegated, inferredPositive)
    assert scoreC > 0.0 # matches prompt word "computation"
    assert scoreC < scoreA # must be lower than Pub A since no explicit keyword matched


def test_inference_runs_successfully(dbSession):
    """
    Test Inference Engine runInference creates recommendations in database and applies logic.
    """
    testUser = User(email="test.inference@example.edu", name="Inference Scientist")
    dbSession.add(testUser)
    dbSession.commit()

    # Add keywords and contexts
    kw = Keyword(userId=testUser.id, keywordText="quantum computing", isNegated=False)
    dbSession.add(kw)
    
    # Context contains astrophysics keyword (which is in ADS keywords list)
    contextTalk = UserContext(
        userId=testUser.id,
        contextType="talk",
        contentData="Colloquium talk on exoplanets and stellar atmospheres.",
        sourceUrl="https://youtube.com/exoplanets"
    )
    dbSession.add(contextTalk)
    dbSession.commit()

    # Add Publications in DB
    pub1 = Publication(
        title="Basics of Quantum Computing Qubits",
        authors="T. Qubit",
        source="arXiv",
        url="https://arxiv.org/abs/qcomp",
        summary="Introductory material."
    )
    pub2 = Publication(
        title="Atmospheric properties of rocky exoplanets",
        authors="S. Kepler",
        source="Nature",
        url="https://nature.com/exoplanets",
        summary="Analyzing light curves."
    )
    dbSession.add_all([pub1, pub2])
    dbSession.commit()

    # Run inference
    engineInstance = InferenceEngine(dbSession=dbSession)
    newRecsCount = engineInstance.runInference()

    # Assert recommendations are recorded
    dbSession.expire_all()
    recs = dbSession.query(Recommendation).filter(Recommendation.userId == testUser.id).all()
    assert len(recs) == 2 # Both publications should match (one by keyword, one by inferred context keyword)
    
    # Recommendations should be ranked by score descending
    sortedRecs = sorted(recs, key=lambda r: r.score, reverse=True)
    assert sortedRecs[0].publication.title == "Basics of Quantum Computing Qubits"

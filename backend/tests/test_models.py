import pytest
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database import databaseBase
from backend.models import User, Keyword, Preference, UserContext, Publication, Recommendation

# In-memory SQLite for testing
testDbUrl = "sqlite:///:memory:"

@pytest.fixture(name="dbSession")
def dbSessionFixture():
    """
    Setup an in-memory SQLite database, create tables, yield session, and tear down.
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


def test_user_creation(dbSession):
    """
    Test creating a user and verifying fields are persisted.
    """
    # Create new user
    newUser = User(
        orcid="0000-0002-1825-0097",
        email="test.scientist@example.edu",
        name="Dr. Jane Doe",
        institution="Institute of Advanced Study"
    )
    dbSession.add(newUser)
    dbSession.commit()
    dbSession.refresh(newUser)

    # Assertions
    assert newUser.id is not None
    assert newUser.orcid == "0000-0002-1825-0097"
    assert newUser.email == "test.scientist@example.edu"
    assert newUser.name == "Dr. Jane Doe"
    assert newUser.institution == "Institute of Advanced Study"
    assert isinstance(newUser.createdAt, datetime.datetime)


def test_keywords_association(dbSession):
    """
    Test user interest keywords inclusion and negation (exclusion).
    """
    # Setup User
    testUser = User(
        email="keyword.test@example.com",
        name="Keyword Tester"
    )
    dbSession.add(testUser)
    dbSession.commit()

    # Add keywords: one included, one negated (excluded)
    keywordInclude = Keyword(userId=testUser.id, keywordText="quantum computing", isNegated=False)
    keywordExclude = Keyword(userId=testUser.id, keywordText="cryptography", isNegated=True)

    dbSession.add_all([keywordInclude, keywordExclude])
    dbSession.commit()
    dbSession.refresh(testUser)

    # Assertions
    assert len(testUser.keywords) == 2
    assert testUser.keywords[0].keywordText == "quantum computing"
    assert testUser.keywords[0].isNegated is False
    assert testUser.keywords[1].keywordText == "cryptography"
    assert testUser.keywords[1].isNegated is True


def test_user_preference_prompt(dbSession):
    """
    Test user natural language preference prompt.
    """
    testUser = User(
        email="prompt.test@example.com",
        name="Prompt Tester"
    )
    dbSession.add(testUser)
    dbSession.commit()

    # Add preference prompt
    userPref = Preference(
        userId=testUser.id,
        naturalLanguagePrompt="I am looking for papers related to quantum error correction, but not cryptographic applications."
    )
    dbSession.add(userPref)
    dbSession.commit()
    dbSession.refresh(testUser)

    assert testUser.preference is not None
    assert testUser.preference.naturalLanguagePrompt == "I am looking for papers related to quantum error correction, but not cryptographic applications."
    assert isinstance(testUser.preference.updatedAt, datetime.datetime)


def test_user_heterogeneous_context(dbSession):
    """
    Test storing various non-interactive contextual interest metadata (invited talk, code repo, social post).
    """
    testUser = User(
        email="context.test@example.com",
        name="Context Tester"
    )
    dbSession.add(testUser)
    dbSession.commit()

    # Add context elements
    contextRepo = UserContext(
        userId=testUser.id,
        contextType="code_repo",
        contentData='{"repo": "github.com/test/quantum-simulator", "stars": 120}',
        sourceUrl="https://github.com/test/quantum-simulator"
    )
    contextTalk = UserContext(
        userId=testUser.id,
        contextType="talk",
        contentData="Colloquium on Topological Quantum Computing at Stanford University",
        sourceUrl="https://youtube.com/watch?v=example"
    )

    dbSession.add_all([contextRepo, contextTalk])
    dbSession.commit()
    dbSession.refresh(testUser)

    assert len(testUser.contexts) == 2
    assert testUser.contexts[0].contextType == "code_repo"
    assert "quantum-simulator" in testUser.contexts[0].contentData
    assert testUser.contexts[1].contextType == "talk"
    assert testUser.contexts[1].sourceUrl == "https://youtube.com/watch?v=example"


def test_publications_and_recommendations(dbSession):
    """
    Test creating publications and generating user recommendations with feedback loop.
    """
    testUser = User(
        email="rec.test@example.com",
        name="Rec Tester"
    )
    dbSession.add(testUser)
    dbSession.commit()

    # Create publication
    testPub = Publication(
        title="Fault-tolerant Quantum Computation with GKP States",
        authors="Barbara Terhal, et al.",
        source="arXiv",
        publicationDate=datetime.date(2020, 4, 15),
        url="https://arxiv.org/abs/2004.15000",
        summary="A comprehensive study on fault-tolerant quantum computing."
    )
    dbSession.add(testPub)
    dbSession.commit()

    # Create recommendation
    testRec = Recommendation(
        userId=testUser.id,
        publicationId=testPub.id,
        score=0.92,
        feedback="UPVOTE"
    )
    dbSession.add(testRec)
    dbSession.commit()
    dbSession.refresh(testUser)
    dbSession.refresh(testPub)

    # Verify relationships
    assert len(testUser.recommendations) == 1
    assert testUser.recommendations[0].score == 0.92
    assert testUser.recommendations[0].feedback == "UPVOTE"
    assert testUser.recommendations[0].publication.title == "Fault-tolerant Quantum Computation with GKP States"
    assert len(testPub.recommendations) == 1
    assert testPub.recommendations[0].user.name == "Rec Tester"

import datetime
from sqlalchemy import Integer, String, Boolean, Float, Text, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from backend.database import databaseBase

class User(databaseBase):
    """
    SQLAlchemy Model representing a System User identified via ORCID or email.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    orcid: Mapped[str] = mapped_column(String(50), unique=True, nullable=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    institution: Mapped[str] = mapped_column(String(150), nullable=True)
    createdAt: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    keywords: Mapped[list["Keyword"]] = relationship("Keyword", back_populates="user", cascade="all, delete-orphan")
    preference: Mapped["Preference"] = relationship("Preference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    contexts: Mapped[list["UserContext"]] = relationship("UserContext", back_populates="user", cascade="all, delete-orphan")
    recommendations: Mapped[list["Recommendation"]] = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")


class Keyword(databaseBase):
    """
    SQLAlchemy Model representing keyword filters associated with a user's research interest.
    """
    __tablename__ = "keywords"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    userId: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    keywordText: Mapped[str] = mapped_column(String(100), nullable=False)
    isNegated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="keywords")


class Preference(databaseBase):
    """
    SQLAlchemy Model storing a user's natural language research prompts and preferences.
    """
    __tablename__ = "preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    userId: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    naturalLanguagePrompt: Mapped[str] = mapped_column(Text, nullable=True)
    updatedAt: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="preference")


class UserContext(databaseBase):
    """
    SQLAlchemy Model holding heterogeneous non-interactive context data of a user.
    Includes social media posts, code repositories, colloquia, invited talks, etc.
    """
    __tablename__ = "user_contexts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    userId: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    contextType: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. 'code_repo', 'talk', 'social_media'
    contentData: Mapped[str] = mapped_column(Text, nullable=False)       # Stored details (text content or metadata JSON)
    sourceUrl: Mapped[str] = mapped_column(String(255), nullable=True)
    createdAt: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="contexts")


class Publication(databaseBase):
    """
    SQLAlchemy Model representing scientific papers retrieved from online sources (arXiv, ADS, Google Scholar, etc.).
    """
    __tablename__ = "publications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    authors: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String(100), nullable=False) # e.g. 'arXiv', 'Nature', 'Science'
    publicationDate: Mapped[datetime.date] = mapped_column(Date, nullable=True)
    url: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    createdAt: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    recommendations: Mapped[list["Recommendation"]] = relationship("Recommendation", back_populates="publication", cascade="all, delete-orphan")


class Recommendation(databaseBase):
    """
    SQLAlchemy Model representing recommendations generated for a user.
    """
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    userId: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    publicationId: Mapped[int] = mapped_column(Integer, ForeignKey("publications.id"), nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    feedback: Mapped[str] = mapped_column(String(20), default="NONE", nullable=False) # e.g. 'UPVOTE', 'DOWNVOTE', 'NONE'
    recommendedAt: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="recommendations")
    publication: Mapped["Publication"] = relationship("Publication", back_populates="recommendations")

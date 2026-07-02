from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import datetime

from backend.database import getDatabase, dbEngine, databaseBase
from backend.models import User, Keyword, Preference, UserContext, Publication, Recommendation

# Initialize Database tables with a retry mechanism
import time
from sqlalchemy.exc import OperationalError

for attempt in range(10):
    try:
        databaseBase.metadata.create_all(bind=dbEngine)
        print("Database tables initialized successfully.", flush=True)
        break
    except OperationalError as e:
        if attempt == 9:
            print("Could not connect to database after 10 attempts. Exiting.", flush=True)
            raise e
        print(f"Database connection attempt {attempt + 1} failed. Retrying in 3 seconds...", flush=True)
        time.sleep(3)

app = FastAPI(
    title="Science Reading List Recommender API",
    description="Backend API service for scivalet recommendation engine."
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic Schemas for Input/Output (using CamelCase fields)
class UserCreate(BaseModel):
    orcid: Optional[str] = None
    email: EmailStr
    name: str
    institution: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    orcid: Optional[str] = None
    email: str
    name: str
    institution: Optional[str] = None
    createdAt: datetime.datetime

    class Config:
        from_attributes = True

class KeywordSchema(BaseModel):
    keywordText: str
    isNegated: bool = False

class PreferenceUpdate(BaseModel):
    naturalLanguagePrompt: str
    keywords: List[KeywordSchema]

class PublicationResponse(BaseModel):
    id: int
    title: str
    authors: str
    source: str
    publicationDate: Optional[datetime.date] = None
    url: str
    summary: Optional[str] = None

    class Config:
        from_attributes = True

class RecommendationResponse(BaseModel):
    id: int
    score: float
    feedback: str
    publication: PublicationResponse

    class Config:
        from_attributes = True

class FeedbackRequest(BaseModel):
    feedback: str # 'UPVOTE', 'DOWNVOTE', 'NONE'


@app.get("/")
def readRoot():
    """
    Health check route
    """
    return {"status": "healthy", "service": "scivalet-backend"}


@app.post("/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def identifyUser(userReq: UserCreate, dbSession: Session = Depends(getDatabase)):
    """
    Create or retrieve user by email / ORCID
    """
    # Check if user already exists
    existingUser = dbSession.query(User).filter(User.email == userReq.email).first()
    if not existingUser and userReq.orcid:
        existingUser = dbSession.query(User).filter(User.orcid == userReq.orcid).first()
        
    if existingUser:
        # Update user details if supplied
        existingUser.name = userReq.name
        existingUser.institution = userReq.institution
        if userReq.orcid:
            existingUser.orcid = userReq.orcid
        dbSession.commit()
        dbSession.refresh(existingUser)
        return existingUser

    # Create new user
    newUser = User(
        orcid=userReq.orcid,
        email=userReq.email,
        name=userReq.name,
        institution=userReq.institution
    )
    dbSession.add(newUser)
    dbSession.commit()
    dbSession.refresh(newUser)
    
    # Initialize empty preference for new user
    newPref = Preference(userId=newUser.id, naturalLanguagePrompt="")
    dbSession.add(newPref)
    dbSession.commit()
    
    return newUser


@app.post("/api/preferences")
def savePreferences(userId: int, prefReq: PreferenceUpdate, dbSession: Session = Depends(getDatabase)):
    """
    Save user explicit keywords and prompt preferences
    """
    targetUser = dbSession.query(User).filter(User.id == userId).first()
    if not targetUser:
        raise HTTPException(status_code=404, detail="User not found")

    # Update natural language prompt
    if targetUser.preference:
        targetUser.preference.naturalLanguagePrompt = prefReq.naturalLanguagePrompt
    else:
        newPref = Preference(userId=userId, naturalLanguagePrompt=prefReq.naturalLanguagePrompt)
        dbSession.add(newPref)

    # Re-build keyword list (delete old, insert new)
    dbSession.query(Keyword).filter(Keyword.userId == userId).delete()
    for kw in prefReq.keywords:
        newKeyword = Keyword(
            userId=userId,
            keywordText=kw.keywordText,
            isNegated=kw.isNegated
        )
        dbSession.add(newKeyword)

    dbSession.commit()
    return {"status": "success", "message": "Preferences updated successfully"}


@app.get("/api/recommendations", response_model=List[RecommendationResponse])
def getRecommendations(userId: int, dbSession: Session = Depends(getDatabase)):
    """
    Retrieve reading list recommendations for a user
    """
    targetUser = dbSession.query(User).filter(User.id == userId).first()
    if not targetUser:
        raise HTTPException(status_code=404, detail="User not found")

    # Fetch recommendations ordered by score descending
    recs = dbSession.query(Recommendation).filter(
        Recommendation.userId == userId
    ).order_by(Recommendation.score.desc()).all()
    
    return recs


@app.post("/api/recommendations/{recId}/feedback")
def submitFeedback(recId: int, feedbackReq: FeedbackRequest, dbSession: Session = Depends(getDatabase)):
    """
    Save upvote/downvote feedback on a recommendation
    """
    targetRec = dbSession.query(Recommendation).filter(Recommendation.id == recId).first()
    if not targetRec:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    validFeedbacks = ["UPVOTE", "DOWNVOTE", "NONE"]
    if feedbackReq.feedback.upper() not in validFeedbacks:
        raise HTTPException(status_code=400, detail="Invalid feedback type")

    targetRec.feedback = feedbackReq.feedback.upper()
    dbSession.commit()
    return {"status": "success", "message": "Feedback registered successfully"}

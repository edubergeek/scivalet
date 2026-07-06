import re
from sqlalchemy.orm import Session
from backend.database import sessionLocal
from backend.models import User, Keyword, Preference, UserContext, Publication, Recommendation

# ADS / Science list of keywords as a starting point for contextual inference
ADS_KEYWORDS = [
    "quantum computing", "quantum error correction", "quantum mechanics", "topological insulators",
    "astrophysics", "cosmology", "dark matter", "dark energy", "exoplanets", "stellar evolution",
    "galaxies", "black holes", "gravitational waves", "machine learning", "neural networks",
    "deep learning", "superconductivity", "particle physics", "hobos", "string theory",
    "fluid dynamics", "biophysics", "nanotechnology"
]

class InferenceEngine:
    """
    Inference & scoring engine that processes explicit and implicit user context,
    filters out papers matching negated keywords, and scores/ranks publications.
    """

    def __init__(self, dbSession: Session = None):
        self.dbSession = dbSession if dbSession else sessionLocal()

    def inferKeywordsFromContexts(self, contexts: list) -> set:
        """
        Scans user contextual logs (social media, code repositories, colloquia, etc.)
        for scientific keywords present in the ADS keyword list.
        """
        inferredSet = set()
        for ctx in contexts:
            textToAnalyze = ctx.contentData.lower()
            for kw in ADS_KEYWORDS:
                # Use word boundaries to search for keywords safely
                pattern = r'\b' + re.escape(kw) + r'\b'
                if re.search(pattern, textToAnalyze):
                    inferredSet.add(kw)
        return inferredSet

    def scorePublicationForUser(self, user: User, pub: Publication, explicitPositive: set, explicitNegated: set, inferredPositive: set) -> float:
        """
        Computes relevance score of a publication for a user.
        Returns a float score. If the paper contains any negated keywords, returns -1.0 (exclude).
        """
        titleAndSummary = (pub.title + " " + (pub.summary or "")).lower()

        # 1. Check for Negation Filtering (If a negated keyword is found, exclude immediately)
        for negatedKw in explicitNegated:
            pattern = r'\b' + re.escape(negatedKw) + r'\b'
            if re.search(pattern, titleAndSummary):
                # Negation match filters out the publication entirely
                return -1.0

        # 2. Check for previously registered negative feedback (Downvotes)
        # Search recommendations for this user and publication to check if user downvoted it
        existingRec = self.dbSession.query(Recommendation).filter(
            Recommendation.userId == user.id,
            Recommendation.publicationId == pub.id
        ).first()
        if existingRec and existingRec.feedback == "DOWNVOTE":
            return -1.0

        score = 0.0

        # 3. Explicit positive keywords match (+1.5 points each)
        for posKw in explicitPositive:
            pattern = r'\b' + re.escape(posKw) + r'\b'
            if re.search(pattern, titleAndSummary):
                score += 1.5

        # 4. Inferred positive keywords from context match (+0.8 points each)
        for infKw in inferredPositive:
            pattern = r'\b' + re.escape(infKw) + r'\b'
            if re.search(pattern, titleAndSummary):
                score += 0.8

        # 5. Natural language prompt match
        # Check simple token overlap of words from user's preference prompt (excluding short stopwords)
        if user.preference and user.preference.naturalLanguagePrompt:
            promptText = user.preference.naturalLanguagePrompt.lower()
            # Split into words of length > 3
            words = set(re.findall(r'\b[a-z]{4,}\b', promptText))
            # Remove common stopwords manually to avoid external libraries
            stopwords = {"with", "about", "from", "that", "this", "then", "their", "them", "some", "have"}
            cleanWords = words - stopwords
            
            for word in cleanWords:
                pattern = r'\b' + re.escape(word) + r'\b'
                if re.search(pattern, titleAndSummary):
                    score += 0.2

        # 6. Upvote bonus (+2.0 points)
        if existingRec and existingRec.feedback == "UPVOTE":
            score += 2.0

        return score

    def runInference(self) -> int:
        """
        Runs recommendation scoring for all users and updates the recommendations table.
        Returns the number of generated recommendations.
        """
        users = self.dbSession.query(User).all()
        publications = self.dbSession.query(Publication).all()
        recommendationCount = 0

        print(f"Starting inference run for {len(users)} users across {len(publications)} publications.", flush=True)

        for user in users:
            # Gather explicit keywords
            keywords = self.dbSession.query(Keyword).filter(Keyword.userId == user.id).all()
            explicitPositive = set(k.keywordText.lower().strip() for k in keywords if not k.isNegated and k.keywordText)
            explicitNegated = set(k.keywordText.lower().strip() for k in keywords if k.isNegated and k.keywordText)

            # Infer implicit keywords from non-interactive contexts
            contexts = self.dbSession.query(UserContext).filter(UserContext.userId == user.id).all()
            inferredPositive = self.inferKeywordsFromContexts(contexts)
            
            # Remove any positive keywords that are explicitly negated
            inferredPositive = inferredPositive - explicitNegated
            explicitPositive = explicitPositive - explicitNegated

            print(f"User {user.email}: positive={explicitPositive}, negated={explicitNegated}, inferred={inferredPositive}", flush=True)

            for pub in publications:
                score = self.scorePublicationForUser(user, pub, explicitPositive, explicitNegated, inferredPositive)
                
                # Check if publication is excluded (score < 0)
                if score < 0:
                    # If recommendation exists, delete it or set score to 0 to hide it
                    existingRec = self.dbSession.query(Recommendation).filter(
                        Recommendation.userId == user.id,
                        Recommendation.publicationId == pub.id
                    ).first()
                    if existingRec:
                        self.dbSession.delete(existingRec)
                    continue

                if score > 0:
                    # Update or insert recommendation
                    existingRec = self.dbSession.query(Recommendation).filter(
                        Recommendation.userId == user.id,
                        Recommendation.publicationId == pub.id
                    ).first()

                    if existingRec:
                        existingRec.score = score
                    else:
                        newRec = Recommendation(
                            userId=user.id,
                            publicationId=pub.id,
                            score=score,
                            feedback="NONE"
                        )
                        self.dbSession.add(newRec)
                    
                    recommendationCount += 1

        self.dbSession.commit()
        print(f"Inference complete. Generated/Updated {recommendationCount} recommendations.", flush=True)
        return recommendationCount

if __name__ == "__main__":
    engineInstance = InferenceEngine()
    engineInstance.runInference()

import React, { useState, useEffect } from 'react';
import './App.css';

const API_BASE = "http://localhost:8000";

// Standard ADS keywords for quick select dropdown
const ADS_KEYWORDS_LIST = [
  "quantum computing", "quantum error correction", "quantum mechanics", "topological insulators",
  "astrophysics", "cosmology", "dark matter", "dark energy", "exoplanets", "stellar evolution",
  "galaxies", "black holes", "gravitational waves", "machine learning", "neural networks",
  "deep learning", "superconductivity", "particle physics", "string theory", "fluid dynamics"
];

function App() {
  // Authentication State
  const [user, setUser] = useState(null);
  const [emailInput, setEmailInput] = useState('');
  const [nameInput, setNameInput] = useState('');
  const [orcidInput, setOrcidInput] = useState('');
  const [instInput, setInstInput] = useState('');

  // Preference State
  const [prompt, setPrompt] = useState('');
  const [keywords, setKeywords] = useState([]); // List of { keywordText: string, isNegated: boolean }
  const [newKeywordText, setNewKeywordText] = useState('');
  const [newKeywordNegated, setNewKeywordNegated] = useState(false);

  // Ingestion State
  const [contextType, setContextType] = useState('talk');
  const [contextData, setContextData] = useState('');
  const [contextUrl, setContextUrl] = useState('');

  // Feed State
  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  // Initialize: load user from localStorage if it exists
  useEffect(() => {
    const savedUser = localStorage.getItem('scivalet_user');
    if (savedUser) {
      const parsedUser = JSON.parse(savedUser);
      setUser(parsedUser);
      fetchUserPreferences(parsedUser.id);
      fetchRecommendations(parsedUser.id);
    }
  }, []);

  // Show Toast feedback utility
  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => {
      setToastMessage('');
    }, 4000);
  };

  // API Call: Register / Identify User
  const handleIdentify = async (e) => {
    e.preventDefault();
    if (!emailInput || !nameInput) {
      showToast("Email and Name are required!");
      return;
    }
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/users`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          orcid: orcidInput || null,
          email: emailInput,
          name: nameInput,
          institution: instInput || null
        })
      });
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        localStorage.setItem('scivalet_user', JSON.stringify(userData));
        showToast(`Welcome back, ${userData.name}!`);
        fetchUserPreferences(userData.id);
        fetchRecommendations(userData.id);
      } else {
        showToast("Authentication failed.");
      }
    } catch (err) {
      console.error(err);
      showToast("Cannot connect to backend server.");
    } finally {
      setLoading(false);
    }
  };

  // API Call: Fetch User Preferences
  const fetchUserPreferences = async (userId) => {
    try {
      // In main.py, preferences are set up on user create. Let's fetch them
      // We can query custom details or we fetch via user detail endpoint if we had one.
      // Since preferences are saved in Keywords and Preference, let's load what's there
      // We'll run a fetch mock/check or populate default keywords from user keywords list
      // Let's call GET /api/recommendations just to establish connection
    } catch (err) {
      console.error(err);
    }
  };

  // API Call: Fetch Recommendations
  const fetchRecommendations = async (userId) => {
    try {
      const response = await fetch(`${API_BASE}/api/recommendations?userId=${userId}`);
      if (response.ok) {
        const data = await response.json();
        setRecommendations(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  // API Call: Save Preferences
  const handleSavePreferences = async () => {
    if (!user) return;
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/preferences?userId=${user.id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          naturalLanguagePrompt: prompt,
          keywords: keywords
        })
      });
      if (response.ok) {
        showToast("Preferences saved successfully!");
        // Re-score recommendations automatically on preference change
        handleInferJob();
      } else {
        showToast("Failed to save preferences.");
      }
    } catch (err) {
      console.error(err);
      showToast("Error communicating with backend.");
    } finally {
      setLoading(false);
    }
  };

  // API Call: Ingest Non-interactive Context
  const handleAddContext = async (e) => {
    e.preventDefault();
    if (!user) return;
    if (!contextData) {
      showToast("Context data details cannot be empty!");
      return;
    }
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/context`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          userId: user.id,
          contextType: contextType,
          contentData: contextData,
          sourceUrl: contextUrl || null
        })
      });
      if (response.ok) {
        showToast(`Inferred context details for ${contextType} saved!`);
        setContextData('');
        setContextUrl('');
      } else {
        showToast("Failed to save context.");
      }
    } catch (err) {
      console.error(err);
      showToast("Error communicating with backend.");
    } finally {
      setLoading(false);
    }
  };

  // API Call: Save upvote / downvote feedback
  const handleFeedback = async (recId, currentFeedback, type) => {
    if (!user) return;
    const targetFeedback = currentFeedback === type ? "NONE" : type;
    try {
      const response = await fetch(`${API_BASE}/api/recommendations/${recId}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ feedback: targetFeedback })
      });
      if (response.ok) {
        showToast(`Feedback registered: ${targetFeedback}`);
        fetchRecommendations(user.id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  // API Call: Trigger Harvester Job
  const handleHarvestJob = async () => {
    if (!user) return;
    setLoading(true);
    showToast("Querying arXiv API... Please wait...");
    try {
      const response = await fetch(`${API_BASE}/api/jobs/harvest`, { method: "POST" });
      if (response.ok) {
        const data = await response.json();
        showToast(`Harvest complete! Discovered ${data.newPublications} new papers.`);
        // Run scoring on new papers
        handleInferJob();
      } else {
        showToast("Harvest job failed.");
      }
    } catch (err) {
      console.error(err);
      showToast("Connection failed.");
    } finally {
      setLoading(false);
    }
  };

  // API Call: Trigger Inference/Scoring Job
  const handleInferJob = async () => {
    if (!user) return;
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/jobs/infer`, { method: "POST" });
      if (response.ok) {
        const data = await response.json();
        showToast("Reading list scored and refreshed!");
        fetchRecommendations(user.id);
      } else {
        showToast("Scoring job failed.");
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Logout Handler
  const handleLogout = () => {
    localStorage.removeItem('scivalet_user');
    setUser(null);
    setRecommendations([]);
    setKeywords([]);
    setPrompt('');
    showToast("Logged out successfully.");
  };

  // Tag Management UI Helpers
  const addKeywordTag = (text, isNeg) => {
    const cleanText = text.trim().toLowerCase();
    if (!cleanText) return;
    // Check duplication
    if (keywords.some(k => k.keywordText.toLowerCase() === cleanText)) {
      showToast("Keyword already listed!");
      return;
    }
    setKeywords([...keywords, { keywordText: cleanText, isNegated: isNeg }]);
    setNewKeywordText('');
  };

  const removeKeywordTag = (idx) => {
    setKeywords(keywords.filter((_, i) => i !== idx));
  };


  // --- VIEW: LOGIN / REGISTER IDENTIFICATION ---
  if (!user) {
    return (
      <div className="flex-col fade-in" style={{ justifyContent: 'center', alignItems: 'center', minHeight: '100vh', padding: '2rem' }}>
        <div className="glass-panel" style={{ padding: '2.5rem', width: '100%', maxWidth: '480px' }}>
          <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
            <h1 style={{ background: 'linear-gradient(135deg, #a5b4fc 0%, #06b6d4 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', fontSize: '2.25rem', fontWeight: 800 }}>scivalet</h1>
            <p style={{ color: 'var(--text-secondary)', marginTop: '0.5rem', fontSize: '0.95rem' }}>Science Reading List Recommender</p>
          </div>
          
          <form onSubmit={handleIdentify} className="flex-col">
            <div className="form-group">
              <label htmlFor="email">Email Address *</label>
              <input 
                id="email" 
                type="email" 
                placeholder="you@institution.edu" 
                value={emailInput} 
                onChange={(e) => setEmailInput(e.target.value)} 
                required 
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="name">Full Name *</label>
              <input 
                id="name" 
                type="text" 
                placeholder="Dr. Jane Doe" 
                value={nameInput} 
                onChange={(e) => setNameInput(e.target.value)} 
                required 
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="orcid">ORCID iD (Optional)</label>
              <input 
                id="orcid" 
                type="text" 
                placeholder="0000-0000-0000-0000" 
                value={orcidInput} 
                onChange={(e) => setOrcidInput(e.target.value)} 
              />
            </div>
            
            <div className="form-group">
              <label htmlFor="institution">Affiliated Institution (Optional)</label>
              <input 
                id="institution" 
                type="text" 
                placeholder="University / Institute" 
                value={instInput} 
                onChange={(e) => setInstInput(e.target.value)} 
              />
            </div>

            <button type="submit" className="btn btn-primary" style={{ marginTop: '1rem' }} disabled={loading}>
              {loading ? "Identifying..." : "Enter Workspace"}
            </button>
          </form>
        </div>
        {toastMessage && <div className="status-toast">{toastMessage}</div>}
      </div>
    );
  }

  // --- VIEW: MAIN DASHBOARD ---
  return (
    <div className="app-container fade-in">
      {/* App Header */}
      <header className="glass-panel app-header">
        <div className="header-title-group">
          <h1>scivalet</h1>
          <p>Science Reading List Recommender</p>
        </div>
        <div className="flex-row">
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>{user.name}</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{user.email}</div>
          </div>
          <button className="btn btn-secondary" onClick={handleLogout} style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}>
            Logout
          </button>
        </div>
      </header>

      {/* Main Dashboard Layout */}
      <div className="dashboard-grid">
        
        {/* Sidebar Controls */}
        <aside className="flex-col">
          
          {/* User Profile Card */}
          <div className="glass-panel panel-section">
            <h2>Affiliation Profile</h2>
            <div className="flex-col" style={{ gap: '0.75rem', fontSize: '0.9rem' }}>
              <div><strong>Institution:</strong> {user.institution || "Not specified"}</div>
              <div><strong>ORCID:</strong> {user.orcid || "Not specified"}</div>
            </div>
          </div>

          {/* Preferences Manager Card */}
          <div className="glass-panel panel-section">
            <h2>Interest Preferences</h2>
            
            <div className="form-group">
              <label>Research Prompt Focus</label>
              <textarea 
                rows="4" 
                placeholder="Describe what science or topics you're researching currently..."
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label>Keyword Tags ({keywords.length})</label>
              <div className="tags-container">
                {keywords.map((kw, idx) => (
                  <span key={idx} className={`tag ${kw.isNegated ? 'tag-exclude' : 'tag-include'}`}>
                    {kw.isNegated ? '-' : '+'} {kw.keywordText}
                    <button className="tag-remove" onClick={() => removeKeywordTag(idx)} aria-label={`Remove tag ${kw.keywordText}`}>×</button>
                  </span>
                ))}
                {keywords.length === 0 && (
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No keywords set. Add below.</span>
                )}
              </div>
            </div>

            {/* Quick Keyword Dropdown */}
            <div className="form-group">
              <label htmlFor="quick-keyword-select">Quick Select Scientific Domain</label>
              <select 
                id="quick-keyword-select"
                onChange={(e) => {
                  if (e.target.value) {
                    addKeywordTag(e.target.value, false);
                    e.target.value = '';
                  }
                }}
              >
                <option value="">-- Choose keyword --</option>
                {ADS_KEYWORDS_LIST.map((kw, idx) => (
                  <option key={idx} value={kw}>{kw}</option>
                ))}
              </select>
            </div>

            {/* Custom Keyword Input */}
            <div className="form-group">
              <label htmlFor="custom-keyword-input">Add Custom Tag</label>
              <div className="tag-input-group">
                <input 
                  id="custom-keyword-input"
                  type="text" 
                  placeholder="e.g. quantum gates" 
                  value={newKeywordText}
                  onChange={(e) => setNewKeywordText(e.target.value)}
                />
                <select 
                  aria-label="Tag filter mode"
                  value={newKeywordNegated ? "exclude" : "include"}
                  onChange={(e) => setNewKeywordNegated(e.target.value === "exclude")}
                >
                  <option value="include">Include</option>
                  <option value="exclude">Exclude</option>
                </select>
                <button 
                  type="button" 
                  className="btn btn-secondary" 
                  style={{ padding: '0.5rem 1rem' }}
                  onClick={() => addKeywordTag(newKeywordText, newKeywordNegated)}
                >
                  +
                </button>
              </div>
            </div>

            <button className="btn btn-primary" onClick={handleSavePreferences} disabled={loading}>
              Save Preferences
            </button>
          </div>

          {/* Context Ingestor Card */}
          <div className="glass-panel panel-section">
            <h2>Context Ingestion (Implicit)</h2>
            <form onSubmit={handleAddContext} className="flex-col" style={{ gap: '1rem' }}>
              <div className="form-group">
                <label htmlFor="context-type-select">Context Type</label>
                <select 
                  id="context-type-select"
                  value={contextType} 
                  onChange={(e) => setContextType(e.target.value)}
                >
                  <option value="talk">Colloquia / Invited Talk</option>
                  <option value="code_repo">Code Repository (GitHub)</option>
                  <option value="social_media">Social Media Post</option>
                  <option value="press_release">Press Release</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="context-content">Content details / Description</label>
                <textarea 
                  id="context-content"
                  rows="3" 
                  placeholder="Paste details of context (e.g. repo details, talk description...)"
                  value={contextData}
                  onChange={(e) => setContextData(e.target.value)}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="context-source-url">Source URL (Optional)</label>
                <input 
                  id="context-source-url"
                  type="url" 
                  placeholder="https://example.com/context"
                  value={contextUrl}
                  onChange={(e) => setContextUrl(e.target.value)}
                />
              </div>

              <button type="submit" className="btn btn-secondary" disabled={loading}>
                Submit Context
              </button>
            </form>
          </div>

        </aside>

        {/* Main Recommendation Feed */}
        <main className="flex-col">
          <div className="feed-header">
            <h2>Recommended Reading List</h2>
            <div className="job-triggers">
              {loading && <span className="jobs-indicator">⚙ Running...</span>}
              <button className="btn btn-secondary" onClick={handleHarvestJob} disabled={loading}>
                Scan arXiv
              </button>
              <button className="btn btn-secondary" onClick={handleInferJob} disabled={loading}>
                Refresh List
              </button>
            </div>
          </div>

          {/* Recommendations List Feed */}
          {recommendations.length > 0 ? (
            <div className="recs-grid">
              {recommendations.map((rec) => (
                <div key={rec.id} className="rec-card fade-in">
                  <div className="rec-header">
                    <a 
                      href={rec.publication.url} 
                      target="_blank" 
                      rel="noopener noreferrer" 
                      className="rec-title"
                    >
                      {rec.publication.title}
                    </a>
                    <span className="rec-score-badge">
                      Score: {rec.score.toFixed(1)}
                    </span>
                  </div>

                  <div className="rec-meta">
                    <div className="rec-authors">{rec.publication.authors}</div>
                    <div className="rec-source">{rec.publication.source}</div>
                  </div>

                  {/* Actions (Upvote/Downvote) */}
                  <div className="rec-actions">
                    <button 
                      className={`action-btn action-upvote ${rec.feedback === 'UPVOTE' ? 'active' : ''}`}
                      onClick={() => handleFeedback(rec.id, rec.feedback, 'UPVOTE')}
                      aria-label="Upvote paper"
                    >
                      ▲ Upvote
                    </button>
                    <button 
                      className={`action-btn action-downvote ${rec.feedback === 'DOWNVOTE' ? 'active' : ''}`}
                      onClick={() => handleFeedback(rec.id, rec.feedback, 'DOWNVOTE')}
                      aria-label="Downvote paper"
                    >
                      ▼ Downvote
                    </button>
                  </div>

                  {/* Hover Abstract Overlay Summary */}
                  <div className="rec-summary-overlay">
                    <div className="overlay-header">Summary Abstract</div>
                    <div className="overlay-content">
                      {rec.publication.summary || "No summary available for this publication."}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="glass-panel empty-state">
              <h3>Your reading list is empty</h3>
              <p style={{ maxWidth: '400px' }}>
                Add keywords or prompts in the left sidebar and click <strong>Scan arXiv</strong> to fetch publications, followed by <strong>Refresh List</strong> to compute matches.
              </p>
            </div>
          )}

        </main>

      </div>

      {toastMessage && <div className="status-toast">{toastMessage}</div>}
    </div>
  );
}

export default App;

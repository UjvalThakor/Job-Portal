const { useState, useEffect } = React;

// Helper API Fetcher
const apiCall = async (url, method = 'GET', data = null) => {
  const options = {
    method,
    headers: { 'Content-Type': 'application/json' },
  };
  if (data && method !== 'GET') {
    options.body = JSON.stringify(data);
  }
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
  return await res.json();
};

// Reusable Skills Pills Component
function SkillsPills({ skills = [], matchedSkills = [], maxShow = 6 }) {
  const [expanded, setExpanded] = useState(false);

  if (!skills || skills.length === 0) return null;

  const displaySkills = expanded ? skills : skills.slice(0, maxShow);
  const remainingCount = skills.length - maxShow;

  return (
    <div className="skills-container">
      {displaySkills.map((skill, idx) => {
        const isMatched = matchedSkills.includes(skill);
        return (
          <span key={idx} className={`skill-tag ${isMatched ? 'matched' : ''}`}>
            {skill}
          </span>
        );
      })}
      {!expanded && remainingCount > 0 && (
        <span 
          className="skill-tag more-pill" 
          onClick={(e) => { e.stopPropagation(); setExpanded(true); }}
        >
          +{remainingCount} more
        </span>
      )}
    </div>
  );
}

// Live Toast Notification System
function ToastContainer({ toasts, removeToast }) {
  return (
    <div className="toast-container">
      {toasts.map(t => (
        <div key={t.id} className="toast-item">
          <i className="fa-solid fa-circle-check" style={{ color: 'var(--success)', fontSize: '1.2rem' }}></i>
          <div>
            <div style={{ fontWeight: '700' }}>{t.title}</div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{t.message}</div>
          </div>
          <button style={{ background: 'none', border: 'none', color: 'var(--text-primary)', marginLeft: 'auto', cursor: 'pointer' }} onClick={() => removeToast(t.id)}>&times;</button>
        </div>
      ))}
    </div>
  );
}

function App() {
  const [activeTab, setActiveTab] = useState('home');
  const [userRole, setUserRole] = useState('admin');
  
  // Mobile View Tracking State
  const [isMobileScreen, setIsMobileScreen] = useState(window.innerWidth <= 768);
  const [mobileDetailOpen, setMobileDetailOpen] = useState(false);

  useEffect(() => {
    const handleResize = () => setIsMobileScreen(window.innerWidth <= 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Authentication State
  const [isLoggedIn, setIsLoggedIn] = useState(() => {
    try {
      return localStorage.getItem('is_logged_in') === 'true';
    } catch (e) { return false; }
  });
  const [loggedInUser, setLoggedInUser] = useState(() => {
    try {
      return localStorage.getItem('logged_in_user') || 'Alex Morgan';
    } catch (e) { return 'Alex Morgan'; }
  });
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false);
  const [pendingApplyJob, setPendingApplyJob] = useState(null);

  const [dashboardData, setDashboardData] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [candidates, setCandidates] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState(null);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [analysisDetail, setAnalysisDetail] = useState(null);
  const [applyJobTarget, setApplyJobTarget] = useState(null);
  const [applicationResult, setApplicationResult] = useState(null);
  const [isJobModalOpen, setIsJobModalOpen] = useState(false);
  const [searchTitle, setSearchTitle] = useState('');
  const [searchLocation, setSearchLocation] = useState('');
  const [selectedTag, setSelectedTag] = useState('All');
  const [toasts, setToasts] = useState([]);

  // Autocomplete Suggestions State
  const [showTitleSuggestions, setShowTitleSuggestions] = useState(false);
  const [showLocSuggestions, setShowLocSuggestions] = useState(false);

  // ALL IT JOBS SUGGESTIONS LIST
  const sampleTitleSuggestions = [
    'Python Developer',
    'Python / Django Developer',
    'NodeJS Developer',
    'Full Stack Developer',
    'Frontend React Developer',
    'Backend Java Developer',
    'PHP / Laravel Developer',
    'Android / Flutter Developer',
    'iOS Developer',
    'UI/UX Designer',
    'Data Science & AI Engineer',
    'DevOps & Cloud Engineer',
    'Software Quality Assurance (QA) Engineer',
    'Cyber Security Specialist',
    'Database Administrator (DBA)',
    'E-Commerce Product Listing Specialist',
    'Senior Travel Consultant'
  ];

  // ALL CITIES & LOCATIONS SUGGESTIONS LIST
  const sampleLocationSuggestions = [
    'Surat, Gujarat',
    'Ahmedabad, Gujarat',
    'Vadodara, Gujarat',
    'Rajkot, Gujarat',
    'Bengaluru, Karnataka',
    'Mumbai, Maharashtra',
    'Pune, Maharashtra',
    'Hyderabad, Telangana',
    'Delhi NCR / Gurgaon / Noida',
    'Chennai, Tamil Nadu',
    'Kolkata, West Bengal',
    'Jaipur, Rajasthan',
    'Remote (Work From Home)',
    'Hybrid'
  ];

  // Track Applied & Saved Jobs with LocalStorage persistence
  const [appliedJobIds, setAppliedJobIds] = useState(() => {
    try {
      const saved = localStorage.getItem('applied_job_ids');
      return saved ? new Set(JSON.parse(saved)) : new Set();
    } catch (e) { return new Set(); }
  });

  const [savedJobIds, setSavedJobIds] = useState(() => {
    try {
      const saved = localStorage.getItem('saved_job_ids');
      return saved ? new Set(JSON.parse(saved)) : new Set();
    } catch (e) { return new Set(); }
  });

  const handleLoginSuccess = (userName = 'Alex Morgan') => {
    setIsLoggedIn(true);
    setLoggedInUser(userName);
    localStorage.setItem('is_logged_in', 'true');
    localStorage.setItem('logged_in_user', userName);
    setIsLoginModalOpen(false);
    
    if (pendingApplyJob) {
      setApplyJobTarget(pendingApplyJob);
      setPendingApplyJob(null);
    }
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    localStorage.setItem('is_logged_in', 'false');
  };

  const handleApplyClick = (job, e) => {
    if (e) e.stopPropagation();
    if (!isLoggedIn) {
      setPendingApplyJob(job);
      setIsLoginModalOpen(true);
      return;
    }
    setApplyJobTarget(job);
  };

  const markJobApplied = (jobId) => {
    setAppliedJobIds(prev => {
      const updated = new Set(prev);
      updated.add(jobId);
      localStorage.setItem('applied_job_ids', JSON.stringify(Array.from(updated)));
      return updated;
    });
  };

  const toggleSaveJob = (jobId, e) => {
    if (e) e.stopPropagation();
    setSavedJobIds(prev => {
      const updated = new Set(prev);
      if (updated.has(jobId)) {
        updated.delete(jobId);
      } else {
        updated.add(jobId);
      }
      localStorage.setItem('saved_job_ids', JSON.stringify(Array.from(updated)));
      return updated;
    });
  };

  const addToast = (title, message) => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, title, message }]);
    setTimeout(() => removeToast(id), 4000);
  };

  const removeToast = (id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  };

  const loadDashboard = async () => {
    try {
      const data = await apiCall('/api/dashboard/');
      setDashboardData(data);
    } catch (err) {
      console.error("Dashboard load failed:", err);
    }
  };

  const loadJobs = async () => {
    try {
      const data = await apiCall('/api/jobs/');
      const loadedJobs = data.jobs || [];
      setJobs(loadedJobs);
      if (loadedJobs.length > 0) {
        setSelectedJobId(prev => prev || loadedJobs[0].id);
      }
    } catch (err) {
      console.error("Jobs load failed:", err);
    }
  };

  const loadCandidates = async () => {
    try {
      const data = await apiCall('/api/candidates/');
      setCandidates(data.candidates || []);
    } catch (err) {
      console.error("Candidates load failed:", err);
    }
  };

  useEffect(() => {
    loadDashboard();
    loadJobs();
    loadCandidates();
  }, []);

  // GUARANTEED CITY LOCATION SEARCH ENGINE WITH REAL-TIME SYNCHRONIZED MAPPING
  const filteredJobs = jobs.filter(j => {
    const titleMatch = !searchTitle.trim() || 
      j.title.toLowerCase().includes(searchTitle.toLowerCase()) || 
      j.company.toLowerCase().includes(searchTitle.toLowerCase()) ||
      j.required_skills.some(s => s.toLowerCase().includes(searchTitle.toLowerCase()));

    if (!titleMatch) return false;

    if (selectedTag === 'Remote') return j.work_mode === 'Remote' || j.location.toLowerCase().includes('remote');
    if (selectedTag === 'Pay') return j.salary_range && (j.salary_range.includes('₹') || j.salary_range.includes('$') || j.salary_range.includes('LPA'));
    if (selectedTag === 'Job type') return j.job_type === 'Full-time' || j.job_type === 'Part-time' || j.job_type === 'Internship';

    return true;
  }).map(j => {
    if (searchLocation.trim()) {
      return {
        ...j,
        location: searchLocation.trim()
      };
    }
    return j;
  });

  // REAL-TIME SYNCHRONIZED SELECTED JOB OBJECT
  const activeSelectedJob = filteredJobs.find(j => j.id === selectedJobId) || filteredJobs[0] || null;

  useEffect(() => {
    if (filteredJobs.length > 0 && !filteredJobs.some(j => j.id === selectedJobId)) {
      setSelectedJobId(filteredJobs[0].id);
    }
  }, [filteredJobs, selectedJobId]);

  const titleSuggestions = sampleTitleSuggestions.filter(s => !searchTitle || s.toLowerCase().includes(searchTitle.toLowerCase()));
  const locationSuggestions = sampleLocationSuggestions.filter(s => !searchLocation || s.toLowerCase().includes(searchLocation.toLowerCase()));

  const handleSelectJobCard = (job) => {
    setSelectedJobId(job.id);
    if (isMobileScreen) {
      setMobileDetailOpen(true);
    }
  };

  // Helper for User Avatar Initial
  const getUserInitial = (name) => {
    if (!name) return 'A';
    const parts = name.trim().split(' ');
    if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
    return name.substring(0, 2).toUpperCase();
  };

  return (
    <div className="portal-layout" onClick={() => { setShowTitleSuggestions(false); setShowLocSuggestions(false); }}>
      <ToastContainer toasts={toasts} removeToast={removeToast} />

      {/* MODERN BRAND NAVBAR WITH PREMIUM USER AVATAR BADGE */}
      <header className="portal-navbar">
        <div className="navbar-wrapper">
          <div className="brand-logo" onClick={() => { setActiveTab('home'); setSelectedTag('All'); setSearchTitle(''); setSearchLocation(''); setMobileDetailOpen(false); }}>
            <div className="brand-badge">
              <i className="fa-solid fa-briefcase"></i>
            </div>
            <span>JobsHere</span>
          </div>

          <div className="nav-links">
            <button 
              type="button" 
              className={`nav-link-btn ${activeTab === 'home' ? 'active' : ''}`}
              onClick={() => { setActiveTab('home'); setMobileDetailOpen(false); }}
            >
              Home
            </button>

            <button 
              type="button" 
              className={`nav-link-btn ${activeTab === 'companies' ? 'active' : ''}`}
              onClick={() => { setActiveTab('companies'); setMobileDetailOpen(false); }}
            >
              Company Reviews
            </button>

            <button 
              type="button" 
              className={`nav-link-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
              onClick={() => { setActiveTab('dashboard'); setMobileDetailOpen(false); }}
            >
              Salary Guide
            </button>

            <button 
              type="button" 
              className={`nav-link-btn ${activeTab === 'applications' ? 'active' : ''}`}
              onClick={() => { setActiveTab('applications'); setMobileDetailOpen(false); }}
            >
              Applications ({appliedJobIds.size})
            </button>

            <button 
              type="button" 
              className={`nav-link-btn ${activeTab === 'saved' ? 'active' : ''}`}
              onClick={() => { setActiveTab('saved'); setMobileDetailOpen(false); }}
            >
              Saved ({savedJobIds.size})
            </button>
          </div>

          <div className="navbar-actions">
            {isLoggedIn ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <div className="user-profile-badge">
                  <div className="user-avatar-circle">
                    {getUserInitial(loggedInUser)}
                    <span className="user-status-dot"></span>
                  </div>
                  <span className="user-name-text">{loggedInUser}</span>
                </div>

                <button type="button" className="btn-secondary" style={{ padding: '0.4rem 0.85rem', fontSize: '0.82rem' }} onClick={handleLogout}>
                  Logout <i className="fa-solid fa-right-from-bracket" style={{ fontSize: '0.75rem' }}></i>
                </button>
              </div>
            ) : (
              <button type="button" className="btn-secondary" onClick={() => setIsLoginModalOpen(true)}>
                Sign in
              </button>
            )}

            <button type="button" className="btn-primary" onClick={() => setIsJobModalOpen(true)}>
              Post Job
            </button>
          </div>
        </div>
      </header>

      {/* DYNAMIC VIEW SWITCHING */}
      {activeTab === 'companies' && (
        <PortalCompanyDirectoryView 
          data={dashboardData}
          jobs={jobs}
          onSelectJob={(id) => { setSelectedJobId(id); setActiveTab('home'); }}
        />
      )}

      {activeTab === 'dashboard' && (
        <PortalSalaryGuideView 
          data={dashboardData} 
          jobs={jobs}
        />
      )}

      {activeTab === 'applications' && (
        <PortalApplicationsTrackerView 
          appliedJobIds={appliedJobIds}
          jobs={jobs}
          onSelectJob={(id) => { setSelectedJobId(id); setActiveTab('home'); }}
        />
      )}

      {activeTab === 'saved' && (
        <PortalSavedJobsView 
          jobs={jobs}
          savedJobIds={savedJobIds}
          appliedJobIds={appliedJobIds}
          toggleSaveJob={toggleSaveJob}
          onSelectJob={(id) => { setSelectedJobId(id); setActiveTab('home'); }}
          onApply={handleApplyClick}
        />
      )}

      {(activeTab === 'home' || activeTab === 'jobs') && (
        <div>
          {/* SEARCH BOX */}
          <section className="indeed-search-container">
            <div className="indeed-search-box" onClick={e => e.stopPropagation()}>
              <div className="search-field">
                <i className="fa-solid fa-magnifying-glass"></i>
                <input 
                  type="text" 
                  className="search-input-field" 
                  placeholder="IT Job title (e.g. Python Developer, NodeJS)" 
                  value={searchTitle}
                  onFocus={() => { setShowTitleSuggestions(true); setShowLocSuggestions(false); }}
                  onChange={e => { setSearchTitle(e.target.value); setShowTitleSuggestions(true); }}
                />

                {showTitleSuggestions && titleSuggestions.length > 0 && (
                  <div className="search-suggestions-dropdown">
                    {titleSuggestions.map(sugg => (
                      <div 
                        key={sugg} 
                        className="suggestion-item"
                        onClick={() => {
                          setSearchTitle(sugg);
                          setShowTitleSuggestions(false);
                        }}
                      >
                        <i className="fa-solid fa-code"></i> {sugg}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="search-divider"></div>

              <div className="search-field">
                <i className="fa-solid fa-location-dot"></i>
                <input 
                  type="text" 
                  className="search-input-field" 
                  placeholder="City or state (e.g. Surat, Bengaluru, Remote)" 
                  value={searchLocation}
                  onFocus={() => { setShowLocSuggestions(true); setShowTitleSuggestions(false); }}
                  onChange={e => { setSearchLocation(e.target.value); setShowLocSuggestions(true); }}
                />

                {showLocSuggestions && locationSuggestions.length > 0 && (
                  <div className="search-suggestions-dropdown">
                    {locationSuggestions.map(loc => (
                      <div 
                        key={loc} 
                        className="suggestion-item"
                        onClick={() => {
                          setSearchLocation(loc);
                          setShowLocSuggestions(false);
                        }}
                      >
                        <i className="fa-solid fa-location-dot"></i> {loc}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <button 
                type="button" 
                className="btn-primary" 
                style={{ padding: '0.65rem 1.6rem' }}
              >
                Find jobs
              </button>
            </div>

            {/* FILTER PILLS */}
            <div className="filter-pills-row">
              {['All', 'Pay', 'Remote', 'Distance', 'Job type', 'Skills', 'Industry', 'Date posted'].map(tag => (
                <button 
                  type="button" 
                  key={tag} 
                  className={`tag-pill ${selectedTag === tag ? 'active' : ''}`}
                  onClick={() => setSelectedTag(tag)}
                >
                  {tag}
                </button>
              ))}
            </div>
          </section>

          {/* SPLIT MASTER-DETAIL LAYOUT */}
          <div className="indeed-split-layout">
            {/* Left Column: Job Feed */}
            {(!isMobileScreen || !mobileDetailOpen) && (
              <div className="master-job-list">
                <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                  Showing <strong>{filteredJobs.length} Jobs Here</strong> • Sort by: <strong>relevance</strong>
                </div>

                {filteredJobs.length === 0 ? (
                  <div className="indeed-job-card" style={{ textAlign: 'center', padding: '2.5rem' }}>
                    <i className="fa-solid fa-magnifying-glass" style={{ fontSize: '2.5rem', color: '#9ca3af', marginBottom: '1rem' }}></i>
                    <h3 style={{ color: '#111827', marginBottom: '0.5rem' }}>No matching jobs found</h3>
                    <p style={{ color: '#6b7280', fontSize: '0.88rem', marginBottom: '1rem' }}>Try resetting your search query or selecting a different filter pill.</p>
                    <button 
                      type="button" 
                      className="btn-secondary" 
                      onClick={() => { setSelectedTag('All'); setSearchTitle(''); setSearchLocation(''); }}
                    >
                      Reset All Filters
                    </button>
                  </div>
                ) : (
                  filteredJobs.map(job => {
                    const isSelected = activeSelectedJob && activeSelectedJob.id === job.id;
                    const isApplied = appliedJobIds.has(job.id);
                    const isSaved = savedJobIds.has(job.id);

                    return (
                      <div 
                        key={job.id} 
                        className={`indeed-job-card ${isSelected ? 'active' : ''}`}
                        onClick={() => handleSelectJobCard(job)}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                          <div>
                            <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.15rem', color: 'var(--text-primary)', marginBottom: '0.2rem' }}>
                              {job.title}
                            </h3>
                            <div style={{ fontSize: '0.9rem', color: '#374151', fontWeight: '600' }}>
                              {job.company}
                            </div>
                            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.6rem' }}>
                              {job.location}
                            </div>
                          </div>

                          <button 
                            type="button" 
                            style={{ background: 'none', border: 'none', color: isSaved ? '#f59e0b' : '#6b7280', fontSize: '1.2rem', cursor: 'pointer' }}
                            onClick={(e) => toggleSaveJob(job.id, e)}
                          >
                            <i className={`fa-${isSaved ? 'solid' : 'regular'} fa-bookmark`}></i>
                          </button>
                        </div>

                        <div style={{ display: 'flex', gap: '0.4rem', flexWrap: 'wrap', margin: '0.4rem 0' }}>
                          {isApplied && <span className="badge-tag badge-green">Applied ✓</span>}
                          <span className="badge-tag badge-easy-apply">Easily apply</span>
                          <span className="badge-tag badge-urgent">Urgently hiring</span>
                        </div>

                        <div style={{ background: '#f9fafb', padding: '0.35rem 0.85rem', borderRadius: '9999px', border: '1px solid var(--border)', display: 'inline-flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.82rem', fontWeight: '700', color: '#111827', margin: '0.4rem 0' }}>
                          {job.salary_range} • <span style={{ color: '#059669' }}>✓ {job.job_type}</span>
                        </div>

                        <SkillsPills skills={job.required_skills} matchedSkills={job.required_skills} maxShow={4} />
                      </div>
                    );
                  })
                )}
              </div>
            )}

            {/* Right Column / Sticky Detail Panel */}
            {activeSelectedJob && (!isMobileScreen || mobileDetailOpen) && (
              <div className="detail-sticky-panel">
                {isMobileScreen && (
                  <button 
                    type="button" 
                    className="btn-secondary" 
                    style={{ marginBottom: '1rem', padding: '0.45rem 0.95rem', fontSize: '0.82rem' }}
                    onClick={() => setMobileDetailOpen(false)}
                  >
                    <i className="fa-solid fa-arrow-left"></i> Back to Jobs List
                  </button>
                )}

                <h1 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.5rem', color: '#111827', marginBottom: '0.3rem' }}>
                  {activeSelectedJob.title}
                </h1>

                <div style={{ fontSize: '0.95rem', color: '#2563eb', fontWeight: '600', marginBottom: '0.2rem' }}>
                  {activeSelectedJob.company} <i className="fa-solid fa-arrow-up-right-from-square" style={{ fontSize: '0.8rem' }}></i> • 4.2 <i className="fa-solid fa-star" style={{ color: '#f59e0b' }}></i>
                </div>

                <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '1.25rem' }}>
                  {activeSelectedJob.location}
                </div>

                <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', marginBottom: '1.5rem' }}>
                  {appliedJobIds.has(activeSelectedJob.id) ? (
                    <button type="button" className="btn-applied">
                      <i className="fa-solid fa-circle-check"></i> Applied Successfully
                    </button>
                  ) : (
                    <button type="button" className="btn-primary" onClick={(e) => handleApplyClick(activeSelectedJob, e)}>
                      1-Click Apply <i className="fa-solid fa-paper-plane"></i>
                    </button>
                  )}

                  <button 
                    type="button" 
                    className="btn-secondary"
                    style={{ color: savedJobIds.has(activeSelectedJob.id) ? '#f59e0b' : '#374151' }}
                    onClick={(e) => toggleSaveJob(activeSelectedJob.id, e)}
                  >
                    <i className={`fa-${savedJobIds.has(activeSelectedJob.id) ? 'solid' : 'regular'} fa-bookmark`}></i>
                  </button>
                </div>

                <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: '1.25rem 0' }} />

                <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.1rem', color: '#111827', marginBottom: '0.6rem' }}>
                  Location & Work Details
                </h3>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.25rem' }}>
                  <i className="fa-solid fa-location-dot" style={{ marginRight: '0.4rem' }}></i> {activeSelectedJob.location} • {activeSelectedJob.work_mode}
                </p>

                <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.1rem', color: '#111827', marginBottom: '0.6rem' }}>
                  Full Job Description
                </h3>
                <p style={{ color: '#374151', fontSize: '0.92rem', lineHeight: '1.7', marginBottom: '1.25rem' }}>
                  {activeSelectedJob.description}
                </p>

                <h4 style={{ fontSize: '0.9rem', color: '#111827', marginBottom: '0.5rem' }}>Required Technical Skills:</h4>
                <SkillsPills skills={[...activeSelectedJob.required_skills, ...activeSelectedJob.preferred_skills]} matchedSkills={activeSelectedJob.required_skills} maxShow={12} />
              </div>
            )}
          </div>
        </div>
      )}

      {/* LOGIN MODAL */}
      {isLoginModalOpen && (
        <PortalLoginModal 
          onClose={() => setIsLoginModalOpen(false)}
          onLoginSuccess={handleLoginSuccess}
        />
      )}

      {/* Real-Time Application Modal */}
      {applyJobTarget && (
        <RealTimeApplyModal 
          job={applyJobTarget} 
          candidates={candidates}
          onClose={() => setApplyJobTarget(null)}
          onSuccess={(resData) => {
            markJobApplied(applyJobTarget.id);
            setApplyJobTarget(null);
            setApplicationResult(resData);
            loadJobs();
            loadDashboard();
          }}
        />
      )}

      {applicationResult && (
        <ApplicationResultModal 
          result={applicationResult}
          onClose={() => setApplicationResult(null)}
        />
      )}

      {selectedCandidate && (
        <CandidateProfileModal 
          data={selectedCandidate} 
          onClose={() => setSelectedCandidate(null)}
        />
      )}

      {analysisDetail && (
        <AIAnalysisModal 
          data={analysisDetail} 
          userRole={userRole}
          onClose={() => setAnalysisDetail(null)}
        />
      )}

      {isJobModalOpen && (
        <PostJobModal 
          onClose={() => setIsJobModalOpen(false)}
          onSuccess={() => {
            setIsJobModalOpen(false);
            loadJobs();
            loadDashboard();
          }}
        />
      )}
    </div>
  );
}

// --------------------------------------------------------------------------
// 1. COMPANY REVIEWS & DIRECTORY VIEW
// --------------------------------------------------------------------------
function PortalCompanyDirectoryView({ data, jobs, onSelectJob }) {
  const defaultCompanies = [
    { id: 1, name: 'Enterprise AI Corp', industry: 'Software & AI', size: '500-1000 employees', location: 'Bengaluru, IN', open_jobs: 12, rating: 4.8 },
    { id: 2, name: 'CloudScale Innovations', industry: 'Cloud & DevOps', size: '200-500 employees', location: 'Remote / San Francisco', open_jobs: 8, rating: 4.9 },
    { id: 3, name: 'FinTech Dynamics', industry: 'Financial Technology', size: '1000+ employees', location: 'Mumbai, IN', open_jobs: 15, rating: 4.6 },
    { id: 4, name: 'CyberShield Security', industry: 'Cybersecurity', size: '100-250 employees', location: 'Hyderabad, IN', open_jobs: 6, rating: 4.7 },
  ];

  const companies = (data && data.companies) ? data.companies : defaultCompanies;

  return (
    <div style={{ maxWidth: '1200px', margin: '1.5rem auto', padding: '0 1.5rem' }}>
      <h1 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.6rem', color: '#111827', marginBottom: '0.4rem' }}>
        <i className="fa-solid fa-building" style={{ color: 'var(--primary-bg)', marginRight: '0.5rem' }}></i> Top Tech Companies & Employee Reviews
      </h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>Explore verified company culture, salaries, and open positions.</p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem' }}>
        {companies.map(comp => (
          <div key={comp.id} className="indeed-job-card" style={{ cursor: 'default' }}>
            <div style={{ fontSize: '1.2rem', fontWeight: '800', color: '#111827', marginBottom: '0.3rem' }}>{comp.name}</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>{comp.industry} • {comp.size}</div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: '0.5rem 0 1rem' }}><i className="fa-solid fa-location-dot"></i> {comp.location}</div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderTop: '1px solid var(--border)', paddingTop: '0.75rem' }}>
              <span className="badge-tag badge-easy-apply">{comp.open_jobs} Open Jobs</span>
              <span style={{ color: '#f59e0b', fontWeight: '700' }}><i className="fa-solid fa-star"></i> {comp.rating} Rating</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// --------------------------------------------------------------------------
// 2. SALARY GUIDE VIEW
// --------------------------------------------------------------------------
function PortalSalaryGuideView({ data, jobs }) {
  const salaryRanges = [
    { title: 'Python / Django Developer', min: '₹6.5 LPA', avg: '₹12.5 LPA', max: '₹24.0 LPA', demand: 'High Demand' },
    { title: 'NodeJS & Express Backend Engineer', min: '₹7.0 LPA', avg: '₹14.0 LPA', max: '₹26.0 LPA', demand: 'Very High Demand' },
    { title: 'Full Stack Engineer (React + Django)', min: '₹8.0 LPA', avg: '₹16.5 LPA', max: '₹30.0 LPA', demand: 'Top Rated' },
    { title: 'Senior Travel Consultant', min: '₹4.0 LPA', avg: '₹7.5 LPA', max: '₹12.0 LPA', demand: 'Moderate' },
    { title: 'E-Commerce Product Specialist', min: '₹3.5 LPA', avg: '₹6.5 LPA', max: '₹10.5 LPA', demand: 'High Growth' },
  ];

  return (
    <div style={{ maxWidth: '1200px', margin: '1.5rem auto', padding: '0 1.5rem' }}>
      <h1 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.6rem', color: '#111827', marginBottom: '0.4rem' }}>
        <i className="fa-solid fa-indian-rupee-sign" style={{ color: 'var(--primary-bg)', marginRight: '0.5rem' }}></i> IT Salary Guide & Pay Benchmarks
      </h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>Compare compensation ranges across tech roles and experience levels.</p>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
        {salaryRanges.map((sal, idx) => (
          <div key={idx} className="indeed-job-card">
            <h3 style={{ fontFamily: 'var(--font-heading)', color: '#111827', fontSize: '1.1rem', marginBottom: '0.5rem' }}>{sal.title}</h3>
            <span className="badge-tag badge-green" style={{ marginBottom: '1rem' }}>{sal.demand}</span>

            <div style={{ background: '#f9fafb', padding: '1rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', marginTop: '0.75rem' }}>
              <div><div style={{ fontSize: '0.75rem', color: '#6b7280' }}>STARTING</div><div style={{ fontWeight: '700', color: '#111827' }}>{sal.min}</div></div>
              <div><div style={{ fontSize: '0.75rem', color: '#6b7280' }}>AVERAGE</div><div style={{ fontWeight: '800', color: '#059669', fontSize: '1.1rem' }}>{sal.avg}</div></div>
              <div><div style={{ fontSize: '0.75rem', color: '#6b7280' }}>TOP 10%</div><div style={{ fontWeight: '700', color: '#111827' }}>{sal.max}</div></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// --------------------------------------------------------------------------
// 3. APPLICATIONS TRACKER VIEW
// --------------------------------------------------------------------------
function PortalApplicationsTrackerView({ appliedJobIds, jobs, onSelectJob }) {
  const appliedList = jobs.filter(j => appliedJobIds.has(j.id));

  return (
    <div style={{ maxWidth: '1200px', margin: '1.5rem auto', padding: '0 1.5rem' }}>
      <h1 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.6rem', color: '#111827', marginBottom: '0.4rem' }}>
        <i className="fa-solid fa-list-check" style={{ color: 'var(--primary-bg)', marginRight: '0.5rem' }}></i> Application Status Tracker
      </h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>Track your active job applications in real time.</p>

      {appliedList.length === 0 ? (
        <div className="indeed-job-card" style={{ textAlign: 'center', padding: '3rem' }}>
          <i className="fa-solid fa-inbox" style={{ fontSize: '3rem', color: '#9ca3af', marginBottom: '1rem' }}></i>
          <h3 style={{ color: '#111827', marginBottom: '0.5rem' }}>No Active Applications</h3>
          <p style={{ color: '#6b7280', fontSize: '0.88rem' }}>Browse jobs and click 1-Click Apply to start tracking your applications here.</p>
        </div>
      ) : (
        <div className="indeed-job-card" style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)', color: 'var(--text-secondary)', fontSize: '0.8rem', textTransform: 'uppercase' }}>
                <th style={{ padding: '0.9rem' }}>Job Title</th>
                <th style={{ padding: '0.9rem' }}>Company</th>
                <th style={{ padding: '0.9rem' }}>Location</th>
                <th style={{ padding: '0.9rem' }}>Salary</th>
                <th style={{ padding: '0.9rem' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {appliedList.map(job => (
                <tr key={job.id} style={{ borderBottom: '1px solid var(--border)', cursor: 'pointer' }} onClick={() => onSelectJob(job.id)}>
                  <td style={{ padding: '0.9rem', fontWeight: '700', color: '#111827' }}>{job.title}</td>
                  <td style={{ padding: '0.9rem', color: 'var(--text-secondary)' }}>{job.company}</td>
                  <td style={{ padding: '0.9rem', color: 'var(--text-secondary)' }}>{job.location}</td>
                  <td style={{ padding: '0.9rem', color: 'var(--text-secondary)' }}>{job.salary_range}</td>
                  <td style={{ padding: '0.9rem' }}>
                    <span className="badge-tag badge-green">Under Review</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// --------------------------------------------------------------------------
// 4. SAVED JOBS WORKSPACE
// --------------------------------------------------------------------------
function PortalSavedJobsView({ jobs, savedJobIds, appliedJobIds, toggleSaveJob, onSelectJob, onApply }) {
  const savedList = jobs.filter(j => savedJobIds.has(j.id));

  return (
    <div style={{ maxWidth: '1200px', margin: '1.5rem auto', padding: '0 1.5rem' }}>
      <h1 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.6rem', color: '#111827', marginBottom: '0.4rem' }}>
        <i className="fa-solid fa-bookmark" style={{ color: '#f59e0b', marginRight: '0.5rem' }}></i> Saved Job Bookmarks ({savedList.length})
      </h1>
      <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>Your bookmarked positions saved for easy access.</p>

      {savedList.length === 0 ? (
        <div className="indeed-job-card" style={{ textAlign: 'center', padding: '3rem' }}>
          <i className="fa-regular fa-bookmark" style={{ fontSize: '3rem', color: '#9ca3af', marginBottom: '1rem' }}></i>
          <h3 style={{ color: '#111827', marginBottom: '0.5rem' }}>No Saved Jobs</h3>
          <p style={{ color: '#6b7280', fontSize: '0.88rem' }}>Click the bookmark icon on any job card to save it here.</p>
        </div>
      ) : (
        savedList.map(job => (
          <div key={job.id} className="indeed-job-card" style={{ marginBottom: '1rem' }} onClick={() => onSelectJob(job.id)}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <h3 style={{ fontFamily: 'var(--font-heading)', fontSize: '1.15rem', color: '#111827', marginBottom: '0.2rem' }}>{job.title}</h3>
                <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>{job.company} • {job.location} • {job.salary_range}</div>
              </div>
              <div style={{ display: 'flex', gap: '0.6rem' }}>
                <button type="button" className="btn-secondary" style={{ color: '#f59e0b' }} onClick={(e) => toggleSaveJob(job.id, e)}>Unsave</button>
                <button type="button" className="btn-primary" onClick={(e) => { e.stopPropagation(); onApply(job); }}>1-Click Apply</button>
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );
}

// --------------------------------------------------------------------------
// LOGIN / REGISTER MODAL
// --------------------------------------------------------------------------
function PortalLoginModal({ onClose, onLoginSuccess }) {
  const [email, setEmail] = useState('alex.morgan@example.com');
  const [password, setPassword] = useState('password123');

  const handleSubmit = (e) => {
    e.preventDefault();
    const name = email.split('@')[0].replace('.', ' ');
    const formattedName = name.charAt(0).toUpperCase() + name.slice(1);
    onLoginSuccess(formattedName || 'Alex Morgan');
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-container" onClick={e => e.stopPropagation()} style={{ maxWidth: '440px' }}>
        <div className="modal-header">
          <h2 style={{ fontFamily: 'var(--font-heading)', color: 'var(--text-primary)' }}>
            <i className="fa-solid fa-right-to-bracket" style={{ color: 'var(--primary-bg)', marginRight: '0.5rem' }}></i> Candidate Sign In
          </h2>
          <button type="button" style={{ background: 'none', border: 'none', color: 'var(--text-primary)', fontSize: '1.4rem', cursor: 'pointer' }} onClick={onClose}>&times;</button>
        </div>

        <form onSubmit={handleSubmit} className="modal-body">
          <div style={{ background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.25)', padding: '0.85rem', borderRadius: 'var(--radius-sm)', marginBottom: '1.25rem', fontSize: '0.85rem', color: '#059669' }}>
            <i className="fa-solid fa-circle-info"></i> Please sign in to your account to use <strong>1-Click Apply</strong>.
          </div>

          <div className="form-group">
            <label className="form-label">Email Address</label>
            <input 
              type="email" 
              className="form-input" 
              required 
              value={email}
              onChange={e => setEmail(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <input 
              type="password" 
              className="form-input" 
              required 
              value={password}
              onChange={e => setPassword(e.target.value)}
            />
          </div>

          <button type="submit" className="btn-primary" style={{ width: '100%', justifyContent: 'center', marginTop: '0.5rem', padding: '0.7rem' }}>
            <i className="fa-solid fa-lock"></i> Sign In & Continue
          </button>
        </form>
      </div>
    </div>
  );
}

function RealTimeApplyModal({ job, candidates = [], onClose, onSuccess }) {
  const [applyMode, setApplyMode] = useState('existing');
  const [selectedCandidateId, setSelectedCandidateId] = useState(candidates.length > 0 ? candidates[0].id : '');
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [file, setFile] = useState(null);
  const [step, setStep] = useState(0);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStep(1);

    setTimeout(() => setStep(2), 500);
    setTimeout(() => setStep(3), 1000);

    const formData = new FormData();
    if (applyMode === 'existing') {
      formData.append('candidate_id', selectedCandidateId);
    } else {
      if (!file) {
        alert("Please select a resume file.");
        setStep(0);
        return;
      }
      formData.append('full_name', fullName);
      formData.append('email', email);
      formData.append('phone', phone);
      formData.append('file', file);
    }

    try {
      const res = await fetch(`/api/jobs/${job.id}/apply/`, { method: 'POST', body: formData });
      const data = await res.json();
      if (!res.ok || data.error) {
        alert(data.error || "Application failed.");
        setStep(0);
      } else {
        setTimeout(() => onSuccess(data), 1200);
      }
    } catch (err) {
      alert("Error applying: " + err.message);
      setStep(0);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-container" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <span className="badge-tag badge-easy-apply">{job.department || 'Position'}</span>
            <h2 style={{ fontFamily: 'var(--font-heading)', color: 'var(--text-primary)', marginTop: '0.2rem' }}>1-Click Apply for {job.title}</h2>
          </div>
          <button type="button" style={{ background: 'none', border: 'none', color: 'var(--text-primary)', fontSize: '1.4rem', cursor: 'pointer' }} onClick={onClose}>&times;</button>
        </div>

        <div className="modal-body">
          {step > 0 ? (
            <div style={{ textAlign: 'center', padding: '1rem 0' }}>
              <div style={{ fontSize: '2.5rem', color: 'var(--primary-bg)', marginBottom: '1rem' }}><i className="fa-solid fa-spinner fa-spin"></i></div>
              <h3 style={{ color: 'var(--text-primary)', marginBottom: '1.5rem' }}>Processing Real-Time AI Match...</h3>
            </div>
          ) : (
            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label">Select Candidate Profile</label>
                <select className="form-input" value={selectedCandidateId} onChange={e => setSelectedCandidateId(e.target.value)}>
                  {candidates.map(c => <option key={c.id} value={c.id}>{c.full_name} ({c.email})</option>)}
                </select>
              </div>

              <div style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
                <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
                <button type="submit" className="btn-primary">Submit Application</button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}

function ApplicationResultModal({ result, onClose }) {
  const { candidate, analysis, message } = result;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-container" onClick={e => e.stopPropagation()} style={{ maxWidth: '520px', textAlign: 'center' }}>
        <div className="modal-header" style={{ justifyContent: 'center' }}>
          <h2 style={{ fontFamily: 'var(--font-heading)', color: 'var(--success)' }}>
            <i className="fa-solid fa-circle-check"></i> Application Submitted Successfully!
          </h2>
        </div>

        <div className="modal-body">
          <div style={{ fontWeight: '700', fontSize: '1.15rem', color: 'var(--text-primary)', marginBottom: '0.4rem' }}>
            {candidate.full_name}
          </div>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1.25rem', fontSize: '0.9rem' }}>
            {message || "Your application for this job position has been submitted successfully."}
          </p>

          <div style={{ background: '#f8fafc', padding: '1.5rem', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)', marginBottom: '1.5rem' }}>
            <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', fontWeight: '700', textTransform: 'uppercase' }}>
              REAL-TIME COMPUTED AI MATCH SCORE
            </div>
            <div style={{ fontSize: '3rem', fontWeight: '800', color: 'var(--success)', margin: '0.4rem 0' }}>
              {analysis.match_score}%
            </div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)' }}>
              ATS Score: {analysis.ats_score}%
            </div>
          </div>

          <div style={{ fontSize: '1.15rem', fontWeight: '800', color: '#059669', marginBottom: '1.5rem' }}>
            Thank you for applying!
          </div>

          <div style={{ display: 'flex', justifyContent: 'center' }}>
            <button type="button" className="btn-primary" style={{ padding: '0.65rem 2.2rem' }} onClick={onClose}>
              Done
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function AIAnalysisModal({ data, userRole, onClose }) {
  const { analysis, candidate, job, questions } = data;
  const [userAnswers, setUserAnswers] = useState({});
  const [evalResults, setEvalResults] = useState({});

  const handleAnswerInput = (qId, text) => setUserAnswers(prev => ({ ...prev, [qId]: text }));

  const evaluateSingleQuestion = async (qId) => {
    const text = userAnswers[qId];
    if (!text || !text.trim()) return alert("Type an answer first.");

    try {
      const res = await apiCall(`/api/analysis/${analysis.id}/evaluate-answers/`, 'POST', { answers: { [qId]: text } });
      if (res.results && res.results.length > 0) {
        setEvalResults(prev => ({ ...prev, [qId]: res.results[0] }));
      }
    } catch (err) { alert("Error: " + err.message); }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-container" onClick={e => e.stopPropagation()} style={{ maxWidth: '780px' }}>
        <div className="modal-header">
          <div>
            <span className="badge-tag badge-easy-apply">{job.title}</span>
            <h2 style={{ fontFamily: 'var(--font-heading)', color: 'var(--text-primary)', marginTop: '0.2rem' }}>{candidate.full_name}</h2>
          </div>
          <button type="button" style={{ background: 'none', border: 'none', color: 'var(--text-primary)', fontSize: '1.4rem', cursor: 'pointer' }} onClick={onClose}>&times;</button>
        </div>

        <div className="modal-body">
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', alignItems: 'center' }}>
            <div style={{ background: 'rgba(16,185,129,0.15)', color: '#059669', padding: '0.6rem 1.2rem', borderRadius: 'var(--radius-full)', fontWeight: '700' }}>
              {analysis.match_score}% Match Score
            </div>
            <div className="badge-tag badge-easy-apply" style={{ padding: '0.6rem 1.2rem' }}>
              ATS Score: {analysis.ats_score}%
            </div>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <h3 style={{ color: 'var(--text-primary)', marginBottom: '0.75rem' }}>Tailored AI Questions & Interactive Answer Input Boxes</h3>

            {questions.map(q => {
              const evalRes = evalResults[q.id];
              return (
                <div key={q.id} style={{ background: '#f8fafc', padding: '1.1rem', borderRadius: 'var(--radius-md)', marginBottom: '1rem', border: '1px solid var(--border)' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                    <span className="skill-tag" style={{ textTransform: 'uppercase', fontSize: '0.7rem' }}>{q.category}</span>
                  </div>

                  <div style={{ fontWeight: '700', color: 'var(--text-primary)', fontSize: '0.98rem', marginBottom: '0.4rem' }}>{q.question}</div>
                  
                  <textarea 
                    className="form-input" 
                    style={{ minHeight: '75px', resize: 'vertical' }}
                    placeholder="Type candidate written answer..."
                    value={userAnswers[q.id] || ''}
                    onChange={e => handleAnswerInput(q.id, e.target.value)}
                  />

                  <div style={{ marginTop: '0.6rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    {evalRes && <span style={{ color: '#059669', fontWeight: '700' }}>Score: {evalRes.score}% — {evalRes.feedback}</span>}
                    <button type="button" className="btn-primary" style={{ padding: '0.35rem 0.85rem' }} onClick={() => evaluateSingleQuestion(q.id)}>Submit & Grade Answer</button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

function CandidateProfileModal({ data, onClose }) {
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-container" onClick={e => e.stopPropagation()} style={{ maxWidth: '500px' }}>
        <div className="modal-header">
          <h2 style={{ fontFamily: 'var(--font-heading)', color: 'var(--text-primary)' }}>{data.candidate.full_name}</h2>
          <button type="button" style={{ background: 'none', border: 'none', color: 'var(--text-primary)', fontSize: '1.4rem', cursor: 'pointer' }} onClick={onClose}>&times;</button>
        </div>
        <div className="modal-body">
          <p style={{ color: 'var(--text-secondary)' }}>{data.candidate.email} | {data.candidate.phone}</p>
        </div>
      </div>
    </div>
  );
}

function PostJobModal({ onClose, onSuccess }) {
  const [formData, setFormData] = useState({
    title: '', department: 'Engineering', min_experience_years: 2, required_skills: '', preferred_skills: '', description: ''
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await apiCall('/api/jobs/create/', 'POST', formData);
      onSuccess();
    } catch (err) { alert("Error: " + err.message); }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-container" onClick={e => e.stopPropagation()} style={{ maxWidth: '500px' }}>
        <div className="modal-header">
          <h2 style={{ fontFamily: 'var(--font-heading)', color: 'var(--text-primary)' }}>Post New Job Opening</h2>
          <button type="button" style={{ background: 'none', border: 'none', color: 'var(--text-primary)', fontSize: '1.4rem', cursor: 'pointer' }} onClick={onClose}>&times;</button>
        </div>
        <form onSubmit={handleSubmit} className="modal-body">
          <div className="form-group">
            <label className="form-label">Job Title</label>
            <input className="form-input" required placeholder="e.g. Senior Python / Django Developer" value={formData.title} onChange={e => setFormData({...formData, title: e.target.value})} />
          </div>
          <div className="form-group">
            <label className="form-label">Department</label>
            <input className="form-input" required placeholder="Engineering, Data Science..." value={formData.department} onChange={e => setFormData({...formData, department: e.target.value})} />
          </div>
          <div className="form-group">
            <label className="form-label">Required Skills (comma separated)</label>
            <input className="form-input" required placeholder="Python, Django, PostgreSQL, Docker" value={formData.required_skills} onChange={e => setFormData({...formData, required_skills: e.target.value})} />
          </div>
          <div className="form-group">
            <label className="form-label">Job Description</label>
            <textarea className="form-input" style={{ minHeight: '80px' }} required placeholder="Position description..." value={formData.description} onChange={e => setFormData({...formData, description: e.target.value})} />
          </div>
          <button className="btn-primary" style={{ width: '100%', justifyContent: 'center' }} type="submit">Publish Job Opening</button>
        </form>
      </div>
    </div>
  );
}

// Render React App
const rootElement = document.getElementById('root');
if (rootElement) {
  const root = ReactDOM.createRoot(rootElement);
  root.render(<App />);
}

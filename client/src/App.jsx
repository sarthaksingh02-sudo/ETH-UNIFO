import React, { useState, useEffect, useRef } from 'react';
import GdGoenkaOfficialLogo from './components/GdGoenkaOfficialLogo.jsx';
import {
  IconUsers,
  IconInstitution,
  IconTerminal,
  IconChart,
  IconPlus,
  IconTray,
  IconDownload,
  IconSearch,
  IconArrowUpRight,
  IconCheck,
  IconAlert,
  IconPlay,
  IconClose
} from './components/AppleIcons.jsx';

export default function App() {
  const [activeTab, setActiveTab] = useState('roster'); // 'roster', 'pipeline', 'explorer'
  const [faculty, setFaculty] = useState([]);
  const [loadingFaculty, setLoadingFaculty] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Single and Bulk Add States
  const [singleName, setSingleName] = useState('');
  const [bulkNames, setBulkNames] = useState('');
  const [isBulkOpen, setIsBulkOpen] = useState(false);
  
  // Pipeline States
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [logs, setLogs] = useState([]);
  const [institution, setInstitution] = useState('GD Goenka University');
  const [delay, setDelay] = useState(0.5);
  const consoleEndRef = useRef(null);
  
  // Publications Explorer States
  const [publications, setPublications] = useState([]);
  const [loadingPubs, setLoadingPubs] = useState(false);
  const [pubFilter, setPubFilter] = useState('');
  const [quartileFilter, setQuartileFilter] = useState('ALL');

  // Toast Notification
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3800);
  };

  // Fetch Faculty List
  const fetchFaculty = async () => {
    setLoadingFaculty(true);
    try {
      const res = await fetch('/api/faculty');
      const data = await res.json();
      setFaculty(data.faculty || []);
    } catch (err) {
      showToast('Error loading faculty roster', 'error');
    } finally {
      setLoadingFaculty(false);
    }
  };

  // Fetch Publications Preview
  const fetchPublications = async () => {
    setLoadingPubs(true);
    try {
      const res = await fetch('/api/publications-preview');
      const data = await res.json();
      setPublications(data.records || []);
    } catch (err) {
      // Ignored if output not generated yet
    } finally {
      setLoadingPubs(false);
    }
  };

  useEffect(() => {
    fetchFaculty();
    fetchPublications();
    // System Engineer Hidden Signature
    console.log(
      "%c GD GOENKA UNIVERSITY %c Vidwan Research Intelligence %c Sarthak Singh- 3096-2023-27 ",
      "background: #0B2545; color: #E0C068; font-weight: bold; padding: 4px 8px; border-radius: 4px 0 0 4px;",
      "background: #133E7C; color: #FFFFFF; font-weight: bold; padding: 4px 8px;",
      "background: #07152B; color: #94A3B8; padding: 4px 8px; border-radius: 0 4px 4px 0;"
    );
  }, []);

  useEffect(() => {
    if (consoleEndRef.current) {
      consoleEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  // Add Single Faculty
  const handleAddSingle = async (e) => {
    e?.preventDefault();
    const name = singleName.trim();
    if (!name) return;
    try {
      const res = await fetch('/api/faculty/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ names: [name] })
      });
      const data = await res.json();
      if (data.success) {
        setSingleName('');
        showToast(`Added ${name} to roster`);
        fetchFaculty();
      } else {
        showToast(data.message || 'Faculty already on file', 'error');
      }
    } catch (err) {
      showToast('Failed to add faculty member', 'error');
    }
  };

  // Add Bulk Faculty
  const handleAddBulk = async () => {
    const raw = bulkNames.trim();
    if (!raw) return;
    const names = raw
      .replace(/,/g, '\n')
      .split('\n')
      .map(s => s.trim())
      .filter(s => s.length > 0);
    if (!names.length) return;

    try {
      const res = await fetch('/api/faculty/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ names })
      });
      const data = await res.json();
      if (data.success) {
        setBulkNames('');
        setIsBulkOpen(false);
        showToast(`Successfully added ${data.added_count} faculty members`);
        fetchFaculty();
      }
    } catch (err) {
      showToast('Failed to ingest faculty roster', 'error');
    }
  };

  // Delete Faculty
  const handleDeleteFaculty = async (name) => {
    try {
      const res = await fetch('/api/faculty/delete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name })
      });
      const data = await res.json();
      if (data.success) {
        showToast(`Removed ${name} from roster`);
        fetchFaculty();
      }
    } catch (err) {
      showToast('Failed to delete faculty member', 'error');
    }
  };

  // Clear All
  const handleClearAll = async () => {
    if (!window.confirm('Are you sure you want to clear all registered faculty?')) return;
    try {
      const res = await fetch('/api/faculty/clear', { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        showToast('Cleared all faculty roster entries');
        fetchFaculty();
      }
    } catch (err) {
      showToast('Error clearing roster', 'error');
    }
  };

  // Clear Publications
  const handleClearPublications = async () => {
    if (!window.confirm('Are you sure you want to clear all publication data and generated reports? This will reset the publication records.')) return;
    try {
      const res = await fetch('/api/publications/clear', { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        setPublications([]);
        showToast('Cleared all publication data and reports');
        fetchPublications();
      } else {
        showToast(data.message || 'Failed to clear publications', 'error');
      }
    } catch (err) {
      showToast('Error clearing publication records', 'error');
    }
  };

  // Launch Pipeline
  const handleRunPipeline = async () => {
    setPipelineRunning(true);
    setLogs(['[System] Initializing Vidwan extraction pipeline...']);
    setActiveTab('pipeline');

    try {
      const res = await fetch('/api/run-pipeline', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ institution, delay })
      });
      const data = await res.json();

      if (!data.success) {
        showToast(data.message, 'error');
        setPipelineRunning(false);
        return;
      }

      // Listen to SSE
      const eventSource = new EventSource('/api/pipeline-logs');
      eventSource.onmessage = (event) => {
        if (event.data === '[[PIPELINE_COMPLETE]]') {
          eventSource.close();
          setPipelineRunning(false);
          setLogs(prev => [
            ...prev,
            '',
            '==================================================',
            'SUCCESS: Pipeline execution complete. Output workbook compiled with native OpenXML hyperlinks.',
            '=================================================='
          ]);
          showToast('Extraction pipeline completed successfully!');
          fetchPublications();
        } else {
          setLogs(prev => [...prev, event.data]);
        }
      };

      eventSource.onerror = () => {
        eventSource.close();
        setPipelineRunning(false);
      };
    } catch (err) {
      showToast('Failed to execute extraction engine', 'error');
      setPipelineRunning(false);
    }
  };

  // Filtered faculty list
  const filteredFaculty = faculty.filter(f => f.toLowerCase().includes(searchQuery.toLowerCase().trim()));

  // Filtered publications
  const filteredPubs = publications.filter(p => {
    const qMatch = quartileFilter === 'ALL' || (p.Scopus_Quartile || 'None').toUpperCase() === quartileFilter;
    const sMatch = !pubFilter.trim() || 
      (p.Article_Title || '').toLowerCase().includes(pubFilter.toLowerCase()) ||
      (p.Journal_Name || '').toLowerCase().includes(pubFilter.toLowerCase()) ||
      (p.Faculty_Name || '').toLowerCase().includes(pubFilter.toLowerCase());
    return qMatch && sMatch;
  });

  const q1Count = publications.filter(p => (p.Scopus_Quartile || '').toUpperCase() === 'Q1').length;
  const totalCites = publications.reduce((acc, p) => acc + (typeof p.Article_Citations === 'number' ? p.Article_Citations : 0), 0);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      
      {/* Apple VisionOS Toast Notification */}
      {toast && (
        <div style={{
          position: 'fixed',
          top: '28px',
          right: '28px',
          zIndex: 1000,
          background: 'rgba(10, 28, 56, 0.88)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          color: '#FFFFFF',
          padding: '14px 24px',
          borderRadius: 'var(--radius-xl)',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.5), inset 0 1px 1px rgba(255, 255, 255, 0.25)',
          fontSize: '0.88rem',
          fontWeight: 600,
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          border: '1px solid rgba(255, 255, 255, 0.2)',
          animation: 'applePulse 0.3s ease-out'
        }}>
          <span style={{ color: toast.type === 'error' ? '#F87171' : '#34D399' }}>
            {toast.type === 'error' ? <IconAlert size={20} /> : <IconCheck size={20} />}
          </span>
          <span>{toast.message}</span>
        </div>
      )}

      {/* ==========================================================================
          MAJESTIC CENTERED APPLE HERO BANNER (Dim Enlarge & Centered Official Logo)
          ========================================================================== */}
      <section style={{
        position: 'relative',
        padding: '54px 24px 38px 24px',
        textAlign: 'center',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        background: 'radial-gradient(ellipse at 50% 10%, rgba(21, 58, 123, 0.6) 0%, rgba(7, 21, 43, 0.95) 75%)',
        overflow: 'hidden'
      }}>
        {/* Ambient Halo Glow */}
        <div style={{
          position: 'absolute',
          top: '-40px',
          left: '50%',
          transform: 'translateX(-50%)',
          width: '540px',
          height: '240px',
          background: 'radial-gradient(circle, rgba(197, 168, 92, 0.22) 0%, rgba(59, 130, 246, 0.15) 50%, transparent 75%)',
          pointerEvents: 'none',
          filter: 'blur(36px)',
          zIndex: 0
        }} className="ambient-halo" />

        <div style={{ position: 'relative', zIndex: 1, maxWidth: '1100px', margin: '0 auto' }}>
          
          {/* Top Overline Pill */}
          <div style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', padding: '5px 16px', borderRadius: 'var(--radius-full)', background: 'rgba(255, 255, 255, 0.08)', border: '1px solid rgba(255, 255, 255, 0.18)', backdropFilter: 'blur(16px)', WebkitBackdropFilter: 'blur(16px)', marginBottom: '22px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--accent-gold)' }}></span>
            <span style={{ fontSize: '0.74rem', fontWeight: 700, letterSpacing: 'var(--tracking-wide)', color: '#FFFFFF', textTransform: 'uppercase' }}>
              RESEARCH &amp; PUBLICATION INTELLIGENCE SYSTEM
            </span>
          </div>

          {/* Centered Enlarged Official Logo Lockup */}
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', marginBottom: '20px' }}>
            <div style={{
              background: 'rgba(255, 255, 255, 0.08)',
              padding: '12px 32px',
              borderRadius: '20px',
              border: '1px solid rgba(255, 255, 255, 0.22)',
              backdropFilter: 'blur(28px)',
              WebkitBackdropFilter: 'blur(28px)',
              boxShadow: 'inset 0 1px 1px rgba(255, 255, 255, 0.3), 0 16px 36px rgba(0, 0, 0, 0.45)',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              {/* Official Vector Logo with Golden Falcon, Typography, and NAAC A+ Seal */}
              <GdGoenkaOfficialLogo height={52} onDark={true} />
            </div>
          </div>

          {/* Subtitle Information */}
          <p style={{ fontSize: '0.94rem', color: 'var(--text-secondary)', maxWidth: '680px', margin: '0 auto 28px auto', lineHeight: 1.6 }}>
            Comprehensive academic metadata harvesting, Scopus Quartiles (Q1–Q4) classification, and citation bibliometrics powered by INFLIBNET Vidwan, OpenAlex &amp; Crossref.
          </p>

          {/* Centered Apple Segmented Navigation Capsule */}
          <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
            <div className="apple-glass-segmented">
              <button 
                className={`apple-glass-segment-btn ${activeTab === 'roster' ? 'active' : ''}`}
                onClick={() => setActiveTab('roster')}
              >
                <IconUsers size={17} /> Faculty Roster ({faculty.length})
              </button>
              <button 
                className={`apple-glass-segment-btn ${activeTab === 'pipeline' ? 'active' : ''}`}
                onClick={() => setActiveTab('pipeline')}
              >
                <IconTerminal size={17} /> Extraction Hub {pipelineRunning && <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#60A5FA', display: 'inline-block' }} className="pulse-indicator"></span>}
              </button>
              <button 
                className={`apple-glass-segment-btn ${activeTab === 'explorer' ? 'active' : ''}`}
                onClick={() => setActiveTab('explorer')}
              >
                <IconChart size={17} /> Publications ({publications.length})
              </button>
            </div>

            {/* Direct Workbook Downloads */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <a href="/api/download-input" className="btn-apple-glass" title="Download faculty_input.xlsx">
                <IconTray size={15} /> Input XLSX
              </a>
              <a href="/api/download-output" className="btn-apple-white" title="Download faculty_publications_output.xlsx">
                <IconDownload size={15} /> Output Report
              </a>
            </div>
          </div>

        </div>
      </section>

      {/* ==========================================================================
          MAIN CONTENT AREA (PURE WHITE GLASSMORPHISM OVER NAVY BLUE)
          ========================================================================== */}
      <main style={{ maxWidth: '1240px', margin: '0 auto', width: '100%', padding: '38px 24px 60px 24px', flex: 1 }}>

        {/* TAB 1: FACULTY ROSTER */}
        {activeTab === 'roster' && (
          <div>
            {/* Top Metric Strip */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', marginBottom: '32px' }}>
              
              <div className="apple-glass-card" style={{ padding: '24px 28px', display: 'flex', alignItems: 'center', gap: '18px' }}>
                <div style={{ width: '48px', height: '48px', borderRadius: 'var(--radius-xl)', background: 'rgba(255, 255, 255, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#FFFFFF', border: '1px solid rgba(255, 255, 255, 0.2)' }}>
                  <IconUsers size={24} />
                </div>
                <div>
                  <div style={{ fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: 'var(--tracking-wide)' }}>Faculty Roster</div>
                  <div style={{ fontSize: '1.65rem', fontWeight: 800, color: '#FFFFFF', letterSpacing: 'var(--tracking-tight)' }}>{faculty.length} Registered</div>
                </div>
              </div>

              <div className="apple-glass-card" style={{ padding: '24px 28px', display: 'flex', alignItems: 'center', gap: '18px' }}>
                <div style={{ width: '48px', height: '48px', borderRadius: 'var(--radius-xl)', background: 'rgba(197, 168, 92, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent-gold-light)', border: '1px solid rgba(197, 168, 92, 0.3)' }}>
                  <IconInstitution size={24} />
                </div>
                <div>
                  <div style={{ fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: 'var(--tracking-wide)' }}>Affiliation Target</div>
                  <div style={{ fontSize: '1.2rem', fontWeight: 800, color: '#FFFFFF', letterSpacing: 'var(--tracking-tight)' }}>GD Goenka University</div>
                </div>
              </div>

              <div className="apple-glass-card" style={{ padding: '24px 28px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: 'var(--tracking-wide)' }}>Automated Pipeline</div>
                  <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Ready for batch execution</div>
                </div>
                <button className="btn-apple-white" style={{ padding: '9px 20px', fontSize: '0.85rem' }} onClick={() => setActiveTab('pipeline')}>
                  Launch Hub <IconArrowUpRight size={14} />
                </button>
              </div>

            </div>

            {/* Split Grid: Management Forms (Left) vs Table (Right) */}
            <div style={{ display: 'grid', gridTemplateColumns: '380px 1fr', gap: '28px', alignItems: 'start' }}>
              
              {/* Left Column */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                
                {/* Single Add Card */}
                <div className="apple-glass-card" style={{ padding: '28px' }}>
                  <h3 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#FFFFFF', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '10px', letterSpacing: 'var(--tracking-tight)' }}>
                    <IconPlus size={20} color="var(--accent-blue-hover)" /> Add Faculty Member
                  </h3>

                  <form onSubmit={handleAddSingle}>
                    <div style={{ marginBottom: '16px' }}>
                      <input 
                        type="text" 
                        value={singleName}
                        onChange={(e) => setSingleName(e.target.value)}
                        placeholder="e.g. Faculty Member Name"
                        className="apple-glass-input"
                        style={{ width: '100%' }}
                      />
                    </div>
                    <button type="submit" className="btn-apple-white" style={{ width: '100%' }}>
                      <IconPlus size={16} /> Add to Roster
                    </button>
                  </form>
                </div>

                {/* Bulk Paste Card */}
                <div className="apple-glass-card" style={{ padding: '28px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }} onClick={() => setIsBulkOpen(!isBulkOpen)}>
                    <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#FFFFFF', display: 'flex', alignItems: 'center', gap: '10px', letterSpacing: 'var(--tracking-tight)' }}>
                      <IconTray size={19} color="var(--accent-gold-light)" /> Bulk Ingest Roster
                    </h3>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{isBulkOpen ? '▲' : '▼'}</span>
                  </div>

                  {isBulkOpen && (
                    <div style={{ marginTop: '18px' }}>
                      <p style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: '12px' }}>
                        Paste multiple faculty names separated by newlines or commas:
                      </p>
                      <textarea
                        rows={6}
                        value={bulkNames}
                        onChange={(e) => setBulkNames(e.target.value)}
                        placeholder={"Faculty Member 1\nFaculty Member 2\nFaculty Member 3"}
                        className="apple-glass-input"
                        style={{ width: '100%', borderRadius: 'var(--radius-md)', resize: 'vertical', marginBottom: '16px' }}
                      />
                      <button className="btn-apple-glass" style={{ width: '100%' }} onClick={handleAddBulk}>
                        <IconTray size={16} /> Add All to Excel
                      </button>
                    </div>
                  )}
                </div>

              </div>

              {/* Right Column: Faculty Table */}
              <div className="apple-glass-card" style={{ padding: '28px 32px' }}>
                
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px', flexWrap: 'wrap', gap: '14px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <h2 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#FFFFFF', letterSpacing: 'var(--tracking-tight)' }}>
                      Registered Faculty Roster
                    </h2>
                    <span style={{ background: 'rgba(255, 255, 255, 0.12)', color: '#FFFFFF', padding: '2px 12px', borderRadius: 'var(--radius-full)', fontSize: '0.82rem', fontWeight: 700, border: '1px solid rgba(255, 255, 255, 0.2)' }}>
                      {filteredFaculty.length}
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{ position: 'relative' }}>
                      <input 
                        type="text" 
                        placeholder="Search faculty..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="apple-glass-input"
                        style={{ padding: '7px 16px 7px 34px', borderRadius: 'var(--radius-full)', fontSize: '0.84rem', width: '220px' }}
                      />
                      <div style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }}>
                        <IconSearch size={14} />
                      </div>
                    </div>
                    {faculty.length > 0 && (
                      <button className="btn-apple-glass" style={{ color: '#F87171', borderColor: 'rgba(239, 68, 68, 0.3)' }} onClick={handleClearAll}>
                        Clear All
                      </button>
                    )}
                  </div>
                </div>

                {/* Table */}
                <div style={{ overflowX: 'auto', border: '1px solid rgba(255, 255, 255, 0.12)', borderRadius: 'var(--radius-xl)' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem' }}>
                    <thead>
                      <tr style={{ background: 'rgba(255, 255, 255, 0.05)', borderBottom: '1px solid rgba(255, 255, 255, 0.12)' }}>
                        <th style={{ padding: '14px 18px', textAlign: 'center', width: '50px', color: 'var(--text-secondary)', fontWeight: 600 }}>#</th>
                        <th style={{ padding: '14px 18px', textAlign: 'left', color: 'var(--text-secondary)', fontWeight: 600 }}>Faculty Name</th>
                        <th style={{ padding: '14px 18px', textAlign: 'center', width: '180px', color: 'var(--text-secondary)', fontWeight: 600 }}>Vidwan Verification</th>
                        <th style={{ padding: '14px 18px', textAlign: 'center', width: '80px', color: 'var(--text-secondary)', fontWeight: 600 }}>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredFaculty.length === 0 ? (
                        <tr>
                          <td colSpan={4} style={{ padding: '48px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                            {faculty.length === 0 ? 'No faculty members on file. Add names using the form on the left!' : 'No faculty matching your query.'}
                          </td>
                        </tr>
                      ) : (
                        filteredFaculty.map((name, idx) => (
                          <tr key={name} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.06)', transition: 'var(--transition-apple)' }} onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)'} onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}>
                            <td style={{ padding: '15px 18px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.82rem' }}>{idx + 1}</td>
                            <td style={{ padding: '15px 18px', fontWeight: 600, color: '#FFFFFF' }}>
                              {name}
                            </td>
                            <td style={{ padding: '15px 18px', textAlign: 'center' }}>
                              <a 
                                href={`https://vidwan.inflibnet.ac.in/profiles/init-filters?q=${encodeURIComponent(name + ' GD Goenka University')}`} 
                                target="_blank" 
                                rel="noreferrer"
                                style={{ color: 'var(--accent-blue-hover)', textDecoration: 'none', fontSize: '0.82rem', fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                              >
                                View Profile <IconArrowUpRight size={13} />
                              </a>
                            </td>
                            <td style={{ padding: '15px 18px', textAlign: 'center' }}>
                              <button 
                                onClick={() => handleDeleteFaculty(name)}
                                style={{ background: 'transparent', border: 'none', color: '#94A8C8', cursor: 'pointer', padding: '6px', borderRadius: '4px', transition: 'var(--transition-apple)' }}
                                onMouseEnter={(e) => e.currentTarget.style.color = '#F87171'}
                                onMouseLeave={(e) => e.currentTarget.style.color = '#94A8C8'}
                                title={`Delete ${name}`}
                              >
                                <IconClose size={15} />
                              </button>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

            </div>
          </div>
        )}

        {/* TAB 2: EXTRACTION HUB */}
        {activeTab === 'pipeline' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
            
            {/* Control Panel Card */}
            <div className="apple-glass-card" style={{ padding: '32px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '20px' }}>
                <div>
                  <h2 style={{ fontSize: '1.35rem', fontWeight: 800, color: '#FFFFFF', marginBottom: '8px', letterSpacing: 'var(--tracking-tight)' }}>
                    Vidwan Publication &amp; Metrics Pipeline
                  </h2>
                  <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)' }}>
                    Scrapes Vidwan profiles, retrieves DOIs, enriches via OpenAlex &amp; Crossref APIs, and compiles native OpenXML clickable reports.
                  </p>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                  <button 
                    className="btn-apple-white"
                    style={{ padding: '12px 28px', fontSize: '0.94rem' }}
                    onClick={handleRunPipeline}
                    disabled={pipelineRunning}
                  >
                    {pipelineRunning ? 'Extracting Metadata...' : <><IconPlay size={16} /> Launch Extraction Pipeline</>}
                  </button>
                </div>
              </div>

              {/* Settings Bar */}
              <div style={{ marginTop: '24px', paddingTop: '20px', borderTop: '1px solid rgba(255, 255, 255, 0.1)', display: 'flex', alignItems: 'center', gap: '28px', flexWrap: 'wrap', fontSize: '0.86rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>University Filter:</span>
                  <input 
                    type="text" 
                    value={institution} 
                    onChange={(e) => setInstitution(e.target.value)}
                    disabled={pipelineRunning}
                    className="apple-glass-input"
                    style={{ padding: '6px 14px', fontSize: '0.84rem' }}
                  />
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <span style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>Polite Rate Delay:</span>
                  <input 
                    type="number" 
                    step="0.1" 
                    value={delay} 
                    onChange={(e) => setDelay(parseFloat(e.target.value) || 0.5)}
                    disabled={pipelineRunning}
                    className="apple-glass-input"
                    style={{ padding: '6px 10px', fontSize: '0.84rem', width: '68px' }}
                  />
                  <span style={{ color: 'var(--text-secondary)' }}>sec</span>
                </div>

                <div style={{ color: 'var(--text-secondary)' }}>
                  Target Output: <strong style={{ color: '#FFFFFF' }}>faculty_publications_output.xlsx</strong>
                </div>
              </div>
            </div>

            {/* Real-time macOS Style Console Window */}
            <div style={{ background: 'rgba(5, 14, 30, 0.85)', borderRadius: 'var(--radius-2xl)', border: '1px solid rgba(255, 255, 255, 0.14)', overflow: 'hidden', boxShadow: '0 24px 60px rgba(0, 0, 0, 0.6), inset 0 1px 1px rgba(255, 255, 255, 0.2)' }}>
              {/* macOS Window Titlebar */}
              <div style={{ background: 'rgba(10, 24, 48, 0.95)', padding: '14px 22px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid rgba(255, 255, 255, 0.1)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#FF5F56' }}></div>
                  <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#FFBD2E' }}></div>
                  <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#27C93F' }}></div>
                  <span style={{ marginLeft: '14px', fontFamily: 'monospace', fontSize: '0.82rem', color: 'var(--text-secondary)' }}>
                    terminal — python fetch_faculty_publications.py
                  </span>
                </div>
                {pipelineRunning && (
                  <span style={{ fontSize: '0.78rem', color: '#60A5FA', display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600 }}>
                    <span className="pulse-indicator" style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#60A5FA' }}></span>
                    Process Active
                  </span>
                )}
              </div>

              {/* Console Output Terminal */}
              <div style={{ padding: '22px 26px', height: '420px', overflowY: 'auto', fontFamily: 'Courier New, monospace', fontSize: '0.86rem', color: '#E2E8F0', lineHeight: 1.65, whiteSpace: 'pre-wrap' }}>
                {logs.length === 0 ? (
                  <span style={{ color: '#64748B' }}>
                    Terminal ready. Click "Launch Extraction Pipeline" above to begin live execution...
                  </span>
                ) : (
                  logs.map((line, i) => (
                    <div key={i} style={{ color: line.includes('ERROR') || line.includes('Error') ? '#F87171' : (line.includes('SUCCESS') || line.includes('finished') || line.includes('Successfully') ? '#34D399' : '#E2E8F0') }}>
                      {line}
                    </div>
                  ))
                )}
                <div ref={consoleEndRef} />
              </div>
            </div>

          </div>
        )}

        {/* TAB 3: PUBLICATIONS EXPLORER */}
        {activeTab === 'explorer' && (
          <div>
            {/* Summary Metrics */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px', marginBottom: '32px' }}>
              <div className="apple-glass-card" style={{ padding: '24px 28px' }}>
                <div style={{ fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: 'var(--tracking-wide)' }}>Total Publications</div>
                <div style={{ fontSize: '2rem', fontWeight: 800, color: '#FFFFFF', marginTop: '6px', letterSpacing: 'var(--tracking-tight)' }}>{publications.length}</div>
              </div>
              <div className="apple-glass-card" style={{ padding: '24px 28px' }}>
                <div style={{ fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: 'var(--tracking-wide)' }}>Q1 Tier Papers</div>
                <div style={{ fontSize: '2rem', fontWeight: 800, color: '#34D399', marginTop: '6px', letterSpacing: 'var(--tracking-tight)', textShadow: '0 0 20px rgba(52, 211, 153, 0.35)' }}>{q1Count}</div>
              </div>
              <div className="apple-glass-card" style={{ padding: '24px 28px' }}>
                <div style={{ fontSize: '0.74rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: 'var(--tracking-wide)' }}>Cumulative Citations</div>
                <div style={{ fontSize: '2rem', fontWeight: 800, color: '#60A5FA', marginTop: '6px', letterSpacing: 'var(--tracking-tight)', textShadow: '0 0 20px rgba(96, 165, 250, 0.35)' }}>{totalCites.toLocaleString()}</div>
              </div>
              <div className="apple-glass-card" style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: '10px', justifyContent: 'center' }}>
                <a href="/api/download-output" className="btn-apple-white" style={{ width: '100%', padding: '9px 16px', fontSize: '0.86rem' }}>
                  <IconDownload size={15} /> Download Full Excel
                </a>
                <button 
                  onClick={handleClearPublications} 
                  className="btn-apple-glass" 
                  style={{ width: '100%', padding: '8px 16px', fontSize: '0.82rem', color: '#F87171', borderColor: 'rgba(239, 68, 68, 0.3)' }}
                  title="Clear all generated publication records and reports"
                >
                  <IconClose size={13} /> Clear Publications
                </button>
              </div>
            </div>

            {/* Filter Bar */}
            <div className="apple-glass-card" style={{ padding: '20px 26px', marginBottom: '24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <span style={{ fontSize: '0.86rem', fontWeight: 600, color: 'var(--text-secondary)' }}>Scopus Quartile:</span>
                {['ALL', 'Q1', 'Q2', 'Q3', 'Q4'].map(q => (
                  <button 
                    key={q}
                    onClick={() => setQuartileFilter(q)}
                    style={{
                      padding: '6px 16px',
                      borderRadius: 'var(--radius-full)',
                      border: '1px solid',
                      borderColor: quartileFilter === q ? '#FFFFFF' : 'rgba(255, 255, 255, 0.18)',
                      background: quartileFilter === q ? '#FFFFFF' : 'rgba(255, 255, 255, 0.08)',
                      color: quartileFilter === q ? '#07152B' : '#FFFFFF',
                      fontSize: '0.84rem',
                      fontWeight: 700,
                      cursor: 'pointer',
                      transition: 'var(--transition-apple)',
                      boxShadow: quartileFilter === q ? '0 2px 10px rgba(255, 255, 255, 0.3)' : 'none'
                    }}
                  >
                    {q}
                  </button>
                ))}
              </div>

              <div style={{ position: 'relative' }}>
                <input 
                  type="text" 
                  placeholder="Search title, journal, or faculty..."
                  value={pubFilter}
                  onChange={(e) => setPubFilter(e.target.value)}
                  className="apple-glass-input"
                  style={{
                    padding: '8px 18px 8px 36px',
                    borderRadius: 'var(--radius-full)',
                    fontSize: '0.86rem',
                    minWidth: '300px'
                  }}
                />
                <div style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }}>
                  <IconSearch size={15} />
                </div>
              </div>
            </div>

            {/* Publications Grid */}
            <div className="apple-glass-card" style={{ padding: '28px 32px', overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem' }}>
                <thead>
                  <tr style={{ background: 'rgba(255, 255, 255, 0.05)', borderBottom: '1px solid rgba(255, 255, 255, 0.12)' }}>
                    <th style={{ padding: '14px 16px', textAlign: 'left', color: 'var(--text-secondary)', fontWeight: 600 }}>Faculty &amp; Qualifications</th>
                    <th style={{ padding: '14px 16px', textAlign: 'left', color: 'var(--text-secondary)', fontWeight: 600 }}>Article Title</th>
                    <th style={{ padding: '14px 16px', textAlign: 'left', color: 'var(--text-secondary)', fontWeight: 600 }}>Journal / ISSN</th>
                    <th style={{ padding: '14px 16px', textAlign: 'center', width: '90px', color: 'var(--text-secondary)', fontWeight: 600 }}>Quartile</th>
                    <th style={{ padding: '14px 16px', textAlign: 'center', width: '80px', color: 'var(--text-secondary)', fontWeight: 600 }}>H-Index</th>
                    <th style={{ padding: '14px 16px', textAlign: 'center', width: '80px', color: 'var(--text-secondary)', fontWeight: 600 }}>Citations</th>
                    <th style={{ padding: '14px 16px', textAlign: 'center', width: '190px', color: 'var(--text-secondary)', fontWeight: 600 }}>Audit Proofs</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredPubs.length === 0 ? (
                    <tr>
                      <td colSpan={7} style={{ padding: '48px', textAlign: 'center', color: 'var(--text-secondary)' }}>
                        {publications.length === 0 ? 'No publications extracted yet. Go to Extraction Hub to run the pipeline!' : 'No publications match your filter.'}
                      </td>
                    </tr>
                  ) : (
                    filteredPubs.map((pub, idx) => (
                      <tr key={idx} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.06)', transition: 'var(--transition-apple)' }} onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)'} onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}>
                        <td style={{ padding: '16px 18px', verticalAlign: 'top', width: '220px' }}>
                          <div style={{ fontWeight: 700, color: '#FFFFFF' }}>{pub.Faculty_Name}</div>
                          <div style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', marginTop: '4px' }}>{pub.Qualifications}</div>
                          {pub.Vidwan_Profile_Link && pub.Vidwan_Profile_Link.startsWith('http') && (
                            <a href={pub.Vidwan_Profile_Link} target="_blank" rel="noreferrer" style={{ fontSize: '0.78rem', color: 'var(--accent-blue-hover)', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '3px', marginTop: '6px', fontWeight: 600 }}>
                              Vidwan Profile <IconArrowUpRight size={12} />
                            </a>
                          )}
                        </td>
                        <td style={{ padding: '16px 18px', verticalAlign: 'top' }}>
                          <div style={{ fontWeight: 600, color: '#FFFFFF', lineHeight: 1.5 }}>{pub.Article_Title}</div>
                          {pub.DOI && pub.DOI !== '-' && (
                            <a href={pub.DOI.startsWith('http') ? pub.DOI : `https://doi.org/${pub.DOI}`} target="_blank" rel="noreferrer" style={{ fontSize: '0.78rem', color: '#60A5FA', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '3px', marginTop: '6px', fontWeight: 500 }}>
                              DOI: {pub.DOI} <IconArrowUpRight size={12} />
                            </a>
                          )}
                        </td>
                        <td style={{ padding: '16px 18px', verticalAlign: 'top', width: '200px' }}>
                          <div style={{ fontWeight: 600, color: '#FFFFFF' }}>{pub.Journal_Name}</div>
                          <div style={{ fontSize: '0.76rem', color: 'var(--text-secondary)', marginTop: '3px' }}>ISSN: {pub.ISSN || '-'}</div>
                          {pub.Journal_Homepage && pub.Journal_Homepage.startsWith('http') && (
                            <a href={pub.Journal_Homepage} target="_blank" rel="noreferrer" style={{ fontSize: '0.78rem', color: 'var(--accent-blue-hover)', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '3px', marginTop: '4px', fontWeight: 600 }}>
                              Journal Site <IconArrowUpRight size={12} />
                            </a>
                          )}
                        </td>
                        <td style={{ padding: '16px 18px', textAlign: 'center', verticalAlign: 'middle' }}>
                          <span className={`badge-${(pub.Scopus_Quartile || 'none').toLowerCase()}`}>
                            {pub.Scopus_Quartile || 'None'}
                          </span>
                        </td>
                        <td style={{ padding: '16px 18px', textAlign: 'center', verticalAlign: 'middle', fontWeight: 700, color: '#FFFFFF' }}>
                          {pub.Journal_H_Index || '-'}
                        </td>
                        <td style={{ padding: '16px 18px', textAlign: 'center', verticalAlign: 'middle', fontWeight: 700, color: '#60A5FA' }}>
                          {pub.Article_Citations !== undefined ? pub.Article_Citations : '-'}
                        </td>
                        <td style={{ padding: '16px 18px', textAlign: 'center', verticalAlign: 'middle' }}>
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.78rem' }}>
                            {pub.Clarivate_MJL_Proof_Link && pub.Clarivate_MJL_Proof_Link.startsWith('http') && (
                              <a href={pub.Clarivate_MJL_Proof_Link} target="_blank" rel="noreferrer" style={{ color: '#38BDF8', textDecoration: 'none', fontWeight: 600, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: '3px' }}>Clarivate MJL <IconArrowUpRight size={11} /></a>
                            )}
                            {pub.Scopus_Proof_Link && pub.Scopus_Proof_Link.startsWith('http') && (
                              <a href={pub.Scopus_Proof_Link} target="_blank" rel="noreferrer" style={{ color: '#FB923C', textDecoration: 'none', fontWeight: 600, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: '3px' }}>Scopus Preview <IconArrowUpRight size={11} /></a>
                            )}
                            {pub.SCImago_Proof_Link && pub.SCImago_Proof_Link.startsWith('http') && (
                              <a href={pub.SCImago_Proof_Link} target="_blank" rel="noreferrer" style={{ color: '#34D399', textDecoration: 'none', fontWeight: 600, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', gap: '3px' }}>SCImago SJR <IconArrowUpRight size={11} /></a>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

          </div>
        )}

      </main>

      {/* Apple Vision Minimalist Translucent Footer */}
      <footer style={{ borderTop: '1px solid rgba(255, 255, 255, 0.08)', padding: '24px', background: 'rgba(7, 21, 43, 0.85)', backdropFilter: 'blur(20px)', WebkitBackdropFilter: 'blur(20px)', textAlign: 'center', fontSize: '0.84rem', color: 'var(--text-secondary)' }}>
        <div>GD Goenka University &bull; INFLIBNET Vidwan Scopus Bibliometrics System &bull; Production Architecture</div>
        <div style={{ marginTop: '8px', fontSize: '0.70rem', color: 'rgba(255, 255, 255, 0.2)', letterSpacing: '0.04em', userSelect: 'none' }} title="System Engineering Watermark">
          Architecture &bull; Sarthak Singh- 3096-2023-27
        </div>
        {/* Hidden System Watermark */}
        <div id="system-signature" style={{ display: 'none' }} data-engineer="Sarthak Singh- 3096-2023-27" aria-hidden="true">
          Sarthak Singh- 3096-2023-27
        </div>
      </footer>
    </div>
  );
}

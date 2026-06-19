import React, { useState } from 'react';
import UploadPage from './pages/UploadPage';
import CandidatesPage from './pages/CandidatesPage';
import './App.css';

function App() {
  const [currentPage, setCurrentPage] = useState('upload');

  return (
    <div className="app">

      {/* ── Background Canvas ── */}
      <div className="bg-canvas">

        {/* Large blurred blobs */}
        <div className="blob" style={{ width: 500, height: 500, background: '#A5F3FC', top: -180, left: -120, opacity: 0.25 }} />
        <div className="blob" style={{ width: 420, height: 420, background: '#C7D2FE', top: -100, right: -100, opacity: 0.3 }} />
        <div className="blob" style={{ width: 350, height: 350, background: '#FDE68A', top: 300, right: -80, opacity: 0.22 }} />
        <div className="blob" style={{ width: 300, height: 300, background: '#F9A8D4', bottom: 100, left: -80, opacity: 0.2 }} />
        <div className="blob" style={{ width: 280, height: 280, background: '#6EE7B7', bottom: 200, right: 200, opacity: 0.18 }} />
        <div className="blob" style={{ width: 220, height: 220, background: '#FCA5A5', top: 500, left: 100, opacity: 0.15 }} />

        {/* Floating circles */}
        <div className="float-circle" style={{ width: 18, height: 18, background: '#6366F1', top: 180, left: '15%' }} />
        <div className="float-circle" style={{ width: 12, height: 12, background: '#06B6D4', top: 240, left: '20%' }} />
        <div className="float-circle" style={{ width: 24, height: 24, background: '#F59E0B', top: 160, right: '18%' }} />
        <div className="float-circle" style={{ width: 14, height: 14, background: '#EC4899', top: 320, right: '12%' }} />
        <div className="float-circle" style={{ width: 20, height: 20, background: '#10B981', top: 400, left: '8%' }} />
        <div className="float-circle" style={{ width: 10, height: 10, background: '#8B5CF6', top: 450, right: '25%' }} />
        <div className="float-circle" style={{ width: 16, height: 16, background: '#FB923C', bottom: 300, left: '30%' }} />
        <div className="float-circle" style={{ width: 22, height: 22, background: '#06B6D4', bottom: 200, right: '10%' }} />

        {/* Floating rings */}
        <div className="float-ring" style={{ width: 48, height: 48, borderColor: '#6366F1', top: 200, left: '25%' }} />
        <div className="float-ring" style={{ width: 32, height: 32, borderColor: '#EC4899', top: 350, right: '20%' }} />
        <div className="float-ring" style={{ width: 56, height: 56, borderColor: '#06B6D4', bottom: 250, left: '15%' }} />
        <div className="float-ring" style={{ width: 36, height: 36, borderColor: '#F59E0B', bottom: 180, right: '30%' }} />

        {/* Dot grid top-right */}
        <svg style={{ position: 'absolute', top: 80, right: 40, opacity: 0.2 }} width="160" height="160">
          <pattern id="d1" x="0" y="0" width="18" height="18" patternUnits="userSpaceOnUse">
            <circle cx="3" cy="3" r="1.8" fill="#6366F1" />
          </pattern>
          <rect width="160" height="160" fill="url(#d1)" />
        </svg>

        {/* Dot grid bottom-left */}
        <svg style={{ position: 'absolute', bottom: 120, left: 40, opacity: 0.18 }} width="140" height="140">
          <pattern id="d2" x="0" y="0" width="18" height="18" patternUnits="userSpaceOnUse">
            <circle cx="3" cy="3" r="1.8" fill="#06B6D4" />
          </pattern>
          <rect width="140" height="140" fill="url(#d2)" />
        </svg>

        {/* Wave top */}
        <svg style={{ position: 'absolute', top: 64, left: 0, width: '100%', opacity: 0.06 }} viewBox="0 0 1440 120" preserveAspectRatio="none">
          <path d="M0,60 C240,110 480,10 720,60 C960,110 1200,10 1440,60 L1440,120 L0,120 Z" fill="#6366F1" />
        </svg>

        {/* Wave bottom */}
        <svg style={{ position: 'absolute', bottom: 0, left: 0, width: '100%', opacity: 0.07 }} viewBox="0 0 1440 120" preserveAspectRatio="none">
          <path d="M0,60 C360,0 720,120 1080,60 C1260,30 1380,80 1440,60 L1440,120 L0,120 Z" fill="#06B6D4" />
        </svg>

        {/* Organic blob shapes SVG */}
        <svg style={{ position: 'absolute', top: 120, left: -60, opacity: 0.12 }} width="320" height="280" viewBox="0 0 320 280">
          <path d="M160,20 C220,20 280,60 290,120 C300,180 260,240 200,260 C140,280 80,250 50,200 C20,150 30,80 80,50 C110,30 130,20 160,20 Z" fill="#A5F3FC" />
        </svg>

        <svg style={{ position: 'absolute', bottom: 80, right: -40, opacity: 0.12 }} width="280" height="240" viewBox="0 0 280 240">
          <path d="M140,15 C195,15 250,55 258,110 C266,165 232,218 177,235 C122,252 65,228 38,178 C11,128 22,62 68,35 C95,18 115,15 140,15 Z" fill="#FDE68A" />
        </svg>

        {/* Small geometric squares */}
        <div style={{ position: 'absolute', top: 280, right: '15%', width: 14, height: 14, background: '#6366F1', borderRadius: 3, opacity: 0.3, transform: 'rotate(20deg)' }} />
        <div style={{ position: 'absolute', top: 500, left: '20%', width: 10, height: 10, background: '#EC4899', borderRadius: 2, opacity: 0.35, transform: 'rotate(35deg)' }} />
        <div style={{ position: 'absolute', bottom: 300, right: '8%', width: 16, height: 16, background: '#F59E0B', borderRadius: 4, opacity: 0.3, transform: 'rotate(15deg)' }} />

      </div>

      {/* ── Navbar ── */}
      <nav className="navbar">
        <div className="navbar-brand">
          <div className="brand-dot">R</div>
          <span className="brand-name">Resume<span>AI</span></span>
        </div>
        <div className="navbar-links">
          <button className={`nav-btn ${currentPage === 'upload' ? 'active' : ''}`} onClick={() => setCurrentPage('upload')}>Upload</button>
          <button className={`nav-btn ${currentPage === 'candidates' ? 'active' : ''}`} onClick={() => setCurrentPage('candidates')}>Candidates</button>
        </div>
      </nav>

      <main className="main-content">
        {currentPage === 'upload' && <UploadPage />}
        {currentPage === 'candidates' && <CandidatesPage />}
      </main>

    </div>
  );
}

export default App;
import React, { useState } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/resumes';

function UploadPage() {
  const [file, setFile] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [bulkFiles, setBulkFiles] = useState([]);
  const [bulkUploading, setBulkUploading] = useState(false);
  const [bulkResults, setBulkResults] = useState(null);

  const handleFileSelect = (e) => {
    const f = e.target.files[0];
    if (f) { setFile(f); setResult(null); setError(null); }
  };

  const handleDragOver = (e) => { e.preventDefault(); setDragging(true); };
  const handleDragLeave = () => setDragging(false);
  const handleDrop = (e) => {
    e.preventDefault(); setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) { setFile(f); setResult(null); setError(null); }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true); setError(null); setResult(null);
    const fd = new FormData();
    fd.append('file', file);
    try {
      const res = await axios.post(`${API_URL}/upload`, fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      if (res.data.status === 'duplicate') {
        const replace = window.confirm(
          `⚠️ ${res.data.message}\n\nDo you want to replace the existing resume with this new one?`
        );
        if (replace) {
          await axios.put(`${API_URL}/replace/${res.data.existing_id}`, res.data.parsed_data);
          setResult({ parsing_status: res.data.parsed_data.parsing_status, data: res.data.parsed_data });
        } else {
          setError('Upload cancelled. Existing resume kept.');
        }
      } else {
        setResult(res.data);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong.');
    } finally { setUploading(false); }
  };

  const handleBulkSelect = (e) => { setBulkFiles(Array.from(e.target.files)); setBulkResults(null); };

  const handleBulkUpload = async () => {
    if (!bulkFiles.length) return;
    setBulkUploading(true);
    const fd = new FormData();
    bulkFiles.forEach(f => fd.append('files', f));
    try {
      const res = await axios.post(`${API_URL}/upload-bulk`, fd, { headers: { 'Content-Type': 'multipart/form-data' } });
      setBulkResults(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Bulk upload failed.');
    } finally { setBulkUploading(false); }
  };

  const sc = (s) => s === 'Success' ? 'success' : s === 'Partial' ? 'partial' : 'failed';

  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 40 }}>
        <p className="section-label">Resume Intelligence</p>
        <h1 style={{ fontSize: 36, fontWeight: 800, letterSpacing: '-1px', color: 'var(--text)', marginBottom: 8, lineHeight: 1.1 }}>
          Parse a Resume
        </h1>
        <p style={{ color: 'var(--text-soft)', fontSize: 15 }}>
          Upload PDF or DOCX — name, skills, experience extracted in seconds.
        </p>
      </div>

      {/* Drop Zone */}
      <div
        onDragOver={handleDragOver} onDragLeave={handleDragLeave} onDrop={handleDrop}
        style={{
          position: 'relative', overflow: 'hidden',
          border: dragging ? '2px dashed #6366F1' : '2px dashed rgba(0,0,0,0.1)',
          borderRadius: 'var(--radius)', padding: '56px 40px', textAlign: 'center',
          background: dragging ? 'rgba(99,102,241,0.05)' : 'rgba(255,255,255,0.7)',
          backdropFilter: 'blur(16px)', cursor: 'pointer', transition: 'all 0.25s',
          marginBottom: 16, boxShadow: '0 8px 32px rgba(0,0,0,0.08)',
        }}
      >
        {/* Mini blobs inside card */}
        <div style={{ position: 'absolute', width: 120, height: 120, background: '#A5F3FC', borderRadius: '50%', filter: 'blur(30px)', top: -40, right: -20, opacity: 0.5, pointerEvents: 'none' }} />
        <div style={{ position: 'absolute', width: 100, height: 100, background: '#FDE68A', borderRadius: '50%', filter: 'blur(25px)', bottom: -30, left: -20, opacity: 0.4, pointerEvents: 'none' }} />
        <div style={{ position: 'absolute', width: 14, height: 14, background: '#6366F1', borderRadius: '50%', top: 20, right: 60, opacity: 0.4, pointerEvents: 'none' }} />
        <div style={{ position: 'absolute', width: 10, height: 10, background: '#EC4899', borderRadius: '50%', bottom: 24, left: 48, opacity: 0.45, pointerEvents: 'none' }} />
        <div style={{ position: 'absolute', width: 10, height: 10, border: '2px solid #06B6D4', borderRadius: '50%', top: 32, left: 56, opacity: 0.5, pointerEvents: 'none' }} />

        <div style={{ width: 72, height: 72, background: file ? 'linear-gradient(135deg,#D1FAE5,#A7F3D0)' : 'linear-gradient(135deg,#FEF3C7,#FDE68A)', border: `1px solid ${file ? '#6EE7B7' : '#FCD34D'}`, borderRadius: 20, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 32, margin: '0 auto 20px', boxShadow: '0 4px 16px rgba(0,0,0,0.08)' }}>
          {file ? '📄' : '📂'}
        </div>
        <h3 style={{ fontSize: 20, fontWeight: 800, marginBottom: 8, color: 'var(--text)' }}>
          {file ? file.name : 'Drop your resume here'}
        </h3>
        <p style={{ color: 'var(--text-muted)', fontSize: 14, marginBottom: 24 }}>
          {file ? <span style={{ color: 'var(--green)', fontWeight: 700 }}>{(file.size/1024).toFixed(1)} KB — ready to parse</span> : 'PDF, DOCX, DOC, TXT — Max 5MB'}
        </p>
        <label style={{ cursor: 'pointer' }}>
          <span className="btn-outline">{file ? '↺ Change File' : '↑ Browse File'}</span>
          <input type="file" hidden accept=".pdf,.docx,.doc,.txt" onChange={handleFileSelect} />
        </label>
      </div>

      {/* Upload Btn */}
      <button className="btn-primary" onClick={handleUpload} disabled={!file || uploading}
        style={{ width: '100%', justifyContent: 'center', padding: 16, fontSize: 15, borderRadius: 14, marginBottom: 20 }}>
        {uploading ? '⟳  Parsing Resume...' : '✦  Upload & Parse Resume'}
      </button>

      {/* Skeleton */}
      {uploading && <div style={{ display: 'grid', gap: 10, marginBottom: 20 }}>
        {[72, 72, 110].map((h, i) => <div key={i} className="skeleton" style={{ height: h }} />)}
      </div>}

      {/* Error */}
      {error && <div style={{ padding: '14px 18px', background: 'var(--pink-light)', border: '1px solid #F9A8D4', borderRadius: 'var(--radius-sm)', color: 'var(--pink)', fontSize: 14, fontWeight: 500, marginBottom: 20 }}>✕ {error}</div>}

      {/* Result */}
      {result && (
        <div style={{ display: 'grid', gap: 16, marginBottom: 48 }}>
          <div style={{ padding: 24, background: 'linear-gradient(135deg,#1E1E2E,#2D2B55)', borderRadius: 'var(--radius)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', boxShadow: '0 8px 32px rgba(0,0,0,0.18)' }}>
            <div>
              <p style={{ color: 'rgba(255,255,255,0.45)', fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '1px', marginBottom: 4 }}>Parsed Successfully</p>
              <h2 style={{ fontSize: 26, fontWeight: 800, color: 'white', letterSpacing: '-0.3px' }}>{result.data?.name || 'Unknown Candidate'}</h2>
            </div>
            <span className={`status-pill ${sc(result.parsing_status)}`}>{result.parsing_status === 'Success' ? '✓' : '!'} {result.parsing_status}</span>
          </div>

          <div>
            <p className="section-label">Basic Information</p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
              {[['Email', result.data?.email], ['Phone', result.data?.phone], ['Location', result.data?.location], ['LinkedIn', result.data?.linkedin], ['GitHub', result.data?.github], ['Experience', result.data?.total_experience ? `${result.data.total_experience} years` : null]].map(([l, v]) => (
                <div key={l} className="info-row"><p className="info-label">{l}</p><p className="info-value">{v || <span style={{ color: 'var(--text-muted)' }}>Not found</span>}</p></div>
              ))}
            </div>
          </div>

          {result.data?.skills?.length > 0 && (
            <div>
              <p className="section-label">Skills</p>
              <div className="card" style={{ padding: 20, display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                {result.data.skills.map((s, i) => <span key={i} className="skill-tag">{s}</span>)}
              </div>
            </div>
          )}

          {result.data?.education?.length > 0 && (
            <div>
              <p className="section-label">Education</p>
              {result.data.education.map((e, i) => (
                <div key={i} className="card" style={{ padding: '14px 20px', marginBottom: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <p style={{ fontSize: 14, fontWeight: 600 }}>{e.degree}</p>
                  {e.year && <span style={{ fontSize: 12, color: 'var(--text-muted)', background: 'var(--bg)', padding: '3px 10px', borderRadius: 'var(--radius-pill)', border: '1px solid var(--border)' }}>{e.year}</span>}
                </div>
              ))}
            </div>
          )}

          {result.data?.profile_summary && (
            <div>
              <p className="section-label">Profile Summary</p>
              <div className="card" style={{ padding: 20, borderLeft: '4px solid var(--indigo)', borderRadius: '0 var(--radius) var(--radius) 0' }}>
                <p style={{ fontSize: 14, color: 'var(--text-soft)', lineHeight: 1.8 }}>{result.data.profile_summary}</p>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Divider */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, margin: '8px 0 36px' }}>
        <div style={{ flex: 1, height: 1, background: 'linear-gradient(to right, transparent, rgba(0,0,0,0.1))' }} />
        <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '1px' }}>OR UPLOAD MULTIPLE</span>
        <div style={{ flex: 1, height: 1, background: 'linear-gradient(to left, transparent, rgba(0,0,0,0.1))' }} />
      </div>

      {/* Bulk Upload */}
      <div style={{ marginBottom: 48 }}>
        <p className="section-label">Bulk Upload</p>
        <h2 style={{ fontSize: 26, fontWeight: 800, letterSpacing: '-0.5px', marginBottom: 8 }}>Parse Multiple Resumes</h2>
        <p style={{ color: 'var(--text-soft)', fontSize: 14, marginBottom: 24 }}>Hold Ctrl and select multiple files at once.</p>

        <label style={{ cursor: 'pointer', display: 'block', marginBottom: 16 }}>
          <div className="card" style={{ padding: 28, textAlign: 'center', border: '2px dashed rgba(0,0,0,0.1)', cursor: 'pointer', transition: 'all 0.2s', position: 'relative', overflow: 'hidden' }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = '#6366F1'; e.currentTarget.style.background = 'rgba(99,102,241,0.04)'; }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = 'rgba(0,0,0,0.07)'; e.currentTarget.style.background = 'rgba(255,255,255,0.75)'; }}
          >
            <div style={{ position: 'absolute', width: 80, height: 80, background: '#C7D2FE', borderRadius: '50%', filter: 'blur(20px)', top: -20, right: -10, opacity: 0.4, pointerEvents: 'none' }} />
            <div style={{ fontSize: 32, marginBottom: 10 }}>📁</div>
            <p style={{ fontWeight: 700, fontSize: 15, marginBottom: 4 }}>
              {bulkFiles.length > 0 ? `${bulkFiles.length} file${bulkFiles.length > 1 ? 's' : ''} selected` : 'Click to select multiple files'}
            </p>
            <p style={{ color: 'var(--text-muted)', fontSize: 13 }}>Hold Ctrl to select multiple</p>
          </div>
          <input type="file" hidden multiple accept=".pdf,.docx,.doc,.txt" onChange={handleBulkSelect} />
        </label>

        {bulkFiles.length > 0 && (
          <div className="card-solid" style={{ padding: '8px 16px', marginBottom: 16 }}>
            {bulkFiles.map((f, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 0', borderBottom: i < bulkFiles.length - 1 ? '1px solid var(--border)' : 'none' }}>
                <span style={{ fontSize: 13, fontWeight: 600 }}>📄 {f.name}</span>
                <span style={{ fontSize: 12, color: 'var(--text-muted)', background: 'var(--bg)', padding: '3px 10px', borderRadius: 'var(--radius-pill)', border: '1px solid var(--border)' }}>{(f.size/1024).toFixed(1)} KB</span>
              </div>
            ))}
          </div>
        )}

        <button className="btn-green" onClick={handleBulkUpload} disabled={!bulkFiles.length || bulkUploading}
          style={{ width: '100%', justifyContent: 'center', padding: 15, fontSize: 15, borderRadius: 14 }}>
          {bulkUploading ? '⟳  Parsing All Resumes...' : `✦  Upload ${bulkFiles.length > 0 ? bulkFiles.length : ''} Resumes`}
        </button>

        {bulkUploading && <div style={{ display: 'grid', gap: 8, marginTop: 16 }}>
          {bulkFiles.map((_, i) => <div key={i} className="skeleton" style={{ height: 52 }} />)}
        </div>}

        {bulkResults && (
          <div style={{ marginTop: 24 }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 12, marginBottom: 20 }}>
              {[['Total', bulkResults.total, 'var(--text)', 'white'], ['Successful', bulkResults.successful, 'var(--green)', 'var(--green-light)'], ['Duplicates', bulkResults.duplicates, 'var(--amber)', 'var(--amber-light)'], ['Failed', bulkResults.failed, 'var(--pink)', 'var(--pink-light)']].map(([l, v, c, bg]) => (
                <div key={l} style={{ padding: '20px 16px', textAlign: 'center', background: bg, border: '1px solid var(--border)', borderRadius: 'var(--radius)', boxShadow: 'var(--shadow-sm)' }}>
                  <p style={{ fontSize: 32, fontWeight: 800, color: c, lineHeight: 1 }}>{v}</p>
                  <p style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 6, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.8px' }}>{l}</p>
                </div>
              ))}
            </div>
            <p className="section-label" style={{ marginBottom: 12 }}>File Results</p>
            {bulkResults.results.map((r, i) => (
              <div key={i} className="card" style={{ padding: '14px 20px', marginBottom: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <p style={{ fontSize: 14, fontWeight: 600 }}>📄 {r.file_name}</p>
                  {r.name && <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>{r.name}</p>}
                  {r.message && <p style={{ fontSize: 12, color: 'var(--pink)', marginTop: 2 }}>{r.message}</p>}
                </div>
                <span className={`status-pill ${r.status === 'Success' ? 'success' : r.status === 'Duplicate' ? 'partial' : 'failed'}`}>{r.status}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default UploadPage;
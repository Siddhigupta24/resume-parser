import React, { useState, useEffect } from 'react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/resumes';

function CandidatesPage() {
  const [candidates, setCandidates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [total, setTotal] = useState(0);
  const [nameFilter, setNameFilter] = useState('');
  const [skill, setSkill] = useState('');
  const [minExp, setMinExp] = useState('');
  const [maxExp, setMaxExp] = useState('');
  const [location, setLocation] = useState('');
  const [status, setStatus] = useState('');
  const [exporting, setExporting] = useState(false);
  const [selected, setSelected] = useState(null);
  const [reparsing, setReparsing] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState({});
  const [saving, setSaving] = useState(false);
  const [toast, setToast] = useState(null);
  const itemsPerPage = 10;

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const fetchCandidates = async () => {
    setLoading(true); setError(null); setCurrentPage(1);
    try {
      const params = {};
      if (nameFilter) params.name = nameFilter;
      if (skill) params.skill = skill;
      if (minExp) params.min_experience = minExp;
      if (maxExp) params.max_experience = maxExp;
      if (location) params.location = location;
      if (status) params.status = status;
      const res = await axios.get(`${API_URL}/candidates`, { params });
      setCandidates(res.data.candidates);
      setTotal(res.data.total);
    } catch {
      setError('Failed to fetch candidates. Is the backend running?');
    } finally { setLoading(false); }
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { fetchCandidates(); }, []);

  const totalPages = Math.ceil(candidates.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const currentCandidates = candidates.slice(startIndex, startIndex + itemsPerPage);

  const handleExport = async (format) => {
    setExporting(true);
    try {
      const mimeTypes = {
        json: 'application/json',
        csv: 'text/csv',
        excel: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
      };
      const extensions = { json: 'json', csv: 'csv', excel: 'xlsx' };
      const res = await axios.get(`${API_URL}/export`, {
        params: { format }, responseType: 'blob'
      });
      const url = window.URL.createObjectURL(
        new Blob([res.data], { type: mimeTypes[format] })
      );
      const a = document.createElement('a');
      a.href = url;
      a.setAttribute('download', `candidates.${extensions[format]}`);
      document.body.appendChild(a); a.click(); a.remove();
      window.URL.revokeObjectURL(url);
      showToast(`Exported as ${format.toUpperCase()} successfully`);
    } catch {
      showToast('Export failed. Please try again.', 'error');
    } finally { setExporting(false); }
  };

  const handleDelete = async (candidateId) => {
    if (!window.confirm('Delete this candidate? This cannot be undone.')) return;
    try {
      await axios.delete(`${API_URL}/candidate/${candidateId}`);
      setSelected(null);
      showToast('Candidate deleted successfully');
      fetchCandidates();
    } catch {
      showToast('Delete failed. Please try again.', 'error');
    }
  };

  const handleEditSave = async () => {
    setSaving(true);
    try {
      const skillsArray = typeof editData.skills === 'string'
        ? editData.skills.split(',').map(s => s.trim()).filter(Boolean)
        : editData.skills;

      const updates = { ...editData, skills: skillsArray };
      const res = await axios.put(`${API_URL}/candidate/${selected.id}`, updates);
      setSelected(res.data);
      setEditing(false);
      showToast('Candidate updated successfully');
      fetchCandidates();
    } catch {
      showToast('Update failed. Please try again.', 'error');
    } finally { setSaving(false); }
  };

  const startEdit = () => {
    setEditData({
      name: selected.name || '',
      email: selected.email || '',
      phone: selected.phone || '',
      location: selected.location || '',
      city: selected.city || '',
      country: selected.country || '',
      linkedin: selected.linkedin || '',
      github: selected.github || '',
      skills: (selected.skills || []).join(', '),
      total_experience: selected.total_experience || '',
      current_company: selected.current_company || '',
      current_designation: selected.current_designation || '',
      profile_summary: selected.profile_summary || '',
    });
    setEditing(true);
  };

  const sc = (s) => s === 'Success' ? 'success' : s === 'Partial' ? 'partial' : 'failed';

  const btnExportStyle = {
    display: 'inline-flex', alignItems: 'center', gap: 6,
    padding: '10px 20px',
    background: 'linear-gradient(135deg, #6366F1, #8B5CF6)',
    color: 'white', border: 'none', borderRadius: 'var(--radius-pill)',
    fontFamily: 'Plus Jakarta Sans, sans-serif',
    fontSize: 13, fontWeight: 700, cursor: 'pointer',
    boxShadow: '0 4px 14px rgba(99,102,241,0.3)', transition: 'all 0.2s'
  };

  const inputStyle = {
    width: '100%', padding: '10px 14px',
    background: 'rgba(255,255,255,0.7)', backdropFilter: 'blur(8px)',
    color: 'var(--text)', border: '1px solid var(--border)',
    borderRadius: 'var(--radius-sm)',
    fontFamily: 'Plus Jakarta Sans, sans-serif',
    fontSize: 13, outline: 'none', transition: 'border 0.2s'
  };

  const labelStyle = {
    display: 'block', fontSize: 10, fontWeight: 700,
    textTransform: 'uppercase', letterSpacing: '1px',
    color: 'var(--text-muted)', marginBottom: 6
  };

  const editInputStyle = {
    width: '100%', padding: '9px 12px',
    background: 'rgba(255,255,255,0.9)',
    color: 'var(--text)', border: '1px solid rgba(99,102,241,0.3)',
    borderRadius: 'var(--radius-sm)',
    fontFamily: 'Plus Jakarta Sans, sans-serif',
    fontSize: 13, outline: 'none',
    transition: 'border 0.2s', marginTop: 4
  };

  return (
    <div style={{ position: 'relative' }}>

      {/* ── Toast Notification ── */}
      {toast && (
        <div style={{
          position: 'fixed', top: 20, right: 20, zIndex: 999,
          padding: '12px 20px',
          background: toast.type === 'error'
            ? 'linear-gradient(135deg,#EC4899,#EF4444)'
            : 'linear-gradient(135deg,#10B981,#06B6D4)',
          color: 'white', borderRadius: 'var(--radius-pill)',
          fontSize: 13, fontWeight: 600,
          boxShadow: '0 8px 24px rgba(0,0,0,0.2)',
          animation: 'slideIn 0.3s ease'
        }}>
          {toast.type === 'error' ? '✕ ' : '✓ '}{toast.message}
        </div>
      )}

      {/* ── Header ── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 32 }}>
        <div>
          <p className="section-label">Talent Pool</p>
          <h1 style={{ fontSize: 36, fontWeight: 800, letterSpacing: '-1px' }}>
            Candidates
            <span style={{ fontSize: 18, color: 'var(--text-muted)', fontWeight: 500, marginLeft: 12 }}>
              {total} total
            </span>
          </h1>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <button onClick={() => handleExport('json')} disabled={exporting}
            style={{ ...btnExportStyle, opacity: exporting ? 0.6 : 1 }}>↓ JSON</button>
          <button onClick={() => handleExport('csv')} disabled={exporting}
            style={{ ...btnExportStyle, opacity: exporting ? 0.6 : 1 }}>↓ CSV</button>
          <button onClick={() => handleExport('excel')} disabled={exporting}
            style={{ ...btnExportStyle, opacity: exporting ? 0.6 : 1 }}>
            {exporting ? '⟳ Exporting...' : '↓ Excel'}
          </button>
          <button className="btn-outline"
            onClick={async () => {
              if (window.confirm('Re-parse ALL candidates with improved parser?')) {
                const res = await axios.post(`${API_URL}/reparse-all`);
                showToast(`Re-parsed: ${res.data.results.success} success, ${res.data.results.failed} failed`);
                fetchCandidates();
              }
            }}
            style={{ padding: '10px 18px' }}>
            ↺ Re-parse All
          </button>
        </div>
      </div>

      {/* ── Filters ── */}
      <div className="card" style={{ padding: 24, marginBottom: 24 }}>
        <p className="section-label" style={{ marginBottom: 14 }}>Filter Candidates</p>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 12, marginBottom: 16 }}>
          {[
            ['Search by Name', nameFilter, setNameFilter, 'e.g. Rahul Sharma', 'text'],
            ['Skill', skill, setSkill, 'e.g. Python, React', 'text'],
            ['Min Experience (yrs)', minExp, setMinExp, '', 'number'],
            ['Max Experience (yrs)', maxExp, setMaxExp, '', 'number'],
            ['Location', location, setLocation, 'e.g. Delhi', 'text'],
          ].map(([l, v, s, ph, t]) => (
            <div key={l}>
              <label style={labelStyle}>{l}</label>
              <input type={t} value={v} onChange={e => s(e.target.value)}
                placeholder={ph} style={inputStyle}
                onFocus={e => e.target.style.borderColor = 'var(--indigo)'}
                onBlur={e => e.target.style.borderColor = 'var(--border)'}
              />
            </div>
          ))}
          <div>
            <label style={labelStyle}>Status</label>
            <select value={status} onChange={e => setStatus(e.target.value)}
              style={{ ...inputStyle, cursor: 'pointer' }}>
              <option value="">All</option>
              <option value="Success">Success</option>
              <option value="Partial">Partial</option>
              <option value="Failed">Failed</option>
            </select>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn-primary" onClick={fetchCandidates} style={{ padding: '10px 24px' }}>
            ⌕ Search
          </button>
          <button className="btn-outline" onClick={() => {
            setNameFilter(''); setSkill(''); setMinExp('');
            setMaxExp(''); setLocation(''); setStatus('');
          }}>↺ Clear</button>
        </div>
      </div>

      {error && <div style={{ padding: 14, background: 'var(--pink-light)', border: '1px solid #F9A8D4', borderRadius: 'var(--radius-sm)', color: 'var(--pink)', marginBottom: 20, fontSize: 14 }}>✕ {error}</div>}

      {loading && <div style={{ display: 'grid', gap: 8 }}>
        {[1,2,3,4,5].map(i => <div key={i} className="skeleton" style={{ height: 60, borderRadius: 'var(--radius-sm)' }} />)}
      </div>}

      {/* ── Table ── */}
      {!loading && (
        <>
          <div className="card" style={{ overflow: 'hidden' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: 'linear-gradient(135deg,#0F172A,#1E1B4B)' }}>
                  {['Name', 'Email', 'Experience', 'Skills', 'Status'].map(h => (
                    <th key={h} style={{ padding: '14px 20px', textAlign: 'left', fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '1px', color: 'rgba(255,255,255,0.45)' }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {currentCandidates.length === 0 ? (
                  <tr><td colSpan={5} style={{ padding: 56, textAlign: 'center', color: 'var(--text-muted)' }}>
                    <div style={{ fontSize: 40, marginBottom: 12 }}>📭</div>
                    <p style={{ fontWeight: 700, fontSize: 16, marginBottom: 4 }}>No candidates yet</p>
                    <p style={{ fontSize: 14 }}>Upload a resume to get started.</p>
                  </td></tr>
                ) : currentCandidates.map(c => (
                  <tr key={c.id} onClick={() => { setSelected(c); setEditing(false); }}
                    style={{ borderBottom: '1px solid var(--border)', cursor: 'pointer', transition: 'background 0.15s' }}
                    onMouseEnter={e => e.currentTarget.style.background = 'rgba(99,102,241,0.04)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                    <td style={{ padding: '16px 20px', fontWeight: 700, fontSize: 14 }}>{c.name || '—'}</td>
                    <td style={{ padding: '16px 20px', color: 'var(--text-soft)', fontSize: 13 }}>{c.email || '—'}</td>
                    <td style={{ padding: '16px 20px', color: 'var(--text-soft)', fontSize: 13 }}>{c.total_experience ? `${c.total_experience} yrs` : '—'}</td>
                    <td style={{ padding: '16px 20px' }}>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                        {c.skills?.slice(0, 3).map((s, i) => <span key={i} className="skill-tag">{s}</span>)}
                        {c.skills?.length > 3 && <span className="skill-tag" style={{ opacity: 0.6 }}>+{c.skills.length - 3}</span>}
                      </div>
                    </td>
                    <td style={{ padding: '16px 20px' }}>
                      <span className={`status-pill ${sc(c.parsing_status)}`}>{c.parsing_status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* ── Pagination ── */}
          {totalPages > 1 && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 20, padding: '16px 20px', background: 'rgba(255,255,255,0.7)', backdropFilter: 'blur(12px)', borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
              <p style={{ fontSize: 13, color: 'var(--text-soft)', fontWeight: 500 }}>
                Showing <strong>{startIndex + 1}–{Math.min(startIndex + itemsPerPage, candidates.length)}</strong> of <strong>{candidates.length}</strong>
              </p>
              <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                <button onClick={() => setCurrentPage(p => Math.max(1, p - 1))} disabled={currentPage === 1}
                  style={{ padding: '8px 16px', background: currentPage === 1 ? 'var(--bg)' : 'white', color: currentPage === 1 ? 'var(--text-muted)' : 'var(--text)', border: '1px solid var(--border)', borderRadius: 'var(--radius-pill)', fontFamily: 'Plus Jakarta Sans, sans-serif', fontSize: 13, fontWeight: 600, cursor: currentPage === 1 ? 'not-allowed' : 'pointer' }}>
                  ← Prev
                </button>
                {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                  <button key={page} onClick={() => setCurrentPage(page)}
                    style={{ width: 36, height: 36, background: currentPage === page ? 'linear-gradient(135deg,#6366F1,#8B5CF6)' : 'white', color: currentPage === page ? 'white' : 'var(--text-soft)', border: currentPage === page ? 'none' : '1px solid var(--border)', borderRadius: 'var(--radius-pill)', fontFamily: 'Plus Jakarta Sans, sans-serif', fontSize: 13, fontWeight: 700, cursor: 'pointer', boxShadow: currentPage === page ? '0 4px 12px rgba(99,102,241,0.3)' : 'none' }}>
                    {page}
                  </button>
                ))}
                <button onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))} disabled={currentPage === totalPages}
                  style={{ padding: '8px 16px', background: currentPage === totalPages ? 'var(--bg)' : 'white', color: currentPage === totalPages ? 'var(--text-muted)' : 'var(--text)', border: '1px solid var(--border)', borderRadius: 'var(--radius-pill)', fontFamily: 'Plus Jakarta Sans, sans-serif', fontSize: 13, fontWeight: 600, cursor: currentPage === totalPages ? 'not-allowed' : 'pointer' }}>
                  Next →
                </button>
              </div>
              <p style={{ fontSize: 13, color: 'var(--text-soft)', fontWeight: 500 }}>
                Page <strong>{currentPage}</strong> of <strong>{totalPages}</strong>
              </p>
            </div>
          )}
        </>
      )}

      {/* ── Slide-in Panel ── */}
      {selected && (
        <>
          <div onClick={() => { setSelected(null); setEditing(false); }}
            style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,0.3)', zIndex: 300, backdropFilter: 'blur(4px)' }} />
          <div style={{ position: 'fixed', top: 0, right: 0, height: '100vh', width: 440, background: 'rgba(255,255,255,0.95)', backdropFilter: 'blur(24px)', boxShadow: '-12px 0 60px rgba(0,0,0,0.15)', zIndex: 400, overflowY: 'auto', animation: 'slideIn 0.25s cubic-bezier(0.16,1,0.3,1)' }}>
            <style>{`@keyframes slideIn{from{transform:translateX(100%)}to{transform:translateX(0)}}`}</style>

            <div style={{ position: 'absolute', width: 200, height: 200, background: '#A5F3FC', borderRadius: '50%', filter: 'blur(60px)', top: -60, right: -60, opacity: 0.35, pointerEvents: 'none' }} />
            <div style={{ position: 'absolute', width: 160, height: 160, background: '#C7D2FE', borderRadius: '50%', filter: 'blur(50px)', top: 100, left: -40, opacity: 0.25, pointerEvents: 'none' }} />

            {/* Panel Header */}
            <div style={{ padding: 24, background: 'linear-gradient(135deg,#0F172A,#1E1B4B)', position: 'sticky', top: 0, zIndex: 10 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 12 }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '1.5px', marginBottom: 4 }}>Candidate Profile</p>
                  <h2 style={{ fontSize: 20, fontWeight: 800, color: 'white', letterSpacing: '-0.3px' }}>{selected.name || 'Unknown'}</h2>
                  {selected.current_designation && (
                    <p style={{ fontSize: 12, color: 'rgba(255,255,255,0.55)', marginTop: 3 }}>
                      {selected.current_designation}{selected.current_company ? ` · ${selected.current_company}` : ''}
                    </p>
                  )}
                </div>
                <button onClick={() => { setSelected(null); setEditing(false); }}
                  style={{ background: 'rgba(255,255,255,0.1)', border: 'none', color: 'white', width: 32, height: 32, borderRadius: 8, cursor: 'pointer', fontSize: 15, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>✕</button>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
                <span className={`status-pill ${sc(selected.parsing_status)}`}>{selected.parsing_status}</span>
                {selected.total_experience && <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.5)' }}>· {selected.total_experience} yrs</span>}
                {selected.accuracy_score !== null && selected.accuracy_score !== undefined && (
                  <span style={{ fontSize: 12, color: 'rgba(255,255,255,0.5)' }}>· Score: {selected.accuracy_score}/100</span>
                )}
              </div>

              {/* Missing Fields */}
              {selected.missing_fields?.length > 0 && (
                <div style={{ padding: '10px 14px', background: selected.parsing_status === 'Failed' ? 'rgba(236,72,153,0.15)' : 'rgba(245,158,11,0.15)', border: `1px solid ${selected.parsing_status === 'Failed' ? '#F9A8D4' : '#FCD34D'}`, borderRadius: 'var(--radius-sm)', marginBottom: 12 }}>
                  <p style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '1px', marginBottom: 6, color: selected.parsing_status === 'Failed' ? '#F9A8D4' : '#FCD34D' }}>⚠ Missing Fields</p>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                    {selected.missing_fields.map((f, i) => (
                      <span key={i} style={{ padding: '2px 8px', background: 'rgba(255,255,255,0.1)', border: `1px solid ${selected.parsing_status === 'Failed' ? '#F9A8D4' : '#FCD34D'}`, borderRadius: 'var(--radius-pill)', fontSize: 11, fontWeight: 600, color: selected.parsing_status === 'Failed' ? '#F9A8D4' : '#FCD34D' }}>{f}</span>
                    ))}
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                <button
                  onClick={() => editing ? setEditing(false) : startEdit()}
                  style={{ padding: '8px 16px', background: editing ? 'rgba(255,255,255,0.15)' : 'linear-gradient(135deg,#F59E0B,#FB923C)', border: 'none', borderRadius: 'var(--radius-pill)', color: 'white', fontSize: 12, fontWeight: 700, cursor: 'pointer' }}>
                  {editing ? '✕ Cancel Edit' : '✏ Edit'}
                </button>
                <button
                  onClick={async () => {
                    setReparsing(true);
                    try {
                      await axios.post(`${API_URL}/reparse/${selected.id}`);
                      showToast('Re-parsed successfully');
                      setSelected(null); fetchCandidates();
                    } catch { showToast('Re-parse failed', 'error'); }
                    finally { setReparsing(false); }
                  }}
                  style={{ padding: '8px 16px', background: 'linear-gradient(135deg,#6366F1,#8B5CF6)', border: 'none', borderRadius: 'var(--radius-pill)', color: 'white', fontSize: 12, fontWeight: 700, cursor: 'pointer', opacity: reparsing ? 0.6 : 1 }}>
                  {reparsing ? '⟳' : '↺'} Re-parse
                </button>
                <button
                  onClick={() => handleDelete(selected.id)}
                  style={{ padding: '8px 16px', background: 'rgba(239,68,68,0.2)', border: '1px solid rgba(239,68,68,0.4)', borderRadius: 'var(--radius-pill)', color: '#FCA5A5', fontSize: 12, fontWeight: 700, cursor: 'pointer' }}>
                  🗑 Delete
                </button>
              </div>
            </div>

            {/* Panel Body */}
            <div style={{ padding: 20, display: 'grid', gap: 20, position: 'relative', zIndex: 1 }}>

              {/* ── EDIT MODE ── */}
              {editing ? (
                <div>
                  <p className="section-label" style={{ marginBottom: 14 }}>Edit Candidate Details</p>
                  <div style={{ display: 'grid', gap: 12 }}>
                    {[
                      ['Name', 'name', 'text'],
                      ['Email', 'email', 'email'],
                      ['Phone', 'phone', 'text'],
                      ['Location', 'location', 'text'],
                      ['City', 'city', 'text'],
                      ['Country', 'country', 'text'],
                      ['LinkedIn', 'linkedin', 'text'],
                      ['GitHub', 'github', 'text'],
                      ['Total Experience (years)', 'total_experience', 'number'],
                      ['Current Company', 'current_company', 'text'],
                      ['Current Designation', 'current_designation', 'text'],
                    ].map(([label, field, type]) => (
                      <div key={field}>
                        <label style={{ ...labelStyle, color: 'var(--text-muted)' }}>{label}</label>
                        <input
                          type={type}
                          value={editData[field] || ''}
                          onChange={e => setEditData(prev => ({ ...prev, [field]: e.target.value }))}
                          style={editInputStyle}
                          onFocus={e => e.target.style.borderColor = 'var(--indigo)'}
                          onBlur={e => e.target.style.borderColor = 'rgba(99,102,241,0.3)'}
                        />
                      </div>
                    ))}

                    <div>
                      <label style={{ ...labelStyle, color: 'var(--text-muted)' }}>Skills (comma separated)</label>
                      <textarea
                        value={editData.skills || ''}
                        onChange={e => setEditData(prev => ({ ...prev, skills: e.target.value }))}
                        rows={3}
                        placeholder="Python, React, MongoDB, Docker..."
                        style={{ ...editInputStyle, resize: 'vertical', lineHeight: 1.6 }}
                        onFocus={e => e.target.style.borderColor = 'var(--indigo)'}
                        onBlur={e => e.target.style.borderColor = 'rgba(99,102,241,0.3)'}
                      />
                    </div>

                    <div>
                      <label style={{ ...labelStyle, color: 'var(--text-muted)' }}>Profile Summary</label>
                      <textarea
                        value={editData.profile_summary || ''}
                        onChange={e => setEditData(prev => ({ ...prev, profile_summary: e.target.value }))}
                        rows={4}
                        style={{ ...editInputStyle, resize: 'vertical', lineHeight: 1.6 }}
                        onFocus={e => e.target.style.borderColor = 'var(--indigo)'}
                        onBlur={e => e.target.style.borderColor = 'rgba(99,102,241,0.3)'}
                      />
                    </div>
                  </div>

                  <button
                    onClick={handleEditSave}
                    disabled={saving}
                    style={{ marginTop: 16, width: '100%', padding: '13px', background: 'linear-gradient(135deg,#10B981,#06B6D4)', border: 'none', borderRadius: 'var(--radius-pill)', color: 'white', fontSize: 14, fontWeight: 700, cursor: 'pointer', opacity: saving ? 0.6 : 1 }}>
                    {saving ? '⟳ Saving...' : '✓ Save Changes'}
                  </button>
                </div>

              ) : (
                /* ── VIEW MODE ── */
                <>
                  {/* Contact */}
                  <div>
                    <p className="section-label">Contact</p>
                    <div style={{ display: 'grid', gap: 8 }}>
                      {[
                        ['📧', 'Email', selected.email],
                        ['📱', 'Phone', selected.phone],
                        ['📍', 'Location', selected.location],
                        ['🔗', 'LinkedIn', selected.linkedin],
                        ['💻', 'GitHub', selected.github],
                        ['🌐', 'Portfolio', selected.portfolio],
                      ].filter(([,, v]) => v).map(([icon, label, val]) => (
                        <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px', background: 'rgba(255,255,255,0.7)', backdropFilter: 'blur(8px)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)' }}>
                          <span style={{ fontSize: 16, flexShrink: 0 }}>{icon}</span>
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <p style={{ fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.8px', color: 'var(--text-muted)' }}>{label}</p>
                            <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{val}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Skills */}
                  {selected.skills?.length > 0 && (
                    <div>
                      <p className="section-label">Skills ({selected.skills.length})</p>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 7 }}>
                        {selected.skills.map((s, i) => <span key={i} className="skill-tag">{s}</span>)}
                      </div>
                    </div>
                  )}

                  {/* Work Experience */}
                  {(selected.current_company || selected.previous_companies?.length > 0) && (
                    <div>
                      <p className="section-label">Work Experience</p>
                      {selected.current_company && (
                        <div style={{ padding: '12px 14px', background: 'rgba(255,255,255,0.7)', border: '1px solid var(--border)', borderLeft: '3px solid var(--green)', borderRadius: '0 var(--radius-sm) var(--radius-sm) 0', marginBottom: 8 }}>
                          <p style={{ fontSize: 11, color: 'var(--green)', fontWeight: 700, marginBottom: 2 }}>CURRENT</p>
                          <p style={{ fontSize: 13, fontWeight: 700 }}>{selected.current_company}</p>
                          {selected.current_designation && <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>{selected.current_designation}</p>}
                        </div>
                      )}
                      {selected.previous_companies?.map((company, i) => (
                        <div key={i} style={{ padding: '12px 14px', background: 'rgba(255,255,255,0.7)', border: '1px solid var(--border)', borderLeft: '3px solid var(--border)', borderRadius: '0 var(--radius-sm) var(--radius-sm) 0', marginBottom: 8 }}>
                          <p style={{ fontSize: 11, color: 'var(--text-muted)', fontWeight: 700, marginBottom: 2 }}>PREVIOUS</p>
                          <p style={{ fontSize: 13, fontWeight: 600 }}>{company}</p>
                          {selected.previous_designations?.[i] && <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>{selected.previous_designations[i]}</p>}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Education */}
                  {selected.education?.length > 0 && (
                    <div>
                      <p className="section-label">Education</p>
                      {selected.education.map((e, i) => (
                        <div key={i} style={{ padding: '12px 14px', background: 'rgba(255,255,255,0.7)', border: '1px solid var(--border)', borderLeft: '3px solid var(--indigo)', borderRadius: '0 var(--radius-sm) var(--radius-sm) 0', marginBottom: 8 }}>
                          <p style={{ fontSize: 13, fontWeight: 600 }}>{e.degree}</p>
                          {e.university && <p style={{ fontSize: 12, color: 'var(--text-soft)', marginTop: 2 }}>{e.university}</p>}
                          {e.specialization && <p style={{ fontSize: 12, color: 'var(--indigo)', marginTop: 2 }}>{e.specialization}</p>}
                          {e.year && <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>Year: {e.year}</p>}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Projects */}
                  {selected.projects?.length > 0 && (
                    <div>
                      <p className="section-label">Projects ({selected.projects.length})</p>
                      {selected.projects.map((p, i) => (
                        <div key={i} style={{ padding: '12px 14px', background: 'rgba(255,255,255,0.7)', border: '1px solid var(--border)', borderLeft: '3px solid var(--cyan)', borderRadius: '0 var(--radius-sm) var(--radius-sm) 0', marginBottom: 8 }}>
                          <p style={{ fontSize: 13, fontWeight: 700 }}>{p.name}</p>
                          {p.role && <p style={{ fontSize: 12, color: 'var(--text-soft)', marginTop: 2 }}>Role: {p.role}</p>}
                          {p.technologies && <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>{p.technologies}</p>}
                          {p.responsibilities && <p style={{ fontSize: 12, color: 'var(--text-soft)', marginTop: 4, lineHeight: 1.6 }}>{p.responsibilities}</p>}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Certifications */}
                  {selected.certifications?.length > 0 && (
                    <div>
                      <p className="section-label">Certifications</p>
                      {selected.certifications.map((c, i) => (
                        <div key={i} style={{ padding: '10px 12px', background: 'var(--amber-light)', border: '1px solid #FCD34D', borderRadius: 'var(--radius-sm)', marginBottom: 6 }}>
                          <p style={{ fontSize: 13, fontWeight: 600, color: 'var(--amber)' }}>🏅 {c.name}</p>
                          <div style={{ display: 'flex', gap: 12, marginTop: 3 }}>
                            {c.issuer && <p style={{ fontSize: 11, color: 'var(--amber)', fontWeight: 500 }}>{c.issuer}</p>}
                            {c.year && <p style={{ fontSize: 11, color: 'var(--amber)', fontWeight: 500 }}>{c.year}</p>}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Accuracy Score */}
                  {selected.accuracy_score != null && (
                    <div>
                      <p className="section-label">Parsing Accuracy</p>
                      <div style={{ padding: '14px 16px', background: 'rgba(255,255,255,0.7)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                          <p style={{ fontSize: 13, fontWeight: 700 }}>Score</p>
                          <p style={{ fontSize: 20, fontWeight: 800, color: selected.accuracy_score >= 75 ? 'var(--green)' : selected.accuracy_score >= 40 ? 'var(--amber)' : 'var(--pink)' }}>
                            {selected.accuracy_score}/100
                          </p>
                        </div>
                        <div style={{ height: 7, background: 'var(--border)', borderRadius: 999, overflow: 'hidden' }}>
                          <div style={{ height: '100%', width: `${selected.accuracy_score}%`, background: selected.accuracy_score >= 75 ? 'linear-gradient(135deg,#10B981,#06B6D4)' : selected.accuracy_score >= 40 ? 'linear-gradient(135deg,#F59E0B,#FB923C)' : 'linear-gradient(135deg,#EC4899,#EF4444)', borderRadius: 999, transition: 'width 0.5s ease' }} />
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Profile Summary */}
                  {selected.profile_summary && (
                    <div>
                      <p className="section-label">Profile Summary</p>
                      <div style={{ padding: 14, background: 'rgba(255,255,255,0.7)', backdropFilter: 'blur(8px)', border: '1px solid var(--border)', borderLeft: '3px solid var(--cyan)', borderRadius: '0 var(--radius-sm) var(--radius-sm) 0' }}>
                        <p style={{ fontSize: 13, color: 'var(--text-soft)', lineHeight: 1.8 }}>{selected.profile_summary}</p>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default CandidatesPage;

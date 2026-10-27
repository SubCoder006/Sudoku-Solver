import React from 'react';
import { Cpu, CheckCircle2, Clock, Hash } from 'lucide-react';

export default function SolverStats({ metrics }) {
  if (!metrics) return null;

  return (
    <div className="stats-grid">
      <div className="stat-card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Hash size={13} color="#a78bfa" />
          <span className="stat-label">Digits Detected</span>
        </div>
        <div className="stat-value highlight-violet">
          {metrics.digits_detected || 0}
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: '400' }}> / 81</span>
        </div>
      </div>

      <div className="stat-card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <CheckCircle2 size={13} color="#34d399" />
          <span className="stat-label">CNN Confidence</span>
        </div>
        <div className="stat-value highlight-emerald">
          {metrics.avg_confidence ? `${(metrics.avg_confidence * 100).toFixed(1)}%` : '—'}
        </div>
      </div>

      <div className="stat-card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Clock size={13} color="#67e8f9" />
          <span className="stat-label">Solve Duration</span>
        </div>
        <div className="stat-value highlight-cyan">
          {metrics.solve_time_ms !== undefined ? `${metrics.solve_time_ms} ms` : '—'}
        </div>
      </div>

      <div className="stat-card">
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Cpu size={13} color="#f59e0b" />
          <span className="stat-label">Search Nodes</span>
        </div>
        <div className="stat-value" style={{ color: '#fcd34d' }}>
          {metrics.nodes_explored !== undefined ? metrics.nodes_explored.toLocaleString() : '—'}
        </div>
      </div>
    </div>
  );
}

import React, { useState } from 'react';
import { Eye, Download, Layers, Sparkles, CheckCircle2, Maximize2 } from 'lucide-react';

export default function VisionInspector({ images, isProcessing, onDownload }) {
  const [activeTab, setActiveTab] = useState('augmented');
  const [fullscreen, setFullscreen] = useState(false);

  if (isProcessing) {
    return (
      <div className="vision-card glass-card" style={{ minHeight: '440px', justifyContent: 'center', alignItems: 'center' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px' }}>
          <div className="spinner spinner-lg" />
          <div style={{ textAlign: 'center' }}>
            <h3 style={{ fontSize: '1.15rem', fontWeight: '700', marginBottom: '6px' }}>
              Neural Computer Vision in Progress
            </h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
              Detecting contour corners, warping perspective & classifying digits...
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!images || (!images.original_b64 && !images.augmented_solution_b64)) {
    return (
      <div className="vision-card glass-card" style={{ minHeight: '440px', justifyContent: 'center', alignItems: 'center' }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px', opacity: 0.6 }}>
          <Layers size={48} color="#8b5cf6" />
          <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
            Upload or choose a sample puzzle to inspect computer vision steps
          </p>
        </div>
      </div>
    );
  }

  // Determine current image based on active tab
  let currentImageSrc = images.augmented_solution_b64 || images.warped_solution_b64 || images.original_b64;
  let currentTitle = 'Augmented Solution Overlay';

  if (activeTab === 'augmented' && images.augmented_solution_b64) {
    currentImageSrc = images.augmented_solution_b64;
    currentTitle = 'Augmented Solution (Unwarped onto Original Photo)';
  } else if (activeTab === 'warped_solution' && images.warped_solution_b64) {
    currentImageSrc = images.warped_solution_b64;
    currentTitle = 'Rectified Warped Solution Grid';
  } else if (activeTab === 'detected_corners' && images.detected_corners_b64) {
    currentImageSrc = images.detected_corners_b64;
    currentTitle = 'Detected 4-Corner Polygon';
  } else if (activeTab === 'warped' && images.warped_b64) {
    currentImageSrc = images.warped_b64;
    currentTitle = 'Perspective Rectified (900×900)';
  } else if (activeTab === 'original' && images.original_b64) {
    currentImageSrc = images.original_b64;
    currentTitle = 'Original Uploaded Photo';
  }

  return (
    <div className="vision-card glass-card">
      <div className="card-topbar">
        <div className="card-title">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h2>Vision & Overlay Inspector</h2>
            <span className="badge-glow badge-cyan">
              <Eye size={13} /> Multi-Stage CV
            </span>
          </div>
          <p>Inspect intermediate computer vision transforms and augmented projections</p>
        </div>

        {images.augmented_solution_b64 && (
          <button
            className="btn btn-emerald"
            onClick={() => onDownload(images.augmented_solution_b64, 'solved_sudoku_augmented.png')}
            style={{ fontSize: '0.82rem', padding: '6px 14px' }}
          >
            <Download size={14} />
            Download Overlay
          </button>
        )}
      </div>

      {/* Tab navigation for CV stages */}
      <div className="vision-tab-nav">
        {images.augmented_solution_b64 && (
          <button
            className={`vision-tab-btn ${activeTab === 'augmented' ? 'active' : ''}`}
            onClick={() => setActiveTab('augmented')}
          >
            <Sparkles size={13} /> AR Solution
          </button>
        )}
        {images.warped_solution_b64 && (
          <button
            className={`vision-tab-btn ${activeTab === 'warped_solution' ? 'active' : ''}`}
            onClick={() => setActiveTab('warped_solution')}
          >
            <CheckCircle2 size={13} /> Solved Grid
          </button>
        )}
        {images.detected_corners_b64 && (
          <button
            className={`vision-tab-btn ${activeTab === 'detected_corners' ? 'active' : ''}`}
            onClick={() => setActiveTab('detected_corners')}
          >
            Corners Polygon
          </button>
        )}
        {images.warped_b64 && (
          <button
            className={`vision-tab-btn ${activeTab === 'warped' ? 'active' : ''}`}
            onClick={() => setActiveTab('warped')}
          >
            Rectified Grid
          </button>
        )}
        {images.original_b64 && (
          <button
            className={`vision-tab-btn ${activeTab === 'original' ? 'active' : ''}`}
            onClick={() => setActiveTab('original')}
          >
            Raw Upload
          </button>
        )}
      </div>

      {/* Image display */}
      <div className="vision-image-display">
        <img
          src={currentImageSrc}
          alt={currentTitle}
          style={{ cursor: 'pointer' }}
          onClick={() => setFullscreen(true)}
          title="Click to view large"
        />
        <div className="vision-corner-tag">
          {currentTitle}
        </div>
      </div>

      {/* Fullscreen lightview modal if clicked */}
      {fullscreen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.88)',
            backdropFilter: 'blur(10px)',
            zIndex: 9999,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '24px'
          }}
          onClick={() => setFullscreen(false)}
        >
          <img
            src={currentImageSrc}
            alt={currentTitle}
            style={{
              maxWidth: '90vw',
              maxHeight: '85vh',
              objectFit: 'contain',
              borderRadius: '12px',
              boxShadow: '0 0 50px rgba(0,0,0,0.8)'
            }}
          />
          <p style={{ marginTop: '14px', color: '#94a3b8', fontSize: '0.85rem' }}>
            Click anywhere to close
          </p>
        </div>
      )}
    </div>
  );
}

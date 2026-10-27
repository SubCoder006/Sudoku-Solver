import React from 'react';
import { Play, Sparkles } from 'lucide-react';

export default function SampleGallery({ samples, onSelectSample, isProcessing }) {
  if (!samples || samples.length === 0) return null;

  return (
    <div className="sample-gallery">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ fontSize: '0.78rem', fontWeight: '600', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-secondary)' }}>
          Quick Test Presets
        </span>
        <span style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
          1-Click AI Recognition
        </span>
      </div>

      <div className="sample-cards-row">
        {samples.map((sample) => (
          <div
            key={sample.id}
            className="sample-card-item"
            onClick={() => !isProcessing && onSelectSample(sample)}
            title={`Load ${sample.name}`}
            style={{ opacity: isProcessing ? 0.6 : 1 }}
          >
            <div className="sample-card-thumb">
              <img
                src={`/api/sample-image/${sample.folder}/${sample.filename}`}
                alt={sample.name}
                loading="lazy"
              />
            </div>
            <div>
              <p>{sample.name}</p>
              <span>{sample.category}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

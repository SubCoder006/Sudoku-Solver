import React, { useRef, useState } from 'react';
import { UploadCloud, Image as ImageIcon, Camera } from 'lucide-react';

export default function ImageDropzone({ onFileSelected, isProcessing }) {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.type.startsWith('image/')) {
        onFileSelected(file);
      }
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      onFileSelected(e.target.files[0]);
    }
  };

  return (
    <div
      className={`dropzone ${isDragOver ? 'is-drag-over' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => fileInputRef.current?.click()}
    >
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept="image/png, image/jpeg, image/webp"
        style={{ display: 'none' }}
        disabled={isProcessing}
      />

      <div className="dropzone-icon-circle">
        <UploadCloud size={28} />
      </div>

      <div className="dropzone-text">
        <h3>Drop Sudoku Image Here</h3>
        <p>Supports PNG, JPG, or WEBP • High contrast works best</p>
      </div>

      <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
        <button
          type="button"
          className="btn btn-outline"
          style={{ fontSize: '0.8rem', padding: '6px 14px' }}
          onClick={(e) => {
            e.stopPropagation();
            fileInputRef.current?.click();
          }}
          disabled={isProcessing}
        >
          <ImageIcon size={14} /> Browse Photo
        </button>
      </div>
    </div>
  );
}

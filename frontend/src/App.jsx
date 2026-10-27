import React, { useState, useEffect, useCallback } from 'react';
import confetti from 'canvas-confetti';
import {
  BrainCircuit,
  Sparkles,
  AlertTriangle,
  RotateCcw,
  CheckCircle2,
  Copy,
  Download,
  Share2
} from 'lucide-react';

import SudokuBoard from './components/SudokuBoard';
import VisionInspector from './components/VisionInspector';
import ImageDropzone from './components/ImageDropzone';
import SampleGallery from './components/SampleGallery';
import SolverStats from './components/SolverStats';

const createEmptyGrid = () => Array(9).fill(0).map(() => Array(9).fill(0));

export default function App() {
  const [grid, setGrid] = useState(createEmptyGrid);
  const [originalGrid, setOriginalGrid] = useState(createEmptyGrid);
  const [solvedGrid, setSolvedGrid] = useState(null);
  const [conflicts, setConflicts] = useState([]);
  const [selectedCell, setSelectedCell] = useState([0, 0]);
  const [isSolving, setIsSolving] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSolved, setIsSolved] = useState(false);
  const [editMode, setEditMode] = useState(true);

  const [images, setImages] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [samples, setSamples] = useState([]);
  const [alert, setAlert] = useState(null);
  const [serverHealth, setServerHealth] = useState(null);

  // Load samples and check backend health on mount
  useEffect(() => {
    fetch('/api/health')
      .then((res) => res.json())
      .then((data) => setServerHealth(data))
      .catch((err) => console.warn('Backend not responding yet:', err));

    fetch('/api/samples')
      .then((res) => res.json())
      .then((data) => {
        if (data && data.samples) setSamples(data.samples);
      })
      .catch((err) => console.warn('Could not load samples:', err));
  }, []);

  // Validate grid conflicts whenever grid changes
  const checkConflicts = useCallback((currentGrid) => {
    fetch('/api/validate-grid', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ grid: currentGrid })
    })
      .then((res) => res.json())
      .then((data) => {
        setConflicts(data.conflicts || []);
      })
      .catch(() => {});
  }, []);

  // Change individual cell value
  const handleChangeCell = useCallback((r, c, val) => {
    setGrid((prev) => {
      const next = prev.map((row, rowIdx) =>
        rowIdx === r ? [...row.slice(0, c), val, ...row.slice(c + 1)] : row
      );
      checkConflicts(next);
      return next;
    });
    // Reset solved state if edited
    setIsSolved(false);
    setSolvedGrid(null);
  }, [checkConflicts]);

  // Process image from upload
  const handleProcessImage = async (file) => {
    setIsProcessing(true);
    setAlert(null);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/process-image', {
        method: 'POST',
        body: formData
      });

      const data = await res.json();
      if (!res.ok || !data.success) {
        setAlert({
          type: 'error',
          text: data.message || 'Image processing failed. Ensure grid is fully visible.'
        });
        setIsProcessing(false);
        return;
      }

      applyProcessResult(data);
    } catch (err) {
      setAlert({
        type: 'error',
        text: 'Network error communicating with Python backend.'
      });
    } finally {
      setIsProcessing(false);
    }
  };

  // Process sample preset
  const handleSelectSample = async (sample) => {
    setIsProcessing(true);
    setAlert(null);
    try {
      const res = await fetch(
        `/api/process-image?sample_folder=${encodeURIComponent(sample.folder)}&sample_file=${encodeURIComponent(sample.filename)}`,
        { method: 'POST' }
      );
      const data = await res.json();
      if (!res.ok || !data.success) {
        setAlert({
          type: 'error',
          text: data.message || 'Sample processing failed.'
        });
        setIsProcessing(false);
        return;
      }

      applyProcessResult(data);
    } catch (err) {
      setAlert({
        type: 'error',
        text: 'Error processing sample image.'
      });
    } finally {
      setIsProcessing(false);
    }
  };

  // Common handler when image detection returns
  const applyProcessResult = (data) => {
    const orig = data.original_grid;
    const solved = data.solved_grid;
    setOriginalGrid(orig);
    setGrid(solved || orig);
    setSolvedGrid(solved);
    setImages(data.images);
    setMetrics(data.metrics);
    setConflicts(data.conflicts || []);

    if (data.solve_success && solved) {
      setIsSolved(true);
      triggerConfetti();
      setAlert({
        type: 'success',
        text: `Sudoku recognized and solved in ${data.metrics?.solve_time_ms} ms!`
      });
    } else {
      setIsSolved(false);
      setAlert({
        type: 'error',
        text: 'Grid was recognized, but the puzzle could not be solved. Check for misclassified digits.'
      });
    }
  };

  // Solve the current interactive grid
  const handleSolveGrid = async () => {
    setIsSolving(true);
    setAlert(null);
    try {
      const res = await fetch('/api/solve-grid', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ grid })
      });
      const data = await res.json();

      if (!res.ok || !data.success) {
        setAlert({
          type: 'error',
          text: data.message || 'Puzzle cannot be solved. Check for duplicate numbers in row, col, or block.'
        });
        if (data.conflicts) setConflicts(data.conflicts);
        setIsSolving(false);
        return;
      }

      setSolvedGrid(data.solved_grid);
      setGrid(data.solved_grid);
      setIsSolved(true);
      setConflicts([]);
      setMetrics((prev) => ({
        ...prev,
        solve_time_ms: data.solve_time_ms,
        nodes_explored: data.nodes_explored
      }));

      triggerConfetti();
      setAlert({
        type: 'success',
        text: `Solved successfully in ${data.solve_time_ms} ms with ${data.nodes_explored} search nodes explored!`
      });
    } catch (err) {
      setAlert({
        type: 'error',
        text: 'Could not connect to solver API.'
      });
    } finally {
      setIsSolving(false);
    }
  };

  // Clear grid
  const handleClear = () => {
    const empty = createEmptyGrid();
    setGrid(empty);
    setOriginalGrid(empty);
    setSolvedGrid(null);
    setConflicts([]);
    setIsSolved(false);
    setImages(null);
    setMetrics(null);
    setAlert(null);
  };

  // Download image
  const handleDownloadImage = (b64, filename) => {
    const link = document.createElement('a');
    link.href = b64;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Copy grid to clipboard
  const handleCopyGrid = () => {
    const text = grid.map((r) => r.join(' ')).join('\n');
    navigator.clipboard.writeText(text);
    setAlert({ type: 'success', text: 'Grid matrix copied to clipboard!' });
  };

  const triggerConfetti = () => {
    confetti({
      particleCount: 80,
      spread: 70,
      origin: { y: 0.6 },
      colors: ['#8b5cf6', '#10b981', '#06b6d4', '#ec4899']
    });
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="app-header">
        <div className="logo-area">
          <div className="logo-icon-box">
            <BrainCircuit size={26} />
          </div>
          <div className="logo-title">
            <h1>Sudoku AI Solver</h1>
            <p>Computer Vision & Neural Backtracking Engine</p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {serverHealth && (
            <div className="header-status-badge">
              <span className="status-dot" />
              <span>{serverHealth.model_loaded ? 'CNN Ready' : 'Model Loading'}</span>
            </div>
          )}

          <button
            className="btn btn-outline"
            onClick={handleCopyGrid}
            title="Copy grid digits to clipboard"
            style={{ fontSize: '0.8rem', padding: '6px 12px' }}
          >
            <Copy size={14} /> Copy
          </button>
        </div>
      </header>

      {/* Alert Notification */}
      {alert && (
        <div className={`alert-box ${alert.type === 'error' ? 'alert-error' : 'alert-success'}`}>
          {alert.type === 'error' ? <AlertTriangle size={18} /> : <CheckCircle2 size={18} />}
          <span>{alert.text}</span>
        </div>
      )}

      {/* Real-time Metrics bar */}
      {metrics && <SolverStats metrics={metrics} />}

      {/* Main 2-Column Workbench */}
      <main className="workbench-grid">
        {/* Left Column: Interactive Sudoku Board */}
        <section className="board-container">
          <SudokuBoard
            grid={grid}
            originalGrid={originalGrid}
            solvedGrid={solvedGrid}
            conflicts={conflicts}
            selectedCell={selectedCell}
            onSelectCell={setSelectedCell}
            onChangeCell={handleChangeCell}
            onSolve={handleSolveGrid}
            onClear={handleClear}
            isSolving={isSolving}
            isSolved={isSolved}
            editMode={editMode}
            onToggleEditMode={() => setEditMode((prev) => !prev)}
          />
        </section>

        {/* Right Column: Vision Inspector, Upload Dropzone, Sample Presets */}
        <section style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Vision Inspector View */}
          <VisionInspector
            images={images}
            isProcessing={isProcessing}
            onDownload={handleDownloadImage}
          />

          {/* Upload Dropzone */}
          <div className="glass-card" style={{ padding: '20px' }}>
            <ImageDropzone
              onFileSelected={handleProcessImage}
              isProcessing={isProcessing}
            />

            {/* Quick 1-Click Samples */}
            <div style={{ marginTop: '18px' }}>
              <SampleGallery
                samples={samples}
                onSelectSample={handleSelectSample}
                isProcessing={isProcessing}
              />
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <div>
          <span>Sudoku AI Engine 2.0 • React + Vite • FastAPI • OpenCV • TensorFlow CNN</span>
        </div>
        <div>
          <span>Perspective Rectification & Deep Backtracking Solver</span>
        </div>
      </footer>
    </div>
  );
}

import React, { useEffect, useCallback } from 'react';
import { Sparkles, Edit3, Trash2, CheckCircle2 } from 'lucide-react';

export default function SudokuBoard({
  grid,
  originalGrid,
  solvedGrid,
  conflicts = [],
  selectedCell,
  onSelectCell,
  onChangeCell,
  onSolve,
  onClear,
  isSolving = false,
  isSolved = false,
  editMode = true,
  onToggleEditMode
}) {
  // Helper to test if cell is part of a conflict
  const isConflict = useCallback((r, c) => {
    return conflicts.some(item => item.row === r && item.col === c);
  }, [conflicts]);

  // Handle keyboard typing (1-9 and Backspace/Delete/0)
  const handleKeyDown = useCallback((e) => {
    if (!selectedCell) return;
    const [r, c] = selectedCell;

    if (e.key >= '1' && e.key <= '9') {
      e.preventDefault();
      onChangeCell(r, c, parseInt(e.key, 10));
    } else if (e.key === 'Backspace' || e.key === 'Delete' || e.key === '0') {
      e.preventDefault();
      onChangeCell(r, c, 0);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      onSelectCell([Math.max(0, r - 1), c]);
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      onSelectCell([Math.min(8, r + 1), c]);
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault();
      onSelectCell([r, Math.max(0, c - 1)]);
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      onSelectCell([r, Math.min(8, c + 1)]);
    }
  }, [selectedCell, onChangeCell, onSelectCell]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  const selRow = selectedCell ? selectedCell[0] : null;
  const selCol = selectedCell ? selectedCell[1] : null;

  return (
    <div className="sudoku-board-card glass-card">
      <div className="card-topbar" style={{ width: '100%' }}>
        <div className="card-title">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h2>Interactive 9×9 Matrix</h2>
            {isSolved && (
              <span className="badge-glow badge-emerald">
                <CheckCircle2 size={13} /> Solved
              </span>
            )}
          </div>
          <p>Click any cell to edit or navigate with arrow keys</p>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            className={`btn btn-outline ${editMode ? 'btn-active' : ''}`}
            onClick={onToggleEditMode}
            title="Toggle manual cell modification"
            style={{ fontSize: '0.8rem', padding: '6px 12px' }}
          >
            <Edit3 size={14} />
            {editMode ? 'Edit Mode On' : 'Edit Mode Off'}
          </button>
          <button
            className="btn btn-outline"
            onClick={onClear}
            title="Reset the grid"
            style={{ fontSize: '0.8rem', padding: '6px 12px' }}
          >
            <Trash2 size={14} />
            Clear
          </button>
        </div>
      </div>

      {/* The 9x9 Sudoku Board */}
      <div className="sudoku-board-wrapper">
        <div className="sudoku-board" role="grid" aria-label="Sudoku Grid">
          {grid.map((rowArr, r) =>
            rowArr.map((val, c) => {
              const isOrig = originalGrid && originalGrid[r] && originalGrid[r][c] !== 0;
              const isSolvedVal = solvedGrid && solvedGrid[r] && solvedGrid[r][c] !== 0 && !isOrig;
              const isSelected = selRow === r && selCol === c;
              const isCrosshair = selRow === r || selCol === c;
              const hasConflict = isConflict(r, c);

              // 3x3 block borders
              const rightBorder = (c + 1) % 3 === 0 && c !== 8;
              const bottomBorder = (r + 1) % 3 === 0 && r !== 8;

              let digitClass = '';
              if (hasConflict) digitClass = 'digit-conflict';
              else if (isOrig) digitClass = 'digit-original';
              else if (isSolvedVal) digitClass = 'digit-solved';
              else if (val !== 0) digitClass = 'digit-user';

              return (
                <div
                  key={`${r}-${c}`}
                  role="gridcell"
                  tabIndex={0}
                  className={`sudoku-cell 
                    ${rightBorder ? 'box-right-border' : ''} 
                    ${bottomBorder ? 'box-bottom-border' : ''} 
                    ${isSelected ? 'is-selected' : ''} 
                    ${isCrosshair && !isSelected ? 'crosshair-highlight' : ''} 
                    ${digitClass}
                  `}
                  onClick={() => onSelectCell([r, c])}
                  aria-selected={isSelected}
                  title={`Row ${r + 1}, Col ${c + 1}: ${val || 'Empty'}`}
                >
                  {val !== 0 ? val : ''}
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Quick Input Keypad */}
      <div className="numpad-row">
        {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((num) => (
          <button
            key={num}
            className="numpad-btn"
            onClick={() => {
              if (selectedCell) {
                onChangeCell(selectedCell[0], selectedCell[1], num);
              }
            }}
          >
            {num}
          </button>
        ))}
        <button
          className="numpad-btn numpad-erase"
          onClick={() => {
            if (selectedCell) {
              onChangeCell(selectedCell[0], selectedCell[1], 0);
            }
          }}
        >
          Erase (0)
        </button>
      </div>

      {/* Main Solve Button */}
      <div style={{ width: '100%', maxWidth: '460px', display: 'flex', gap: '10px' }}>
        <button
          className="btn btn-emerald"
          style={{ width: '100%', padding: '13px', fontSize: '1rem' }}
          onClick={onSolve}
          disabled={isSolving}
        >
          {isSolving ? (
            <>
              <div className="spinner" />
              <span>Solving with Backtracking...</span>
            </>
          ) : (
            <>
              <Sparkles size={18} />
              <span>Solve Grid Instantaneously</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
}

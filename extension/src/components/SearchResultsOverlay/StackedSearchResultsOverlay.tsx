import * as React from 'react';
import { useState } from 'react';
import { Summary, TaggedUrl } from '../../types/summary';
import StackedBarVisualization from './StackedBarComponents';

interface Props {
  summary: Summary;
  onClose: () => void;
}

const StackedSearchResultsOverlay: React.FC<Props> = ({ summary, onClose }) => {
  const [isMinimized, setIsMinimized] = useState(false);
  const [showRawData, setShowRawData] = useState(false);

  if (!summary) return null;

  return (
    <div className={`lessonlens_overlay ${isMinimized ? 'minimized' : ''}`}>
      <div className="overlay-header">
        <h3>Summary of Search Results</h3>
        <div className="button-group">
          <button onClick={() => setShowRawData(!showRawData)}>
            {showRawData ? 'Show Visualization' : 'Show Raw Data'}
          </button>
          <button onClick={() => setIsMinimized(!isMinimized)}>
            {isMinimized ? 'Expand' : 'Minimize'}
          </button>
          <button onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>
      </div>
      
      {!isMinimized && (
        <div className="overlay-content">
          {showRawData ? 
            <textarea
              className="results-textarea"
              value={JSON.stringify(summary, null, 2)}
              readOnly
            /> : <StackedBarVisualization data={summary} />}
        </div>
      )}
    </div>
  );
};

export default StackedSearchResultsOverlay;
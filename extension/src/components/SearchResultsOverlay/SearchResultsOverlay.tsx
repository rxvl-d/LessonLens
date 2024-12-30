import * as React from 'react';
import { useState } from 'react';
import { SummaryResult, SummaryV4, TaggedUrl } from '../../types/summary';
import { SunburstChart, SliceDescription, toTitleCase } from './SunburstComponents';
import { Box } from '@mui/material';

interface Props {
  summary: SummaryV4;
  onClose: () => void;
}

const SearchResultsOverlay: React.FC<Props> = ({ summary, onClose }) => {
  const [isMinimized, setIsMinimized] = useState(false);
  const [showRawData, setShowRawData] = useState(false);
  const [hoveredSliceInfo, setHoveredSliceInfo] = useState<{
    items: TaggedUrl[];
    path: Array<{ attribute: string; value: string }>;
    count: number;
  }>({
    items: summary.tagged_urls,
    path: [],
    count: summary.tagged_urls.length
  });

  if (!summary) return null;

  return (
    <div className={`lessonlens_overlay ${isMinimized ? 'minimized' : ''}`}>
      <div className="overlay-header">
        <h3>Summary of {toTitleCase(summary.query_type)}s</h3>
        <div className="button-group">
          <button onClick={() => setShowRawData(!showRawData)}>
            {showRawData ? 'Show Charts' : 'Show Raw Data'}
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
          {showRawData ? (
            <textarea
              className="results-textarea"
              value={JSON.stringify(summary, null, 2)}
              readOnly
            />
          ) : (
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
              <Box sx={{ width: '100%', maxWidth: 800, aspectRatio: '1/1' }}>
                <SunburstChart 
                  data={summary} 
                  onHover={(items, path, count) => 
                    setHoveredSliceInfo({ items, path, count })
                  } 
                />
              </Box>
              <Box sx={{ width: '100%', maxWidth: 800 }}>
                <SliceDescription 
                  count={hoveredSliceInfo.count}
                  path={hoveredSliceInfo.path}
                />
              </Box>
            </Box>
          )}
        </div>
      )}
    </div>
  );
};

export default SearchResultsOverlay;
import * as React from 'react';

interface DataPoint {
  name: string;
  value: number;
}

const BarChart: React.FC<{ data: DataPoint[] }> = ({ data }) => {
  const baseBarHeight = 24;
  const baseGap = 3;
  const width = 500;
  const labelWidth = 200;
  const chartWidth = width - labelWidth;
  const lineHeight = 14;
  const maxLines = 3;
  const maxCharsPerLine = 30;
  const barPadding = 8;

  const wrapText = (text: string): string[] => {
    const words = text.split(' ');
    const lines: string[] = [];
    let currentLine = '';
    
    for (const word of words) {
      const testLine = currentLine ? `${currentLine} ${word}` : word;
      if (testLine.length > maxCharsPerLine) {
        if (lines.length === maxLines - 1) {
          lines.push(currentLine ? `${currentLine} ${word}`.slice(0, maxCharsPerLine - 3) + '...' : word.slice(0, maxCharsPerLine - 3) + '...');
          break;
        } else {
          lines.push(currentLine);
          currentLine = word;
        }
      } else {
        currentLine = testLine;
      }
    }
    
    if (lines.length < maxLines && currentLine) {
      lines.push(currentLine);
    }
    
    return lines.slice(0, maxLines);
  };

  // Calculate positions and heights for all items
  const itemLayouts = data.map(item => {
    const lines = wrapText(item.name);
    const textHeight = lines.length * lineHeight;
    // Adaptive gap: more lines = more space
    // const gap = Math.max(baseGap, textHeight + barPadding * 2);
    // Constant gap
    const gap = baseGap + textHeight
    return {
      lines,
      textHeight,
      gap,
      totalHeight: baseBarHeight + gap
    };
  });

  // Calculate cumulative positions
  let currentY = 0;
  const positions = itemLayouts.map(layout => {
    const position = currentY;
    currentY += layout.totalHeight;
    return position;
  });

  const totalHeight = currentY;

  return (
    <svg 
      width="100%" 
      height={totalHeight} 
      style={{ maxWidth: width }}
    >
      {data.map((item, index) => {
        const layout = itemLayouts[index];
        const y = positions[index];
        // Center text block relative to bar
        const textBlockHeight = layout.lines.length * lineHeight;
        const textStartY = y + layout.gap/2 - textBlockHeight/2;

        return (
          <g key={item.name}>
            {/* Add a subtle guide line to connect text with bar */}
            <line 
              x1={labelWidth - 10}
              y1={y + baseBarHeight/2}
              x2={labelWidth - 5}
              y2={y + baseBarHeight/2}
              stroke="#e5e7eb"
              strokeWidth={1}
            />
            
            {/* Render wrapped text lines */}
            {layout.lines.map((line, lineIndex) => (
              <text
                key={`${item.name}-${lineIndex}`}
                x={0}
                y={textStartY + (lineIndex * lineHeight)}
                className="text-xs"
                dominantBaseline="hanging"
                style={{
                  fontSize: '12px',
                  fontFamily: 'system-ui, -apple-system, sans-serif'
                }}
              >
                {line}
              </text>
            ))}
            {/* Background bar */}
            <rect
              x={labelWidth}
              y={y + layout.gap/2 - baseBarHeight/2}
              width={chartWidth}
              height={baseBarHeight}
              fill="#e5e7eb"
              rx={4}
            />
            {/* Foreground bar */}
            <rect
              x={labelWidth}
              y={y + layout.gap/2 - baseBarHeight/2}
              width={Math.max((item.value / 100) * chartWidth, 0)}
              height={baseBarHeight}
              fill="#3b82f6"
              rx={4}
            />
            {/* Percentage text */}
            <text
              x={labelWidth + 10}
              y={y + layout.gap/2}
              dominantBaseline="middle"
              fill="white"
              className="text-sm font-medium"
              style={{
                fontSize: '12px',
                fontFamily: 'system-ui, -apple-system, sans-serif'
              }}
            >
              {item.value.toFixed(1)}%
            </text>
          </g>
        );
      })}
    </svg>
  );
};

export {DataPoint, BarChart};
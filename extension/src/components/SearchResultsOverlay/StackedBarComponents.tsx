import * as React from 'react';
import * as d3 from 'd3';
import { Summary, TaggedUrl, SummaryAllFields } from '../../types/summary';
import { Box, IconButton, Typography, Tooltip } from '@mui/material';

// Constants 
const PASTEL_COLORS = [
  '#FFB3BA', // Pastel Red/Pink
  '#BAFFC9', // Pastel Green
  '#BAE1FF', // Pastel Blue
  '#FFFFBA', // Pastel Yellow
  '#FFB3F7', // Pastel Purple
  '#E0BBE4'  // Pastel Lavender
];

// Types
interface AttributeData {
  attribute: string;
  importance: number;
  segments: MergedSegment[] | AggregatedSegment[];
}

interface MergedSegment {
  value: string;
  startIndex: number;
  length: number;
  urls: string[];
  confidences: number[];
}

interface AggregatedSegment {
  value: string;
  count: number;
  percentage: number;
  confidences: number[];
}

// Helper Functions
const getSegmentColors = (baseColor: string, numSegments: number): string[] => {
  const baseHsl = d3.hsl(baseColor);
  return Array.from({ length: numSegments }, (_, i) => {
    const hue = ((baseHsl.h || 0) + (i * 60 / numSegments)) % 360;
    return d3.hsl(hue, baseHsl.s, baseHsl.l).toString();
  });
};

const truncateText = (text: string, maxWidth: number, fontSize: number = 12): string => {
  const approxCharWidth = fontSize * 0.6; // Approximate width of a character
  const maxChars = Math.floor(maxWidth / approxCharWidth);
  if (text.length > maxChars) {
    return text.slice(0, maxChars - 3) + '...';
  }
  return text;
};

// Confidence Bar Component
const ConfidenceBar: React.FC<{ confidences: number[] }> = ({ confidences }) => {
  const avgConfidence = d3.mean(confidences) || 0;
  const normalizedConfidence = Math.round(avgConfidence * 100);
  const filledBlocks = Math.floor(normalizedConfidence / 20);

  const getColor = (level: number) => {
    if (level >= 4) return '#4CAF50';
    if (level >= 3) return '#8BC34A';
    if (level >= 2) return '#FFEB3B';
    if (level >= 1) return '#FF9800';
    return '#F44336';
  };

  return (
    <Tooltip title={`Confidence: ${normalizedConfidence}%`}>
      <div style={{ 
        width: '20px', 
        display: 'flex', 
        flexDirection: 'column-reverse', 
        gap: '2px',
        height: '40px',
        justifyContent: 'center'
      }}>
        {Array.from({ length: 5 }, (_, i) => (
          <div
            key={i}
            style={{
              width: '20px',
              height: '6px',
              backgroundColor: i < filledBlocks ? getColor(filledBlocks) : '#e0e0e0',
              borderRadius: '2px',
            }}
          />
        ))}
      </div>
    </Tooltip>
  );
};

// Aligned View Component
const AlignedView: React.FC<{ data: AttributeData[] }> = ({ data }) => {
  const dimensions = {
    width: 800,
    barHeight: 40,
    labelWidth: 180,
    confidenceWidth: 40,
    margin: { top: 20, right: 50, bottom: 20, left: 180 },
    gap: 2,
  };

  const innerWidth = (dimensions.width - dimensions.margin.left - dimensions.margin.right);
  const totalSegments = data[0]?.segments.length || 1;
  const segmentBaseWidth = (innerWidth - ((totalSegments - 1) * dimensions.gap)) / totalSegments / 3.0;

  return (
    <svg 
      width={dimensions.width} 
      height={(data.length * (dimensions.barHeight + 20)) + dimensions.margin.top + dimensions.margin.bottom}
    >
      <g transform={`translate(${dimensions.margin.left},${dimensions.margin.top})`}>
        {data.map((attrData, attrIndex) => {
          const baseColor = PASTEL_COLORS[attrIndex % PASTEL_COLORS.length];
          const segmentColors = getSegmentColors(baseColor, attrData.segments.length);
          const y = attrIndex * (dimensions.barHeight + 20);

          return (
            <g key={attrData.attribute}>
              {/* Attribute Label */}
              <text
                x={-10}
                y={y + dimensions.barHeight / 2}
                textAnchor="end"
                dominantBaseline="middle"
                fontSize="12px"
              >
                {formatAttributeName(attrData.attribute)}
              </text>

              {/* Segments */}
              {(attrData.segments as MergedSegment[]).map((segment, segIndex) => {
                const x = segment.startIndex * (segmentBaseWidth + dimensions.gap);
                const width = (segment.length * segmentBaseWidth) - dimensions.gap;
                
                const displayText = truncateText(
                  segment.value, 
                  width - 10, 
                  12
                );

                return (
                  <Tooltip 
                    key={`${attrData.attribute}-${segIndex}`}
                    title={segment.value}
                  >
                    <g>
                      <rect
                        x={x}
                        y={y}
                        width={width}
                        height={dimensions.barHeight}
                        fill={segmentColors[segIndex]}
                        opacity={0.8}
                        stroke="#fff"
                        strokeWidth={1}
                      />
                      <text
                        x={x + width / 2}
                        y={y + dimensions.barHeight / 2}
                        textAnchor="middle"
                        dominantBaseline="middle"
                        fill="black"
                        fontSize="12px"
                      >
                        {displayText}
                      </text>
                    </g>
                  </Tooltip>
                );
              })}

              {/* Confidence Bar */}
              <foreignObject
                x={innerWidth + 10}
                y={y}
                width={dimensions.confidenceWidth}
                height={dimensions.barHeight}
              >
                <ConfidenceBar 
                  confidences={(attrData.segments as MergedSegment[])
                    .flatMap(segment => segment.confidences)} 
                />
              </foreignObject>
            </g>
          );
        })}
      </g>
    </svg>
  );
};

// Aggregated View Component
const AggregatedView: React.FC<{ data: AttributeData[] }> = ({ data }) => {
  const dimensions = {
    width: 800,
    barHeight: 40,
    labelWidth: 180,
    confidenceWidth: 40,
    margin: { top: 20, right: 50, bottom: 20, left: 180 },
    gap: 2,
  };

  const innerWidth = dimensions.width - dimensions.margin.left - dimensions.margin.right;

  return (
    <svg 
      width={dimensions.width} 
      height={(data.length * (dimensions.barHeight + 20)) + dimensions.margin.top + dimensions.margin.bottom}
    >
      <g transform={`translate(${dimensions.margin.left},${dimensions.margin.top})`}>
        {data.map((attrData, attrIndex) => {
          const baseColor = PASTEL_COLORS[attrIndex % PASTEL_COLORS.length];
          const segmentColors = getSegmentColors(baseColor, attrData.segments.length);
          const y = attrIndex * (dimensions.barHeight + 20);

          let cumulativeX = 0;

          return (
            <g key={attrData.attribute}>
              {/* Attribute Label */}
              <text
                x={-10}
                y={y + dimensions.barHeight / 2}
                textAnchor="end"
                dominantBaseline="middle"
                fontSize="12px"
              >
                {formatAttributeName(attrData.attribute)}
              </text>

              {/* Segments */}
              {(attrData.segments as AggregatedSegment[]).map((segment, segIndex) => {
                const width = (segment.percentage / 100) * innerWidth - dimensions.gap;
                const x = cumulativeX;
                cumulativeX += width + dimensions.gap;

                const displayText = truncateText(
                  `${segment.value} (${segment.percentage.toFixed(1)}%)`,
                  width - 10,
                  12
                );

                return (
                  <Tooltip 
                    key={`${attrData.attribute}-${segIndex}`}
                    title={`${segment.value} (${segment.percentage.toFixed(1)}%)`}
                  >
                    <g>
                      <rect
                        x={x}
                        y={y}
                        width={width}
                        height={dimensions.barHeight}
                        fill={segmentColors[segIndex]}
                        opacity={0.8}
                        stroke="#fff"
                        strokeWidth={1}
                      />
                      <text
                        x={x + width / 2}
                        y={y + dimensions.barHeight / 2}
                        textAnchor="middle"
                        dominantBaseline="middle"
                        fill="black"
                        fontSize="12px"
                      >
                        {displayText}
                      </text>
                    </g>
                  </Tooltip>
                );
              })}

              {/* Confidence Bar */}
              <foreignObject
                x={innerWidth + 10}
                y={y}
                width={dimensions.confidenceWidth}
                height={dimensions.barHeight}
              >
                <ConfidenceBar 
                  confidences={(attrData.segments as AggregatedSegment[])
                    .flatMap(segment => segment.confidences)}
                />
              </foreignObject>
            </g>
          );
        })}
      </g>
    </svg>
  );
};

// Helper function for formatting attribute names
const formatAttributeName = (attr: string): string => {
  return attr
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
};

// Container component remains the same
const StackedBarVisualization: React.FC<{ data: Summary }> = ({ data }) => {
  const [viewMode, setViewMode] = React.useState<'aligned' | 'aggregated'>('aligned');
  
  const transformedData = React.useMemo(() => {
    return viewMode === 'aligned' 
      ? transformDataAligned(data)
      : transformDataAggregated(data);
  }, [data, viewMode]);

  return (
    <Box sx={{ position: 'relative', mt: 4 }}>
      <Box sx={{ 
        position: 'absolute', 
        right: 0, 
        top: -40, 
        display: 'flex', 
        gap: 1,
        zIndex: 1
      }}>
        <IconButton 
          onClick={() => setViewMode('aligned')}
          color={viewMode === 'aligned' ? 'primary' : 'default'}
        >
          <Typography variant="body2">Each Result</Typography>
        </IconButton>
        <IconButton 
          onClick={() => setViewMode('aggregated')}
          color={viewMode === 'aggregated' ? 'primary' : 'default'}
        >
          <Typography variant="body2">All Results</Typography>
        </IconButton>
      </Box>
      
      {viewMode === 'aligned' 
        ? <AlignedView data={transformedData} />
        : <AggregatedView data={transformedData} />
      }
    </Box>
  );
};

function transformDataAligned(data: Summary): AttributeData[] {
  const sortedAttributes = [...SummaryAllFields].sort((a, b) => {
    const aImp = data.attribute_importances.find(ai => ai.attribute === a)?.importance || 0;
    const bImp = data.attribute_importances.find(ai => ai.attribute === b)?.importance || 0;
    return bImp - aImp;
  });

  const results = data.tagged_urls;
  const similarityGroups = groupBySimilarity(results);

  return sortedAttributes.map(attr => {
    const rawSegments = similarityGroups.map((result, index) => ({
      value: result[attr].label,
      confidence: result[attr].confidence,
      url: result.url,
      index
    }));

    const mergedSegments: MergedSegment[] = [];
    let currentSegment: MergedSegment | null = null;

    rawSegments.forEach((segment, index) => {
      if (!currentSegment) {
        currentSegment = {
          value: segment.value,
          startIndex: index,
          length: 1,
          urls: [segment.url],
          confidences: [segment.confidence]
        };
      } else if (currentSegment.value === segment.value) {
        currentSegment.length++;
        currentSegment.urls.push(segment.url);
        currentSegment.confidences.push(segment.confidence);
      } else {
        mergedSegments.push(currentSegment);
        currentSegment = {
          value: segment.value,
          startIndex: index,
          length: 1,
          urls: [segment.url],
          confidences: [segment.confidence]
        };
      }
    });

    if (currentSegment) {
      mergedSegments.push(currentSegment);
    }

    return {
      attribute: attr,
      importance: data.attribute_importances.find(ai => ai.attribute === attr)?.importance || 0,
      segments: mergedSegments
    };
  });
}

function transformDataAggregated(data: Summary): AttributeData[] {
  const sortedAttributes = [...SummaryAllFields].sort((a, b) => {
    const aImp = data.attribute_importances.find(ai => ai.attribute === a)?.importance || 0;
    const bImp = data.attribute_importances.find(ai => ai.attribute === b)?.importance || 0;
    return bImp - aImp;
  });

  return sortedAttributes.map(attr => {
    const valueMap = new Map<string, { count: number; confidences: number[] }>();
    const totalResults = data.tagged_urls.length;

    // Count occurrences of each value
    data.tagged_urls.forEach(result => {
      const value = result[attr].label;
      const confidence = result[attr].confidence;
      
      if (!valueMap.has(value)) {
        valueMap.set(value, { count: 1, confidences: [confidence] });
      } else {
        const current = valueMap.get(value)!;
        current.count++;
        current.confidences.push(confidence);
      }
    });

    // Convert to array and sort by count
    const segments: AggregatedSegment[] = Array.from(valueMap.entries())
      .map(([value, data]) => ({
        value,
        count: data.count,
        percentage: (data.count / totalResults) * 100,
        confidences: data.confidences
      }))
      .sort((a, b) => a.count - b.count);

    return {
      attribute: attr,
      importance: data.attribute_importances.find(ai => ai.attribute === attr)?.importance || 0,
      segments
    };
  });
}

function groupBySimilarity(results: TaggedUrl[]): TaggedUrl[] {
  const sorted = [...results];
  sorted.sort((a, b) => {
    let matches = 0;
    SummaryAllFields.forEach(field => {
      if (a[field].label === b[field].label) matches++;
    });
    return matches;
  });
  return sorted;
}


export default StackedBarVisualization;
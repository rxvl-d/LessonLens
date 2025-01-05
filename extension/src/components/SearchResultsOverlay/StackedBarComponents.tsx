import * as React from 'react';
import * as d3 from 'd3';
import { Summary, TaggedUrl, SummaryAllFields } from '../../types/summary';
import { Box } from '@mui/material';

interface StackedBarVisualizationProps {
  data: Summary;
}

interface MergedSegment {
  value: string;
  startIndex: number;
  length: number;
  urls: string[];
  confidences: number[];
}

interface AttributeData {
  attribute: string;
  importance: number;
  segments: MergedSegment[];
}

function transformData(data: Summary): AttributeData[] {
  // Sort attributes by importance
  const sortedAttributes = [...SummaryAllFields].sort((a, b) => {
    const aImp = data.attribute_importances.find(ai => ai.attribute === a)?.importance || 0;
    const bImp = data.attribute_importances.find(ai => ai.attribute === b)?.importance || 0;
    return bImp - aImp;
  });

  // Group results by similarity
  const results = data.tagged_urls;
  const similarityGroups = groupBySimilarity(results);

  // Create data structure for each attribute with merged segments
  return sortedAttributes.map(attr => {
    const rawSegments = similarityGroups.map((result, index) => ({
      value: result[attr].label,
      confidence: result[attr].confidence,
      url: result.url,
      index
    }));

    // Merge adjacent segments with same value
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

// Group results by similarity (number of matching attributes)
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

const StackedBarVisualization: React.FC<StackedBarVisualizationProps> = ({ data }) => {
  const svgRef = React.useRef<SVGSVGElement>(null);
  const tooltipRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (!svgRef.current || !tooltipRef.current) return;

    // Clear previous content
    d3.select(svgRef.current).selectAll("*").remove();

    const transformedData = transformData(data);
    
    // Setup dimensions
    const width = 800;
    const height = 400;
    const margin = { top: 20, right: 120, bottom: 20, left: 180 };
    const barHeight = 40;
    const confidenceBarWidth = 40;
    const innerWidth = width - margin.left - margin.right;
    const tooltipPadding = 4;

    // Create SVG
    const svg = d3.select(svgRef.current)
      .attr("viewBox", [0, 0, width, height])
      .attr("width", width)
      .attr("height", height);

    // Create tooltip
    const tooltip = d3.select(tooltipRef.current)
      .style("position", "absolute")
      .style("visibility", "hidden")
      .style("background", "white")
      .style("border", "1px solid #ddd")
      .style("border-radius", "4px")
      .style("padding", "8px")
      .style("font-size", "12px");

    // Create scales
    const xScale = d3.scaleLinear()
      .domain([0, data.tagged_urls.length])
      .range([0, innerWidth]);

    // Base colors for each attribute (matching sunburst)
    const baseColors = [
      '#FFB3BA', // Pastel Red/Pink
      '#BAFFC9', // Pastel Green
      '#BAE1FF', // Pastel Blue
      '#FFFFBA', // Pastel Yellow
      '#FFB3F7', // Pastel Purple
    ];

    // Create color scales for each attribute
    const colorScales = baseColors.map(baseColor => 
      d3.scaleLinear<string>()
        .domain([0, 10]) // Assuming max 10 different values per attribute
        .range([d3.rgb(baseColor).brighter(0.1), d3.rgb(baseColor).darker(0.5)])
        .interpolate(d3.interpolateHcl)
    );

    // Color scale for confidence bars
    const confidenceColorScale = d3.scaleSequential()
      .domain([0, 1])
      .interpolator(d3.interpolateRgb("#ff4444", "#44ff44"));

    // Create container for bars
    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // Draw bars for each attribute
    transformedData.forEach((attrData, attrIndex) => {
      const y = attrIndex * (barHeight + 20);
      const colorScale = colorScales[attrIndex % colorScales.length];

      // Draw attribute label
      g.append("text")
        .attr("x", -10)
        .attr("y", y + barHeight / 2)
        .attr("text-anchor", "end")
        .attr("dominant-baseline", "middle")
        .text(formatAttributeName(attrData.attribute));

      // Get unique values for this attribute to assign consistent colors
      const uniqueValues = Array.from(new Set(attrData.segments.map(s => s.value)));

      // Draw merged segments
      attrData.segments.forEach((segment, segmentIndex) => {
        const x = xScale(segment.startIndex);
        const width = xScale(segment.length) - 2; // 2px gap

        // Draw segment rectangle
        const rect = g.append("rect")
          .attr("x", x)
          .attr("y", y)
          .attr("width", width)
          .attr("height", barHeight)
          .attr("fill", colorScale(uniqueValues.indexOf(segment.value)))
          .attr("stroke", "#fff")
          .attr("stroke-width", 1);

        // Add segment label
        const label = g.append("text")
          .attr("x", x + width / 2)
          .attr("y", y + barHeight / 2)
          .attr("text-anchor", "middle")
          .attr("dominant-baseline", "middle")
          .attr("fill", "black")
          .attr("font-size", "12px")
          .text(segment.value);

        // Check if label fits
        const labelWidth = (label.node() as SVGTextElement).getComputedTextLength();
        if (labelWidth > width - tooltipPadding * 2) {
          label.text(truncateText(segment.value, width - tooltipPadding * 2));
          
          // Add hover behavior
          rect.on("mouseover", (event) => {
            const pt = svg.node().createSVGPoint();
            pt.x = event.clientX;
            pt.y = event.clientY;
            const svgP = pt.matrixTransform(svg.node().getScreenCTM().inverse());
        
            tooltip
                .style("visibility", "visible")
                .style("left", `${svgP.x + 10}px`)
                .style("top", `${svgP.y - 10}px`)
                .html(`${segment.value}<br/>(${segment.length} results)`);
          })
          .on("mouseout", () => {
            tooltip.style("visibility", "hidden");
          });
        }
      });

      // Draw confidence bar
      const meanConfidence = d3.mean(attrData.segments.flatMap(s => s.confidences)) || 0;
      const confidenceBar = g.append("rect")
        .attr("x", innerWidth + 10)
        .attr("y", y)
        .attr("width", confidenceBarWidth)
        .attr("height", barHeight)
        .attr("fill", confidenceColorScale(meanConfidence))
        .attr("stroke", "#fff")
        .attr("stroke-width", 1);

      // Add confidence hover behavior
      confidenceBar.on("mouseover", (event) => {
        const confidenceText = attrData.segments
          .map(s => `${s.value} (${s.length} results): ${Math.round(d3.mean(s.confidences)! * 100)}% confidence`)
          .join("\n");
        
        tooltip
          .style("visibility", "visible")
          .style("left", `${event.pageX + 10}px`)
          .style("top", `${event.pageY - 10}px`)
          .style("white-space", "pre-line")
          .html(confidenceText);
      })
      .on("mouseout", () => {
        tooltip.style("visibility", "hidden");
      });
    });

  }, [data]);

  return (
    <Box sx={{ position: 'relative', width: '100%', height: '100%' }}>
      <svg ref={svgRef} />
      <div ref={tooltipRef} />
    </Box>
  );
};

// Helper function to format attribute names
function formatAttributeName(attr: string): string {
  return attr
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

// Helper function to truncate text with ellipsis
function truncateText(text: string, width: number): string {
  const ellipsis = '...';
  const textWidth = getTextWidth(text);
  
  if (textWidth <= width) return text;
  
  const ratio = width / textWidth;
  const truncLength = Math.floor((text.length * ratio) - ellipsis.length);
  return text.slice(0, truncLength) + ellipsis;
}

// Helper function to estimate text width
function getTextWidth(text: string): number {
  return text.length * 7;
}

export default StackedBarVisualization;
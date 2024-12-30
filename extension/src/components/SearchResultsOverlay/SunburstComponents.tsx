import { useEffect, useRef } from 'react';
import * as React from 'react';
import * as d3 from 'd3';
import { Typography, Box } from '@mui/material';
import { SummaryV4, TaggedUrl, SummaryAllFields, AttributeImportance } from '../../types/summary';

interface SunburstChartProps {
  data: SummaryV4;
  onHover?: (items: TaggedUrl[], path: Array<{ attribute: string, value: string }>, count: number) => void;
}

// Get all attributes except 'url'
const allAttributes = SummaryAllFields;

function transformData(data: SummaryV4) {
  // Sort attributes by importance
  const attrImportanceMap = new Map(
    data.attribute_importances.map(ai => [ai.attribute, ai.importance])
  );
  
  const sortedAttributes = [...allAttributes].sort((a, b) => 
    (attrImportanceMap.get(b) || 0) - (attrImportanceMap.get(a) || 0)
  );

  function buildHierarchy(items: TaggedUrl[], attrs: string[], level = 0) {
    if (level >= attrs.length) {
      return null;
    }

    const currentAttr = attrs[level];
    
    // Handle values as strings or arrays of strings
    const getValues = (item: TaggedUrl, attr: string): string[] => {
      const value = item[attr];
      if (value === undefined || value === null) {
        return [];
      }
      if (Array.isArray(value)) {
        return value.map(String);
      }
      return [String(value)];
    };

    // Count occurrences of each value, skipping empty arrays
    const valueCounts = new Map<string, TaggedUrl[]>();
    items.forEach(item => {
      const values = getValues(item, currentAttr);
      if (values.length > 0) {  // Only process items that have this attribute
        values.forEach(value => {
          if (!valueCounts.has(value)) {
            valueCounts.set(value, []);
          }
          valueCounts.get(value)?.push(item);
        });
      }
    });

    // If no values were found for this attribute, skip to next level
    if (valueCounts.size === 0) {
      return buildHierarchy(items, attrs, level + 1);
    }

    // Convert to array and sort by count
    return Array.from(valueCounts.entries())
      .map(([value, matchingItems]) => {
        const node = {
          name: value,
        };

        if (level === attrs.length - 1) {
          return {
            ...node,
            value: matchingItems.length,
            items: matchingItems
          };
        } else {
          const children = buildHierarchy(matchingItems, attrs, level + 1);
          return children ? {
            ...node,
            children
          } : {
            ...node,
            value: matchingItems.length,
            items: matchingItems
          };
        }
      })
      .filter(node => node.value > 0 || (node.children && node.children.length > 0));
  }

  return {
    name: "root",
    children: buildHierarchy(data.tagged_urls, sortedAttributes)
  };
}


export const SunburstChartNew: React.FC<SunburstChartProps> = ({ data, onHover }) => {
  const svgRef = useRef<SVGSVGElement>(null);
  
  useEffect(() => {
    if (!svgRef.current) return;

    // Clear previous content
    d3.select(svgRef.current).selectAll("*").remove();

    // Setup dimensions
    const margin = { top: 40, right: 40, bottom: 40, left: 70 };
    const width = 800 - margin.left - margin.right;
    const height = 400 - margin.top - margin.bottom;

    // Process data to get combinations
    const combinations = new Map();
    data.tagged_urls.forEach(url => {
      const key = [
        url.includes_analogies,
        url.visualization_tools,
        url.curriculum_alignment
      ].join('|');
      
      if (!combinations.has(key)) {
        combinations.set(key, {
          values: [
            url.includes_analogies,
            url.visualization_tools,
            url.curriculum_alignment
          ],
          urls: [url],
          count: 1
        });
      } else {
        const existing = combinations.get(key);
        existing.urls.push(url);
        existing.count++;
      }
    });

    // Convert to array and sort by count
    const combinationsArray = Array.from(combinations.entries())
      .map(([key, value]) => ({
        id: key,
        ...value
      }))
      .sort((a, b) => b.count - a.count);

    // Create SVG
    const svg = d3.select(svgRef.current)
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // Attributes we're visualizing
    const attributes = ['includes_analogies', 'visualization_tools', 'curriculum_alignment'];
    const attributeLabels = ['Analogies', 'Visualizations', 'Curriculum'];

    // Create scales
    const xScale = d3.scaleBand()
      .domain(attributes)
      .range([0, width])
      .padding(0.1);

    const yScale = d3.scaleBand()
      .domain(combinationsArray.map(d => d.id))
      .range([0, height])
      .padding(0.1);

    // Color scale for the circles
    const colorScale = d3.scaleOrdinal()
      .domain(['Includes Analogies', 'Includes Visualization Tools', 'Includes Curriculum Alignment'])
      .range(['#4299e1', '#48bb78', '#ed64a6']);

    // Draw attribute labels
    svg.selectAll(".attribute-label")
      .data(attributeLabels)
      .join("text")
      .attr("class", "attribute-label")
      .attr("x", (d, i) => xScale(attributes[i])! + xScale.bandwidth() / 2)
      .attr("y", -10)
      .attr("text-anchor", "middle")
      .text(d => d)
      .style("font-size", "16px");

    // Create rows for each combination
    const rows = svg.selectAll(".combination-row")
      .data(combinationsArray)
      .join("g")
      .attr("class", "combination-row")
      .attr("transform", d => `translate(0,${yScale(d.id)})`)
      .on("mouseenter", (event, d) => {
        const path = d.values.map((value, i) => ({
          attribute: attributes[i],
          value: value
        }));
        onHover?.(d.urls, path, d.count);
      });

    // Add count labels
    rows.append("text")
      .attr("x", -10)
      .attr("y", yScale.bandwidth() / 2)
      .attr("dy", "0.35em")
      .attr("text-anchor", "end")
      .text(d => `${d.count} URLs`)
      .style("font-size", "12px");

    // Add circles for each attribute
    rows.selectAll("circle")
      .data(d => d.values.map((value, i) => ({
        value,
        attribute: attributes[i]
      })))
      .join("circle")
      .attr("cx", d => xScale(d.attribute)! + xScale.bandwidth() / 2)
      .attr("cy", yScale.bandwidth() / 2)
      .attr("r", yScale.bandwidth() / 3)
      .attr("fill", d => 
        d.value.startsWith('Includes') ? colorScale(d.value) : "#e2e8f0"
      )
      .attr("stroke", d => 
        d.value.startsWith('Includes') ? d3.rgb(colorScale(d.value)).darker(0.5) : "#cbd5e0"
      )
      .attr("stroke-width", 1);

    // Add background hover areas
    rows.insert("rect", ":first-child")
      .attr("x", -margin.left)
      .attr("width", width + margin.left)
      .attr("height", yScale.bandwidth())
      .attr("fill", "transparent")
      .attr("class", "hover-area")
      .on("mouseenter", function() {
        d3.select(this.parentNode).select(".combination-background")
          .attr("opacity", 0.1);
      })
      .on("mouseleave", function() {
        d3.select(this.parentNode).select(".combination-background")
          .attr("opacity", 0);
      });

    rows.insert("rect", ":first-child")
      .attr("class", "combination-background")
      .attr("x", -margin.left)
      .attr("width", width + margin.left)
      .attr("height", yScale.bandwidth())
      .attr("fill", "#000")
      .attr("opacity", 0);

  }, [data, onHover]);

  return (
    <svg 
      ref={svgRef} 
      className="w-full h-full"
      style={{ minHeight: "400px" }}
    />
  );
};


export const SunburstChart: React.FC<SunburstChartProps> = ({ data, onHover }) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const width = 800;
  const height = 800;
  const radius = width / 2;

  useEffect(() => {
    if (!svgRef.current) return;

    // Clear previous content
    d3.select(svgRef.current).selectAll("*").remove();

    const svg = d3.select(svgRef.current)
      .attr("viewBox", [-width / 2, -height / 2, width, width])
      .style("font", "10px sans-serif");

    // Create distinct colors for each layer using pastel rainbow spectrum
    const baseColors = [
      '#FFB3BA', // Pastel Red/Pink
      '#BAFFC9', // Pastel Green
      '#BAE1FF', // Pastel Blue
      '#FFFFBA', // Pastel Yellow
      '#FFB3F7', // Pastel Purple
      '#E0BBE4'  // Pastel Lavender
    ];


    // Create color scales for each level with more saturated variations
    const colorScales = baseColors.map(baseColor => 
      d3.scaleLinear<string>()
        .domain([0, 1])
        .range([d3.rgb(baseColor).brighter(0.1), d3.rgb(baseColor).darker(0.5)])
        .interpolate(d3.interpolateHcl)
    );

    const partition = (data: any) => d3.partition()
      .size([2 * Math.PI, radius])
      (d3.hierarchy(data)
        .sum((d: any) => d.value || 0)
        .sort((a: any, b: any) => b.value - a.value));

    const arc = d3.arc()
      .startAngle((d: any) => d.x0)
      .endAngle((d: any) => d.x1)
      .padAngle((d: any) => Math.min((d.x1 - d.x0) / 2, 0.005))
      .padRadius(radius / 2)
      .innerRadius((d: any) => d.y0)
      .outerRadius((d: any) => d.y1 - 1);

    const root = partition(transformData(data));

    // Sort attributes by importance
    const sortedAttributes = [...allAttributes].sort((a, b) => {
      const aImp = data.attribute_importances.find(ai => ai.attribute === a)?.importance || 0;
      const bImp = data.attribute_importances.find(ai => ai.attribute === b)?.importance || 0;
      return bImp - aImp;
    });

    function getMatchingItemsAndPath(node: any): { 
      items: TaggedUrl[], 
      path: Array<{ attribute: string, value: string }> 
    } {
      const path: Array<{ attribute: string, value: string }> = [];
      let currentNode = node;
      
      while (currentNode && currentNode.parent && currentNode.parent.data.name !== "root") {
        path.unshift({
          attribute: sortedAttributes[currentNode.depth - 1],
          value: currentNode.data.name
        });
        currentNode = currentNode.parent;
      }
    
      if (node.data.items) {
        return { 
          items: node.data.items,
          path 
        };
      }
      
      const items = new Set<TaggedUrl>();
      node.descendants().forEach((d: any) => {
        if (d.data.items) {
          d.data.items.forEach((item: TaggedUrl) => items.add(item));
        }
      });
      
      return { 
        items: Array.from(items),
        path 
      };
    }

    svg.append("g")
      .attr("fill-opacity", 0.8)
      .selectAll("path")
      .data(root.descendants().slice(1))
      .join("path")
      .attr("fill", (d: any) => {
        const depth = d.depth - 1;
        const colorScale = colorScales[depth];
        const siblings = d.parent.children;
        const index = siblings.indexOf(d);
        return colorScale(index / siblings.length);
      })
      .attr("d", arc as any)
      .on("mouseover", (_: any, d: any) => {
        const result = getMatchingItemsAndPath(d);
        onHover?.(result.items, result.path, result.items.length);
      });

      svg.append("g")
      .attr("pointer-events", "none")
      .attr("text-anchor", "middle")
      .attr("font-size", "15px")
      .selectAll("text")
      .data(root.descendants().slice(1))
      .join("text")
      .attr("transform", (d: any) => {
        const x = (d.x0 + d.x1) / 2 * 180 / Math.PI;
        const y = (d.y0 + d.y1) / 2;
        return `rotate(${x - 90}) translate(${y},0) rotate(270)`;
      })
      .attr("dy", "0.25em")
      .text((d: any) => formatLabel(sortedAttributes[d.depth - 1], d.data.name));

  }, [data, onHover]);

  return <svg ref={svgRef} className="w-full h-full" />;
};

export const URLList: React.FC<{ items: TaggedUrl[] }> = ({ items }) => {
  return (
    <Box sx={{ bgcolor: '#f9fafb', p: 3, borderRadius: 2, maxHeight: 800, overflow: 'auto' }}>
      {items.map((item, index) => (
        <Box key={index} sx={{ mb: 2, pb: 2, borderBottom: '1px solid #e5e7eb' }}>
          <Typography variant="body2" component="a" href={item.url} target="_blank" sx={{ color: 'text.secondary', '&:hover': { color: 'primary.main' } }}>
            {item.url}
          </Typography>
        </Box>
      ))}
    </Box>
  );
};

interface SliceDescriptionProps {
  count: number;
  path: Array<{
    attribute: string;
    value: string;
  }>;
}

function formatLabel(attribute: string, value: string): string {
  return toTitleCase(value);
}

export const toTitleCase = (str: string) => {
  str = str.replace('private ', '')
  str = str.replace(' foundation', '')
  str = str.replace('undarstufe', '.')
  return str
    .split(/[\s_]+/)
    .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
};


export const SliceDescription: React.FC<SliceDescriptionProps> = ({ count, path }) => {
  const formatAttribute = (attr: string): string => {
    return toTitleCase(attr.replace(/_/g, ' '));
  };

  const buildDescription = (): string => {
    if (path.length === 0) return '';

    let description = `${count} result${count !== 1 ? 's' : ''} `;

    const pathDescription = path.map(({ attribute, value }) => 
      `${formatAttribute(attribute)}: ${toTitleCase(value)}`
    ).join(', ');

    return `${description}with ${pathDescription}`;
  };

  return (
    <Box sx={{ 
      mt: 4,
      p: 3, 
      bgcolor: 'background.paper',
      borderRadius: 2,
      boxShadow: 1
    }}>
      <Typography variant="body1" sx={{ mt: 2 }}>
        {buildDescription()}
      </Typography>
    </Box>
  );
};


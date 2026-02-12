import { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import type { RelationshipEdge } from '../types';

interface Props {
  relationships: RelationshipEdge[];
}

interface D3Node extends d3.SimulationNodeDatum {
  id: string;
  type: string;
  label: string;
}

interface D3Link extends d3.SimulationLinkDatum<D3Node> {
  relationship: string;
}

const typeColors: Record<string, string> = {
  person: '#00d4ff',
  email: '#ffaa00',
  domain: '#00ff88',
  ip: '#ff3b3b',
  organization: '#c084fc',
  entity: '#64748b',
};

export default function NetworkGraph({ relationships }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 600, height: 300 });

  useEffect(() => {
    if (!containerRef.current) return;
    const obs = new ResizeObserver((entries) => {
      const { width, height } = entries[0].contentRect;
      setDimensions({ width, height: Math.max(height, 300) });
    });
    obs.observe(containerRef.current);
    return () => obs.disconnect();
  }, []);

  useEffect(() => {
    if (!svgRef.current || relationships.length === 0) return;

    const { width, height } = dimensions;
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    // Build nodes and links from relationships
    const nodesMap = new Map<string, D3Node>();
    const links: D3Link[] = [];

    relationships.forEach((rel) => {
      if (!nodesMap.has(rel.source)) {
        nodesMap.set(rel.source, {
          id: rel.source,
          type: rel.source_type,
          label: rel.source.length > 20 ? rel.source.slice(0, 20) + '…' : rel.source,
        });
      }
      if (!nodesMap.has(rel.target)) {
        nodesMap.set(rel.target, {
          id: rel.target,
          type: rel.target_type,
          label: rel.target.length > 20 ? rel.target.slice(0, 20) + '…' : rel.target,
        });
      }
      links.push({
        source: rel.source,
        target: rel.target,
        relationship: rel.relationship,
      });
    });

    const nodes = Array.from(nodesMap.values());

    // Simulation
    const simulation = d3
      .forceSimulation(nodes)
      .force(
        'link',
        d3.forceLink<D3Node, D3Link>(links).id((d) => d.id).distance(90)
      )
      .force('charge', d3.forceManyBody().strength(-200))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(30));

    // Links
    const link = svg
      .append('g')
      .selectAll('line')
      .data(links)
      .enter()
      .append('line')
      .attr('stroke', '#243056')
      .attr('stroke-width', 1.5)
      .attr('stroke-opacity', 0.6);

    // Nodes
    const node = svg
      .append('g')
      .selectAll('g')
      .data(nodes)
      .enter()
      .append('g')
      .call(
        d3.drag<SVGGElement, D3Node>()
          .on('start', (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on('drag', (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on('end', (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          })
      );

    node
      .append('circle')
      .attr('r', 8)
      .attr('fill', (d) => typeColors[d.type] || typeColors.entity)
      .attr('stroke', '#0a0e1a')
      .attr('stroke-width', 2);

    node
      .append('text')
      .text((d) => d.label)
      .attr('x', 12)
      .attr('y', 4)
      .attr('fill', '#94a3b8')
      .attr('font-size', '10px')
      .attr('font-family', 'JetBrains Mono, monospace');

    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      node.attr('transform', (d: any) => `translate(${d.x},${d.y})`);
    });

    return () => {
      simulation.stop();
    };
  }, [relationships, dimensions]);

  if (relationships.length === 0) {
    return (
      <div className="h-64 bg-navy-700 rounded-lg flex items-center justify-center text-gray-500 text-sm">
        No relationship data available
      </div>
    );
  }

  return (
    <div ref={containerRef} className="h-72 bg-navy-900/50 rounded-lg overflow-hidden border border-navy-600">
      <svg ref={svgRef} width={dimensions.width} height={dimensions.height} />
      {/* Legend */}
      <div className="flex gap-4 px-3 py-2 flex-wrap">
        {Object.entries(typeColors).filter(([k]) => k !== 'entity').map(([type, color]) => (
          <div key={type} className="flex items-center gap-1.5 text-xs text-gray-500">
            <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
            {type}
          </div>
        ))}
      </div>
    </div>
  );
}

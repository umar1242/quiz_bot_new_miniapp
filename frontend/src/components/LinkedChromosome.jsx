import React from 'react';

export default function LinkedChromosome({ genotype, scale = 1 }) {
  if (!genotype) return null;
  
  const isSingle = !genotype.includes('/');
  const [leftStr, rightStr] = genotype.split('/');
  const leftGenes = leftStr ? leftStr.split('.') : [];
  const rightGenes = rightStr ? rightStr.split('.') : [];
  
  const count = Math.max(leftGenes.length, rightGenes.length);
  const height = 50 + count * 28;
  const width = isSingle ? 66 : 90;
  
  const line1TopX = isSingle ? 40 : 34;
  const line1BotX = isSingle ? 30 : 24;
  const line2TopX = 66;
  const line2BotX = 56;
  
  const yStart = 14;
  const yEnd = height - 14;
  
  const getX = (y, topX, botX) => {
    const ratio = (y - yStart) / (yEnd - yStart);
    return topX - ratio * (topX - botX);
  };
  
  return (
    <div style={{ 
      display: 'inline-flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      transform: `scale(${scale})`,
      transformOrigin: 'center',
      margin: '0 4px',
      overflow: 'visible'
    }}>
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} style={{ overflow: 'visible' }}>
        <g stroke="var(--text-secondary)" strokeWidth="2.5" strokeLinecap="round">
          <line x1={line1TopX} y1={yStart} x2={line1BotX} y2={yEnd} />
          {!isSingle && <line x1={line2TopX} y1={yStart} x2={line2BotX} y2={yEnd} />}
        </g>
        
        {Array.from({ length: count }).map((_, i) => {
          const y = yStart + ((yEnd - yStart) * (i + 1)) / (count + 1);
          const x1 = getX(y, line1TopX, line1BotX);
          const x2 = !isSingle ? getX(y, line2TopX, line2BotX) : 0;
          
          return (
            <g key={i}>
              <line x1={x1 - 5} y1={y} x2={x1 + 5} y2={y} stroke="var(--text-secondary)" strokeWidth="2.5" />
              {!isSingle && <line x1={x2 - 5} y1={y} x2={x2 + 5} y2={y} stroke="var(--text-secondary)" strokeWidth="2.5" />}
              
              <text 
                x={x1 - 8} y={y} 
                fill="var(--accent-primary)" 
                fontSize="16" 
                fontFamily="monospace"
                fontWeight="bold"
                textAnchor="end"
                dominantBaseline="central"
              >
                {leftGenes[i] || ''}
              </text>
              {!isSingle && (
                <text 
                  x={x2 + 8} y={y} 
                  fill="var(--accent-primary)" 
                  fontSize="16" 
                  fontFamily="monospace"
                  fontWeight="bold"
                  textAnchor="start"
                  dominantBaseline="central"
                >
                  {rightGenes[i] || ''}
                </text>
              )}
            </g>
          );
        })}
      </svg>
    </div>
  );
}

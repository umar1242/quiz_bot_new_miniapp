import React from 'react';
import { 
  determinePhenotype, 
  determineLinkedPhenotype, 
  determineEpistasisPhenotype,
  determineComplementaryPhenotype,
  determinePolymeriaPhenotype,
  determineBloodGroupPhenotype,
  determinePleiotropyPhenotype,
  getLinkedRadical, 
  getMendelianRadical, 
  getPhenotypicRadical, 
  formatPercent,
  normalizeGenotype 
} from '../utils/genetics';
import LinkedChromosome from './LinkedChromosome';

export default function PunnettGrid({ 
  gametes1, gametes2, grid, genotypeRatios, phenotypeRatios, traitNames, crossType, specialType, options,
  gametesProbs1, gametesProbs2, cellProbs, totalOffspring 
}) {
  const phenotypes = Array.from(phenotypeRatios.keys());
  
  const totalCells = Array.from(genotypeRatios.values()).reduce((a, b) => a + b, 0);
  const isProb = totalCells <= 1.01;

  const resolveCellPheno = (cellGenotype) => {
    if (crossType === 'linked') {
      return determineLinkedPhenotype(cellGenotype, traitNames);
    }
    const sType = specialType || crossType;
    if (sType === 'epistasis') {
      return determineEpistasisPhenotype(cellGenotype, options?.epistasisMode, traitNames);
    }
    if (sType === 'complementary') {
      return determineComplementaryPhenotype(cellGenotype, options?.compMode, traitNames);
    }
    if (sType === 'polymeria') {
      return determinePolymeriaPhenotype(cellGenotype, options?.isCumulative, traitNames);
    }
    if (sType === 'blood') {
      return determineBloodGroupPhenotype(cellGenotype);
    }
    if (sType === 'pleiotropy') {
      return determinePleiotropyPhenotype(cellGenotype, options?.lethalGenotype, traitNames);
    }
    return determinePhenotype(cellGenotype, traitNames);
  };

  const isLethalCell = (cellGenotype) => {
    if (!options?.lethalGenotype) return false;
    const lG = options.lethalGenotype;
    return cellGenotype === lG || normalizeGenotype(cellGenotype) === normalizeGenotype(lG);
  };

  const phenoToRadicalMap = new Map();
  if (grid) {
    for (let i = 0; i < grid.length; i++) {
      for (let j = 0; j < grid[i].length; j++) {
        const cellGenotype = grid[i][j];
        if (isLethalCell(cellGenotype)) continue;
        const pheno = resolveCellPheno(cellGenotype);
        const rad = crossType === 'linked'
          ? getLinkedRadical(cellGenotype)
          : getMendelianRadical(cellGenotype);
        if (pheno && rad && !phenoToRadicalMap.has(pheno)) {
          phenoToRadicalMap.set(pheno, rad);
        }
      }
    }
  }
  
  const getPhenoColor = (phenotype, cellGenotype) => {
    if (cellGenotype && isLethalCell(cellGenotype)) {
      return 'rgba(255, 77, 77, 0.2)';
    }
    const count = phenotypeRatios.get(phenotype);
    if (!count) return 'rgba(255, 255, 255, 0.05)';
    const allCounts = Array.from(phenotypeRatios.values());
    const maxCount = allCounts.length > 0 ? Math.max(...allCounts) : 1;
    const ratio = isProb ? count : (maxCount > 0 ? count / maxCount : 0);
    
    const index = phenotypes.indexOf(phenotype);
    const hues = [275, 220, 320, 240, 190, 0];
    const baseHue = index >= 0 ? hues[index % hues.length] : 275;
    
    const lightness = 75 - (ratio * 30); 
    
    return `hsla(${baseHue}, 85%, ${lightness}%, 0.25)`;
  };

  const getPhenoBaseColor = (phenotype) => {
    const count = phenotypeRatios.get(phenotype);
    if (!count) return 'hsl(275, 90%, 65%)';
    const allCounts = Array.from(phenotypeRatios.values());
    const maxCount = allCounts.length > 0 ? Math.max(...allCounts) : 1;
    const ratio = isProb ? count : (maxCount > 0 ? count / maxCount : 0);
    
    const index = phenotypes.indexOf(phenotype);
    const hues = [275, 220, 320, 240, 190, 0];
    const baseHue = index >= 0 ? hues[index % hues.length] : 275;
    
    const lightness = 75 - (ratio * 30);
    return `hsl(${baseHue}, 90%, ${lightness}%)`;
  };

  return (
    <div>
      <div className="punnett-wrapper">
        <table className="punnett-grid">
          <thead>
            <tr>
              <th>♀ \ ♂</th>
              {gametes2.map((g, i) => (
                <th key={i}>
                  {crossType === 'linked' ? (
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '4px' }}>
                      <LinkedChromosome genotype={g} scale={0.9} />
                      {gametesProbs2 && gametesProbs2[i] && (
                        <span style={{ fontSize: '0.75rem', color: 'var(--accent-secondary)', marginTop: '2px' }}>
                          {formatPercent(gametesProbs2[i].prob)}
                        </span>
                      )}
                    </div>
                  ) : g}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {gametes1.map((g1, i) => (
              <tr key={i}>
                <th>
                  {crossType === 'linked' ? (
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '4px' }}>
                      <LinkedChromosome genotype={g1} scale={0.9} />
                      {gametesProbs1 && gametesProbs1[i] && (
                        <span style={{ fontSize: '0.75rem', color: 'var(--accent-secondary)', marginTop: '2px' }}>
                          {formatPercent(gametesProbs1[i].prob)}
                        </span>
                      )}
                    </div>
                  ) : g1}
                </th>
                {gametes2.map((g2, j) => {
                  const cellGenotype = grid[i][j];
                  const pheno = resolveCellPheno(cellGenotype);
                  const lethal = isLethalCell(cellGenotype);
                  const probVal = cellProbs && cellProbs[i] ? cellProbs[i][j] : null;
                  return (
                    <td
                      key={j}
                      style={{ 
                        backgroundColor: getPhenoColor(pheno, cellGenotype),
                        border: lethal ? '2px dashed #ff4d4d' : undefined,
                        opacity: lethal ? 0.7 : 1
                      }}
                      title={lethal ? '☠️ Летальный генотип' : pheno}
                    >
                      {crossType === 'linked' ? (
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '4px' }}>
                          <LinkedChromosome genotype={cellGenotype} scale={0.9} />
                          {probVal !== null && (
                            <span style={{ fontSize: '0.8rem', fontWeight: 'bold', color: 'var(--text-primary)', marginTop: '2px' }}>
                              {formatPercent(probVal)}
                            </span>
                          )}
                        </div>
                      ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                          <span style={{ textDecoration: lethal ? 'line-through' : 'none' }}>{cellGenotype}</span>
                          {lethal && <span style={{ fontSize: '0.75rem', color: '#ff6b6b', fontWeight: 'bold' }}>☠️ Летальный</span>}
                        </div>
                      )}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="section-title">Генотипическое расщепление</div>
      {!isProb && <div className="card-desc">Всего комбинаций: {totalCells}</div>}
      <ul className="ratio-list">
        {Array.from(genotypeRatios.entries()).map(([genotype, count]) => (
          <li key={genotype} className="ratio-item">
            <span style={{ fontFamily: 'monospace', fontSize: '1.1rem' }}>
              {crossType === 'linked' ? <LinkedChromosome genotype={genotype} scale={1.0} /> : genotype}
            </span>
            {isProb ? (
              <span style={{ fontWeight: '600', color: 'var(--accent-primary)' }}>
                {formatPercent(count)}
              </span>
            ) : (
              <span>{count} / {totalCells} ({Math.round((count / totalCells) * 100)}%)</span>
            )}
          </li>
        ))}
      </ul>

      <div className="section-title">Фенотипическое расщепление</div>
      <ul className="ratio-list">
        {Array.from(phenotypeRatios.entries()).map(([phenotype, count]) => {
          const percentage = isProb ? count * 100 : (count / totalCells) * 100;
          const radical = phenoToRadicalMap.get(phenotype) || getPhenotypicRadical(phenotype, traitNames);
          const individCount = totalOffspring ? Math.round(isProb ? count * totalOffspring : (count / totalCells) * totalOffspring) : null;
          
          return (
            <li key={phenotype} className="ratio-item" style={{ flexDirection: 'column', alignItems: 'stretch' }}>
              <div className="flex-between">
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                  <span style={{ fontWeight: '600', fontSize: '1rem' }}>{phenotype}</span>
                  {radical && (
                    <span style={{ 
                      fontFamily: 'monospace', 
                      fontSize: '0.9rem', 
                      background: 'rgba(138, 43, 226, 0.25)', 
                      border: '1.5px solid var(--accent-primary)',
                      color: '#e0aaff', 
                      padding: '2px 10px', 
                      borderRadius: '6px',
                      fontWeight: 'bold',
                      letterSpacing: '1px'
                    }}>
                      {radical}
                    </span>
                  )}
                </div>

                <span style={{ fontWeight: 600, color: getPhenoBaseColor(phenotype) }}>
                  {individCount !== null ? (
                    `${individCount.toLocaleString('ru-RU')} особей (${formatPercent(isProb ? count : count / totalCells)})`
                  ) : isProb ? (
                    `${formatPercent(count)} (p = ${parseFloat(count.toFixed(6))})`
                  ) : (
                    `${count} (${Math.round(percentage)}%)`
                  )}
                </span>
              </div>
              <div className="ratio-bar-container" style={{ marginTop: '8px' }}>
                <div 
                  className="ratio-bar" 
                  style={{ 
                    width: `${percentage}%`,
                    backgroundColor: getPhenoBaseColor(phenotype) 
                  }} 
                />
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

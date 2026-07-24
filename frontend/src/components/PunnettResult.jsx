import React from 'react';
import PunnettGrid from './PunnettGrid';
import { 
  determinePhenotype, 
  determineLinkedPhenotype, 
  determineEpistasisPhenotype,
  determineComplementaryPhenotype,
  determinePolymeriaPhenotype,
  determineBloodGroupPhenotype,
  determinePleiotropyPhenotype,
  formatPercent 
} from '../utils/genetics';
import LinkedChromosome from './LinkedChromosome';

export default function PunnettResult({ data, onBack, onNewCross }) {
  if (!data) return null;

  const { 
    parent1, parent2, traitNames, gametes1, gametes2, grid, genotypeRatios, phenotypeRatios, 
    crossType, specialType, options, gametesProbs1, gametesProbs2, cellProbs, totalOffspring 
  } = data;

  const resolvePheno = (genotype) => {
    if (crossType === 'linked') {
      return determineLinkedPhenotype(genotype, traitNames);
    }
    const sType = specialType || crossType;
    if (sType === 'epistasis') {
      return determineEpistasisPhenotype(genotype, options?.epistasisMode, traitNames);
    }
    if (sType === 'complementary') {
      return determineComplementaryPhenotype(genotype, options?.compMode, traitNames);
    }
    if (sType === 'polymeria') {
      return determinePolymeriaPhenotype(genotype, options?.isCumulative, traitNames);
    }
    if (sType === 'blood') {
      return determineBloodGroupPhenotype(genotype);
    }
    if (sType === 'pleiotropy') {
      return determinePleiotropyPhenotype(genotype, options?.lethalGenotype, traitNames);
    }
    return determinePhenotype(genotype, traitNames);
  };

  const pheno1 = resolvePheno(parent1);
  const pheno2 = resolvePheno(parent2);

  const handleSendToTelegram = () => {
    if (window.Telegram && window.Telegram.WebApp) {
      // Format data to send back to bot
      const textResult = `
Решетка Пеннета: ${parent1} x ${parent2}

Родители:
♀: ${parent1} (${pheno1})
♂: ${parent2} (${pheno2})

Расщепление по фенотипу:
${Array.from(phenotypeRatios.entries()).map(([p, c]) => `- ${p}: ${c}`).join('\n')}
      `.trim();
      
      fetch('/api/send-result', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Init-Data': window.Telegram.WebApp.initData
        },
        body: JSON.stringify({ text: textResult })
      }).then(() => {
        window.Telegram.WebApp.close();
      }).catch(console.error);
    }
  };

  return (
    <>
      <button className="btn btn-back" onClick={onBack}>← Изменить данные</button>

      <div className="card">
        <h2 className="card-title">Результат скрещивания</h2>
        
        <div className="section-title">Родители (P)</div>
        <div style={{ marginBottom: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <strong>♀:</strong> 
            {crossType === 'linked' ? <LinkedChromosome genotype={parent1} scale={0.95} /> : <span style={{ fontFamily: 'monospace' }}>{parent1}</span>}
            <span style={{ color: 'var(--text-secondary)' }}>— {pheno1}</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '8px' }}>
            <strong>♂:</strong> 
            {crossType === 'linked' ? <LinkedChromosome genotype={parent2} scale={0.95} /> : <span style={{ fontFamily: 'monospace' }}>{parent2}</span>}
            <span style={{ color: 'var(--text-secondary)' }}>— {pheno2}</span>
          </div>
        </div>

        <div className="section-title">Гаметы (G)</div>
        <div style={{ marginBottom: '16px' }}>
          <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '12px' }}>
            <strong>♀:</strong> 
            {crossType === 'linked' ? (
              gametesProbs1 ? gametesProbs1.map((gp, i) => (
                <div key={i} style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', background: 'rgba(0,0,0,0.15)', padding: '4px 6px', borderRadius: '8px' }}>
                  <LinkedChromosome genotype={gp.gamete} scale={0.9} />
                  <span style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--accent-primary)' }}>{formatPercent(gp.prob)}</span>
                  {gp.type && <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>{gp.type}</span>}
                </div>
              )) : gametes1.map((g, i) => <LinkedChromosome key={i} genotype={g} scale={0.9} />)
            ) : <span style={{ fontFamily: 'monospace' }}>{gametes1.join(', ')}</span>}
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '12px', marginTop: '12px' }}>
            <strong>♂:</strong> 
            {crossType === 'linked' ? (
              gametesProbs2 ? gametesProbs2.map((gp, i) => (
                <div key={i} style={{ display: 'inline-flex', flexDirection: 'column', alignItems: 'center', background: 'rgba(0,0,0,0.15)', padding: '4px 6px', borderRadius: '8px' }}>
                  <LinkedChromosome genotype={gp.gamete} scale={0.9} />
                  <span style={{ fontSize: '0.8rem', fontWeight: '600', color: 'var(--accent-primary)' }}>{formatPercent(gp.prob)}</span>
                  {gp.type && <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>{gp.type}</span>}
                </div>
              )) : gametes2.map((g, i) => <LinkedChromosome key={i} genotype={g} scale={0.9} />)
            ) : <span style={{ fontFamily: 'monospace' }}>{gametes2.join(', ')}</span>}
          </div>
        </div>

        <PunnettGrid 
          gametes1={gametes1}
          gametes2={gametes2}
          grid={grid}
          genotypeRatios={genotypeRatios}
          phenotypeRatios={phenotypeRatios}
          traitNames={traitNames}
          crossType={crossType}
          specialType={specialType}
          options={options}
          gametesProbs1={gametesProbs1}
          gametesProbs2={gametesProbs2}
          cellProbs={cellProbs}
          totalOffspring={totalOffspring}
        />

        <div style={{ display: 'flex', gap: '12px', marginTop: '24px' }}>
          <button className="btn btn-primary" onClick={handleSendToTelegram}>
            📤 Отправить в Telegram
          </button>
          <button className="btn btn-secondary" onClick={onNewCross} style={{ width: 'auto' }}>
            🔄
          </button>
        </div>
      </div>
    </>
  );
}

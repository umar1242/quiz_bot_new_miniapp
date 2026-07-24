import React, { useState } from 'react';
import LinkedChromosome from './LinkedChromosome';

export default function LinkedGenotypeInput({ onSubmit, onBack }) {
  const [geneCount, setGeneCount] = useState(2);
  const [error, setError] = useState('');
  const [traitNames, setTraitNames] = useState(
    Array.from({ length: 5 }, () => ({ dominant: '', recessive: '' }))
  );
  const [distance1, setDistance1] = useState(0);
  const [distance2, setDistance2] = useState(0);
  const [dcoPercent, setDcoPercent] = useState(0);
  const [totalOffspring, setTotalOffspring] = useState('');
  
  // State for parents: array of [leftGenes, rightGenes]
  // leftGenes and rightGenes are arrays of strings (alleles)
  const [parent1, setParent1] = useState([
    Array(3).fill(''), Array(3).fill('')
  ]);
  const [parent2, setParent2] = useState([
    Array(3).fill(''), Array(3).fill('')
  ]);

  const handleParentChange = (parentNum, isLeft, index, value) => {
    const letter = value.slice(-1).replace(/[^a-zA-Z]/g, ''); // only single letter
    const newParent = parentNum === 1 ? [...parent1] : [...parent2];
    const sideIdx = isLeft ? 0 : 1;
    const newSide = [...newParent[sideIdx]];
    newSide[index] = letter;
    newParent[sideIdx] = newSide;
    
    if (parentNum === 1) setParent1(newParent);
    else setParent2(newParent);
  };

  const handleTraitChange = (index, field, value) => {
    const newTraits = [...traitNames];
    newTraits[index][field] = value;
    setTraitNames(newTraits);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');

    const d1 = Number(distance1) || 0;
    const d2 = Number(distance2) || 0;
    const dco = Number(dcoPercent) || 0;

    if (geneCount === 2) {
      if (d1 < 0 || d1 > 100) {
        setError('Частота кроссинговера должна быть в пределах от 0% до 100%');
        return;
      }
    }

    if (geneCount === 3) {
      if (d1 < 0 || d2 < 0 || dco < 0) {
        setError('Частоты кроссинговера не могут быть отрицательными');
        return;
      }
      if (d1 + d2 + dco > 100) {
        setError(`Некорректные данные: сумма частот кроссинговера (${(d1 + d2 + dco).toFixed(1)}%) превышает 100%!`);
        return;
      }
    }
    
    // Validate
    let isValid = true;
    for (let i = 0; i < geneCount; i++) {
      if (!parent1[0][i] || !parent1[1][i] || !parent2[0][i] || !parent2[1][i]) {
        isValid = false;
      }
    }
    
    if (!isValid) {
      alert('Пожалуйста, заполните все аллели на хромосомах');
      return;
    }

    // Format as A.B/a.b
    const formatParent = (parent) => {
      const left = parent[0].slice(0, geneCount).join('.');
      const right = parent[1].slice(0, geneCount).join('.');
      return `${left}/${right}`;
    };

    const traitsToPass = traitNames.slice(0, geneCount).map((t, i) => ({
      dominant: t.dominant || `Дом. ${i+1}`,
      recessive: t.recessive || `Рец. ${i+1}`
    }));

    onSubmit({
      parent1: formatParent(parent1),
      parent2: formatParent(parent2),
      traitNames: traitsToPass,
      distance1: Number(distance1) || 0,
      distance2: geneCount === 3 ? (Number(distance2) || 0) : 0,
      dcoPercent: geneCount === 3 ? (Number(dcoPercent) || 0) : 0,
      totalOffspring: Number(totalOffspring) || null
    });
  };

  const p1Str = `${parent1[0].slice(0, geneCount).join('.') || '?'}/${parent1[1].slice(0, geneCount).join('.') || '?'}`;
  const p2Str = `${parent2[0].slice(0, geneCount).join('.') || '?'}/${parent2[1].slice(0, geneCount).join('.') || '?'}`;

  return (
    <div className="card">
      <button className="btn btn-back" onClick={onBack}>← Назад</button>
      <h2 className="card-title">Сцепленное наследование</h2>
      <p className="card-desc" style={{ marginBottom: '20px' }}>
        Гены находятся в одной аутосоме и наследуются вместе. Заполните аллели для каждой хромосомы (левой и правой).
      </p>

      {error && (
        <div style={{ background: 'rgba(255, 77, 77, 0.2)', border: '1px solid #ff4d4d', color: '#ff6b6b', padding: '12px', borderRadius: '8px', marginBottom: '20px', fontWeight: '500' }}>
          ⚠️ {error}
        </div>
      )}

      <div className="form-group">
        <label className="input-label">Количество сцепленных генов</label>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button 
            type="button"
            className={`btn ${geneCount === 2 ? 'btn-primary' : 'btn-secondary'}`} 
            onClick={() => setGeneCount(2)}
          >
            2 гена
          </button>
          <button 
            type="button"
            className={`btn ${geneCount === 3 ? 'btn-primary' : 'btn-secondary'}`} 
            onClick={() => setGeneCount(3)}
          >
            3 гена
          </button>
        </div>
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px', marginBottom: '24px' }}>
        {/* Родитель 1 */}
        <div style={{ flex: '1 1 200px', background: 'rgba(0,0,0,0.2)', padding: '16px', borderRadius: '12px' }}>
          <label className="input-label" style={{ textAlign: 'center', marginBottom: '16px' }}>Родитель 1 (♀)</label>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '20px' }}>
            
            {/* Ввод аллелей */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'flex', gap: '10px', fontWeight: 'bold', color: 'var(--text-secondary)' }}>
                <span>Лев.</span>
                <span>Прав.</span>
              </div>
              {Array.from({ length: geneCount }).map((_, i) => (
                <div key={i} style={{ display: 'flex', gap: '10px' }}>
                  <input 
                    type="text" 
                    className="input-field" 
                    style={{ width: '45px', textAlign: 'center', padding: '8px' }}
                    value={parent1[0][i]}
                    onChange={(e) => handleParentChange(1, true, i, e.target.value)}
                  />
                  <input 
                    type="text" 
                    className="input-field" 
                    style={{ width: '45px', textAlign: 'center', padding: '8px' }}
                    value={parent1[1][i]}
                    onChange={(e) => handleParentChange(1, false, i, e.target.value)}
                  />
                </div>
              ))}
            </div>

            {/* Визуализация */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100px', borderLeft: '1px solid var(--border)' }}>
              <LinkedChromosome genotype={p1Str} scale={1.25} />
            </div>

          </div>
        </div>

        {/* Родитель 2 */}
        <div style={{ flex: '1 1 200px', background: 'rgba(0,0,0,0.2)', padding: '16px', borderRadius: '12px' }}>
          <label className="input-label" style={{ textAlign: 'center', marginBottom: '16px' }}>Родитель 2 (♂)</label>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '20px' }}>
            
            {/* Ввод аллелей */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <div style={{ display: 'flex', gap: '10px', fontWeight: 'bold', color: 'var(--text-secondary)' }}>
                <span>Лев.</span>
                <span>Прав.</span>
              </div>
              {Array.from({ length: geneCount }).map((_, i) => (
                <div key={i} style={{ display: 'flex', gap: '10px' }}>
                  <input 
                    type="text" 
                    className="input-field" 
                    style={{ width: '45px', textAlign: 'center', padding: '8px' }}
                    value={parent2[0][i]}
                    onChange={(e) => handleParentChange(2, true, i, e.target.value)}
                  />
                  <input 
                    type="text" 
                    className="input-field" 
                    style={{ width: '45px', textAlign: 'center', padding: '8px' }}
                    value={parent2[1][i]}
                    onChange={(e) => handleParentChange(2, false, i, e.target.value)}
                  />
                </div>
              ))}
            </div>

            {/* Визуализация */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', width: '100px', borderLeft: '1px solid var(--border)' }}>
              <LinkedChromosome genotype={p2Str} scale={1.25} />
            </div>

          </div>
        </div>
      </div>

      <div className="section-title" style={{ marginTop: '20px' }}>Названия признаков (необязательно)</div>
      {Array.from({ length: geneCount }).map((_, i) => (
        <div key={i} className="form-group" style={{ display: 'flex', gap: '10px', marginBottom: '12px' }}>
          <div style={{ flex: 1 }}>
            <label className="input-label">Доминантный {i+1} ({String.fromCharCode(65+i)})</label>
            <input 
              type="text" 
              className="input-field" 
              placeholder="напр. жёлтый" 
              value={traitNames[i].dominant}
              onChange={e => handleTraitChange(i, 'dominant', e.target.value)}
            />
          </div>
          <div style={{ flex: 1 }}>
            <label className="input-label">Рецессивный {i+1} ({String.fromCharCode(97+i)})</label>
            <input 
              type="text" 
              className="input-field" 
              placeholder="напр. зелёный"
              value={traitNames[i].recessive}
              onChange={e => handleTraitChange(i, 'recessive', e.target.value)}
            />
          </div>
        </div>
      ))}

      {geneCount === 2 && (
        <div className="form-group">
          <label className="input-label">Расстояние между генами 1 и 2 (в морганидах / %)</label>
          <input 
            type="number" 
            className="input-field" 
            placeholder="0"
            min="0"
            max="50"
            value={distance1}
            onChange={(e) => setDistance1(e.target.value)}
          />
          <div className="card-desc" style={{ marginTop: '4px' }}>Оставьте 0 для полного сцепления</div>
        </div>
      )}

      {geneCount === 3 && (() => {
        const d1 = Number(distance1) || 0;
        const d2 = Number(distance2) || 0;
        const dco = Number(dcoPercent) || 0;
        const totalCrossover = d1 + d2 + dco;
        const autoNR = 100 - totalCrossover;
        const isInvalid = totalCrossover > 100 || d1 < 0 || d2 < 0 || dco < 0;

        return (
          <div style={{ background: 'rgba(0,0,0,0.15)', padding: '16px', borderRadius: '12px', marginBottom: '20px' }}>
            <div className="section-title" style={{ marginTop: 0, marginBottom: '12px' }}>📊 Параметры Кроссинговера</div>
            
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', marginBottom: '12px' }}>
              <div style={{ flex: 1, minWidth: '140px' }}>
                <label className="input-label">Одинарный кроссинговер 1-2 (SCO I, %)</label>
                <input 
                  type="number" 
                  className="input-field" 
                  placeholder="напр. 24"
                  min="0"
                  max="100"
                  step="0.1"
                  value={distance1}
                  onChange={(e) => setDistance1(e.target.value)}
                />
              </div>
              
              <div style={{ flex: 1, minWidth: '140px' }}>
                <label className="input-label">Одинарный кроссинговер 2-3 (SCO II, %)</label>
                <input 
                  type="number" 
                  className="input-field" 
                  placeholder="напр. 18"
                  min="0"
                  max="100"
                  step="0.1"
                  value={distance2}
                  onChange={(e) => setDistance2(e.target.value)}
                />
              </div>
            </div>

            <div style={{ marginBottom: '12px' }}>
              <label className="input-label">Двойной кроссинговер (DCO, %)</label>
              <input 
                type="number" 
                className="input-field" 
                placeholder="напр. 6"
                step="0.1"
                min="0"
                max="100"
                value={dcoPercent}
                onChange={(e) => setDcoPercent(e.target.value)}
              />
              <div className="card-desc" style={{ marginTop: '4px' }}>
                Оставьте 0, если двойного кроссинговера нет.
              </div>
            </div>

            {/* Автоматический некросс */}
            <div style={{ 
              marginTop: '12px', 
              padding: '12px', 
              borderRadius: '8px', 
              background: isInvalid ? 'rgba(255, 77, 77, 0.15)' : 'rgba(255, 255, 255, 0.06)',
              border: isInvalid ? '1px solid #ff4d4d' : '1px solid var(--border)'
            }}>
              <div style={{ fontWeight: '600', fontSize: '0.95rem', color: isInvalid ? '#ff4d4d' : 'var(--text-primary)' }}>
                🧬 Некроссоверные гаметы (ноккросс): {isInvalid ? 'Ошибка (> 100%)' : `${autoNR.toFixed(1)}%`}
              </div>
              <div style={{ fontSize: '0.8rem', opacity: 0.8, marginTop: '2px', color: 'var(--text-secondary)' }}>
                Рассчитывается автоматически: 100% - ({d1}% + {d2}% + {dco}%)
              </div>
            </div>
          </div>
        );
      })()}

      <div className="form-group" style={{ marginTop: '16px' }}>
        <label className="input-label">Общее количество потомков (опционально)</label>
        <input 
          type="number" 
          className="input-field" 
          placeholder="напр. 10000 или 15000" 
          min="1"
          value={totalOffspring}
          onChange={e => setTotalOffspring(e.target.value)}
        />
        <div className="card-desc" style={{ marginTop: '4px' }}>Укажите число из условия задачи для автоматического подсчета особeй</div>
      </div>

      <button className="btn btn-primary" onClick={handleSubmit}>
        Построить решетку →
      </button>
    </div>
  );
}

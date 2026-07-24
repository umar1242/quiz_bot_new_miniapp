import React, { useState } from 'react';
import GenotypeInput from './GenotypeInput';
import { calculateCross, validateGenotype } from '../utils/genetics';

export default function PunnettCalc({ crossType, genesCount: initialGenesCount, onBack, onCalculate }) {
  const [genesCount, setGenesCount] = useState(initialGenesCount);
  const [parent1, setParent1] = useState('');
  const [parent2, setParent2] = useState('');
  const [totalOffspring, setTotalOffspring] = useState('');
  const [traitNames, setTraitNames] = useState(
    Array.from({ length: 5 }, () => ({ dominant: '', recessive: '' }))
  );
  
  const title = crossType === 'mono' ? 'Моногибридное скрещивание' :
                crossType === 'di' ? 'Дигибридное скрещивание' : 'Полигибридное скрещивание';

  const handleTraitChange = (index, field, value) => {
    const newTraits = [...traitNames];
    newTraits[index][field] = value;
    setTraitNames(newTraits);
  };

  const handleCalculate = () => {
    const val1 = validateGenotype(parent1, genesCount);
    const val2 = validateGenotype(parent2, genesCount);
    
    if (!val1.valid || !val2.valid) {
      alert('Пожалуйста, введите корректные генотипы.');
      return;
    }

    const traitsToPass = traitNames.slice(0, genesCount).map((t, i) => ({
      dominant: t.dominant || `Дом. ${i+1}`,
      recessive: t.recessive || `Рец. ${i+1}`
    }));

    const result = calculateCross(parent1, parent2, traitsToPass);
    onCalculate({ 
      ...result, 
      parent1, 
      parent2, 
      traitNames: traitsToPass, 
      totalOffspring: Number(totalOffspring) || null 
    });
  };

  return (
    <>
      <button className="btn btn-back" onClick={onBack}>← Назад</button>
      
      <div className="card">
        <h2 className="card-title">{title}</h2>
        
        {crossType === 'poly' && (
          <div className="form-group">
            <label className="input-label">Количество генов (1-5):</label>
            <input 
              type="number" 
              className="input-field" 
              min="1" max="5" 
              value={genesCount} 
              onChange={e => setGenesCount(Math.min(5, Math.max(1, parseInt(e.target.value) || 1)))}
            />
          </div>
        )}

        <div className="section-title">Родительские особи</div>
        
        <GenotypeInput 
          label="Материнский организм (♀)" 
          value={parent1} 
          onChange={setParent1} 
          geneCount={genesCount} 
        />
        
        <GenotypeInput 
          label="Отцовский организм (♂)" 
          value={parent2} 
          onChange={setParent2} 
          geneCount={genesCount} 
        />

        <div className="section-title">Названия признаков (необязательно)</div>
        
        {Array.from({ length: genesCount }).map((_, i) => (
          <div key={i} className="form-group" style={{ display: 'flex', gap: '10px' }}>
            <div style={{ flex: 1 }}>
              <label className="input-label">Доминантный {i+1} (AA/Aa)</label>
              <input 
                type="text" 
                className="input-field" 
                placeholder="напр. жёлтый" 
                value={traitNames[i].dominant}
                onChange={e => handleTraitChange(i, 'dominant', e.target.value)}
              />
            </div>
            <div style={{ flex: 1 }}>
              <label className="input-label">Рецессивный {i+1} (aa)</label>
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
          <div className="card-desc" style={{ marginTop: '4px' }}>Укажите число из условия задачи для подсчета особей</div>
        </div>

        <button className="btn btn-primary" style={{ marginTop: '20px' }} onClick={handleCalculate}>
          Рассчитать
        </button>
      </div>
    </>
  );
}

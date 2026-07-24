import React, { useState } from 'react';

export default function EpistasisInput({ onBack, onSubmit }) {
  const [epistasisMode, setEpistasisMode] = useState('dom_12_3_1');
  const [parent1, setParent1] = useState('AaBb');
  const [parent2, setParent2] = useState('AaBb');
  const [totalOffspring, setTotalOffspring] = useState('');
  
  // Custom trait names depending on mode
  const [traitName1, setTraitName1] = useState('Эпистатический (Белый/Подавленный)');
  const [traitName2, setTraitName2] = useState('Окрашенный (Доминантный A)');
  const [traitName3, setTraitName3] = useState('Рецессивный (aa)');

  const modes = [
    {
      id: 'dom_12_3_1',
      icon: '🎃',
      title: 'Доминантный эпистаз',
      ratio: '12 : 3 : 1',
      desc: 'Доминантный аллель одного гена (B) полностью подавляет проявление второго гена (A).',
      example: 'Пример: Окраска плодов тыквы, масть лошадей.',
      defaultTraits: ['Белый / Подавленный (B_)', 'Окрашенный (bbA_)', 'Рецессивный (bbaa)']
    },
    {
      id: 'dom_13_3',
      icon: '🐔',
      title: 'Доминантный эпистаз с подавлением',
      ratio: '13 : 3',
      desc: 'Доминантный ген-ингибитор (I) подавляет окраску + двойная рецессивная гомозигота (iiaa) также не имеет цвета.',
      example: 'Пример: Оперение кур (белые шелковистые и окрашенные).',
      defaultTraits: ['Белый / Без цвета (I_A_, I_aa, iiaa)', 'Окрашенный (iiA_)']
    },
    {
      id: 'rec_9_3_4',
      icon: '🧅',
      title: 'Рецессивный эпистаз (Криптомерия)',
      ratio: '9 : 3 : 4',
      desc: 'Рецессивная гомозигота одного гена (bb) маскирует проявление аллелей другого гена (A/a).',
      example: 'Пример: Окраска шерсти мышей, чешуй лука.',
      defaultTraits: ['Криптомерный / Маскированный (bbA_, bbaa)', 'Основной / Пурпурный (B_A_)', 'Альтернативный / Красный (B_aa)']
    }
  ];

  const handleModeChange = (modeId) => {
    setEpistasisMode(modeId);
    const m = modes.find(item => item.id === modeId);
    if (m && m.defaultTraits) {
      setTraitName1(m.defaultTraits[0] || '');
      setTraitName2(m.defaultTraits[1] || '');
      setTraitName3(m.defaultTraits[2] || '');
    }
  };

  const handlePreset = (p1, p2) => {
    setParent1(p1);
    setParent2(p2);
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    const traitNames = epistasisMode === 'dom_13_3'
      ? [traitName1, traitName2]
      : [traitName1, traitName2, traitName3];

    onSubmit({
      parent1: parent1.trim(),
      parent2: parent2.trim(),
      specialType: 'epistasis',
      options: {
        epistasisMode,
        traitNames,
        totalOffspring: totalOffspring ? parseInt(totalOffspring, 10) : null
      }
    });
  };

  return (
    <div className="card" style={{ maxWidth: '620px', margin: '0 auto', padding: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <button className="btn btn-back" onClick={onBack} style={{ margin: 0 }}>
          ← Назад
        </button>
        <span style={{ 
          fontSize: '0.85rem', 
          fontWeight: '700', 
          background: 'rgba(192, 132, 252, 0.15)', 
          color: 'var(--accent-primary)',
          border: '1px solid var(--accent-primary)',
          padding: '4px 12px',
          borderRadius: '20px'
        }}>
          🧬 Неаллельное взаимодействие
        </span>
      </div>

      <div style={{ textAlignment: 'center', marginBottom: '20px' }}>
        <h2 style={{ fontSize: '1.8rem', fontWeight: '700', marginBottom: '4px' }}>
          🎭 Эпистаз
        </h2>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
          Подавление действия одной неаллельной пары генов другой
        </p>
      </div>

      <form onSubmit={handleSubmit}>
        {/* 1. ВЫБОР ТИПА ЭПИСТАЗА (ИНТЕРАКТИВНЫЕ КАРТОЧКИ) */}
        <label className="input-label" style={{ fontWeight: '700', fontSize: '1rem', marginBottom: '10px', display: 'block' }}>
          1. Выберите тип эпистаза:
        </label>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '24px' }}>
          {modes.map((m) => {
            const isSelected = epistasisMode === m.id;
            return (
              <div
                key={m.id}
                onClick={() => handleModeChange(m.id)}
                style={{
                  background: isSelected ? 'rgba(192, 132, 252, 0.18)' : 'rgba(255, 255, 255, 0.04)',
                  border: isSelected ? '2px solid var(--accent-primary)' : '1px solid var(--border)',
                  borderRadius: '16px',
                  padding: '14px 16px',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  boxShadow: isSelected ? '0 0 16px rgba(192, 132, 252, 0.25)' : 'none'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <span style={{ fontSize: '1.4rem' }}>{m.icon}</span>
                    <strong style={{ fontSize: '1.05rem', color: isSelected ? '#fff' : 'var(--text-primary)' }}>
                      {m.title}
                    </strong>
                  </div>
                  <span style={{
                    fontFamily: 'monospace',
                    fontSize: '0.9rem',
                    fontWeight: '800',
                    background: isSelected ? 'var(--accent-gradient)' : 'rgba(255, 255, 255, 0.1)',
                    color: '#fff',
                    padding: '3px 10px',
                    borderRadius: '8px',
                    letterSpacing: '0.5px'
                  }}>
                    {m.ratio}
                  </span>
                </div>
                
                <p style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', marginBottom: '4px', lineHeight: '1.35' }}>
                  {m.desc}
                </p>
                <span style={{ fontSize: '0.8rem', color: 'var(--accent-primary)', opacity: 0.9 }}>
                  {m.example}
                </span>
              </div>
            );
          })}
        </div>

        {/* 2. БЫСТРЫЙ ВЫБОР ГЕНОТИПОВ РОДИТЕЛЕЙ */}
        <label className="input-label" style={{ fontWeight: '700', fontSize: '1rem', marginBottom: '8px', display: 'block' }}>
          2. Генотипы родителей:
        </label>
        
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '14px' }}>
          <button
            type="button"
            className="btn btn-secondary"
            style={{ fontSize: '0.85rem', padding: '6px 12px' }}
            onClick={() => handlePreset('AaBb', 'AaBb')}
          >
            ⚡ AaBb × AaBb (F₁ × F₁)
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            style={{ fontSize: '0.85rem', padding: '6px 12px' }}
            onClick={() => handlePreset('AaBb', 'aabb')}
          >
            🔬 AaBb × aabb (Анализирующее)
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            style={{ fontSize: '0.85rem', padding: '6px 12px' }}
            onClick={() => handlePreset('Aabb', 'aaBb')}
          >
            🧪 Aabb × aaBb
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '20px' }}>
          <div>
            <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '4px', display: 'block' }}>
              Мать (♀):
            </label>
            <input
              type="text"
              value={parent1}
              onChange={(e) => setParent1(e.target.value)}
              placeholder="AaBb"
              className="genotype-input"
              style={{ width: '100%', padding: '10px', textAlignment: 'center', fontFamily: 'monospace', fontWeight: 'bold' }}
            />
          </div>
          <div>
            <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '4px', display: 'block' }}>
              Отец (♂):
            </label>
            <input
              type="text"
              value={parent2}
              onChange={(e) => setParent2(e.target.value)}
              placeholder="AaBb"
              className="genotype-input"
              style={{ width: '100%', padding: '10px', textAlignment: 'center', fontFamily: 'monospace', fontWeight: 'bold' }}
            />
          </div>
        </div>

        {/* 3. НАЗВАНИЯ ФЕНОТИПИЧЕСКИХ КЛАССОВ (НАСТРОЙКА ДЛЯ ЗАДАЧИ) */}
        <div style={{ 
          background: 'rgba(255, 255, 255, 0.03)', 
          border: '1px solid var(--border)', 
          padding: '14px', 
          borderRadius: '14px', 
          marginBottom: '20px' 
        }}>
          <label style={{ fontWeight: '700', fontSize: '0.95rem', marginBottom: '10px', display: 'block' }}>
            🎨 Названия признаков фенотипов в задаче:
          </label>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--accent-primary)', marginBottom: '2px', display: 'block' }}>
                Класс 1 (Эпистатический / Основной):
              </label>
              <input
                type="text"
                value={traitName1}
                onChange={(e) => setTraitName1(e.target.value)}
                className="genotype-input"
                style={{ width: '100%', padding: '8px 12px', fontSize: '0.9rem' }}
              />
            </div>

            <div>
              <label style={{ fontSize: '0.8rem', color: 'var(--accent-primary)', marginBottom: '2px', display: 'block' }}>
                Класс 2 (Гипостатический / Окрашенный):
              </label>
              <input
                type="text"
                value={traitName2}
                onChange={(e) => setTraitName2(e.target.value)}
                className="genotype-input"
                style={{ width: '100%', padding: '8px 12px', fontSize: '0.9rem' }}
              />
            </div>

            {epistasisMode !== 'dom_13_3' && (
              <div>
                <label style={{ fontSize: '0.8rem', color: 'var(--accent-primary)', marginBottom: '2px', display: 'block' }}>
                  Класс 3 (Рецессивный):
                </label>
                <input
                  type="text"
                  value={traitName3}
                  onChange={(e) => setTraitName3(e.target.value)}
                  className="genotype-input"
                  style={{ width: '100%', padding: '8px 12px', fontSize: '0.9rem' }}
                />
              </div>
            )}
          </div>
        </div>

        {/* 4. ЧИСЛО ПОТОМКОВ (N) */}
        <div style={{ marginBottom: '24px' }}>
          <label className="input-label" style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
            Число потомков в задаче (N, опционально):
          </label>
          <input
            type="number"
            value={totalOffspring}
            onChange={(e) => setTotalOffspring(e.target.value)}
            placeholder="например 1600 или 10000"
            className="genotype-input"
            style={{ width: '100%', padding: '10px' }}
          />
        </div>

        <button 
          type="submit" 
          className="btn btn-primary" 
          style={{ 
            width: '100%', 
            padding: '14px', 
            fontSize: '1.1rem', 
            fontWeight: '700',
            boxShadow: '0 4px 20px rgba(192, 132, 252, 0.4)'
          }}
        >
          🚀 Рассчитать эпистаз
        </button>
      </form>
    </div>
  );
}

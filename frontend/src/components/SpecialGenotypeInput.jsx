import React, { useState } from 'react';

export default function SpecialGenotypeInput({ specialType, onBack, onSubmit }) {
  // Common states
  const [parent1, setParent1] = useState(specialType === 'blood' ? 'Ai' : 'AaBb');
  const [parent2, setParent2] = useState(specialType === 'blood' ? 'Bi' : 'AaBb');
  const [totalOffspring, setTotalOffspring] = useState('');
  const [error, setError] = useState('');

  // Special options
  const [epistasisMode, setEpistasisMode] = useState('dom_12_3_1');
  const [compMode, setCompMode] = useState('comp_9_7');
  const [isCumulative, setIsCumulative] = useState(true);
  const [lethalGenotype, setLethalGenotype] = useState('AA');
  const [enableLethal, setEnableLethal] = useState(false);

  // Blood group specific states
  const [bloodP1, setBloodP1] = useState('Ai');
  const [bloodP2, setBloodP2] = useState('Bi');
  const [rhP1, setRhP1] = useState('Rr'); // Rr = Rh(+), rr = Rh(-)
  const [rhP2, setRhP2] = useState('Rr');
  const [includeRh, setIncludeRh] = useState(false);

  const getTitle = () => {
    switch (specialType) {
      case 'epistasis': return '🎭 Эпистаз';
      case 'complementary': return '🧩 Комплементарность';
      case 'polymeria': return '📊 Полимерия';
      case 'blood': return '🩸 Группы крови (ABO & Rh)';
      case 'pleiotropy': return '⚠️ Плейотропия и Летальные гены';
      default: return 'Неаллельное наследование';
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');

    let p1 = parent1.trim();
    let p2 = parent2.trim();

    if (specialType === 'blood') {
      p1 = bloodP1 + (includeRh ? rhP1 : '');
      p2 = bloodP2 + (includeRh ? rhP2 : '');
    }

    if (!p1 || !p2) {
      setError('Заполните генотипы обоих родителей');
      return;
    }

    const options = {
      epistasisMode,
      compMode,
      isCumulative,
      lethalGenotype: (specialType === 'pleiotropy' && enableLethal) ? lethalGenotype : null,
      totalOffspring: totalOffspring ? parseInt(totalOffspring, 10) : null
    };

    onSubmit({ parent1: p1, parent2: p2, specialType, options });
  };

  return (
    <div className="card">
      <button className="btn btn-back" onClick={onBack} style={{ marginBottom: '12px' }}>
        ← Назад
      </button>

      <h2 className="card-title">{getTitle()}</h2>

      {error && (
        <div style={{
          background: 'rgba(255, 77, 77, 0.15)',
          border: '1px solid #ff4d4d',
          color: '#ff6b6b',
          padding: '10px 14px',
          borderRadius: '8px',
          marginBottom: '16px',
          fontSize: '0.9rem'
        }}>
          ⚠️ {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        {/* --- 1. ЭПИСТАЗ --- */}
        {specialType === 'epistasis' && (
          <div style={{ marginBottom: '16px' }}>
            <label className="input-label" style={{ fontWeight: '600', marginBottom: '6px', display: 'block' }}>
              Тип эпистаза:
            </label>
            <select
              value={epistasisMode}
              onChange={(e) => setEpistasisMode(e.target.value)}
              className="genotype-input"
              style={{ width: '100%', padding: '10px' }}
            >
              <option value="dom_12_3_1">Доминантный эпистаз (расщепление 12 : 3 : 1)</option>
              <option value="dom_13_3">Доминантный эпистаз с подавлением (расщепление 13 : 3)</option>
              <option value="rec_9_3_4">Рецессивный эпистаз / Криптомерия (расщепление 9 : 3 : 4)</option>
            </select>
          </div>
        )}

        {/* --- 2. КОМПЛЕМЕНТАРНОСТЬ --- */}
        {specialType === 'complementary' && (
          <div style={{ marginBottom: '16px' }}>
            <label className="input-label" style={{ fontWeight: '600', marginBottom: '6px', display: 'block' }}>
              Тип комплементарного взаимодействия:
            </label>
            <select
              value={compMode}
              onChange={(e) => setCompMode(e.target.value)}
              className="genotype-input"
              style={{ width: '100%', padding: '10px' }}
            >
              <option value="comp_9_7">Новый признак при A_B_ (расщепление 9 : 7)</option>
              <option value="comp_9_6_1">Три фенотипических класса (расщепление 9 : 6 : 1)</option>
              <option value="comp_9_3_4">Видоизменённое расщепление (расщепление 9 : 3 : 4)</option>
            </select>
          </div>
        )}

        {/* --- 3. ПОЛИМЕРИЯ --- */}
        {specialType === 'polymeria' && (
          <div style={{ marginBottom: '16px' }}>
            <label className="input-label" style={{ fontWeight: '600', marginBottom: '6px', display: 'block' }}>
              Разновидность полимерии:
            </label>
            <div style={{ display: 'flex', gap: '12px', marginTop: '6px' }}>
              <button
                type="button"
                className={`btn ${isCumulative ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setIsCumulative(true)}
                style={{ flex: 1 }}
              >
                Кумулятивная (1:4:6:4:1)
              </button>
              <button
                type="button"
                className={`btn ${!isCumulative ? 'btn-primary' : 'btn-secondary'}`}
                onClick={() => setIsCumulative(false)}
                style={{ flex: 1 }}
              >
                Некумулятивная (15:1)
              </button>
            </div>
          </div>
        )}

        {/* --- 4. ГРУППЫ КРОВИ (ABO & Rh) --- */}
        {specialType === 'blood' ? (
          <>
            <div style={{ marginBottom: '14px' }}>
              <label className="input-label">Мать (♀):</label>
              <select
                value={bloodP1}
                onChange={(e) => setBloodP1(e.target.value)}
                className="genotype-input"
                style={{ width: '100%', padding: '10px', marginTop: '4px' }}
              >
                <option value="ii">I (0) группа — [ii]</option>
                <option value="Ai">II (A) группа (гетерозигота) — [I^A i]</option>
                <option value="AA">II (A) группа (гомозигота) — [I^A I^A]</option>
                <option value="Bi">III (B) группа (гетерозигота) — [I^B i]</option>
                <option value="BB">III (B) группа (гомозигота) — [I^B I^B]</option>
                <option value="AB">IV (AB) группа — [I^A I^B] (Кодоминирование)</option>
              </select>
            </div>

            <div style={{ marginBottom: '14px' }}>
              <label className="input-label">Отец (♂):</label>
              <select
                value={bloodP2}
                onChange={(e) => setBloodP2(e.target.value)}
                className="genotype-input"
                style={{ width: '100%', padding: '10px', marginTop: '4px' }}
              >
                <option value="ii">I (0) группа — [ii]</option>
                <option value="Ai">II (A) группа (гетерозигота) — [I^A i]</option>
                <option value="AA">II (A) группа (гомозигота) — [I^A I^A]</option>
                <option value="Bi">III (B) группа (гетерозигота) — [I^B i]</option>
                <option value="BB">III (B) группа (гомозигота) — [I^B I^B]</option>
                <option value="AB">IV (AB) группа — [I^A I^B] (Кодоминирование)</option>
              </select>
            </div>

            <div style={{ marginBottom: '16px', background: 'rgba(255,255,255,0.05)', padding: '10px', borderRadius: '8px' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontWeight: '600' }}>
                <input
                  type="checkbox"
                  checked={includeRh}
                  onChange={(e) => setIncludeRh(e.target.checked)}
                />
                Добавить учет Резус-фактора (Rh+ / Rh-)
              </label>

              {includeRh && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginTop: '10px' }}>
                  <div>
                    <label style={{ fontSize: '0.85rem' }}>Rh Матери:</label>
                    <select value={rhP1} onChange={(e) => setRhP1(e.target.value)} className="genotype-input" style={{ width: '100%', padding: '6px' }}>
                      <option value="Rr">Rh(+) гетерозигота [Rr]</option>
                      <option value="RR">Rh(+) гомозигота [RR]</option>
                      <option value="rr">Rh(-) отрицательный [rr]</option>
                    </select>
                  </div>
                  <div>
                    <label style={{ fontSize: '0.85rem' }}>Rh Отца:</label>
                    <select value={rhP2} onChange={(e) => setRhP2(e.target.value)} className="genotype-input" style={{ width: '100%', padding: '6px' }}>
                      <option value="Rr">Rh(+) гетерозигота [Rr]</option>
                      <option value="RR">Rh(+) гомозигота [RR]</option>
                      <option value="rr">Rh(-) отрицательный [rr]</option>
                    </select>
                  </div>
                </div>
              )}
            </div>
          </>
        ) : (
          /* --- ОБЫЧНЫЙ ВВОД ГЕНОТИПОВ ДЛЯ ЭПИСТАЗА, КОМПЛЕМЕНТАРНОСТИ, ПОЛИМЕРИИ И ПЛЕЙОТРОПИИ --- */
          <>
            <div style={{ marginBottom: '14px' }}>
              <label className="input-label">Генотип Родителя 1 (♀):</label>
              <input
                type="text"
                value={parent1}
                onChange={(e) => setParent1(e.target.value)}
                placeholder="например AaBb"
                className="genotype-input"
              />
            </div>

            <div style={{ marginBottom: '14px' }}>
              <label className="input-label">Генотип Родителя 2 (♂):</label>
              <input
                type="text"
                value={parent2}
                onChange={(e) => setParent2(e.target.value)}
                placeholder="например AaBb"
                className="genotype-input"
              />
            </div>
          </>
        )}

        {/* --- 5. ПЛЕЙОТРОПИЯ И ЛЕТАЛЬНОСТЬ --- */}
        {specialType === 'pleiotropy' && (
          <div style={{ marginBottom: '16px', background: 'rgba(255, 77, 77, 0.08)', border: '1px solid rgba(255,77,77,0.3)', padding: '12px', borderRadius: '8px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontWeight: '600', color: '#ff6b6b' }}>
              <input
                type="checkbox"
                checked={enableLethal}
                onChange={(e) => setEnableLethal(e.target.checked)}
              />
              ⚠️ Включить летальный генотип (отсев гибнущих эмбрионов)
            </label>

            {enableLethal && (
              <div style={{ marginTop: '10px' }}>
                <label style={{ fontSize: '0.85rem', display: 'block', marginBottom: '4px' }}>
                  Летальный генотип (гибнет до рождения):
                </label>
                <input
                  type="text"
                  value={lethalGenotype}
                  onChange={(e) => setLethalGenotype(e.target.value)}
                  placeholder="например AA"
                  className="genotype-input"
                  style={{ width: '100%', padding: '8px' }}
                />
                <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'block', marginTop: '4px' }}>
                  💡 Для моногибридного скрещивания `Aa x Aa` с летальным `AA` расщепление составит **2 : 1**.
                </span>
              </div>
            )}
          </div>
        )}

        {/* --- 6. ЧИСЛО ПОТОМКОВ (N) --- */}
        <div style={{ marginBottom: '16px' }}>
          <label className="input-label" style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
            Число потомков (N, опционально):
          </label>
          <input
            type="number"
            value={totalOffspring}
            onChange={(e) => setTotalOffspring(e.target.value)}
            placeholder="например 10000"
            className="genotype-input"
            style={{ width: '100%', padding: '8px' }}
          />
        </div>

        <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '8px' }}>
          🧬 Рассчитать скрещивание
        </button>
      </form>
    </div>
  );
}

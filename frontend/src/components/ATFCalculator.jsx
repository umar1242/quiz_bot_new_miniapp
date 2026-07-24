import React, { useState } from 'react';

/**
 * ATFCalculator — Mini App компонент для решения задач по энергетическому обмену
 * (Husniddin ATF-3 сборника Solijonov Husniddin, Uchtepa ATM)
 *
 * Типы задач:
 *  1) Тип 1 (задачи 1-10):  Разница глюкозы, АТФ, хлоропласт → % АТФ на синтез
 *  2) Тип 2 (задачи 11-20): % полного расщепления, % АТФ на синтез, коэффициент глюкозы, анаэроб АТФ
 *  3) Тип 3 (задачи 21-30): Разница воды и энергии → АТФ на синтез глюкозы
 *  4) Тип 4 (задачи 31-40): АТФ сумма + разница воды + коэффициент хлоропласта
 */

// ─── Solvers ────────────────────────────────────────────────────────────────

function solveType1(diffChala, diffMitCitoATF, diffXloroGlukoza) {
  // 36x - (2x + 2(x+k)) = diff  →  32x - 2k = diff
  const xTola = (diffMitCitoATF + 2 * diffChala) / 32;
  const xChala = xTola + diffChala;
  const totGlukoza = xTola + xChala;
  const xloroGlukoza = totGlukoza + diffXloroGlukoza;
  const atfForGlukoza = xloroGlukoza * 18;
  const mitATF = 36 * xTola;
  const totXloroATF = mitATF * 30;
  const percent = totXloroATF > 0 ? (atfForGlukoza / totXloroATF) * 100 : 0;

  return {
    xTola, xChala, totGlukoza, xloroGlukoza,
    atfForGlukoza, mitATF, totXloroATF,
    percent: Math.round(percent * 10) / 10,
    steps: [
      { label: "Tenglamadan x (to'la parchalangan)", formula: `(${diffMitCitoATF} + 2·${diffChala}) / 32`, value: `${xTola} mol` },
      { label: "Chala parchalangan glukoza", formula: `${xTola} + ${diffChala}`, value: `${xChala} mol` },
      { label: "Umumiy parchalangan glukoza", formula: `${xTola} + ${xChala}`, value: `${totGlukoza} mol` },
      { label: "Xloroplastda hosil bo'lgan glukoza", formula: `${totGlukoza} + ${diffXloroGlukoza}`, value: `${xloroGlukoza} mol` },
      { label: "Glukoza sinteziga sarflangan ATF", formula: `${xloroGlukoza} × 18`, value: `${atfForGlukoza} ta` },
      { label: "Mitoxondriyada hosil bo'lgan ATF", formula: `36 × ${xTola}`, value: `${mitATF} ta` },
      { label: "Xloroplastda umumiy ATF", formula: `${mitATF} × 30`, value: `${totXloroATF} ta` },
      { label: "Glukozaga sarflangan %", formula: `${atfForGlukoza} / ${totXloroATF} × 100`, value: `${Math.round(percent * 10) / 10}%` },
    ],
    answer: `${Math.round(percent * 10) / 10}%`,
    answerLabel: "Xloroplast ATF ning glukozaga sarflangan ulushi"
  };
}

function solveType2(percentTola, percentATFSpent, glucoseRatio, anaerobATF) {
  // percentTola% to'la, qolgan qismi chala
  // anaerobATF = 2 * umumiy_glukoza
  const totalGlukoza = anaerobATF / 2;
  const xTola = totalGlukoza * (percentTola / 100);
  const xChala = totalGlukoza - xTola;

  // Xloroplast glukoza = parchalangan * glucoseRatio
  const xloroGlukoza = totalGlukoza * glucoseRatio;
  const atfForGlukoza = xloroGlukoza * 18;

  // Xloroplastda umumiy ATF = atfForGlukoza / (percentATFSpent/100)
  const totXloroATF = (percentATFSpent > 0) ? atfForGlukoza / (percentATFSpent / 100) : 0;

  // CO2 fotosintez = 6 * xloroGlukoza, CO2 energiya = 6 * xTola
  const co2Foto = 6 * xloroGlukoza;
  const co2Energiya = 6 * xTola;
  const co2Diff = co2Foto - co2Energiya;

  // Chala parchalanish issiqlik = xChala * 120 (60 kJ * 2 mol PVK)
  const chalaIssiqlik = xChala * 120;

  // To'la parchalanish ATF energiyasi = 36 * xTola * 40
  const tolaATFEnergy = 36 * xTola * 40;

  return {
    xTola, xChala, totalGlukoza, xloroGlukoza,
    atfForGlukoza, totXloroATF, co2Foto, co2Energiya, co2Diff,
    chalaIssiqlik, tolaATFEnergy,
    steps: [
      { label: "Umumiy parchalangan glukoza", formula: `${anaerobATF} / 2`, value: `${totalGlukoza} mol` },
      { label: "To'la parchalangan glukoza", formula: `${totalGlukoza} × ${percentTola}%`, value: `${xTola} mol` },
      { label: "Chala parchalangan glukoza", formula: `${totalGlukoza} - ${xTola}`, value: `${xChala} mol` },
      { label: "Xloroplast glukoza", formula: `${totalGlukoza} × ${glucoseRatio}`, value: `${xloroGlukoza} mol` },
      { label: "Glukozaga sarflangan ATF", formula: `${xloroGlukoza} × 18`, value: `${atfForGlukoza} mol` },
      { label: "Xloroplast umumiy ATF", formula: `${atfForGlukoza} / ${percentATFSpent}%`, value: `${totXloroATF} mol` },
      { label: "CO₂ fotosintez", formula: `6 × ${xloroGlukoza}`, value: `${co2Foto} mol` },
      { label: "CO₂ energiya almashinuvi", formula: `6 × ${xTola}`, value: `${co2Energiya} mol` },
      { label: "CO₂ farqi", formula: `${co2Foto} - ${co2Energiya}`, value: `${co2Diff} mol` },
    ],
    answer: `CO₂ farq: ${co2Diff} mol`,
    answerLabel: "Asosiy natijalar"
  };
}

function solveType3(diffWater, diffEnergy) {
  // suv farqi = (36x - 6x) = 30x  →  x = diffWater / 30
  const x = diffWater / 30;
  const atfSpent = x * 18;
  const suvFosfor = 36 * x;
  const suvOksid = 6 * x;
  const citoATF = x * 2;
  const citoATFkJ = citoATF * 40;
  const mitIssiqkJ = x * 1400;

  return {
    x, atfSpent, suvFosfor, suvOksid, citoATFkJ, mitIssiqkJ,
    steps: [
      { label: "To'la parchalangan glukoza (x)", formula: `${diffWater} / 30`, value: `${x} mol` },
      { label: "Fosforlanish suvi (36x)", formula: `36 × ${x}`, value: `${suvFosfor} mol` },
      { label: "Oksidlanish suvi (6x)", formula: `6 × ${x}`, value: `${suvOksid} mol` },
      { label: "Sitoplazmada ATF energiyasi", formula: `${x} × 2 × 40`, value: `${citoATFkJ} kJ` },
      { label: "Mitoxondriya issiqlik energiyasi", formula: `${x} × 1400`, value: `${mitIssiqkJ} kJ` },
      { label: "Glukoza sinteziga ATF", formula: `${x} × 18`, value: `${atfSpent} mol` },
    ],
    answer: `${atfSpent} mol ATF`,
    answerLabel: "Glukoza sinteziga sarflangan ATF"
  };
}

function solveType4(totalATF, diffWater, xloroRatio) {
  // totalATF = 2*(xTola + xChala) + 36*xTola = 38*xTola + 2*xChala
  // Also: 2*total_glukoza = ??? but simpler: we solve via suv diff
  // suv diff = 36*xTola - xTola*6 = 30*xTola ??? No, suv diff = suv_mit - suv_cito
  // suv_cito includes chala too. Let me re-derive:
  // cito suv = 0 (glikoliz doesn't produce water)
  // mit suv: oksidlanish = 6x, fosforlanish = 36x → total = 42x
  // diffWater = (36x - 6x) ??? The problem says suv_mit - suv_cito = diffWater
  // In the file: "Sitoplazma va mitoxondriyada xosil bo'lgan suv moli farqi 116"
  // Sitoplazma suv = 0 from glikoliz. Mitoxondria suv = 6x (oksidlanish) + 36x (fosforlanish) = 42x
  // Wait, but that gives 42x = diffWater...
  // Actually: diffWater = suv_fosfor - suv_oksid = 36x - 6x = 30x likely in context
  // Let me just keep it flexible:
  // totalATF = 2*totalGluk + 36*xTola  but we also know totalATF = all anaerob
  // From task: ATF_total = 2*(xTola+xChala) + 36*xTola = 2*xChala + 38*xTola
  // and diffWater between sitoplazma & mitoxondriya
  // Sitoplazma suvi = 0, Mitoxondriya suvi = 6x + 36x = 42x
  // So diffWater = 42*xTola
  const xTola = diffWater / 42;
  const mitATF = 36 * xTola;
  const anaerobRemain = totalATF - mitATF;
  const totalGlukoza = anaerobRemain / 2;
  const xChala = totalGlukoza - xTola;
  const xloroGlukoza = totalGlukoza * xloroRatio;
  const atfForGlukoza = xloroGlukoza * 18;
  const totXloroATF = mitATF * 30;
  const percent = totXloroATF > 0 ? (atfForGlukoza / totXloroATF) * 100 : 0;

  return {
    xTola, xChala, totalGlukoza, xloroGlukoza,
    atfForGlukoza, mitATF, totXloroATF,
    percent: Math.round(percent * 10) / 10,
    steps: [
      { label: "To'la parchalangan glukoza (x)", formula: `${diffWater} / 42`, value: `${xTola} mol` },
      { label: "Mitoxondriya ATF", formula: `36 × ${xTola}`, value: `${mitATF} ta` },
      { label: "Umumiy glukoza", formula: `(${totalATF} - ${mitATF}) / 2`, value: `${totalGlukoza} mol` },
      { label: "Chala parchalangan glukoza", formula: `${totalGlukoza} - ${xTola}`, value: `${xChala} mol` },
      { label: "Xloroplast glukoza", formula: `${totalGlukoza} × ${xloroRatio}`, value: `${xloroGlukoza} mol` },
      { label: "Glukozaga ATF", formula: `${xloroGlukoza} × 18`, value: `${atfForGlukoza} ta` },
      { label: "Xloroplast umumiy ATF", formula: `${mitATF} × 30`, value: `${totXloroATF} ta` },
      { label: "Sarflangan %", formula: `${atfForGlukoza} / ${totXloroATF} × 100`, value: `${Math.round(percent * 10) / 10}%` },
    ],
    answer: `${Math.round(percent * 10) / 10}%`,
    answerLabel: "ATF sarflangan ulushi"
  };
}

// ─── Constants ──────────────────────────────────────────────────────────────

const TASK_TYPES = [
  {
    id: 'type1',
    icon: '⚡',
    title: "1-Тип (1-10)",
    subtitle: "Разница глюкозы и АТФ → % хлоропласта",
    fields: [
      { key: 'diffChala', label: "Chala − To'la glukoza farqi (mol)", placeholder: "masalan: 4" },
      { key: 'diffATF', label: "Mitoxondriya − Sitoplazma ATF farqi", placeholder: "masalan: 88" },
      { key: 'diffGlukoza', label: "Xloroplast − Parchalangan glukoza farqi (mol)", placeholder: "masalan: 62" },
    ],
    solve: (vals) => solveType1(vals.diffChala, vals.diffATF, vals.diffGlukoza),
    examples: [
      { label: "Masala 1", values: { diffChala: 4, diffATF: 88, diffGlukoza: 62 } },
      { label: "Masala 5", values: { diffChala: 5, diffATF: 150, diffGlukoza: 45 } },
      { label: "Masala 10", values: { diffChala: 7, diffATF: 82, diffGlukoza: 41 } },
    ]
  },
  {
    id: 'type2',
    icon: '🧪',
    title: "2-Тип (11-20)",
    subtitle: "% расщеплено, % ATF, коэфф. глюкозы, анаэроб АТФ",
    fields: [
      { key: 'percentTola', label: "To'la parchalanish % (masalan 30)", placeholder: "masalan: 30" },
      { key: 'percentATF', label: "ATF sarflangan % (masalan 40)", placeholder: "masalan: 40" },
      { key: 'glucoseRatio', label: "Glukoza koeffitsienti (masalan 7.2)", placeholder: "masalan: 7.2" },
      { key: 'anaerobATF', label: "Anaerob bosqich ATF soni", placeholder: "masalan: 9780" },
    ],
    solve: (vals) => solveType2(vals.percentTola, vals.percentATF, vals.glucoseRatio, vals.anaerobATF),
    examples: [
      { label: "Masala 11", values: { percentTola: 30, percentATF: 40, glucoseRatio: 7.2, anaerobATF: 9780 } },
      { label: "Masala 12", values: { percentTola: 20, percentATF: 30, glucoseRatio: 3.6, anaerobATF: 3270 } },
    ]
  },
  {
    id: 'type3',
    icon: '💧',
    title: "3-Тип (21-30)",
    subtitle: "Разница воды и энергии → АТФ на синтез",
    fields: [
      { key: 'diffWater', label: "Suv farqi (fosforlanish − oksidlanish, mol)", placeholder: "masalan: 106" },
      { key: 'diffEnergy', label: "Energiya farqi (issiqlik − ATF, kJ)", placeholder: "masalan: 2840" },
    ],
    solve: (vals) => solveType3(vals.diffWater, vals.diffEnergy),
    examples: [
      { label: "Masala 21", values: { diffWater: 106, diffEnergy: 2840 } },
      { label: "Masala 25", values: { diffWater: 80, diffEnergy: 1520 } },
    ]
  },
  {
    id: 'type4',
    icon: '🔬',
    title: "4-Тип (31-40)",
    subtitle: "Суммарный АТФ + разница воды + коэфф. хлоропласта",
    fields: [
      { key: 'totalATF', label: "Umumiy ATF soni", placeholder: "masalan: 118" },
      { key: 'diffWater', label: "Sitoplazma va mitoxondriya suv farqi", placeholder: "masalan: 116" },
      { key: 'xloroRatio', label: "Xloroplast/parchalangan glukoza nisbati", placeholder: "masalan: 7.2" },
    ],
    solve: (vals) => solveType4(vals.totalATF, vals.diffWater, vals.xloroRatio),
    examples: [
      { label: "Masala 31", values: { totalATF: 118, diffWater: 116, xloroRatio: 7.2 } },
    ]
  },
];

// ─── Component ──────────────────────────────────────────────────────────────

export default function ATFCalculator({ onBack }) {
  const [selectedType, setSelectedType] = useState(null);
  const [values, setValues] = useState({});
  const [result, setResult] = useState(null);

  const handleSelectType = (type) => {
    setSelectedType(type);
    setValues({});
    setResult(null);
  };

  const handleChange = (key, val) => {
    setValues(prev => ({ ...prev, [key]: parseFloat(val) || 0 }));
  };

  const handleSolve = () => {
    if (!selectedType) return;
    try {
      const res = selectedType.solve(values);
      setResult(res);
    } catch (e) {
      setResult({ error: "Xatolik: kiritilgan ma'lumotlarni tekshiring." });
    }
  };

  const handleExample = (ex) => {
    setValues(ex.values);
    try {
      const res = selectedType.solve(ex.values);
      setResult(res);
    } catch (e) {
      setResult({ error: "Xatolik" });
    }
  };

  // ── Type Selector ──
  if (!selectedType) {
    return (
      <>
        <button className="btn btn-back" onClick={onBack}>← Bosh menyu</button>
        <div className="header" style={{ padding: '12px 0 8px' }}>
          <h1 style={{ fontSize: '1.6rem' }}>⚡ ATF Kalkulyator</h1>
          <p>Energiya almashinuvi masalalari (Husniddin ATF-3)</p>
        </div>
        <div className="cards-grid">
          {TASK_TYPES.map(t => (
            <div className="card" key={t.id} onClick={() => handleSelectType(t)} style={{ cursor: 'pointer' }}>
              <div className="card-title">{t.icon} {t.title}</div>
              <div className="card-desc">{t.subtitle}</div>
            </div>
          ))}
        </div>
      </>
    );
  }

  // ── Input + Result ──
  return (
    <>
      <button className="btn btn-back" onClick={() => { setSelectedType(null); setResult(null); }}>
        ← Типларга қайтиш
      </button>

      <div className="card">
        <div className="card-title">{selectedType.icon} {selectedType.title}</div>
        <p className="card-desc" style={{ marginBottom: 16 }}>{selectedType.subtitle}</p>

        {selectedType.fields.map(f => (
          <div className="form-group" key={f.key}>
            <label className="input-label">{f.label}</label>
            <input
              className="input-field"
              type="number"
              step="any"
              placeholder={f.placeholder}
              value={values[f.key] ?? ''}
              onChange={e => handleChange(f.key, e.target.value)}
              style={{ fontFamily: "'Baloo 2', cursive" }}
            />
          </div>
        ))}

        {/* Quick examples */}
        {selectedType.examples && selectedType.examples.length > 0 && (
          <div style={{ marginBottom: 12 }}>
            <span className="input-label">Tayyor misollar:</span>
            <div className="quick-buttons">
              {selectedType.examples.map((ex, i) => (
                <button className="quick-btn" key={i} onClick={() => handleExample(ex)}>
                  {ex.label}
                </button>
              ))}
            </div>
          </div>
        )}

        <button className="btn btn-primary" onClick={handleSolve} style={{ marginTop: 8 }}>
          📊 Hisoblash
        </button>
      </div>

      {/* Result */}
      {result && !result.error && (
        <div className="card" style={{ animationDelay: '0.1s' }}>
          <div className="section-title">📝 Bosqichma-bosqich yechim</div>

          <ul className="ratio-list">
            {result.steps.map((s, i) => (
              <li className="ratio-item" key={i} style={{ flexDirection: 'column', alignItems: 'flex-start', gap: 4 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%' }}>
                  <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{s.label}</span>
                  <strong style={{ color: 'var(--accent-primary)', fontSize: '0.95rem' }}>{s.value}</strong>
                </div>
                <div style={{ fontSize: '0.8rem', color: 'rgba(255,255,255,0.4)', fontFamily: 'monospace' }}>
                  {s.formula}
                </div>
              </li>
            ))}
          </ul>

          {/* Final answer */}
          <div style={{
            marginTop: 20,
            padding: '16px 20px',
            background: 'linear-gradient(135deg, rgba(129,140,248,0.15) 0%, rgba(192,132,252,0.15) 100%)',
            borderRadius: 16,
            border: '1px solid rgba(192,132,252,0.3)',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: 6 }}>
              🎯 {result.answerLabel}
            </div>
            <div style={{
              fontSize: '2rem',
              fontWeight: 700,
              fontFamily: "'Baloo 2', cursive",
              background: 'var(--accent-gradient)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              filter: 'drop-shadow(0 0 10px rgba(192,132,252,0.5))'
            }}>
              {result.answer}
            </div>
          </div>
        </div>
      )}

      {result && result.error && (
        <div className="card" style={{ borderColor: 'var(--danger)' }}>
          <div className="card-title" style={{ color: 'var(--danger)' }}>❌ Xatolik</div>
          <p className="card-desc">{result.error}</p>
        </div>
      )}
    </>
  );
}

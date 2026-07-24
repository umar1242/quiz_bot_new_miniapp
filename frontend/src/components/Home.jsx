import React, { useState } from 'react';

export default function Home({ onSelectType, onOpenATF }) {
  const [activeMenu, setActiveMenu] = useState('main'); // main, mendel, special

  return (
    <>
      <div className="header">
        <h1>🧬 BioHelper</h1>
        <p>Помощник по задачам биологии</p>
      </div>

      {activeMenu === 'main' && (
        <div className="cards-grid">
          <div className="card" onClick={() => setActiveMenu('mendel')} style={{ cursor: 'pointer' }}>
            <div className="card-title">
              🧬 Менделевское наследование
            </div>
            <div className="card-desc">
              Независимое наследование признаков (Моно-, Ди-, Полигибридное)
            </div>
          </div>

          <div className="card" onClick={() => onSelectType('linked', 2)} style={{ cursor: 'pointer' }}>
            <div className="card-title">
              🔗 Сцепленное наследование
            </div>
            <div className="card-desc">
              Аутосомное сцепление генов (с кроссинговером или без)
            </div>
          </div>

          <div className="card" onClick={() => setActiveMenu('special')} style={{ cursor: 'pointer' }}>
            <div className="card-title">
              🧪 Неаллельное и спец. наследование
            </div>
            <div className="card-desc">
              Эпистаз, Комплементарность, Полимерия, Группы крови (ABO) и Плейотропия
            </div>
          </div>

          <div className="card" onClick={onOpenATF} style={{ cursor: 'pointer' }}>
            <div className="card-title">
              ⚡ Energiya almashinuvi (ATF)
            </div>
            <div className="card-desc">
              Glikoliz, mitoxondriya, xloroplast — ATF, suv, CO₂ hisoblash
            </div>
          </div>
        </div>
      )}

      {activeMenu === 'mendel' && (
        <div className="card">
          <button className="btn btn-back" onClick={() => setActiveMenu('main')}>← Назад</button>
          <h2 className="card-title">Менделевское наследование</h2>
          <p className="card-desc" style={{ marginBottom: '16px' }}>Выберите тип скрещивания:</p>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <button className="btn btn-secondary" style={{ textAlign: 'left', justifyContent: 'flex-start' }} onClick={() => onSelectType('mono', 1)}>
              <strong>🧬 Моногибридное</strong> (1 ген)
            </button>
            <button className="btn btn-secondary" style={{ textAlign: 'left', justifyContent: 'flex-start' }} onClick={() => onSelectType('di', 2)}>
              <strong>🔬 Дигибридное</strong> (2 гена)
            </button>
            <button className="btn btn-secondary" style={{ textAlign: 'left', justifyContent: 'flex-start' }} onClick={() => onSelectType('poly', 3)}>
              <strong>🧪 Полигибридное</strong> (3-5 генов)
            </button>
          </div>
        </div>
      )}

      {activeMenu === 'special' && (
        <div className="card">
          <button className="btn btn-back" onClick={() => setActiveMenu('main')}>← Назад</button>
          <h2 className="card-title">Неаллельное и спец. наследование</h2>
          <p className="card-desc" style={{ marginBottom: '16px' }}>Выберите механизм взаимодействия генов:</p>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <button className="btn btn-secondary" style={{ textAlign: 'left', justifyContent: 'flex-start' }} onClick={() => onSelectType('epistasis')}>
              <strong>🎭 Эпистаз</strong> (Доминантный / Рецессивный)
            </button>
            <button className="btn btn-secondary" style={{ textAlign: 'left', justifyContent: 'flex-start' }} onClick={() => onSelectType('complementary')}>
              <strong>🧩 Комплементарность</strong> (9:7, 9:6:1, 9:3:4)
            </button>
            <button className="btn btn-secondary" style={{ textAlign: 'left', justifyContent: 'flex-start' }} onClick={() => onSelectType('polymeria')}>
              <strong>📊 Полимерия</strong> (Кумулятивная / Некумулятивная)
            </button>
            <button className="btn btn-secondary" style={{ textAlign: 'left', justifyContent: 'flex-start' }} onClick={() => onSelectType('blood')}>
              <strong>🩸 Группы крови</strong> (ABO, Кодоминантность & Rh)
            </button>
            <button className="btn btn-secondary" style={{ textAlign: 'left', justifyContent: 'flex-start' }} onClick={() => onSelectType('pleiotropy')}>
              <strong>⚠️ Плейотропия и летальные гены</strong> (Отсев гибнущих эмбрионов)
            </button>
          </div>
        </div>
      )}
    </>
  );
}


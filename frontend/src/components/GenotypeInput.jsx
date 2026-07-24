import React, { useState, useEffect } from 'react';
import { validateGenotype } from '../utils/genetics';

export default function GenotypeInput({ value, onChange, label, geneCount }) {
  const [validation, setValidation] = useState({ valid: true, error: '' });

  useEffect(() => {
    if (value) {
      setValidation(validateGenotype(value, geneCount));
    } else {
      setValidation({ valid: true, error: '' });
    }
  }, [value, geneCount]);

  const setQuick = (pattern) => {
    let result = '';
    const letters = ['A', 'B', 'C', 'D', 'E'];
    for (let i = 0; i < geneCount; i++) {
      const letter = letters[i] || 'X';
      if (pattern === 'dom') result += letter.toUpperCase() + letter.toUpperCase();
      if (pattern === 'het') result += letter.toUpperCase() + letter.toLowerCase();
      if (pattern === 'rec') result += letter.toLowerCase() + letter.toLowerCase();
    }
    onChange(result);
  };

  return (
    <div className="form-group">
      <label className="input-label">{label}</label>
      <input
        type="text"
        className="input-field"
        value={value}
        onChange={(e) => onChange(e.target.value.replace(/[^a-zA-Z]/g, ''))}
        placeholder={`Например: ${geneCount === 1 ? 'Aa' : geneCount === 2 ? 'AaBb' : 'AaBbCc'}`}
      />
      
      {value && (
        <div className={`validation-msg ${validation.valid ? 'success' : 'error'}`}>
          {validation.valid ? '✓ Корректный генотип' : `⚠ ${validation.error}`}
        </div>
      )}

      <div className="quick-buttons">
        <button className="quick-btn" onClick={() => setQuick('dom')}>Дом. гомозигота (AA)</button>
        <button className="quick-btn" onClick={() => setQuick('het')}>Гетерозигота (Aa)</button>
        <button className="quick-btn" onClick={() => setQuick('rec')}>Рец. гомозигота (aa)</button>
      </div>
    </div>
  );
}

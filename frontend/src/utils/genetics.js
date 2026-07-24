export function parseGenotype(genotype) {
  const pairs = [];
  for (let i = 0; i < genotype.length; i += 2) {
    pairs.push([genotype[i], genotype[i + 1]]);
  }
  return pairs;
}

export function generateGametes(allelePairs) {
  if (allelePairs.length === 0) return [''];
  const firstPair = allelePairs[0];
  const restGametes = generateGametes(allelePairs.slice(1));
  const gametes = [];
  for (const allele of firstPair) {
    for (const rest of restGametes) {
      gametes.push(allele + rest);
    }
  }
  return [...new Set(gametes)];
}

export function combineGametes(g1, g2) {
  let genotype = '';
  for (let i = 0; i < g1.length; i++) {
    const alleles = [g1[i], g2[i]].sort((a, b) => {
      if (a.toLowerCase() === b.toLowerCase()) {
        return a < b ? -1 : 1;
      }
      return a.toLowerCase() < b.toLowerCase() ? -1 : 1;
    });
    genotype += alleles.join('');
  }
  return genotype;
}

export function buildPunnettGrid(gametes1, gametes2) {
  const grid = [];
  for (let i = 0; i < gametes1.length; i++) {
    const row = [];
    for (let j = 0; j < gametes2.length; j++) {
      row.push(combineGametes(gametes1[i], gametes2[j]));
    }
    grid.push(row);
  }
  return grid;
}

export function normalizeGenotype(genotype) {
  const pairs = [];
  for (let i = 0; i < genotype.length; i += 2) {
    const alleles = [genotype[i], genotype[i + 1]].sort((a, b) => {
      if (a.toLowerCase() === b.toLowerCase()) return a < b ? -1 : 1;
      return a.toLowerCase() < b.toLowerCase() ? -1 : 1;
    });
    pairs.push(alleles.join(''));
  }
  return pairs.join('');
}

export function getGenotypeRatios(grid) {
  const counts = new Map();
  for (const row of grid) {
    for (const cell of row) {
      counts.set(cell, (counts.get(cell) || 0) + 1);
    }
  }
  return counts;
}

export function determinePhenotype(genotype, traitNames) {
  const traits = [];
  for (let i = 0; i < genotype.length; i += 2) {
    const pair = genotype.substring(i, i + 2);
    const geneIndex = i / 2;
    const isDominant = pair[0] === pair[0].toUpperCase();
    
    if (traitNames && traitNames[geneIndex]) {
      traits.push(isDominant ? traitNames[geneIndex].dominant : traitNames[geneIndex].recessive);
    } else {
      traits.push(isDominant ? `Доминантный ${geneIndex + 1}` : `Рецессивный ${geneIndex + 1}`);
    }
  }
  return traits.join(', ');
}

export function getPhenotypeRatios(grid, traitNames) {
  const counts = new Map();
  for (const row of grid) {
    for (const cell of row) {
      const phenotype = determinePhenotype(cell, traitNames);
      counts.set(phenotype, (counts.get(phenotype) || 0) + 1);
    }
  }
  return counts;
}

export function validateGenotype(genotype, expectedGenes) {
  if (genotype.length !== expectedGenes * 2) {
    return { valid: false, error: `Длина должна быть ${expectedGenes * 2} (пары аллелей)` };
  }
  for (let i = 0; i < genotype.length; i += 2) {
    const a = genotype[i];
    const b = genotype[i + 1];
    if (a.toLowerCase() !== b.toLowerCase()) {
      return { valid: false, error: `Аллели в паре ${i / 2 + 1} должны быть одной буквой` };
    }
    if (!/^[a-zA-Z]$/.test(a) || !/^[a-zA-Z]$/.test(b)) {
      return { valid: false, error: 'Используйте только латинские буквы' };
    }
  }
  return { valid: true, error: '' };
}

export function calculateCross(parent1, parent2, traitNames) {
  const pairs1 = parseGenotype(parent1);
  const pairs2 = parseGenotype(parent2);
  const gametes1 = generateGametes(pairs1);
  const gametes2 = generateGametes(pairs2);
  const grid = buildPunnettGrid(gametes1, gametes2);
  const genotypeRatios = getGenotypeRatios(grid);
  const phenotypeRatios = getPhenotypeRatios(grid, traitNames);
  return { pairs1, pairs2, gametes1, gametes2, grid, genotypeRatios, phenotypeRatios };
}

export function determineLinkedPhenotype(genotype, traitNames) {
  if (!genotype || !genotype.includes('/')) return '';
  const [left, right] = genotype.split('/');
  const leftGenes = left.split('.');
  const rightGenes = right.split('.');
  const traits = [];
  for (let i = 0; i < leftGenes.length; i++) {
    const a = leftGenes[i];
    const b = rightGenes[i];
    if (!a || !b) continue;
    const isDominant = a === a.toUpperCase() || b === b.toUpperCase();
    
    if (traitNames && traitNames[i]) {
      traits.push(isDominant ? traitNames[i].dominant : traitNames[i].recessive);
    } else {
      traits.push(isDominant ? `Дом. ${i + 1}` : `Рец. ${i + 1}`);
    }
  }
  return traits.join(', ');
}

export function getLinkedRadical(genotype) {
  if (!genotype || !genotype.includes('/')) return '';
  const [left, right] = genotype.split('/');
  const lGenes = left.split('.');
  const rGenes = right.split('.');
  let radical = '';
  for (let i = 0; i < lGenes.length; i++) {
    const a = lGenes[i] || '';
    const b = rGenes[i] || '';
    if (!a && !b) continue;
    const isDom = (a === a.toUpperCase() && /[A-Za-z]/.test(a) && a !== a.toLowerCase()) || 
                  (b === b.toUpperCase() && /[A-Za-z]/.test(b) && b !== b.toLowerCase());
    const letter = (a || b).toUpperCase();
    if (isDom) {
      radical += `${letter}_`;
    } else {
      radical += letter.toLowerCase() + letter.toLowerCase();
    }
  }
  return radical;
}

export function formatPercent(prob) {
  if (!prob || prob === 0) return '0%';
  const pct = prob * 100;
  if (pct < 0.01) {
    return `${parseFloat(pct.toFixed(4))}%`;
  }
  return `${parseFloat(pct.toFixed(2))}%`;
}

export function getPhenotypicRadical(phenotype, traitNames) {
  if (!phenotype) return '';
  const traits = phenotype.split(', ').map(t => t.trim());
  let radical = '';
  for (let i = 0; i < traits.length; i++) {
    const letter = String.fromCharCode(65 + i);
    const t = traits[i];
    
    let isDom = false;
    if (traitNames && traitNames[i]) {
      const domName = (traitNames[i].dominant || '').trim().toLowerCase();
      const recName = (traitNames[i].recessive || '').trim().toLowerCase();
      const tLower = t.toLowerCase();
      if (domName && tLower === domName) {
        isDom = true;
      } else if (recName && tLower === recName) {
        isDom = false;
      } else {
        isDom = tLower.includes('дом') || tLower.includes('dom');
      }
    } else {
      isDom = t.toLowerCase().includes('дом') || t.toLowerCase().includes('dom');
    }
    
    if (isDom) {
      radical += `${letter}_`;
    } else {
      radical += letter.toLowerCase() + letter.toLowerCase();
    }
  }
  return radical;
}

export function getMendelianRadical(genotype) {
  if (!genotype) return '';
  let radical = '';
  for (let i = 0; i < genotype.length; i += 2) {
    const pair = genotype.substring(i, i + 2);
    const a = pair[0] || '';
    const b = pair[1] || '';
    const isDom = (a === a.toUpperCase() && /[A-Za-z]/.test(a) && a !== a.toLowerCase()) || 
                  (b === b.toUpperCase() && /[A-Za-z]/.test(b) && b !== b.toLowerCase());
    const letter = a.toUpperCase();
    if (isDom) {
      radical += `${letter}_`;
    } else {
      radical += letter.toLowerCase() + letter.toLowerCase();
    }
  }
  return radical;
}

export function calculateLinkedCross(parent1, parent2, traitNames, distance1 = 0, distance2 = 0, dcoPercent = 0) {
  const getLinkedGametesWithProbs = (p) => {
    const [left, right] = p.split('/');
    const lGenes = left.split('.');
    const rGenes = right.split('.');
    const geneCount = lGenes.length;
    
    const map = new Map();
    const add = (g, prob, type = 'NR') => {
      const existing = map.get(g);
      if (existing) {
        existing.prob += prob;
      } else {
        map.set(g, { gamete: g, prob, type });
      }
    };
    
    if (geneCount === 2) {
      const rf = distance1 / 100;
      if (rf > 0) {
        const nr1 = `${lGenes[0]}.${lGenes[1]}`;
        const nr2 = `${rGenes[0]}.${rGenes[1]}`;
        const r1 = `${lGenes[0]}.${rGenes[1]}`;
        const r2 = `${rGenes[0]}.${lGenes[1]}`;
        
        add(nr1, (1 - rf) / 2, 'NR');
        add(nr2, (1 - rf) / 2, 'NR');
        add(r1, rf / 2, 'SCO');
        add(r2, rf / 2, 'SCO');
      } else {
        add(left, 0.5, 'NR');
        add(right, 0.5, 'NR');
      }
    } else if (geneCount === 3) {
      // Формула учебника: d1 = SCO_I%, d2 = SCO_II%, DCO% — прямые частоты
      // NR = 100% - SCO_I - SCO_II - DCO
      const pSCO1 = distance1 / 100;
      const pSCO2 = distance2 / 100;
      const pDCO = dcoPercent / 100;
      
      if (pSCO1 > 0 || pSCO2 > 0 || pDCO > 0) {
        const pNR = Math.max(0, 1.0 - pSCO1 - pSCO2 - pDCO);
        
        // 1. Некроссоверные (NR) — родительские
        const nr1 = `${lGenes[0]}.${lGenes[1]}.${lGenes[2]}`;
        const nr2 = `${rGenes[0]}.${rGenes[1]}.${rGenes[2]}`;
        add(nr1, pNR / 2, 'NR');
        add(nr2, pNR / 2, 'NR');
        
        // 2. SCO I — одинарный кроссинговер между генами 1 и 2
        const sco1_1 = `${rGenes[0]}.${lGenes[1]}.${lGenes[2]}`;
        const sco1_2 = `${lGenes[0]}.${rGenes[1]}.${rGenes[2]}`;
        add(sco1_1, pSCO1 / 2, 'SCO I');
        add(sco1_2, pSCO1 / 2, 'SCO I');
        
        // 3. SCO II — одинарный кроссинговер между генами 2 и 3
        const sco2_1 = `${lGenes[0]}.${lGenes[1]}.${rGenes[2]}`;
        const sco2_2 = `${rGenes[0]}.${rGenes[1]}.${lGenes[2]}`;
        add(sco2_1, pSCO2 / 2, 'SCO II');
        add(sco2_2, pSCO2 / 2, 'SCO II');
        
        // 4. DCO — двойной кроссинговер (средний ген меняется)
        const dco1 = `${lGenes[0]}.${rGenes[1]}.${lGenes[2]}`;
        const dco2 = `${rGenes[0]}.${lGenes[1]}.${rGenes[2]}`;
        add(dco1, pDCO / 2, 'DCO');
        add(dco2, pDCO / 2, 'DCO');
      } else {
        add(left, 0.5, 'NR');
        add(right, 0.5, 'NR');
      }
    } else {
      add(left, 0.5, 'NR');
      add(right, 0.5, 'NR');
    }
    
    return Array.from(map.values()).filter(item => item.prob > 0);
  };
  
  const gametesProbs1 = getLinkedGametesWithProbs(parent1);
  const gametesProbs2 = getLinkedGametesWithProbs(parent2);
  
  const gametes1 = gametesProbs1.map(g => g.gamete);
  const gametes2 = gametesProbs2.map(g => g.gamete);
  
  const combineLinkedGametes = (g1, g2) => {
    return [g1, g2].sort().join('/');
  };
  
  const grid = [];
  const cellProbs = [];
  for (let i = 0; i < gametes1.length; i++) {
    const row = [];
    const probRow = [];
    for (let j = 0; j < gametes2.length; j++) {
      row.push(combineLinkedGametes(gametes1[i], gametes2[j]));
      probRow.push(gametesProbs1[i].prob * gametesProbs2[j].prob);
    }
    grid.push(row);
    cellProbs.push(probRow);
  }
  
  const genotypeRatios = new Map();
  for (let i = 0; i < grid.length; i++) {
    for (let j = 0; j < grid[i].length; j++) {
      const g = grid[i][j];
      const p = cellProbs[i][j];
      genotypeRatios.set(g, (genotypeRatios.get(g) || 0) + p);
    }
  }
  
  const phenotypeRatios = new Map();
  for (let i = 0; i < grid.length; i++) {
    for (let j = 0; j < grid[i].length; j++) {
      const g = grid[i][j];
      const p = cellProbs[i][j];
      const phenotype = determineLinkedPhenotype(g, traitNames);
      phenotypeRatios.set(phenotype, (phenotypeRatios.get(phenotype) || 0) + p);
    }
  }
  
  return { 
    parent1, 
    parent2, 
    gametes1, 
    gametes2, 
    gametesProbs1, 
    gametesProbs2, 
    cellProbs, 
    grid, 
    genotypeRatios, 
    phenotypeRatios, 
    crossType: 'linked' 
  };
}

// --- НЕАЛЛЕЛЬНОЕ И СПЕЦИАЛЬНОЕ НАСЛЕДОВАНИЕ ---

export function isLocusDominant(genotype, locusIndex = 0) {
  const start = locusIndex * 2;
  const a1 = genotype[start];
  const a2 = genotype[start + 1];
  if (!a1) return false;
  const isUpper1 = a1 === a1.toUpperCase() && /[A-Za-z]/.test(a1);
  const isUpper2 = a2 && a2 === a2.toUpperCase() && /[A-Za-z]/.test(a2);
  return isUpper1 || isUpper2;
}

export function determineEpistasisPhenotype(genotype, mode = 'dom_12_3_1', traitNames) {
  // locus 1 (genes 0,1) and locus 2 (genes 2,3)
  const hasA = isLocusDominant(genotype, 0);
  const hasB = isLocusDominant(genotype, 1);
  
  const name1 = (traitNames && traitNames[0]) || 'Эпистатический (Белый/Подавленный)';
  const name2 = (traitNames && traitNames[1]) || 'Окрашенный (Дом. A)';
  const name3 = (traitNames && traitNames[2]) || 'Рецессивный (aa)';

  if (mode === 'dom_12_3_1') {
    // Ген B подавляет ген A
    if (hasB) return name1; // B_A_ или B_aa -> 12/16
    if (hasA) return name2; // bbA_ -> 3/16
    return name3;           // bbaa -> 1/16
  }
  
  if (mode === 'dom_13_3') {
    // Подавляющий ген B (или bb) -> 13/16 против 3/16
    if (hasB || !hasA) return name1; // 13/16 (B_A_, B_aa, bbaa)
    return name2;                    // 3/16 (bbA_)
  }
  
  if (mode === 'rec_9_3_4') {
    // Рецессивный эпистаз: bb подавляет проявление гена A (Криптомерия)
    if (!hasB) return name1; // bbA_ или bbaa -> 4/16 (Криптомерный)
    if (hasA) return name2;  // B_A_ -> 9/16 (Пурпурный/Основной)
    return name3;           // B_aa -> 3/16 (Красный)
  }
  
  return determinePhenotype(genotype, traitNames);
}

export function determineComplementaryPhenotype(genotype, mode = 'comp_9_7', traitNames) {
  const hasA = isLocusDominant(genotype, 0);
  const hasB = isLocusDominant(genotype, 1);
  
  const t1 = (traitNames && traitNames[0]) || 'Новый комплементарный признак (A_B_)';
  const t2 = (traitNames && traitNames[1]) || 'Промежуточный признак (A_bb / aaB_)';
  const t3 = (traitNames && traitNames[2]) || 'Исходный/Рецессивный признак (aabb)';

  if (mode === 'comp_9_7') {
    if (hasA && hasB) return t1; // 9/16
    return t3;                   // 7/16 (A_bb, aaB_, aabb)
  }
  
  if (mode === 'comp_9_6_1') {
    if (hasA && hasB) return t1; // 9/16 (Дисковидная)
    if (hasA || hasB) return t2; // 6/16 (Сферическая)
    return t3;                   // 1/16 (Удлинённая)
  }
  
  if (mode === 'comp_9_3_4') {
    if (hasA && hasB) return t1; // 9/16
    if (hasA) return t2;         // 3/16
    return t3;                   // 4/16
  }
  
  return determinePhenotype(genotype, traitNames);
}

export function determinePolymeriaPhenotype(genotype, isCumulative = true, traitNames) {
  let domCount = 0;
  for (let i = 0; i < genotype.length; i++) {
    const char = genotype[i];
    if (char === char.toUpperCase() && /[A-Z]/.test(char)) {
      domCount++;
    }
  }
  
  if (!isCumulative) {
    // Некумулятивная полимерия (15 : 1)
    const domTrait = (traitNames && traitNames[0]) || 'Доминантный признак (Есть хотя бы 1 доминантный аллель)';
    const recTrait = (traitNames && traitNames[1]) || 'Рецессивный признак (Нет доминантных аллелей)';
    return domCount > 0 ? domTrait : recTrait;
  }
  
  // Кумулятивная полимерия (Зависит от количества доминантных аллелей)
  if (traitNames && traitNames[domCount]) {
    return traitNames[domCount];
  }
  
  const totalAlleles = genotype.length;
  if (domCount === totalAlleles) return `Максимальное проявление (${domCount} доминантных аллелей)`;
  if (domCount === 0) return `Минимальное/Отсутствует (${domCount} доминантных аллелей)`;
  return `Промежуточное проявление (${domCount} домин. аллелей из ${totalAlleles})`;
}

export function determineBloodGroupPhenotype(genotype) {
  // ABO System: IA, IB, i
  // Rh System: R (Rh+), r (Rh-)
  let bloodABO = '';
  let rhFactor = '';

  const isIA = (c) => c === 'A' || c === '1';
  const isIB = (c) => c === 'B' || c === '2';
  const isI0 = (c) => c === '0' || c === 'i' || c === 'o';

  // Разбор первых 2 символов ABO
  const aboPair = genotype.substring(0, 2);
  const a1 = aboPair[0];
  const a2 = aboPair[1];

  const hasA = isIA(a1) || isIA(a2);
  const hasB = isIB(a1) || isIB(a2);

  if (hasA && hasB) {
    bloodABO = 'IV (AB) группа крови [Кодоминирование]';
  } else if (hasA) {
    bloodABO = 'II (A) группа крови';
  } else if (hasB) {
    bloodABO = 'III (B) группа крови';
  } else {
    bloodABO = 'I (0) группа крови';
  }

  if (genotype.length >= 4) {
    const rhPair = genotype.substring(2, 4);
    const hasRhPlus = rhPair.includes('R') || rhPair.includes('+');
    rhFactor = hasRhPlus ? ' Rh(+)' : ' Rh(-)';
  }

  return bloodABO + rhFactor;
}

export function determinePleiotropyPhenotype(genotype, lethalGenotype, traitNames) {
  if (lethalGenotype && (genotype === lethalGenotype || normalizeGenotype(genotype) === normalizeGenotype(lethalGenotype))) {
    return '☠️ Летальный генотип (Гибель на эмбриональной стадии)';
  }
  
  return determinePhenotype(genotype, traitNames);
}

export function calculateSpecialCross(parent1, parent2, specialType, options = {}) {
  const pairs1 = parseGenotype(parent1);
  const pairs2 = parseGenotype(parent2);
  const gametes1 = generateGametes(pairs1);
  const gametes2 = generateGametes(pairs2);
  const rawGrid = buildPunnettGrid(gametes1, gametes2);

  const { epistasisMode, compMode, isCumulative, lethalGenotype, traitNames } = options;

  const phenotypeResolver = (cellGenotype) => {
    switch (specialType) {
      case 'epistasis':
        return determineEpistasisPhenotype(cellGenotype, epistasisMode, traitNames);
      case 'complementary':
        return determineComplementaryPhenotype(cellGenotype, compMode, traitNames);
      case 'polymeria':
        return determinePolymeriaPhenotype(cellGenotype, isCumulative, traitNames);
      case 'blood':
        return determineBloodGroupPhenotype(cellGenotype);
      case 'pleiotropy':
        return determinePleiotropyPhenotype(cellGenotype, lethalGenotype, traitNames);
      default:
        return determinePhenotype(cellGenotype, traitNames);
    }
  };

  // Фильтрация летальных генотипов из итогового расщепления, если есть летальность
  const genotypeRatios = new Map();
  const phenotypeRatios = new Map();

  let validCellsCount = 0;
  for (const row of rawGrid) {
    for (const cell of row) {
      const isLethal = specialType === 'pleiotropy' && 
        lethalGenotype && 
        (cell === lethalGenotype || normalizeGenotype(cell) === normalizeGenotype(lethalGenotype));

      if (isLethal) continue;

      validCellsCount++;
      genotypeRatios.set(cell, (genotypeRatios.get(cell) || 0) + 1);

      const pheno = phenotypeResolver(cell);
      phenotypeRatios.set(pheno, (phenotypeRatios.get(pheno) || 0) + 1);
    }
  }

  return {
    pairs1,
    pairs2,
    gametes1,
    gametes2,
    grid: rawGrid,
    genotypeRatios,
    phenotypeRatios,
    totalValidCells: validCellsCount,
    totalRawCells: rawGrid.length * rawGrid[0].length,
    crossType: specialType,
    specialType,
    options
  };
}


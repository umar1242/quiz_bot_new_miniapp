import React, { useState, useEffect } from 'react';
import Home from './components/Home';
import PunnettCalc from './components/PunnettCalc';
import PunnettResult from './components/PunnettResult';
import LinkedGenotypeInput from './components/LinkedGenotypeInput';
import SpecialGenotypeInput from './components/SpecialGenotypeInput';
import EpistasisInput from './components/EpistasisInput';
import ATFCalculator from './components/ATFCalculator';
import { calculateLinkedCross, calculateSpecialCross } from './utils/genetics';

function App() {
  const [currentScreen, setCurrentScreen] = useState('home');
  const [crossType, setCrossType] = useState('mono'); // mono, di, poly, linked, epistasis, complementary, polymeria, blood, pleiotropy
  const [resultData, setResultData] = useState(null);
  const [genesCount, setGenesCount] = useState(1);

  useEffect(() => {
    if (window.Telegram && window.Telegram.WebApp) {
      window.Telegram.WebApp.ready();
      window.Telegram.WebApp.expand();
    }
  }, []);

  const navigateTo = (screen) => setCurrentScreen(screen);

  const startCalculation = (type, count = 1) => {
    setCrossType(type);
    setGenesCount(count);
    navigateTo('punnett');
  };

  const showResults = (data) => {
    setResultData(data);
    navigateTo('result');
  };

  const isMendelian = ['mono', 'di', 'poly'].includes(crossType);
  const isSpecialOther = ['complementary', 'polymeria', 'blood', 'pleiotropy'].includes(crossType);

  return (
    <div className="app-container">
      {currentScreen === 'home' && (
        <Home onSelectType={startCalculation} onOpenATF={() => navigateTo('atf')} />
      )}

      {currentScreen === 'atf' && (
        <ATFCalculator onBack={() => navigateTo('home')} />
      )}
      
      {currentScreen === 'punnett' && isMendelian && (
        <PunnettCalc 
          crossType={crossType}
          genesCount={genesCount}
          onBack={() => navigateTo('home')}
          onCalculate={showResults}
        />
      )}

      {currentScreen === 'punnett' && crossType === 'linked' && (
        <LinkedGenotypeInput 
          onBack={() => navigateTo('home')}
          onSubmit={(data) => {
            const result = calculateLinkedCross(
              data.parent1, 
              data.parent2, 
              data.traitNames, 
              data.distance1, 
              data.distance2, 
              data.dcoPercent
            );
            showResults(result);
          }}
        />
      )}

      {currentScreen === 'punnett' && crossType === 'epistasis' && (
        <EpistasisInput
          onBack={() => navigateTo('home')}
          onSubmit={(data) => {
            const result = calculateSpecialCross(
              data.parent1,
              data.parent2,
              'epistasis',
              data.options
            );
            if (data.options && data.options.totalOffspring) {
              result.totalOffspring = data.options.totalOffspring;
            }
            showResults(result);
          }}
        />
      )}

      {currentScreen === 'punnett' && isSpecialOther && (
        <SpecialGenotypeInput 
          specialType={crossType}
          onBack={() => navigateTo('home')}
          onSubmit={(data) => {
            const result = calculateSpecialCross(
              data.parent1,
              data.parent2,
              data.specialType,
              data.options
            );
            if (data.options && data.options.totalOffspring) {
              result.totalOffspring = data.options.totalOffspring;
            }
            showResults(result);
          }}
        />
      )}
      
      {currentScreen === 'result' && (
        <PunnettResult
          data={resultData}
          onBack={() => navigateTo('punnett')}
          onNewCross={() => navigateTo('home')}
        />
      )}
    </div>
  );
}

export default App;

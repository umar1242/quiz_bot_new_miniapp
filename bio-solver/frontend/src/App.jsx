import { useState, useEffect } from 'react';

// Специальные символы для биологии
const BIO_SYMBOLS = [
  ['А', 'Т', 'Г', 'Ц', 'У', '×', '→', '♀', '♂'],
  ['X^A', 'X^a', 'Y', '_', '^', '(', ')', '⌫'],
  ['α', 'β', 'γ', 'δ', 'ε', 'λ', 'μ', 'σ'],
];

// Шаблоны задач
const TASK_TEMPLATES = [
  {
    id: 'genetics-mono',
    name: 'Моногибридное скрещивание',
    icon: '🧬',
    fields: [
      { id: 'P', label: 'Родители (P)', placeholder: 'Например: Aa × Aa' },
      { id: 'G', label: 'Гаметы (G)', placeholder: 'Например: A, a' },
      { id: 'F1', label: 'Потомство (F1)', placeholder: 'Например: AA, 2Aa, aa' },
      { id: 'phenotype', label: 'Фенотипическое соотношение', placeholder: 'Например: 3:1' },
    ]
  },
  {
    id: 'genetics-di',
    name: 'Дигибридное скрещивание',
    icon: '🔬',
    fields: [
      { id: 'P', label: 'Родители (P)', placeholder: 'Например: AaBb × aabb' },
      { id: 'G', label: 'Гаметы (G)', placeholder: 'Например: AB, Ab, aB, ab' },
      { id: 'F1', label: 'Потомство (F1)', placeholder: 'Заполните таблицу Пеннета' },
      { id: 'phenotype', label: 'Фенотипы', placeholder: 'Например: 9:3:3:1' },
    ]
  },
  {
    id: 'protein-synthesis',
    name: 'Биосинтез белка',
    icon: '🧪',
    fields: [
      { id: 'dna', label: 'ДНК', placeholder: 'Например: АТГ ЦЦА ГГТ' },
      { id: 'mrna', label: 'иРНК', placeholder: 'Автозаполнение: УАЦ ГГУ ЦЦА' },
      { id: 'protein', label: 'Белок (аминокислоты)', placeholder: 'Например: Тир-Гли-Про' },
    ]
  },
  {
    id: 'ecology-pyramid',
    name: 'Экологическая пирамида',
    icon: '🌿',
    fields: [
      { id: 'level1', label: 'Уровень 1 (продуценты)', placeholder: 'Масса/энергия', type: 'number' },
      { id: 'level2', label: 'Уровень 2 (консументы 1 порядка)', placeholder: '10% от уровня 1', type: 'number' },
      { id: 'level3', label: 'Уровень 3 (консументы 2 порядка)', placeholder: '10% от уровня 2', type: 'number' },
      { id: 'level4', label: 'Уровень 4 (консументы 3 порядка)', placeholder: '10% от уровня 3', type: 'number' },
    ]
  },
];

function App() {
  const [currentView, setCurrentView] = useState('home');
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [formData, setFormData] = useState({});
  const [subscriptMode, setSubscriptMode] = useState(false);
  const [superscriptMode, setSuperscriptMode] = useState(false);

  // Инициализация Telegram WebApp
  useEffect(() => {
    if (window.Telegram && window.Telegram.WebApp) {
      window.Telegram.WebApp.ready();
      window.Telegram.WebApp.expand();
    }
  }, []);

  const handleTemplateSelect = (template) => {
    setSelectedTemplate(template);
    setFormData({});
    setCurrentView('editor');
  };

  const handleFieldChange = (fieldId, value) => {
    setFormData(prev => ({
      ...prev,
      [fieldId]: value
    }));
  };

  const handleSymbolClick = (symbol) => {
    if (symbol === '_') {
      setSubscriptMode(!subscriptMode);
      setSuperscriptMode(false);
      return;
    }
    if (symbol === '^') {
      setSuperscriptMode(!superscriptMode);
      setSubscriptMode(false);
      return;
    }
    if (symbol === '⌫') {
      // Backspace - удаляем последний символ из активного поля
      return;
    }

    // Вставка символа в активное поле (упрощенно)
    const activeField = Object.keys(formData).pop() || 'P';
    const currentValue = formData[activeField] || '';
    handleFieldChange(activeField, currentValue + symbol);
  };

  const generateSolution = () => {
    setCurrentView('result');
  };

  const sendToTelegram = () => {
    if (window.Telegram && window.Telegram.WebApp) {
      window.Telegram.WebApp.sendData(JSON.stringify({
        template: selectedTemplate.id,
        data: formData
      }));
    }
  };

  // Главный экран - выбор шаблона
  if (currentView === 'home') {
    return (
      <div className="min-h-screen bg-gradient-to-br from-bio-dark to-bio-primary p-4">
        <div className="max-w-md mx-auto">
          <h1 className="text-3xl font-bold text-white mb-2 text-center">BioSolver</h1>
          <p className="text-bio-accent text-center mb-8">Решай биологические задачи в 3 клика</p>
          
          <div className="grid gap-4">
            {TASK_TEMPLATES.map((template) => (
              <button
                key={template.id}
                onClick={() => handleTemplateSelect(template)}
                className="bg-white/90 backdrop-blur-sm rounded-xl p-4 shadow-lg hover:shadow-xl transition-all duration-200 transform hover:scale-105"
              >
                <div className="flex items-center gap-4">
                  <span className="text-4xl">{template.icon}</span>
                  <div className="text-left">
                    <h3 className="font-semibold text-gray-800">{template.name}</h3>
                    <p className="text-sm text-gray-600">{template.fields.length} полей для заполнения</p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Экран редактора
  if (currentView === 'editor' && selectedTemplate) {
    return (
      <div className="min-h-screen bg-gray-50 pb-32">
        {/* Заголовок */}
        <div className="bg-bio-primary text-white p-4 sticky top-0 z-10">
          <div className="flex items-center gap-2">
            <button 
              onClick={() => setCurrentView('home')}
              className="text-white text-xl"
            >
              ←
            </button>
            <h2 className="text-xl font-bold">{selectedTemplate.icon} {selectedTemplate.name}</h2>
          </div>
        </div>

        {/* Поля ввода */}
        <div className="p-4 space-y-4">
          {selectedTemplate.fields.map((field) => (
            <div key={field.id}>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {field.label}
              </label>
              <input
                type={field.type || 'text'}
                value={formData[field.id] || ''}
                onChange={(e) => handleFieldChange(field.id, e.target.value)}
                placeholder={field.placeholder}
                className="w-full px-4 py-3 border-2 border-gray-200 rounded-lg focus:border-bio-primary focus:outline-none transition-colors"
              />
            </div>
          ))}
        </div>

        {/* Кнопка генерации */}
        <div className="fixed bottom-24 left-0 right-0 p-4">
          <button
            onClick={generateSolution}
            className="w-full bg-bio-primary hover:bg-bio-secondary text-white font-bold py-4 rounded-xl shadow-lg transition-colors"
          >
            ✨ Сформировать решение
          </button>
        </div>

        {/* Специальная клавиатура */}
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t-2 border-gray-200 p-2">
          <div className="flex gap-1 mb-2 overflow-x-auto">
            {BIO_SYMBOLS[0].map((symbol) => (
              <button
                key={symbol}
                onClick={() => handleSymbolClick(symbol)}
                className="px-3 py-2 bg-gray-100 hover:bg-bio-accent rounded-lg text-sm font-medium min-w-[40px]"
              >
                {symbol}
              </button>
            ))}
          </div>
          <div className="flex gap-1 overflow-x-auto">
            {BIO_SYMBOLS[1].map((symbol) => (
              <button
                key={symbol}
                onClick={() => handleSymbolClick(symbol)}
                className={`px-3 py-2 rounded-lg text-sm font-medium min-w-[40px] ${
                  subscriptMode || superscriptMode ? 'bg-bio-accent text-white' : 'bg-gray-100 hover:bg-bio-accent'
                }`}
              >
                {symbol}
              </button>
            ))}
            {BIO_SYMBOLS[2].map((symbol) => (
              <button
                key={symbol}
                onClick={() => handleSymbolClick(symbol)}
                className="px-3 py-2 bg-gray-100 hover:bg-bio-accent rounded-lg text-sm font-medium min-w-[40px]"
              >
                {symbol}
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Экран результата
  if (currentView === 'result') {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="max-w-md mx-auto bg-white rounded-xl shadow-lg overflow-hidden">
          {/* Заголовок решения */}
          <div className="bg-bio-primary text-white p-4">
            <h2 className="text-xl font-bold">{selectedTemplate.icon} {selectedTemplate.name}</h2>
            <p className="text-bio-accent text-sm">Решение сгенерировано автоматически</p>
          </div>

          {/* Содержимое решения */}
          <div className="p-6 space-y-4">
            {selectedTemplate.fields.map((field) => (
              formData[field.id] && (
                <div key={field.id}>
                  <p className="text-sm text-gray-600 font-medium">{field.label}</p>
                  <p className="text-lg text-gray-800">{formData[field.id]}</p>
                </div>
              )
            ))}
          </div>

          {/* Кнопки действий */}
          <div className="p-4 bg-gray-50 border-t">
            <button
              onClick={sendToTelegram}
              className="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-3 rounded-lg mb-2 flex items-center justify-center gap-2"
            >
              <span>📤</span> Отправить в Telegram
            </button>
            <button
              onClick={() => setCurrentView('editor')}
              className="w-full bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-3 rounded-lg"
            >
              ✏️ Редактировать
            </button>
          </div>
        </div>
      </div>
    );
  }

  return null;
}

export default App;

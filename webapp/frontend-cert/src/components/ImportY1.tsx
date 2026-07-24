import { useState } from "react";
import { api } from "../api";

interface Props {
  variantId: number;
  onImported: (msg: string) => void;
  onError: (msg: string) => void;
}

export function ImportY1({ variantId, onImported, onError }: Props) {
  const [mode, setMode] = useState<"text" | "file">("text");
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [mdMode, setMdMode] = useState(false); // v2: markdown mode toggle

  async function submitText() {
    if (!text.trim()) return;
    setBusy(true);
    try {
      const res = mdMode
        ? await api.importY1MdText(variantId, text)
        : await api.importY1Text(variantId, text);
      onImported(`Добавлено ${res.added} из ${res.found} заданий`);
      setText("");
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function submitFile(file: File) {
    setBusy(true);
    try {
      const isMd = file.name.toLowerCase().endsWith(".md");
      const res = (isMd || mdMode)
        ? await api.importY1MdFile(variantId, file)
        : await api.importY1File(variantId, file);
      onImported(`Добавлено ${res.added} из ${res.found} заданий`);
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card import-panel">
      <span className="label">Импорт текстовой части (Y1)</span>
      <div className="import-tabs">
        <button className={`import-tab ${mode === "text" ? "active" : ""}`} onClick={() => setMode("text")}>
          Вставить текст
        </button>
        <button className={`import-tab ${mode === "file" ? "active" : ""}`} onClick={() => setMode("file")}>
          Загрузить файл
        </button>
      </div>

      {/* v2: Markdown mode toggle */}
      <label className="md-toggle" style={{ display: "flex", alignItems: "center", gap: 8, margin: "8px 0", fontSize: 13 }}>
        <input
          type="checkbox"
          checked={mdMode}
          onChange={(e) => setMdMode(e.target.checked)}
        />
        <span>Markdown v2 <small style={{ opacity: 0.6 }}>(таблицы и рисунки inline)</small></span>
      </label>

      {mode === "text" ? (
        <>
          <textarea
            placeholder={"Savol matni?\n=\n#To'g'ri javob\n=\nJavob 2\n=\nJavob 3\n=\nJavob 4\n+\n..."}
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={5}
          />
          <div style={{ marginTop: 10, display: "flex", justifyContent: "flex-end" }}>
            <button className="btn btn-primary" onClick={submitText} disabled={busy || !text.trim()}>
              {busy ? <span className="spinner" /> : "Распознать и добавить"}
            </button>
          </div>
        </>
      ) : (
        <input
          type="file"
          accept=".txt,.docx,.pdf,.md"
          disabled={busy}
          onChange={(e) => e.target.files?.[0] && submitFile(e.target.files[0])}
        />
      )}

      <p className="hint">
        Формат: задания разделяются знаком «+», варианты ответа — знаком «=», правильный вариант
        начинается с «#». Если в задании есть рисунок — отметьте его маркером <code>[рис]</code>{" "}
        рядом с текстом: такое задание попадёт в раздел «нужен рисунок», и рисунок можно будет
        загрузить прямо на листе ответов.
      </p>
      <p className="hint">
        В файле <code>.md</code> можно использовать обычную markdown-таблицу вместо «+/=/#» —
        каждая строка таблицы станет отдельным заданием: первый столбец — вопрос, остальные —
        варианты ответа, правильный отмечается «#» в начале ячейки. Картинки, вставленные в
        markdown как base64 (<code>{'![...](data:image/...)'}</code>), прикрепятся к заданию
        автоматически; обычные ссылки/пути на файл система скачать не может — такое задание, как
        и с маркером <code>[рис]</code>, попадёт в раздел «нужен рисунок».
      </p>
      {mdMode && (
        <p className="hint" style={{ background: "rgba(108,92,231,0.08)", padding: "8px 12px", borderRadius: 8 }}>
          <strong>✨ Markdown v2:</strong> таблицы и рисунки сохраняются <em>на своём месте</em> внутри
          текста вопроса. Base64-картинки загружаются автоматически. Обычные ссылки становятся
          кнопками «📷 Загрузить рисунок» — нажмите на кнопку, чтобы загрузить рисунок прямо
          в нужную позицию. Pandoc grid-таблицы (<code>+---+---+</code>) автоматически конвертируются
          в GFM pipe-таблицы.
        </p>
      )}
      <p className="hint">
        Задания на этом листе можно создавать и вручную, в любом разделе, включая текстовую часть
        (Y1). Но учтите: повторный импорт из парсера полностью пересоздаёт раздел Y1 — все
        вручную добавленные там задания будут удалены и заменены заданиями из файла.
      </p>
    </div>
  );
}

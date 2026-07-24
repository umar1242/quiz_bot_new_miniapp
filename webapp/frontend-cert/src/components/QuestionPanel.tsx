import { useState } from "react";
import { api } from "../api";
import type { CertQuestion, O1Answer, O2Band, QType, Y1Option, Y2Option, Y2Pair } from "../types";
import { SECTION_LABELS } from "../types";
import { MarkdownText } from "./MarkdownText";
import { ImageUploader } from "./ImageUploader";
import { O1Editor } from "./editors/O1Editor";
import { O2Editor } from "./editors/O2Editor";
import { Y1Editor } from "./editors/Y1Editor";
import { Y2Editor } from "./editors/Y2Editor";

interface Props {
  variantId: number;
  question: CertQuestion | null; // null = создание нового задания
  newQType: QType | null;
  onClose: () => void;
  onSaved: (q: CertQuestion) => void;
  onDeleted: (id: number) => void;
  onError: (msg: string) => void;
}

function emptyDraft(qtype: QType): CertQuestion {
  const DEFAULT_Y2_PAIRS: Y2Pair[] = [
    { left: "", right: "A" },
    { left: "", right: "A" },
    { left: "", right: "A" },
  ];
  const DEFAULT_Y2_OPTIONS: Y2Option[] = [
    { text: "" }, { text: "" }, { text: "" },
    { text: "" }, { text: "" }, { text: "" },
  ];
  return {
    id: 0,
    number: 0,
    part: qtype === "O2" ? 2 : 1,
    qtype,
    text: "",
    points: 1,
    needs_image: false,
    images: [],
    options: qtype === "Y1" ? [{ text: "", is_correct: true }, { text: "", is_correct: false }, { text: "", is_correct: false }, { text: "", is_correct: false }] : undefined,
    pairs: qtype === "Y2" ? DEFAULT_Y2_PAIRS : undefined,
    y2options: qtype === "Y2" ? DEFAULT_Y2_OPTIONS : undefined,
    answers: qtype === "O1" ? [{ text: "", match_mode: "exact", tolerance: null }] : undefined,
    bands: qtype === "O2" ? [{ band_no: 1, prompt: "", reference_answer: "", match_mode: "numeric", tolerance: 0, max_points: 1 }] : undefined,
  };
}

export function QuestionPanel({ variantId, question, newQType, onClose, onSaved, onDeleted, onError }: Props) {
  const [draft, setDraft] = useState<CertQuestion>(question ?? emptyDraft(newQType!));
  const [busy, setBusy] = useState(false);
  const isNew = !question;

  async function save() {
    setBusy(true);
    try {
      const payload: Record<string, unknown> = { text: draft.text, points: draft.points, qtype: draft.qtype };
      if (draft.qtype === "Y1") payload.options = draft.options;
      if (draft.qtype === "Y2") {
        payload.pairs = draft.pairs;
        payload.options = draft.y2options; // A-F options stored via options field
      }
      if (draft.qtype === "O1") payload.answers = draft.answers;
      if (draft.qtype === "O2") payload.bands = draft.bands;

      const res = isNew
        ? await api.addQuestion(variantId, payload)
        : await api.updateQuestion(draft.id, payload);
      onSaved(res.question);
      onClose();
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    if (!question) return;
    if (!confirm("Удалить это задание?")) return;
    setBusy(true);
    try {
      await api.deleteQuestion(question.id);
      onDeleted(question.id);
      onClose();
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="panel-overlay" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="panel">
        <div className="panel-head">
          <div className="panel-head-title">
            <span className="badge">{draft.qtype}{draft.number ? ` · №${draft.number}` : ""}</span>
            <span style={{ color: "var(--ink-soft)", fontSize: 13 }}>{SECTION_LABELS[draft.qtype]}</span>
          </div>
          <button className="btn btn-ghost" onClick={onClose} aria-label="Закрыть">✕</button>
        </div>

        <div className="field">
          <span className="label">Текст задания</span>
          <textarea value={draft.text} onChange={(e) => setDraft({ ...draft, text: e.target.value })} rows={3} />
          {draft.text && (
            <details className="md-preview-wrap">
              <summary className="hint">Предпросмотр Markdown</summary>
              <MarkdownText content={draft.text} className="md-preview" />
            </details>
          )}
        </div>

        {draft.qtype === "Y1" && (
          <Y1Editor options={draft.options ?? []} onChange={(options: Y1Option[]) => setDraft({ ...draft, options })} />
        )}
        {draft.qtype === "Y2" && (
          <Y2Editor
            pairs={draft.pairs ?? []}
            y2options={draft.y2options ?? []}
            onChange={(pairs: Y2Pair[], y2options: Y2Option[]) => setDraft({ ...draft, pairs, y2options })}
          />
        )}
        {draft.qtype === "O1" && (
          <O1Editor answers={draft.answers ?? []} onChange={(answers: O1Answer[]) => setDraft({ ...draft, answers })} />
        )}
        {draft.qtype === "O2" && (
          <O2Editor bands={draft.bands ?? []} onChange={(bands: O2Band[]) => setDraft({ ...draft, bands })} />
        )}

        {!isNew && (
          <ImageUploader
            questionId={draft.id}
            images={draft.images}
            onChange={(images) => setDraft({ ...draft, images })}
            onError={onError}
          />
        )}
        {isNew && <p className="hint">Рисунок можно будет прикрепить после сохранения задания.</p>}

        <div className="panel-footer">
          {!isNew ? (
            <button className="btn btn-danger" onClick={remove} disabled={busy}>Удалить</button>
          ) : (
            <span />
          )}
          <button className="btn btn-primary" onClick={save} disabled={busy}>
            {busy ? <span className="spinner" /> : "Сохранить"}
          </button>
        </div>
      </div>
    </div>
  );
}

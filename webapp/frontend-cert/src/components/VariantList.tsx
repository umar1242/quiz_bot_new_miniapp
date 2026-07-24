import { useState } from "react";
import type { VariantBrief } from "../types";

interface Props {
  variants: VariantBrief[];
  onOpen: (id: number) => void;
  onCreate: (title: string) => void;
  onDelete: (id: number) => void;
  loading: boolean;
}

export function VariantList({ variants, onOpen, onCreate, onDelete, loading }: Props) {
  const [title, setTitle] = useState("");
  const [deletingId, setDeletingId] = useState<number | null>(null);

  async function handleDelete(e: React.MouseEvent, id: number, variantTitle: string) {
    e.stopPropagation();
    if (!confirm(`Удалить вариант «${variantTitle}»? Это действие нельзя отменить.`)) return;
    setDeletingId(id);
    try {
      await onDelete(id);
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div>
      <div className="new-variant-row">
        <input
          type="text"
          placeholder="Название варианта, напр. «Биология — вариант 1»"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && title.trim()) {
              onCreate(title.trim());
              setTitle("");
            }
          }}
        />
        <button
          className="btn btn-primary"
          onClick={() => {
            if (!title.trim()) return;
            onCreate(title.trim());
            setTitle("");
          }}
        >
          Создать
        </button>
      </div>

      {loading ? (
        <div className="empty-state"><span className="spinner" /></div>
      ) : variants.length === 0 ? (
        <div className="card empty-state">Пока нет ни одного варианта — создайте первый выше.</div>
      ) : (
        <div className="variant-list">
          {variants.map((v) => (
            <div
              className="card variant-row"
              key={v.id}
              onClick={() => onOpen(v.id)}
              style={{ cursor: "pointer" }}
            >
              <div className="variant-row-main">
                <span className="variant-row-title">{v.title}</span>
                <span className="variant-row-meta">
                  <span className={`status-dot ${v.status === "ready" ? "ready" : ""}`} />
                  {v.status === "ready" ? "готов" : "черновик"} · {v.question_count}/43 заданий
                </span>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                <button
                  className="btn btn-danger"
                  style={{ padding: "4px 10px", fontSize: "13px" }}
                  disabled={deletingId === v.id}
                  onClick={(e) => handleDelete(e, v.id, v.title)}
                  title="Удалить вариант"
                >
                  {deletingId === v.id ? <span className="spinner" /> : "🗑"}
                </button>
                <span style={{ color: "var(--ink-soft)" }}>
                  →
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

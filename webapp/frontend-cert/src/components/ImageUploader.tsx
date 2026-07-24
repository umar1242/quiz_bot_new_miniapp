import { useRef, useState } from "react";
import { api } from "../api";
import type { QuestionImage } from "../types";

interface Props {
  questionId: number | null;
  images: QuestionImage[];
  onChange: (images: QuestionImage[]) => void;
  onError: (msg: string) => void;
}

export function ImageUploader({ questionId, images, onChange, onError }: Props) {
  const [busy, setBusy] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleFile(file: File) {
    if (!questionId) {
      onError("Сначала сохраните задание, потом добавьте рисунок");
      return;
    }
    setBusy(true);
    try {
      const res = await api.uploadImage(questionId, file);
      onChange([...images, res.image]);
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setBusy(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  async function handleDelete(imageId: number) {
    if (!questionId) return;
    try {
      await api.deleteImage(questionId, imageId);
      onChange(images.filter((im) => im.id !== imageId));
    } catch (e) {
      onError((e as Error).message);
    }
  }

  return (
    <div className="field">
      <span className="label">Рисунок</span>
      <div className="image-strip">
        {images.map((im) => (
          <div className="image-thumb" key={im.id}>
            <img src={im.url} alt="" />
            <button onClick={() => handleDelete(im.id)} aria-label="Удалить рисунок">✕</button>
          </div>
        ))}
        <button className="image-upload-btn" onClick={() => inputRef.current?.click()} disabled={busy}>
          {busy ? "…" : "+ Добавить"}
        </button>
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          hidden
          onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
        />
      </div>
    </div>
  );
}

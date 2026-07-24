import { useRef, useState } from "react";
import { api } from "../../api";
import type { TakeQuestion } from "../../types";

interface Props {
  attemptId: number;
  question: TakeQuestion;
  onAnswered: (patch: Partial<TakeQuestion>) => void;
  onError: (msg: string) => void;
}

export function O2Take({ attemptId, question, onAnswered, onError }: Props) {
  const savedBands = (question.your_answer?.bands as Record<string, string>) ?? {};
  const [values, setValues] = useState<Record<number, string>>(() => {
    const init: Record<number, string> = {};
    (question.bands ?? []).forEach((b) => { init[b.id] = savedBands[String(b.id)] ?? ""; });
    return init;
  });
  const [imageUrl, setImageUrl] = useState<string | null>((question.your_answer?.image_url as string) ?? null);
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  async function uploadPhoto(file: File) {
    setUploading(true);
    try {
      const res = await api.uploadSolutionImage(attemptId, file);
      setImageUrl(res.url);
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setUploading(false);
    }
  }

  async function save() {
    setBusy(true);
    try {
      const bands: Record<string, string> = {};
      Object.entries(values).forEach(([k, v]) => { bands[k] = v; });
      const res = await api.submitPart2Answer(attemptId, question.id, { bands, image_url: imageUrl });
      onAnswered({
        answered: true,
        your_answer: { bands, image_url: imageUrl },
        points_earned: res.points_earned as number,
      });
    } catch (e) {
      onError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      {(question.bands ?? []).map((b) => (
        <div className="band-take-row" key={b.id}>
          <span className="band-take-label">{b.prompt || `Пункт ${b.band_no}`} <span className="badge">{b.max_points} б.</span></span>
          <input
            type="text"
            style={{ maxWidth: 160 }}
            value={values[b.id] ?? ""}
            onChange={(e) => setValues((v) => ({ ...v, [b.id]: e.target.value }))}
            placeholder="Ответ"
          />
        </div>
      ))}

      <div className="solution-photo-row">
        {imageUrl && <img className="solution-photo-preview" src={imageUrl} alt="Фото решения" />}
        <button className="btn" onClick={() => fileRef.current?.click()} disabled={uploading}>
          {uploading ? <span className="spinner" /> : imageUrl ? "Заменить фото решения" : "Прикрепить фото решения"}
        </button>
        <input ref={fileRef} type="file" accept="image/*" hidden onChange={(e) => e.target.files?.[0] && uploadPhoto(e.target.files[0])} />
      </div>

      <button className="btn btn-primary" onClick={save} disabled={busy}>
        {busy ? <span className="spinner" /> : question.answered ? "Обновить ответ" : "Сохранить ответ"}
      </button>

      <p className="hint">
        Баллы за пункты выше считаются автоматически. Ход решения и вычисления оцениваются по
        приложенному фото — прикрепите полное решение, чтобы задание было засчитано целиком.
      </p>
    </div>
  );
}

/**
 * Planner.tsx — вкладка «Учебный план» в cert_bot_miniapp.
 * Адаптирован из quiz_bot_new/webapp/static/index.html.
 * Показывает прогресс по активному плану и позволяет создавать/редактировать планы.
 */
import { useEffect, useState } from "react";
import { api } from "../api";

// ---------- Типы ----------

interface Material { id: number; title: string; count: number }
interface PlanItem { id: number; kind: string; ref_id: number; title: string; target: number }
interface Plan { id: number; title: string; start_day: string; end_day: string; items: PlanItem[] }
interface OverallStats {
  done: number; target: number; pct: number;
  correct: number; incorrect: number; answered: number; accuracy: number;
}
interface ItemStats {
  id: number; kind: string; ref_id: number; title: string;
  target: number; done: number; pct: number;
  correct: number; incorrect: number; answered: number; accuracy: number;
}
interface DashData {
  plan: { id: number; title: string; start_day: string; end_day: string; days_left: number | null } | null;
  overall: OverallStats;
  items: ItemStats[];
  bot_username: string;
}
interface PlanData {
  plan: Plan | null;
  bot_username: string;
}

// ---------- Вспомогательные ----------

const fmtd = (s: string) => {
  const p = String(s || "").split("-");
  return p.length === 3 ? `${p[2]}.${p[1]}.${p[0]}` : s;
};
const ymd = (d: Date) =>
  `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
const pct = (v: number) => Math.round((v || 0) * 100);
const WD = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

// ---------- Компонент ----------


export function Planner() {
  const tg = (window as unknown as { Telegram?: { WebApp?: { HapticFeedback?: { selectionChanged?: () => void; notificationOccurred?: (t: string) => void; impactOccurred?: (t: string) => void }; showConfirm?: (msg: string, cb: (ok: boolean) => void) => void } } }).Telegram?.WebApp;

  const [tab, setTab] = useState<"dash" | "plan">("dash");
  const [dash, setDash] = useState<DashData | null>(null);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [botUsername, setBotUsername] = useState("");
  const [materials, setMaterials] = useState<{ decks: Material[]; quizzes: Material[]; certs: Material[] }>({ decks: [], quizzes: [], certs: [] });
  const [loading, setLoading] = useState(true);

  // Черновик нового плана
  const [draft, setDraft] = useState<{ start: string | null; end: string | null; items: Array<{ kind: string; ref_id: number; title: string; target: number }> }>({ start: null, end: null, items: [] });
  const [calMonth, setCalMonth] = useState(() => { const d = new Date(); d.setDate(1); return d; });
  const [itemKind, setItemKind] = useState<"quiz" | "tf" | "cert">("quiz");
  const [selectedMaterial, setSelectedMaterial] = useState<number>(0);
  const [itemTarget, setItemTarget] = useState(1);

  // Добавление к существующему плану
  const [apKind, setApKind] = useState<"quiz" | "tf" | "cert">("quiz");
  const [apMaterial, setApMaterial] = useState<number>(0);
  const [apTarget, setApTarget] = useState(1);

  async function reloadAll() {
    try {
      const d = await api.getDashboard() as unknown as DashData;
      setDash(d);
      setBotUsername(d.bot_username || botUsername);
    } catch { setDash(null); }
    try {
      const p = await api.getPlan() as unknown as PlanData;
      setPlan(p.plan || null);
      setBotUsername(p.bot_username || botUsername);
    } catch { setPlan(null); }
  }

  useEffect(() => {
    (async () => {
      try { const m = await api.getMaterials(); setMaterials({ decks: m.decks ?? [], quizzes: m.quizzes ?? [], certs: m.certs ?? [] }); } catch { /* ignore */ }
      await reloadAll();
      setLoading(false);
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Устанавливаем начальный выбор материала при смене типа
  useEffect(() => {
    const items = itemKind === "quiz" ? materials.quizzes : itemKind === "tf" ? materials.decks : materials.certs;
    setSelectedMaterial(items[0]?.id ?? 0);
  }, [itemKind, materials]);
  useEffect(() => {
    const items = apKind === "quiz" ? materials.quizzes : apKind === "tf" ? materials.decks : materials.certs;
    setApMaterial(items[0]?.id ?? 0);
  }, [apKind, materials]);

  // ---------- Календарь ----------
  function renderCal() {
    const y = calMonth.getFullYear(), m = calMonth.getMonth();
    const lead = (new Date(y, m, 1).getDay() + 6) % 7;
    const dim = new Date(y, m + 1, 0).getDate();
    const todayStr = ymd(new Date());
    const cells: React.ReactElement[] = WD.map((w, i) => <div key={`wd-${i}`} className="pl-wd">{w}</div>);
    for (let i = 0; i < lead; i++) cells.push(<div key={`e-${i}`} className="pl-day empty" />);
    for (let d = 1; d <= dim; d++) {
      const ds = ymd(new Date(y, m, d));
      let cls = "pl-day";
      if (draft.start && draft.end) {
        if (ds >= draft.start && ds <= draft.end) cls += (ds === draft.start || ds === draft.end) ? " edge" : " in";
      } else if (draft.start && ds === draft.start) cls += " edge";
      if (ds === todayStr) cls += " today";
      cells.push(
        <div key={ds} className={cls} onClick={() => pickDay(ds)}>{d}</div>
      );
    }
    return cells;
  }

  function pickDay(ds: string) {
    setDraft(prev => {
      if (!prev.start || (prev.start && prev.end)) return { ...prev, start: ds, end: null };
      if (ds < prev.start) return { ...prev, start: ds, end: null };
      return { ...prev, end: ds };
    });
    tg?.HapticFeedback?.selectionChanged?.();
  }

  // ---------- Добавить задание в черновик ----------
  function addItem() {
    const items = itemKind === "quiz" ? materials.quizzes : itemKind === "tf" ? materials.decks : materials.certs;
    const mat = items.find(m => m.id === selectedMaterial);
    if (!mat) { alert("Нет материалов этого типа. Создай их в боте."); return; }
    if (draft.items.some(it => it.kind === itemKind && it.ref_id === mat.id)) {
      alert("Это задание уже добавлено."); return;
    }
    setDraft(prev => ({ ...prev, items: [...prev.items, { kind: itemKind, ref_id: mat.id, title: mat.title, target: Math.max(1, itemTarget) }] }));
    tg?.HapticFeedback?.impactOccurred?.("light");
  }

  function removeItem(i: number) {
    setDraft(prev => ({ ...prev, items: prev.items.filter((_, idx) => idx !== i) }));
  }

  // ---------- Сохранить план ----------
  async function savePlan() {
    if (!draft.start || !draft.end) { alert("Выбери период — начало и конец."); return; }
    if (!draft.items.length) { alert("Добавь хотя бы одно задание."); return; }
    try {
      await api.createPlan({ start_day: draft.start, end_day: draft.end, items: draft.items });
      tg?.HapticFeedback?.notificationOccurred?.("success");
      setDraft({ start: null, end: null, items: [] });
      await reloadAll();
      setTab("dash");
    } catch { alert("Не удалось сохранить план."); }
  }

  // ---------- Добавить задание к существующему плану ----------
  async function addToPlan() {
    const items = apKind === "quiz" ? materials.quizzes : apKind === "tf" ? materials.decks : materials.certs;
    const mat = items.find(m => m.id === apMaterial);
    if (!mat) { alert("Нет материалов этого типа."); return; }
    if (plan?.items.some(it => it.kind === apKind && it.ref_id === mat.id)) {
      alert("Это задание уже в плане."); return;
    }
    try {
      await api.addPlanItems([{ kind: apKind, ref_id: mat.id, title: mat.title, target: Math.max(1, apTarget) }]);
      tg?.HapticFeedback?.notificationOccurred?.("success");
      await reloadAll();
    } catch { alert("Не удалось добавить задание."); }
  }

  // ---------- Удалить план ----------
  function delPlan(id: number) {
    const go = async () => {
      try { await api.deletePlan(id); await reloadAll(); } catch { /* ignore */ }
    };
    if (tg?.showConfirm) tg.showConfirm("Удалить текущий план? Прогресс по нему пропадёт.", ok => { if (ok) go(); });
    else if (confirm("Удалить план?")) go();
  }

  // ---------- Запустить задание из планнера ----------
  function launch(itemId: number) {
    const url = `https://t.me/${botUsername}?start=pi_${itemId}`;
    const tgApp = (window as unknown as { Telegram?: { WebApp?: { openTelegramLink?: (url: string) => void; close?: () => void } } }).Telegram?.WebApp;
    if (tgApp) { tgApp.openTelegramLink?.(url); tgApp.close?.(); }
    else location.href = url;
  }

  if (loading) return <div className="empty-state"><span className="spinner" /></div>;

  const calTitle = calMonth.toLocaleDateString("ru-RU", { month: "long", year: "numeric" });
  const periodLabel = draft.start && draft.end
    ? `✅ Период: ${fmtd(draft.start)} — ${fmtd(draft.end)}`
    : draft.start ? `Начало ${fmtd(draft.start)} · выбери конец периода`
    : "Нажми на дату — начало периода";

  return (
    <div className="planner-wrap">
      <header className="app-header" style={{ flexDirection: "column", alignItems: "stretch", gap: 12 }}>
        <div>
          <p className="app-eyebrow">Milliy sertifikat · Biologiya</p>
          <h1 className="app-title">Учебный план</h1>
        </div>
        <div className="pl-seg">
          <button className={tab === "dash" ? "active" : ""} onClick={() => setTab("dash")}>📊 Прогресс</button>
          <button className={tab === "plan" ? "active" : ""} onClick={() => setTab("plan")}>🗓 Настройка плана</button>
        </div>
      </header>

      <div className="planner-content" style={{ paddingBottom: 0 }}>
        {/* ========== ДАШБОРД ========== */}
        {tab === "dash" && (
          <div className="pl-view">
            {dash && (
              <div style={{ textAlign: "right", padding: "0 16px 8px" }}>
                <span className="pl-pill">Прогресс плана: {pct(dash.overall?.pct ?? 0)}%</span>
              </div>
            )}

            {!dash?.plan ? (
              <div className="card">
                <div className="empty-state">📭 Плана пока нет.<br />Создай его во вкладке «🗓 План».</div>
                <button className="btn btn-primary" style={{ width: "100%", marginTop: 12 }} onClick={() => setTab("plan")}>
                  Создать план
                </button>
              </div>
            ) : (
              <>
                {/* Общий прогресс */}
                <div className="card pl-hero">
                  <div className="pl-hero-label">Общий прогресс</div>
                  <div className="pl-big-pct">{pct(dash.overall.pct)}<small>%</small></div>
                  <div className="pl-sub2">пройдено {dash.overall.done} из {dash.overall.target}
                    {dash.plan.days_left != null && ` · ${dash.plan.days_left > 0 ? `осталось ${dash.plan.days_left} дн` : dash.plan.days_left === 0 ? "последний день" : "период завершён"}`}
                  </div>
                  <div className="pl-path-track">
                    <div className="pl-path-fill" style={{ width: `${pct(dash.overall.pct)}%` }} />
                    <div className="pl-path-knob" style={{ left: `${pct(dash.overall.pct)}%` }}>
                      {pct(dash.overall.pct) >= 100 ? "🏁" : "🚶"}
                    </div>
                  </div>
                  <div className="pl-path-scale">
                    <span>{fmtd(dash.plan.start_day)}</span>
                    <span>цель {dash.overall.target}</span>
                    <span>{fmtd(dash.plan.end_day)}</span>
                  </div>
                </div>

                {/* Ответы */}
                <div className="card">
                  <h2>🎯 Ответы за период · точность {dash.overall.answered ? pct(dash.overall.accuracy) + "%" : "—"}</h2>
                  <div className="pl-split">
                    <div className="pl-ok" style={{ width: `${dash.overall.answered ? pct(dash.overall.correct / dash.overall.answered) : 0}%` }} />
                    <div className="pl-no" style={{ width: `${dash.overall.answered ? pct(dash.overall.incorrect / dash.overall.answered) : 0}%` }} />
                  </div>
                  <div className="pl-splitrow">
                    <div className="pl-b ok"><div className="pl-n">{dash.overall.correct}</div><div className="pl-l">✓ правильно</div></div>
                    <div className="pl-b no"><div className="pl-n">{dash.overall.incorrect}</div><div className="pl-l">✗ неправильно</div></div>
                  </div>
                </div>

                {/* По заданиям */}
                {dash.items.length > 0 && (
                  <div className="card">
                    <h2>📚 По заданиям</h2>
                    {dash.items.map(it => (
                      <div key={it.id} className="pl-item">
                        <div className="pl-item-top">
                          <span>{it.kind === "tf" ? "📇" : it.kind === "cert" ? "🎓" : "📚"}</span>
                          <span className="pl-item-name">{it.title}</span>
                          <span className="pl-item-cnt">{Math.min(it.done, it.target)}/{it.target} · {pct(it.pct)}%</span>
                        </div>
                        <div className="pl-bartrack"><div className="pl-barfill" style={{ width: `${pct(it.pct)}%` }} /></div>
                        <div className="pl-item-acc">
                          пройдено {it.done}× · <b>✓ {it.correct}</b> · <span style={{ color: "var(--danger)" }}>✗ {it.incorrect}</span> · точность {it.answered ? pct(it.accuracy) + "%" : "—"}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* ========== ПЛАН ========== */}
        {tab === "plan" && (
          <div className="pl-view">

            {/* Текущий план */}
            {plan && (
              <div className="card">
                <h2>📌 Текущий план <span className="pl-sub">{fmtd(plan.start_day)} — {fmtd(plan.end_day)}</span></h2>
                {plan.items.map(it => (
                  <div key={it.id} className="pl-prow">
                    <span>{it.kind === "tf" ? "📇" : it.kind === "cert" ? "🎓" : "📚"}</span>
                    <div className="pl-prow-grow">
                      <div className="pl-pname">{it.title}</div>
                      <div className="pl-pmeta">цель {it.target}× · {it.kind === "tf" ? "тест «Верно/Неверно»" : it.kind === "cert" ? "сертификат" : "квиз"}</div>
                    </div>
                    <button className="pl-play" onClick={() => launch(it.id)} title="Пройти с регистрацией">▶</button>
                  </div>
                ))}

                {/* Добавить задание к текущему плану */}
                <div style={{ borderTop: "1px solid var(--line)", marginTop: 12, paddingTop: 14 }}>
                  <h2 style={{ marginBottom: 12 }}>➕ Добавить задание</h2>
                  <div className="pl-seg">
                    <button className={apKind === "quiz" ? "active" : ""} onClick={() => setApKind("quiz")}>📚 Квиз</button>
                    <button className={apKind === "tf" ? "active" : ""} onClick={() => setApKind("tf")}>📇 Колода (В/Н)</button>
                    <button className={apKind === "cert" ? "active" : ""} onClick={() => setApKind("cert")}>🎓 Серт.</button>
                  </div>
                  <select className="pl-select" value={apMaterial} onChange={e => setApMaterial(Number(e.target.value))}>
                    {(apKind === "quiz" ? materials.quizzes : apKind === "tf" ? materials.decks : materials.certs).map(m => (
                      <option key={m.id} value={m.id}>{m.title} ({m.count})</option>
                    ))}
                    {(apKind === "quiz" ? materials.quizzes : apKind === "tf" ? materials.decks : materials.certs).length === 0 && (
                      <option value={0}>— нет материалов —</option>
                    )}
                  </select>
                  <div className="pl-row2">
                    <div>
                      <label className="pl-label">Раз за период</label>
                      <input type="number" min={1} max={99} value={apTarget} onChange={e => setApTarget(Number(e.target.value))} />
                    </div>
                    <button className="btn btn-primary" onClick={addToPlan}>＋</button>
                  </div>
                </div>

                <button className="btn" style={{ background: "transparent", color: "var(--danger)", border: "1.5px solid var(--danger)", width: "100%", marginTop: 12 }} onClick={() => delPlan(plan.id)}>
                  🗑 Удалить план
                </button>
              </div>
            )}

            {/* Новый план */}
            <div className="card">
              <h2>🗓 {plan ? "Создать новый план (заменит текущий)" : "Новый план"}</h2>

              {/* Календарь */}
              <div className="pl-cal-head">
                <button onClick={() => setCalMonth(new Date(calMonth.getFullYear(), calMonth.getMonth() - 1, 1))}>‹</button>
                <span className="pl-cal-title">{calTitle}</span>
                <button onClick={() => setCalMonth(new Date(calMonth.getFullYear(), calMonth.getMonth() + 1, 1))}>›</button>
              </div>
              <div className="pl-cal-grid">{renderCal()}</div>
              <div className="pl-period-label">{periodLabel}</div>
            </div>

            {/* Задания черновика */}
            <div className="card">
              <h2>➕ Добавить задание</h2>
              <div className="pl-seg">
                <button className={itemKind === "quiz" ? "active" : ""} onClick={() => setItemKind("quiz")}>📚 Квиз</button>
                <button className={itemKind === "tf" ? "active" : ""} onClick={() => setItemKind("tf")}>📇 Колода (В/Н)</button>
                <button className={itemKind === "cert" ? "active" : ""} onClick={() => setItemKind("cert")}>🎓 Серт.</button>
              </div>
              <select className="pl-select" value={selectedMaterial} onChange={e => setSelectedMaterial(Number(e.target.value))}>
                {(itemKind === "quiz" ? materials.quizzes : itemKind === "tf" ? materials.decks : materials.certs).map(m => (
                  <option key={m.id} value={m.id}>{m.title} ({m.count})</option>
                ))}
                {(itemKind === "quiz" ? materials.quizzes : itemKind === "tf" ? materials.decks : materials.certs).length === 0 && (
                  <option value={0}>— нет материалов —</option>
                )}
              </select>
              <div className="pl-row2">
                <div>
                  <label className="pl-label">Раз за период</label>
                  <input type="number" min={1} max={99} value={itemTarget} onChange={e => setItemTarget(Number(e.target.value))} />
                </div>
                <button className="btn btn-primary" onClick={addItem}>＋</button>
              </div>
            </div>

            <div className="card">
              <h2>📋 Задания плана {draft.items.length > 0 && <span className="pl-sub">{draft.items.length} шт.</span>}</h2>
              {draft.items.length === 0 ? (
                <div className="empty-state" style={{ padding: "16px 0" }}>Пока пусто. Добавь задания выше ☝️</div>
              ) : (
                draft.items.map((it, i) => (
                  <div key={i} className="pl-chip">
                    <span>{it.kind === "tf" ? "📇" : it.kind === "cert" ? "🎓" : "📚"}</span>
                    <div className="pl-chip-grow">
                      <div className="pl-cname">{it.title}</div>
                      <div className="pl-pmeta">{it.kind === "tf" ? "тест «Верно/Неверно»" : it.kind === "cert" ? "сертификат" : "квиз"} · интервал {it.target}×</div>
                    </div>
                    <button className="icon-btn" onClick={() => removeItem(i)}>✕</button>
                  </div>
                ))
              )}
              <button className="btn btn-primary" style={{ width: "100%", marginTop: 12 }} onClick={savePlan}>
                💾 Сохранить план
              </button>
              <p className="hint" style={{ textAlign: "center", marginTop: 8 }}>
                Запускай задания кнопкой ▶ в разделе «Текущий план» — только так прохождение засчитается.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

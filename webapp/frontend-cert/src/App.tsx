import { useEffect, useState } from "react";
import "./App.css";
import { api } from "./api";
import { AnswerSheet } from "./components/AnswerSheet";
import { ImportY1 } from "./components/ImportY1";
import { QuestionPanel } from "./components/QuestionPanel";
import { TakeTest } from "./components/TakeTest";
import { VariantList } from "./components/VariantList";
import { TakeList } from "./components/TakeList";


import type { CertQuestion, QType, Variant, VariantBrief } from "./types";

type Toast = { kind: "ok" | "error"; text: string } | null;

function useTakeParams(): { variantId: number; attemptId: number | null } | null {
  const params = new URLSearchParams(window.location.search);
  const take = params.get("take");
  if (!take) return null;
  const attempt = params.get("attempt");
  return { variantId: Number(take), attemptId: attempt ? Number(attempt) : null };
}

export default function App() {
  useEffect(() => {
    window.Telegram?.WebApp?.ready();
    window.Telegram?.WebApp?.expand();
  }, []);

  const takeParams = useTakeParams();

  const [variants, setVariants] = useState<VariantBrief[]>([]);
  const [listLoading, setListLoading] = useState(true);
  const [variant, setVariant] = useState<Variant | null>(null);
  const [panel, setPanel] = useState<{ question: CertQuestion | null; newQType: QType | null } | null>(null);
  const [toast, setToast] = useState<Toast>(null);
  const [takeState, setTakeState] = useState<{ variantId: number; attemptId: number | null } | null>(null);
  const [appTab, setAppTab] = useState<"tests" | "take">("tests");

  function notify(text: string, kind: "ok" | "error" = "ok") {
    setToast({ kind, text });
    setTimeout(() => setToast(null), 3200);
  }

  async function loadList() {
    setListLoading(true);
    try {
      const res = await api.listVariants();
      setVariants(res.variants);
    } catch (e) {
      notify((e as Error).message, "error");
    } finally {
      setListLoading(false);
    }
  }

  useEffect(() => {
    if (!takeParams) loadList();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function openVariant(id: number) {
    try {
      const v = await api.getVariant(id);
      setVariant(v);
    } catch (e) {
      notify((e as Error).message, "error");
    }
  }

  async function createVariant(title: string) {
    try {
      const res = await api.createVariant(title);
      await loadList();
      openVariant(res.id);
    } catch (e) {
      notify((e as Error).message, "error");
    }
  }

  function refreshVariant() {
    if (variant) openVariant(variant.id);
  }

  function openTake(id: number) {
    setTakeState({ variantId: id, attemptId: null });
  }

  async function deleteVariant(id: number) {
    try {
      await api.deleteVariant(id);
      await loadList();
      notify("Вариант удалён");
    } catch (e) {
      notify((e as Error).message, "error");
    }
  }

  const activeTake = takeState ?? takeParams;

  if (activeTake) {
    return (
      <div className="app">
        <TakeTest
          variantId={activeTake.variantId}
          initialAttemptId={activeTake.attemptId}
          onBack={takeState ? () => setTakeState(null) : undefined}
        />
      </div>
    );
  }

  if (!variant) {
    return (
      <div className="app" style={{ paddingBottom: "70px" }}>
        <header className="app-header">
          <div>
            <p className="app-eyebrow">Milliy sertifikat · Biologiya</p>
            <h1 className="app-title">
              {appTab === "take" ? "Прохождение тестов" : "Конструктор вариантов"}
            </h1>
          </div>
        </header>

        {appTab === "take" ? (
          <TakeList variants={variants} onTake={openTake} loading={listLoading} />
        ) : (
          <VariantList variants={variants} onOpen={openVariant} onCreate={createVariant} onDelete={deleteVariant} loading={listLoading} />
        )}

        {toast && <div className={`toast ${toast.kind === "error" ? "error" : ""}`}>{toast.text}</div>}
        
        {/* Нижняя навигация */}
        <nav className="planner-nav">
          <button className={`pl-navbtn ${appTab === "tests" ? "active" : ""}`} onClick={() => setAppTab("tests")}>
            <span className="pl-ni">🛠</span>
            <span className="pl-nl">Конструктор</span>
          </button>
          <button className={`pl-navbtn ${appTab === "take" ? "active" : ""}`} onClick={() => setAppTab("take")}>
            <span className="pl-ni">▶️</span>
            <span className="pl-nl">Прохождение</span>
          </button>
        </nav>
      </div>
    );
  }




  return (
    <div className="app">
      <header className="app-header">
        <div>
          <button className="back-btn" onClick={() => { setVariant(null); loadList(); }}>← Все варианты</button>
          <h1 className="app-title">{variant.title}</h1>
        </div>
        <button
          className={`btn ${variant.status === "ready" ? "btn-primary" : ""}`}
          onClick={async () => {
            const next = variant.status === "ready" ? "draft" : "ready";
            await api.setStatus(variant.id, next);
            refreshVariant();
          }}
        >
          {variant.status === "ready" ? "Готов ✓" : "Отметить готовым"}
        </button>
      </header>

      <ImportY1
        variantId={variant.id}
        onImported={(msg) => {
          notify(msg);
          refreshVariant();
        }}
        onError={(msg) => notify(msg, "error")}
      />

      <AnswerSheet
        questions={variant.questions}
        progress={variant.progress}
        selectedId={panel?.question?.id ?? null}
        onSelectQuestion={(q) => setPanel({ question: q, newQType: null })}
        onAddInSection={(qtype) => setPanel({ question: null, newQType: qtype })}
      />

      {panel && (
        <QuestionPanel
          variantId={variant.id}
          question={panel.question}
          newQType={panel.newQType}
          onClose={() => setPanel(null)}
          onSaved={() => {
            notify("Сохранено");
            refreshVariant();
          }}
          onDeleted={() => {
            notify("Удалено");
            refreshVariant();
          }}
          onError={(msg) => notify(msg, "error")}
        />
      )}

      {toast && <div className={`toast ${toast.kind === "error" ? "error" : ""}`}>{toast.text}</div>}
    </div>
  );
}

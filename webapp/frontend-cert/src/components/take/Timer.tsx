import { useEffect, useState } from "react";

interface Props {
  secondsLeft: number;
  onExpire: () => void;
}

function fmt(total: number): string {
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export function Timer({ secondsLeft, onExpire }: Props) {
  const [left, setLeft] = useState(secondsLeft);

  useEffect(() => setLeft(secondsLeft), [secondsLeft]);

  useEffect(() => {
    if (left <= 0) {
      onExpire();
      return;
    }
    const t = setTimeout(() => setLeft((v) => v - 1), 1000);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [left]);

  return <span className={`timer ${left <= 60 ? "low" : ""}`}>{fmt(Math.max(0, left))}</span>;
}

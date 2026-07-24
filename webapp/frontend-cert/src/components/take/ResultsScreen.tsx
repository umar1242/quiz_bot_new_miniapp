import type { ResultsView } from "../../types";

export function ResultsScreen({ results }: { results: ResultsView }) {
  return (
    <div>
      <div className="card results-hero">
        <div className="results-pct">{results.total.percent}%</div>
        <div className="results-label">{results.total.earned} из {results.total.max} баллов</div>
      </div>
      <div className="results-grid">
        <div className="results-tile">
          <div className="results-tile-pct">{results.part1.percent}%</div>
          <div className="results-tile-label">Тестовая часть</div>
          <div className="results-tile-pts">{results.part1.earned}/{results.part1.max}</div>
        </div>
        <div className="results-tile">
          <div className="results-tile-pct">{results.part2.percent}%</div>
          <div className="results-tile-label">Письменная часть</div>
          <div className="results-tile-pts">{results.part2.earned}/{results.part2.max}</div>
        </div>
      </div>
    </div>
  );
}

export default function Metrics({ results }) {
  if (!results) return null;

  const formatBaht = (val) => new Intl.NumberFormat('th-TH', { style: 'decimal', maximumFractionDigits: 0 }).format(val) + ' บาท';

  return (
    <>
      <div className="divider"></div>
      <h2>4) ผลคำนวณงบประมาณ (จากตัวคูณ X)</h2>
      
      <div className="metrics-grid">
        <div className="metric-card">
          <span className="metric-label">Baseline total budget</span>
          <span className="metric-value">{formatBaht(results.metrics.baseline_total)}</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">Revised total budget</span>
          <span className="metric-value">{formatBaht(results.metrics.revised_total)}</span>
          <span className={`metric-delta ${results.metrics.revised_total - results.metrics.baseline_total > 0 ? 'positive' : 'negative'}`}>
            {(results.metrics.revised_total - results.metrics.baseline_total > 0 ? '+' : '')}
            {formatBaht(results.metrics.revised_total - results.metrics.baseline_total)}
          </span>
        </div>
        <div className="metric-card">
          <span className="metric-label">National baseline</span>
          <span className="metric-value">{formatBaht(results.metrics.national_baseline)}</span>
        </div>
        <div className="metric-card">
          <span className="metric-label">National revised</span>
          <span className="metric-value">{formatBaht(results.metrics.national_revised)}</span>
          <span className={`metric-delta ${results.metrics.national_revised - results.metrics.national_baseline > 0 ? 'positive' : 'negative'}`}>
            {(results.metrics.national_revised - results.metrics.national_baseline > 0 ? '+' : '')}
            {formatBaht(results.metrics.national_revised - results.metrics.national_baseline)}
          </span>
        </div>
      </div>
    </>
  );
}

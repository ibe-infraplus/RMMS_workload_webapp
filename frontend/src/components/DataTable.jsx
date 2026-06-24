export default function DataTable({ results }) {
  if (!results || !results.breakdown) return null;

  const formatBaht = (val) => new Intl.NumberFormat('th-TH', { style: 'decimal', maximumFractionDigits: 0 }).format(val);

  return (
    <>
      <div className="divider"></div>
      <h2>รายละเอียดโครงสร้างงบประมาณ (Breakdown)</h2>
      <div className="table-wrapper">
        <table className="data-grid">
          <thead>
            <tr>
              <th>Component</th>
              <th style={{textAlign: 'right'}}>Baseline (บาท)</th>
              <th style={{textAlign: 'right'}}>Revised (บาท)</th>
              <th style={{textAlign: 'right'}}>Diff (บาท)</th>
            </tr>
          </thead>
          <tbody>
            {results.breakdown.map((row, idx) => {
              const diff = row.revised - row.baseline;
              const isTotal = row.component.includes('Total');
              return (
                <tr key={idx} style={isTotal ? {fontWeight: 'bold', fontSize: '1.1rem', color: 'var(--accent)', borderTop: '2px solid var(--border-color)'} : {}}>
                  <td>{row.component}</td>
                  <td style={{textAlign: 'right'}}>{formatBaht(row.baseline)}</td>
                  <td style={{textAlign: 'right'}}>{formatBaht(row.revised)}</td>
                  <td style={{textAlign: 'right', color: diff > 0 ? '#ef4444' : 'inherit'}}>
                    {diff > 0 ? '+' : ''}{formatBaht(diff)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}

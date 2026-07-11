export default function FrameworkTable({ results }) {
  if (!results || !results.framework_comparison) return null;

  const formatBaht = (val) => new Intl.NumberFormat('th-TH', { style: 'decimal', maximumFractionDigits: 0 }).format(val);

  return (
    <>
      <div className="divider"></div>
      <h3 style={{marginTop: '20px', marginBottom: '10px'}}>เปรียบเทียบงบประมาณตามกรอบสัดส่วนกับคำนวณจริง (Budget Framework Comparison)</h3>
      <div className="table-wrapper">
        <table className="data-grid">
          <thead>
            <tr>
              <th>หมวดหมู่งาน</th>
              <th style={{textAlign: 'right'}}>สัดส่วนตามกรอบ (%)</th>
              <th style={{textAlign: 'right'}}>งบเป้าหมาย (บาท)</th>
              <th style={{textAlign: 'right'}}>งบคำนวณจริง (บาท)</th>
              <th style={{textAlign: 'right'}}>ส่วนต่าง (บาท)</th>
            </tr>
          </thead>
          <tbody>
            {results.framework_comparison.map((row, idx) => {
              const diff = row.revised_diff;
              return (
                <tr key={idx}>
                  <td>{row.category_name}</td>
                  <td style={{textAlign: 'right'}}>{row.target_pct.toFixed(1)}%</td>
                  <td style={{textAlign: 'right'}}>{formatBaht(row.revised_target)}</td>
                  <td style={{textAlign: 'right'}}>{formatBaht(row.revised_actual)}</td>
                  <td style={{textAlign: 'right', color: diff > 0 ? '#ef4444' : '#10b981', fontWeight: 'bold'}}>
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

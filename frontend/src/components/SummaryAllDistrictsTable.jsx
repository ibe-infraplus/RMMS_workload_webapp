export default function SummaryAllDistrictsTable({ results }) {
  if (!results || !results.summary_all) return null;

  return (
    <>
      <div className="divider"></div>
      <h2>7) Summary ทุกแขวง</h2>
      <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>ข้อมูลจริงจากสูตร model โดยยังไม่มีการ scale/cap งบประมาณ</p>
      <div className="table-wrapper">
        <table className="data-grid">
          <thead>
            <tr>
              <th>รหัส</th>
              <th>สำนักงาน</th>
              <th>แขวง</th>
              <th style={{ textAlign: 'right' }}>Base Workload Cost</th>
              <th style={{ textAlign: 'right' }}>Factor Cost</th>
              <th style={{ textAlign: 'right' }}>Fixed Cost</th>
              <th style={{ textAlign: 'right' }}>Total Budget</th>
            </tr>
          </thead>
          <tbody>
            {results.summary_all.map((row, idx) => (
              <tr key={idx}>
                <td>{row.dept3}</td>
                <td>{row.division_name}</td>
                <td style={{ fontWeight: 500 }}>{row.district_name}</td>
                <td style={{ textAlign: 'right' }}>{Number(row.base_workload_cost).toLocaleString()}</td>
                <td style={{ textAlign: 'right' }}>{Number(row.factor_cost).toLocaleString()}</td>
                <td style={{ textAlign: 'right' }}>{Number(row.fixed_cost).toLocaleString()}</td>
                <td style={{ textAlign: 'right', fontWeight: 'bold', color: 'var(--accent)' }}>{Number(row.total_budget_model).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

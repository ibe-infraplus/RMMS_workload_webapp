export default function WorkloadDetailTable({ results }) {
  if (!results || !results.workload_detail) return null;

  return (
    <>
      <div className="divider"></div>
      <h2>7) Workload Detail รายการคำนวณ</h2>
      <div className="table-wrapper" style={{ overflowX: 'auto' }}>
        <table className="data-grid">
          <thead>
            <tr>
              <th>Workload Item</th>
              <th>Category</th>
              <th style={{ textAlign: 'right' }}>Quantity</th>
              <th>Unit</th>
              <th style={{ textAlign: 'right' }}>D. Prob</th>
              <th style={{ textAlign: 'right' }}>Unit Cost</th>
              <th style={{ textAlign: 'right' }}>Base Value</th>
              <th style={{ textAlign: 'right' }}>Total Qty</th>
              <th style={{ textAlign: 'right' }}>Workload Unit</th>
              <th style={{ textAlign: 'right' }}>Workload Score</th>
              <th style={{ textAlign: 'right' }}>Base Cost (บาท)</th>
              <th style={{ textAlign: 'right' }}>Factor Index</th>
              <th style={{ textAlign: 'right' }}>Factor Cost</th>
              <th style={{ textAlign: 'right' }}>Total</th>
            </tr>
          </thead>
          <tbody>
            {results.workload_detail.map((row, idx) => (
              <tr key={idx}>
                <td style={{ fontWeight: 500 }}>{row.workload_item}</td>
                <td>{row.category}</td>
                <td style={{ textAlign: 'right' }}>{Number(row.quantity).toLocaleString(undefined, { maximumFractionDigits: 3 })}</td>
                <td>{row.unit}</td>
                <td style={{ textAlign: 'right' }}>{Number(row.damage_probability).toFixed(4)}</td>
                <td style={{ textAlign: 'right' }}>{Number(row.unit_cost).toLocaleString()}</td>
                <td style={{ textAlign: 'right' }}>{Number(row.base_value || 0).toFixed(4)}</td>
                <td style={{ textAlign: 'right' }}>{Number(row.total_quantity || 0).toLocaleString(undefined, { maximumFractionDigits: 3 })}</td>
                <td style={{ textAlign: 'right' }}>{Number(row.workload_unit || 0).toLocaleString(undefined, { maximumFractionDigits: 6 })}</td>
                <td style={{ textAlign: 'right' }}>{Number(row.workload_score || 0).toLocaleString(undefined, { maximumFractionDigits: 6 })}</td>
                <td style={{ textAlign: 'right' }}>{Number(row.base_workload_cost).toLocaleString()}</td>
                <td style={{ textAlign: 'right' }}>{Number(row.factor_index_0_1).toFixed(4)}</td>
                <td style={{ textAlign: 'right' }}>{Number(row.factor_cost).toLocaleString()}</td>
                <td style={{ textAlign: 'right', fontWeight: 'bold' }}>{Number(row.workload_plus_factor).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

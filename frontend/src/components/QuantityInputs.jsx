import { RotateCcw } from 'lucide-react';
import Expander from './Expander';

export default function QuantityInputs({
  configsByCategory,
  results,
  quantityUpdates,
  setQuantityUpdates,
  selectedDept3,
  initData
}) {
  const handleQuantityChange = (col, val) => {
    setQuantityUpdates(prev => ({ ...prev, [col]: parseFloat(val) || 0 }));
  };

  const selectedDistrictObj = initData?.districts?.find(d => d.dept3 == selectedDept3);
  const clusterVal = selectedDistrictObj ? selectedDistrictObj.Cluster : null;
  const grassRates = { 0: 7623.59, 1: 10742.39, 2: 28697.51 };
  const rate = clusterVal !== null ? grassRates[clusterVal] : null;

  return (
    <>
      <div style={{display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '16px'}}>
        <div>
          <h2 style={{marginTop: 0}}>ปรับแก้ปริมาณภาระงาน (Quantity)</h2>
          <p style={{margin: 0}}>ระบบแสดงค่าปริมาณงานตั้งต้นของแขวงที่เลือก คุณสามารถแก้ไขตัวเลขในแต่ละรายการเพื่อจำลองงบประมาณใหม่ได้ทันที</p>
        </div>
        <button 
          className="btn btn-secondary" 
          onClick={() => setQuantityUpdates({})} 
          style={{padding: '6px 12px', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '6px', whiteSpace: 'nowrap'}}
          title="รีเซ็ตค่าปริมาณงานกลับเป็นค่าเริ่มต้น"
        >
          <RotateCcw size={16} /> Reset Values
        </button>
      </div>
      
      {Object.keys(configsByCategory).map(cat => (
        <Expander key={cat} title={`${cat} (${configsByCategory[cat].length} รายการ)`} defaultOpen={true}>
          <div className="grid-cols-3">
            {configsByCategory[cat].map((cfg, idx) => {
              const col = cfg.quantity_col;
              if (!col) return null;
              const defaultVal = results ? (results.default_quantities[col] || 0) : 0;
              const currentVal = quantityUpdates[col] !== undefined ? quantityUpdates[col] : defaultVal;
              const step = ['กม.', 'เมตร'].includes(cfg.unit) ? "0.001" : "1";
              return (
                <div key={idx} className="form-group">
                  <label title={`source column: ${col}\n${cfg.note || ''}`}>{cfg.workload_item} ({cfg.unit})</label>
                  <input 
                    type="number" 
                    step={step} 
                    value={currentVal} 
                    onChange={e => handleQuantityChange(col, e.target.value)} 
                  />
                  {cfg.workload_item.includes("ตัดหญ้า") && clusterVal !== null && rate !== null && (
                    <div style={{ fontSize: '0.8rem', color: '#888', marginTop: '4px' }}>
                      ℹ️ แขวงนี้เป็น Cluster {clusterVal} (ราคากลางเริ่มต้น: {rate.toLocaleString('th-TH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} บาท/กม.)
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </Expander>
      ))}
    </>
  );
}

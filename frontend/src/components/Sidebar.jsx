import { Settings2 } from 'lucide-react';

export default function Sidebar({
  useDamageProbability,
  setUseDamageProbability,
  maxFactorUplift,
  setMaxFactorUplift,
  setIsParamModalOpen
}) {
  return (
    <div className="sidebar">
      <div>
        <h2 style={{marginTop: 0, display: 'flex', alignItems: 'center', gap: '8px'}}>
          <Settings2 color="var(--accent)"/> ตั้งค่า
        </h2>
        
        <div className="form-group">
          <label>Use Damage Probability</label>
          <select value={useDamageProbability ? 'On' : 'Off'} onChange={e => setUseDamageProbability(e.target.value === 'On')}>
            <option value="On">On</option>
            <option value="Off">Off</option>
          </select>
        </div>

        <div className="form-group">
          <label>Max Factor Uplift ({maxFactorUplift.toFixed(2)})</label>
          <input 
            type="range" min="0" max="0.5" step="0.01" 
            value={maxFactorUplift} 
            onChange={e => setMaxFactorUplift(parseFloat(e.target.value))} 
          />
        </div>
      </div>

      <div className="divider" style={{margin: '8px 0'}}></div>
      
      <div>
        <h3 style={{fontSize: '1rem'}}>Workload Parameter Grid</h3>
        <p style={{marginBottom: '12px', fontSize: '0.75rem'}}>ปรับแก้ Damage Probability, Unit Cost ได้ที่นี่</p>
        <button className="btn" onClick={() => setIsParamModalOpen(true)} style={{width: '100%'}}>
          <Settings2 size={16} /> เปิดตารางตั้งค่า Workload
        </button>
      </div>

      <div className="divider" style={{margin: '8px 0'}}></div>

      <div>
        <h3>สูตรหลัก</h3>
        <div className="code-block">
{`Asset / Policy workload:
quantity × damage_probability × unit_cost

Pavement workload:
pavement_area × unit_cost
  (Note: ไม่นำ damage_probability มาคิดใน Pavement)

Cost Scaling Index (Condition):
(max_uplift × Score) + 1.0`}
        </div>
      </div>
    </div>
  );
}

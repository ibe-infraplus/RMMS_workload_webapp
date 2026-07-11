import { Settings2, X, Plus, Trash2, RotateCcw } from 'lucide-react';

export default function ParameterModal({
  isOpen,
  setIsOpen,
  currentConfig,
  setCurrentConfig,
  initData,
  setWorkloadOverrides
}) {
  if (!isOpen) return null;

  const handleOverrideChange = (idx, field, value) => {
    const updatedConfig = [...currentConfig];
    updatedConfig[idx] = { ...updatedConfig[idx], [field]: value };
    setCurrentConfig(updatedConfig);
    
    // Also update workloadOverrides so the backend respects the change
    setWorkloadOverrides(prev => {
      const qCol = updatedConfig[idx].quantity_col;
      if (!qCol) return prev;
      return {
        ...prev,
        [qCol]: {
          ...prev[qCol],
          [field]: value
        }
      };
    });
  };

  const handleAddParameter = (category) => {
    const newParamName = prompt(`Enter new parameter name for ${category}:`);
    if (!newParamName) return;
    
    const uniqueCol = `custom_${Date.now()}`;
    const newConfigRow = {
      workload_item: newParamName,
      category: category,
      quantity_col: uniqueCol,
      unit: "หน่วย",
      damage_probability: 1.0,
      unit_cost: 0.0,
      apply_damage_probability: true,
      note: "Custom parameter",
      condition_profile: "none",
      damage_key: null
    };
    
    setCurrentConfig([...currentConfig, newConfigRow]);
  };

  const handleDeleteParameter = (idx) => {
    const confirmDelete = window.confirm("Are you sure you want to delete this parameter?");
    if (!confirmDelete) return;
    
    const updatedConfig = [...currentConfig];
    updatedConfig.splice(idx, 1);
    setCurrentConfig(updatedConfig);
  };

  const handleResetToDefault = () => {
    const confirmReset = window.confirm("This will revert all parameters and overrides back to the original system defaults. Proceed?");
    if (!confirmReset) return;
    
    localStorage.removeItem('parameter_grid');
    localStorage.removeItem('workload_overrides');

    setCurrentConfig(initData.param_grid);
    const overrides = {};
    initData.param_grid.forEach(row => {
      if (row.quantity_col) {
        overrides[row.quantity_col] = {
          damage_probability: row.damage_probability,
          unit_cost: row.unit_cost,
          apply_damage_probability: row.apply_damage_probability
        };
      }
    });
    setWorkloadOverrides(overrides);
  };

  return (
    <div className="modal-overlay" onClick={() => setIsOpen(false)}>
      <div className="modal-content" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{display: 'flex', alignItems: 'center', gap: '16px'}}>
            <h2><Settings2 style={{display: 'inline', verticalAlign: 'middle'}}/> Workload Parameter Grid</h2>
            <button className="btn btn-secondary" onClick={handleResetToDefault} style={{padding: '6px 12px', fontSize: '0.85rem'}}>
              <RotateCcw size={16} /> Reset to Default
            </button>
          </div>
          <button className="close-btn" onClick={() => setIsOpen(false)}>
            <X size={24} />
          </button>
        </div>
        <div className="modal-body">
          <p style={{marginBottom: '16px'}}>สามารถปรับแก้ Damage Probability และ Unit Cost ได้ที่ตารางด้านล่าง หรือเพิ่ม/ลบตัวแปรตามหมวดหมู่ การเปลี่ยนแปลงจะนำไปคำนวณทันที</p>
          
          {['Pavement', 'Asset', 'Policy', 'Other'].map(category => {
            const itemsInCat = currentConfig.map((c, i) => ({...c, originalIndex: i})).filter(c => (c.category || 'Other') === category);
            if (itemsInCat.length === 0) return null;

            return (
              <div key={category} style={{marginBottom: '32px'}}>
                <h3 style={{marginBottom: '8px', paddingBottom: '8px', borderBottom: '1px solid var(--border-color)', color: 'var(--accent)'}}>{category}</h3>
                <div className="table-wrapper">
                  <table className="data-grid">
                    <thead>
                      <tr>
                        <th style={{width: '25%'}}>Workload Item</th>
                        <th style={{width: '15%'}}>Quantity Col</th>
                        <th style={{width: '20%'}}>Damage Probability</th>
                        <th style={{width: '20%'}}>Unit Cost (บาท)</th>
                        <th style={{width: '10%', textAlign: 'center'}}>Apply Prob</th>
                        <th style={{width: '10%', textAlign: 'center'}}>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {itemsInCat.map((cfg) => {
                        if (!cfg.quantity_col) return null;
                        const idx = cfg.originalIndex;
                        return (
                          <tr key={idx}>
                            <td style={{fontWeight: 500}}>
                              <input 
                                type="text" 
                                value={cfg.workload_item} 
                                onChange={e => handleOverrideChange(idx, 'workload_item', e.target.value)}
                                style={{width: '100%', padding: '4px', background: 'transparent', border: '1px solid transparent'}}
                              />
                            </td>
                            <td style={{color: 'var(--text-secondary)'}}>{cfg.quantity_col}</td>
                            <td>
                              <input 
                                type="number" step="0.0001" 
                                value={cfg.damage_probability} 
                                onChange={e => handleOverrideChange(idx, 'damage_probability', parseFloat(e.target.value) || 0)}
                                style={{width: '100px'}}
                              />
                            </td>
                            <td>
                              <input 
                                type="number" step="1" 
                                value={cfg.unit_cost} 
                                onChange={e => handleOverrideChange(idx, 'unit_cost', parseFloat(e.target.value) || 0)}
                                style={{width: '120px'}}
                              />
                            </td>
                            <td style={{textAlign: 'center'}}>
                              <input 
                                type="checkbox" 
                                checked={cfg.apply_damage_probability} 
                                onChange={e => handleOverrideChange(idx, 'apply_damage_probability', e.target.checked)}
                              />
                            </td>
                            <td style={{textAlign: 'center'}}>
                              <button onClick={() => handleDeleteParameter(idx)} style={{background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', padding: '4px'}}>
                                <Trash2 size={16} />
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
                <button className="btn btn-secondary" onClick={() => handleAddParameter(category)} style={{marginTop: '-16px', marginBottom: '16px'}}>
                  <Plus size={16} /> Add Parameter
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

import { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import Plot from 'react-plotly.js';
import { ChevronDown, ChevronUp, Settings2, Activity, Map, LayoutDashboard, Search, X, Plus, Trash2, RotateCcw } from 'lucide-react';
import './App.css';

const API_BASE = '/api';

const formatBaht = (val) => new Intl.NumberFormat('th-TH', { style: 'decimal', maximumFractionDigits: 0 }).format(val) + ' บาท';

function Expander({ title, children, defaultOpen = false }) {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  return (
    <div className="expander">
      <div className="expander-header" onClick={() => setIsOpen(!isOpen)}>
        <span className="expander-title">{title}</span>
        {isOpen ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
      </div>
      {isOpen && <div className="expander-content">{children}</div>}
    </div>
  );
}

function App() {
  const [loadingInit, setLoadingInit] = useState(true);
  const [initData, setInitData] = useState(null);
  
  // State
  const [selectedDept3, setSelectedDept3] = useState(null);
  const [useDamageProbability, setUseDamageProbability] = useState(true);
  const [maxFactorUplift, setMaxFactorUplift] = useState(0.15);
  const [quantityUpdates, setQuantityUpdates] = useState({});
  const [workloadOverrides, setWorkloadOverrides] = useState({});
  const [currentConfig, setCurrentConfig] = useState([]);
  
  // UI State
  const [isParamModalOpen, setIsParamModalOpen] = useState(false);
  
  // Results
  const [calculating, setCalculating] = useState(false);
  const [results, setResults] = useState(null);

  useEffect(() => {
    axios.get(`${API_BASE}/init`).then(res => {
      setInitData(res.data);
      setSelectedDept3(res.data.districts[0].dept3);
      setMaxFactorUplift(res.data.max_factor_uplift);
      
      const overrides = {};
      res.data.param_grid.forEach(row => {
        if (row.quantity_col) {
          overrides[row.quantity_col] = {
            damage_probability: row.damage_probability,
            unit_cost: row.unit_cost,
            apply_damage_probability: row.apply_damage_probability
          };
        }
      });
      setWorkloadOverrides(overrides);
      setCurrentConfig(res.data.param_grid);
      setLoadingInit(false);
    }).catch(err => {
      console.error(err);
      alert("Failed to connect to backend API. Is FastAPI running on port 8000?");
    });
  }, []);

  useEffect(() => {
    if (!selectedDept3 || !initData) return;
    
    setCalculating(true);
    axios.post(`${API_BASE}/calculate`, {
      selected_dept3: selectedDept3,
      max_factor_uplift: maxFactorUplift,
      use_damage_probability: useDamageProbability,
      workload_overrides: workloadOverrides,
      quantity_updates: quantityUpdates,
      custom_config: currentConfig
    }).then(res => {
      setResults(res.data);
      setCalculating(false);
    }).catch(err => {
      console.error(err);
      setCalculating(false);
    });
  }, [selectedDept3, maxFactorUplift, useDamageProbability, workloadOverrides, quantityUpdates, currentConfig]);

  if (loadingInit) {
    return (
      <div className="loader-container">
        <div className="spinner"></div>
        <p>กำลังเชื่อมต่อกับ Backend API...</p>
      </div>
    );
  }

  const handleQuantityChange = (col, val) => {
    setQuantityUpdates(prev => ({ ...prev, [col]: parseFloat(val) || 0 }));
  };

  const handleOverrideChange = (idx, field, value) => {
    const updatedConfig = [...currentConfig];
    updatedConfig[idx] = { ...updatedConfig[idx], [field]: value };
    setCurrentConfig(updatedConfig);
  };

  const handleAddParameter = (category) => {
    const newParamName = prompt(`Enter new parameter name for ${category}:`);
    if (!newParamName) return;
    
    // Generate a unique quantity_col key
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

  // Group config by category for inputs
  const configsByCategory = {};
  currentConfig.forEach(cfg => {
    const cat = cfg.category || 'Other';
    if (!configsByCategory[cat]) configsByCategory[cat] = [];
    configsByCategory[cat].push(cfg);
  });

  return (
    <div className="app-container">
      {/* Sidebar */}
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
Asset workload:
quantity × damage_probability × unit_cost

Pavement workload:
length_to2 × pavement_unit_cost

Total Budget:
Σ(workload) + factor + fixed_cost
          </div>
          <p style={{marginTop: '8px'}}>Version นี้ยังไม่ตัดงบด้วย cap limit และผิวจราจรไม่คูณ probability</p>
        </div>
      </div>

      {/* Main Content */}
      <div className="main-content">
        <h1><Map style={{display: 'inline', verticalAlign: 'middle', marginRight: '12px', marginBottom: '4px'}}/> ระบบคำนวณงบประมาณ (Workload Cost)</h1>
        <p>แพลตฟอร์มปรับแก้ปริมาณงานและตัวแปรเพื่อจำลองผลกระทบต่องบประมาณแบบ Real-time</p>
        
        <div className="divider"></div>

        {/* 1) District Selector */}
        <h2>เลือกพื้นที่ดำเนินการ (แขวงทางหลวง)</h2>
        <div className="form-group" style={{maxWidth: '400px'}}>
          <select value={selectedDept3} onChange={e => {
            setSelectedDept3(parseInt(e.target.value));
            setQuantityUpdates({}); // Reset quantities on district change
          }}>
            {initData.districts.map(d => (
              <option key={d.dept3} value={d.dept3}>{d.district_label}</option>
            ))}
          </select>
        </div>

        {/* 2) Quantity Inputs */}
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
                    <label title={`source column: ${col}\n${cfg.note}`}>{cfg.workload_item} ({cfg.unit})</label>
                    <input 
                      type="number" 
                      step={step} 
                      value={currentVal} 
                      onChange={e => handleQuantityChange(col, e.target.value)} 
                    />
                  </div>
                );
              })}
            </div>
          </Expander>
        ))}

        {results && (
          <>
            <div className="divider"></div>
            <h2>สรุปผลการคำนวณงบประมาณ</h2>
            
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
              </div>
            </div>

            <div className="chart-container">
              <Plot
                data={[{
                  x: ['Baseline', 'Revised'],
                  y: [results.metrics.baseline_total, results.metrics.revised_total],
                  type: 'bar',
                  text: [results.metrics.baseline_total, results.metrics.revised_total].map(formatBaht),
                  textposition: 'outside',
                  marker: { color: ['#94a3b8', '#3b82f6'] }
                }]}
                layout={{
                  title: 'เปรียบเทียบงบประมาณของแขวงที่เลือก',
                  paper_bgcolor: 'rgba(0,0,0,0)',
                  plot_bgcolor: 'rgba(0,0,0,0)',
                  font: { color: '#f8fafc' },
                  yaxis: { title: 'บาท', gridcolor: '#334155' }
                }}
                useResizeHandler={true}
                style={{ width: '100%', height: '400px' }}
                config={{responsive: true}}
              />
            </div>

            <h2>กราฟเส้นงบประมาณรวมทุกแขวง</h2>
            <div className="chart-container">
              {(() => {
                const sortedData = [...results.chart_data.all_districts_revised]
                  .map((rev, index) => ({
                    rev: rev,
                    base: results.chart_data.all_districts_baseline[index]
                  }))
                  .sort((a, b) => b.rev.total_budget_model - a.rev.total_budget_model);

                const xSorted = sortedData.map(item => `${item.rev.dept3} - ${item.rev.district_name}`);
                const baseSorted = sortedData.map(item => item.base.total_budget_model);
                const revSorted = sortedData.map(item => item.rev.total_budget_model);

                return (
                  <Plot
                    data={[
                      {
                        x: xSorted,
                        y: baseSorted,
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Baseline',
                        line: { color: '#94a3b8', width: 2, dash: 'dot' }
                      },
                      {
                        x: xSorted,
                        y: revSorted,
                        type: 'scatter',
                        mode: 'lines',
                        name: 'Revised',
                        line: { color: '#38bdf8', width: 3, shape: 'spline' },
                        fill: 'tozeroy',
                        fillcolor: 'rgba(56, 189, 248, 0.15)'
                      }
                    ]}
                    layout={{
                      paper_bgcolor: 'rgba(0,0,0,0)',
                      plot_bgcolor: 'rgba(0,0,0,0)',
                      font: { color: '#f8fafc', family: 'Inter' },
                      yaxis: { 
                        title: 'งบประมาณ (บาท)', 
                        gridcolor: '#334155', 
                        zerolinecolor: '#334155' 
                      },
                      xaxis: { 
                        tickangle: -45, 
                        gridcolor: 'transparent',
                        tickfont: { size: 10 }
                      },
                      margin: { b: 140, t: 40, l: 80, r: 20 },
                      hovermode: 'x unified',
                      legend: { orientation: 'h', y: 1.1 }
                    }}
                    useResizeHandler={true}
                    style={{ width: '100%', height: '560px' }}
                    config={{responsive: true}}
                  />
                );
              })()}
            </div>

            <div className="divider"></div>
            <h2>รายละเอียดโครงสร้างงบประมาณ (Breakdown)</h2>
            <div className="table-wrapper">
              <table className="data-grid">
                <thead>
                  <tr>
                    <th>Component</th>
                    <th>Baseline</th>
                    <th>Revised</th>
                    <th>Change</th>
                  </tr>
                </thead>
                <tbody>
                  {results.breakdown.map((row, i) => (
                    <tr key={i}>
                      <td>{row.component}</td>
                      <td>{formatBaht(row.baseline)}</td>
                      <td>{formatBaht(row.revised)}</td>
                      <td className={row.revised - row.baseline > 0 ? 'positive' : (row.revised - row.baseline < 0 ? 'negative' : '')}>
                        {formatBaht(row.revised - row.baseline)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <h2>ตารางแสดงรายละเอียดการคำนวณราย Item</h2>
            <div className="table-wrapper">
              <table className="data-grid">
                <thead>
                  <tr>
                    <th>Workload Item</th>
                    <th>Category</th>
                    <th>Quantity</th>
                    <th>Unit</th>
                    <th>D. Prob</th>
                    <th>Unit Cost</th>
                    <th>Base Cost</th>
                    <th>Factor Index</th>
                    <th>Factor Cost</th>
                    <th>Total</th>
                  </tr>
                </thead>
                <tbody>
                  {results.workload_detail.map((row, i) => (
                    <tr key={i}>
                      <td>{row.workload_item}</td>
                      <td>{row.category}</td>
                      <td>{Number(row.quantity).toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 3})}</td>
                      <td>{row.unit}</td>
                      <td>{Number(row.damage_probability).toFixed(4)}</td>
                      <td>{Number(row.unit_cost).toLocaleString()}</td>
                      <td>{Number(row.base_workload_cost).toLocaleString()}</td>
                      <td>{Number(row.factor_index_0_1).toFixed(4)}</td>
                      <td>{Number(row.factor_cost).toLocaleString()}</td>
                      <td>{Number(row.workload_plus_factor).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            <Expander title="แสดงค่าตัวแปรตั้งต้นและ Factor Score สำหรับแขวงที่เลือก">
               <div className="table-wrapper">
                <table className="data-grid">
                  <tbody>
                    {Object.entries(results.debug).map(([k, v]) => (
                      <tr key={k}>
                        <td style={{fontWeight: 600}}>{k}</td>
                        <td>{typeof v === 'number' ? Number(v).toLocaleString(undefined, {maximumFractionDigits: 4}) : v}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Expander>

          </>
        )}
      </div>

      {/* Parameter Grid Modal */}
      {isParamModalOpen && (
        <div className="modal-overlay" onClick={() => setIsParamModalOpen(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <div style={{display: 'flex', alignItems: 'center', gap: '16px'}}>
                <h2><Settings2 style={{display: 'inline', verticalAlign: 'middle'}}/> Workload Parameter Grid</h2>
                <button className="btn btn-secondary" onClick={handleResetToDefault} style={{padding: '6px 12px', fontSize: '0.85rem'}}>
                  <RotateCcw size={16} /> Reset to Default
                </button>
              </div>
              <button className="close-btn" onClick={() => setIsParamModalOpen(false)}>
                <X size={24} />
              </button>
            </div>
            <div className="modal-body">
              <p style={{marginBottom: '16px'}}>สามารถปรับแก้ Damage Probability และ Unit Cost ได้ที่ตารางด้านล่าง หรือเพิ่ม/ลบตัวแปรตามหมวดหมู่ การเปลี่ยนแปลงจะนำไปคำนวณทันที</p>
              
              {['Pavement', 'Asset', 'Other'].map(category => {
                const itemsInCat = currentConfig.map((c, i) => ({...c, originalIndex: i})).filter(c => (c.category || 'Other') === category);
                if (itemsInCat.length === 0 && category === 'Other') return null;

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
      )}

    </div>
  );
}

export default App;

import { useState, useEffect } from 'react';
import axios from 'axios';
import { Map } from 'lucide-react';
import './App.css';

// Components
import ParameterModal from './components/ParameterModal';
import QuantityInputs from './components/QuantityInputs';
import Metrics from './components/Metrics';
import Charts from './components/Charts';
import DataTable from './components/DataTable';
import WorkloadDetailTable from './components/WorkloadDetailTable';
import SummaryAllDistrictsTable from './components/SummaryAllDistrictsTable';
import WorkloadCharts from './components/WorkloadCharts';
import FrameworkTable from './components/FrameworkTable';

const API_BASE = '/api';

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
  const [budgetMultiplier, setBudgetMultiplier] = useState(100.0);
  const [budgetFramework, setBudgetFramework] = useState({
    pavement: 50,
    traffic: 15,
    drainage: 15,
    others: 10,
    bridge: 5,
    shoulder: 5
  });
  
  // UI State
  const [isParamModalOpen, setIsParamModalOpen] = useState(false);
  
  // Results
  const [calculating, setCalculating] = useState(false);
  const [results, setResults] = useState(null);

  useEffect(() => {
    axios.get(`${API_BASE}/init`).then(res => {
      setInitData(res.data);
      setSelectedDept3(res.data.districts[0].dept3);

      // Load parameter grid & overrides from localStorage if present
      const savedGrid = localStorage.getItem('parameter_grid');
      const savedOverrides = localStorage.getItem('workload_overrides');

      if (savedGrid) {
        setCurrentConfig(JSON.parse(savedGrid));
      } else {
        setCurrentConfig(res.data.param_grid);
      }

      if (savedOverrides) {
        setWorkloadOverrides(JSON.parse(savedOverrides));
      } else {
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
      }

      // Load other inputs if saved
      const savedUplift = localStorage.getItem('max_factor_uplift');
      setMaxFactorUplift(savedUplift ? parseFloat(savedUplift) : res.data.max_factor_uplift);

      const savedUseDP = localStorage.getItem('use_damage_probability');
      setUseDamageProbability(savedUseDP !== null ? savedUseDP === 'true' : true);

      const savedMultiplier = localStorage.getItem('budget_multiplier');
      setBudgetMultiplier(savedMultiplier ? parseFloat(savedMultiplier) : (res.data.default_budget_multiplier || 100.0));

      const savedFramework = localStorage.getItem('budget_framework');
      if (savedFramework) {
        setBudgetFramework(JSON.parse(savedFramework));
      }

      setLoadingInit(false);
    }).catch(err => {
      console.error(err);
      alert("Failed to connect to backend API. Is FastAPI running on port 8001?");
    });
  }, []);

  // Sync state changes to localStorage
  useEffect(() => {
    if (currentConfig && currentConfig.length > 0) {
      localStorage.setItem('parameter_grid', JSON.stringify(currentConfig));
    }
  }, [currentConfig]);

  useEffect(() => {
    if (workloadOverrides && Object.keys(workloadOverrides).length > 0) {
      localStorage.setItem('workload_overrides', JSON.stringify(workloadOverrides));
    }
  }, [workloadOverrides]);

  useEffect(() => {
    localStorage.setItem('max_factor_uplift', maxFactorUplift);
  }, [maxFactorUplift]);

  useEffect(() => {
    localStorage.setItem('use_damage_probability', useDamageProbability);
  }, [useDamageProbability]);

  useEffect(() => {
    localStorage.setItem('budget_multiplier', budgetMultiplier);
  }, [budgetMultiplier]);

  useEffect(() => {
    localStorage.setItem('budget_framework', JSON.stringify(budgetFramework));
  }, [budgetFramework]);

  useEffect(() => {
    if (!selectedDept3 || !initData) return;
    
    setCalculating(true);
    
    const timeoutId = setTimeout(() => {
      axios.post(`${API_BASE}/calculate`, {
        selected_dept3: selectedDept3,
        max_factor_uplift: maxFactorUplift,
        use_damage_probability: useDamageProbability,
        workload_overrides: workloadOverrides,
        quantity_updates: quantityUpdates,
        custom_config: currentConfig,
        budget_multiplier: budgetMultiplier,
        budget_framework: budgetFramework
      }).then(res => {
        setResults(res.data);
        setCalculating(false);
      }).catch(err => {
        console.error(err);
        setCalculating(false);
      });
    }, 500); // 500ms Debounce

    return () => clearTimeout(timeoutId);
  }, [selectedDept3, maxFactorUplift, useDamageProbability, workloadOverrides, quantityUpdates, currentConfig, budgetMultiplier, budgetFramework]);

  const exportToExcel = () => {
    if (!selectedDept3 || !initData) return;
    axios.post(`${API_BASE}/export_excel`, {
      selected_dept3: selectedDept3,
      max_factor_uplift: maxFactorUplift,
      use_damage_probability: useDamageProbability,
      workload_overrides: workloadOverrides,
      quantity_updates: quantityUpdates,
      custom_config: currentConfig,
      budget_multiplier: budgetMultiplier,
      budget_framework: budgetFramework
    }, { responseType: 'blob' })
    .then(res => {
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'revised_workload_cost_model.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
    })
    .catch(err => {
      console.error(err);
      alert("Failed to export Excel file from backend.");
    });
  };

  if (loadingInit) {
    return (
      <div className="loader-container">
        <div className="spinner"></div>
        <p>กำลังเชื่อมต่อกับ Backend API...</p>
      </div>
    );
  }

  // Group config by category for inputs
  const configsByCategory = {};
  currentConfig.forEach(cfg => {
    const cat = cfg.category || 'Other';
    if (!configsByCategory[cat]) configsByCategory[cat] = [];
    configsByCategory[cat].push(cfg);
  });

  return (
    <div className="app-container" style={{display: 'flex', gap: '24px', alignItems: 'flex-start', padding: '24px'}}>
      
      {/* Sidebar Panel */}
      <div className="sidebar-panel" style={{
        width: '300px',
        flexShrink: 0,
        padding: '20px',
        backgroundColor: 'var(--bg-card)',
        borderRadius: 'var(--radius)',
        border: '1px solid var(--border-color)',
        height: 'fit-content'
      }}>
        <h3 style={{marginTop: 0, marginBottom: '16px'}}>กรอบสัดส่วนงบประมาณ (%)</h3>
        
        <div style={{display: 'flex', flexDirection: 'column', gap: '16px'}}>
          <div className="form-group" style={{marginBottom: 0}}>
            <label style={{display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '0.9rem'}}>
              <span>งานผิวทาง</span>
              <span style={{fontWeight: 'bold', color: 'var(--accent)'}}>{budgetFramework.pavement}%</span>
            </label>
            <input 
              type="range" min="0" max="100" step="1" 
              value={budgetFramework.pavement} 
              onChange={e => setBudgetFramework(prev => ({ ...prev, pavement: parseFloat(e.target.value) || 0 }))} 
              style={{width: '100%'}}
            />
          </div>

          <div className="form-group" style={{marginBottom: 0}}>
            <label style={{display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '0.9rem'}}>
              <span>งานจราจรสงเคราะห์</span>
              <span style={{fontWeight: 'bold', color: 'var(--accent)'}}>{budgetFramework.traffic}%</span>
            </label>
            <input 
              type="range" min="0" max="100" step="1" 
              value={budgetFramework.traffic} 
              onChange={e => setBudgetFramework(prev => ({ ...prev, traffic: parseFloat(e.target.value) || 0 }))} 
              style={{width: '100%'}}
            />
          </div>

          <div className="form-group" style={{marginBottom: 0}}>
            <label style={{display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '0.9rem'}}>
              <span>งานระบายน้ำ</span>
              <span style={{fontWeight: 'bold', color: 'var(--accent)'}}>{budgetFramework.drainage}%</span>
            </label>
            <input 
              type="range" min="0" max="100" step="1" 
              value={budgetFramework.drainage} 
              onChange={e => setBudgetFramework(prev => ({ ...prev, drainage: parseFloat(e.target.value) || 0 }))} 
              style={{width: '100%'}}
            />
          </div>

          <div className="form-group" style={{marginBottom: 0}}>
            <label style={{display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '0.9rem'}}>
              <span>งานเขตทางและอื่นๆ</span>
              <span style={{fontWeight: 'bold', color: 'var(--accent)'}}>{budgetFramework.others}%</span>
            </label>
            <input 
              type="range" min="0" max="100" step="1" 
              value={budgetFramework.others} 
              onChange={e => setBudgetFramework(prev => ({ ...prev, others: parseFloat(e.target.value) || 0 }))} 
              style={{width: '100%'}}
            />
          </div>

          <div className="form-group" style={{marginBottom: 0}}>
            <label style={{display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '0.9rem'}}>
              <span>งานสะพาน</span>
              <span style={{fontWeight: 'bold', color: 'var(--accent)'}}>{budgetFramework.bridge}%</span>
            </label>
            <input 
              type="range" min="0" max="100" step="1" 
              value={budgetFramework.bridge} 
              onChange={e => setBudgetFramework(prev => ({ ...prev, bridge: parseFloat(e.target.value) || 0 }))} 
              style={{width: '100%'}}
            />
          </div>

          <div className="form-group" style={{marginBottom: 0}}>
            <label style={{display: 'flex', justifyContent: 'space-between', marginBottom: '6px', fontSize: '0.9rem'}}>
              <span>งานไหล่ทางและทางเชื่อม</span>
              <span style={{fontWeight: 'bold', color: 'var(--accent)'}}>{budgetFramework.shoulder}%</span>
            </label>
            <input 
              type="range" min="0" max="100" step="1" 
              value={budgetFramework.shoulder} 
              onChange={e => setBudgetFramework(prev => ({ ...prev, shoulder: parseFloat(e.target.value) || 0 }))} 
              style={{width: '100%'}}
            />
          </div>

          {(() => {
            const sum = budgetFramework.pavement + budgetFramework.traffic + budgetFramework.drainage + budgetFramework.others + budgetFramework.bridge + budgetFramework.shoulder;
            if (Math.abs(sum - 100) > 0.01) {
              return (
                <div style={{color: '#ef4444', fontSize: '0.85rem', marginTop: '4px', fontWeight: 'bold'}}>
                  ⚠️ สัดส่วนรวมต้องเท่ากับ 100% (ปัจจุบัน: {sum}%)
                </div>
              );
            }
            return null;
          })()}
        </div>
      </div>

      {/* Main Content */}
      <div className="main-content" style={{flex: 1, minWidth: 0, padding: 0}}>
        <h1><Map style={{display: 'inline', verticalAlign: 'middle', marginRight: '12px', marginBottom: '4px'}}/> ระบบคำนวณงบประมาณ (Workload Cost)</h1>
        <p>แพลตฟอร์มปรับแก้ปริมาณงานและตัวแปรเพื่อจำลองผลกระทบต่องบประมาณแบบ Real-time</p>
        
        <div className="settings-panel" style={{marginTop: '24px', marginBottom: '24px', padding: '20px', backgroundColor: 'var(--bg-card)', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)', display: 'flex', flexWrap: 'wrap', gap: '24px', alignItems: 'center'}}>
          <div className="form-group" style={{marginBottom: 0, minWidth: '180px'}}>
            <label>Use Damage Probability (Revised)</label>
            <select value={useDamageProbability ? 'On' : 'Off'} onChange={e => setUseDamageProbability(e.target.value === 'On')}>
              <option value="On">On</option>
              <option value="Off">Off</option>
            </select>
          </div>

          <div className="form-group" style={{marginBottom: 0, minWidth: '220px'}}>
            <label>Max Factor Uplift (Revised: {maxFactorUplift.toFixed(2)})</label>
            <input 
              type="range" min="0" max="0.5" step="0.01" 
              value={maxFactorUplift} 
              onChange={e => setMaxFactorUplift(parseFloat(e.target.value))} 
            />
          </div>

          <div style={{marginLeft: 'auto', display: 'flex', gap: '12px'}}>
            <button className="btn" onClick={() => setIsParamModalOpen(true)}>
               ตั้งค่า Workload Parameter Grid (Revised)
            </button>
            <button className="btn" style={{backgroundColor: '#10b981', color: 'white'}} onClick={exportToExcel}>
               Export to Excel
            </button>
          </div>
        </div>

        <div className="divider"></div>

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

        <QuantityInputs 
          configsByCategory={configsByCategory}
          results={results}
          quantityUpdates={quantityUpdates}
          setQuantityUpdates={setQuantityUpdates}
          selectedDept3={selectedDept3}
          initData={initData}
        />

        {results && (
          <>
            <div className="divider"></div>
            <h2>3) ผลการคำนวณ Workload</h2>
            <div className="metrics-grid">
              <div className="metric-card">
                <span className="metric-label">Baseline Workload Score</span>
                <span className="metric-value">{Number(results.metrics.baseline_workload_score).toLocaleString(undefined, {maximumFractionDigits: 4})} คะแนน</span>
              </div>
              <div className="metric-card">
                <span className="metric-label">Revised Workload Score</span>
                <span className="metric-value">{Number(results.metrics.revised_workload_score).toLocaleString(undefined, {maximumFractionDigits: 4})} คะแนน</span>
                <span className={`metric-delta ${results.metrics.revised_workload_score - results.metrics.baseline_workload_score > 0 ? 'positive' : 'negative'}`}>
                  {(results.metrics.revised_workload_score - results.metrics.baseline_workload_score > 0 ? '+' : '')}
                  {Number(results.metrics.revised_workload_score - results.metrics.baseline_workload_score).toLocaleString(undefined, {maximumFractionDigits: 4})} คะแนน
                </span>
              </div>
              <div className="metric-card">
                <span className="metric-label">National Baseline Workload</span>
                <span className="metric-value">{Number(results.metrics.national_baseline_workload).toLocaleString(undefined, {maximumFractionDigits: 4})} คะแนน</span>
              </div>
              <div className="metric-card">
                <span className="metric-label">National Revised Workload</span>
                <span className="metric-value">{Number(results.metrics.national_revised_workload).toLocaleString(undefined, {maximumFractionDigits: 4})} คะแนน</span>
                <span className={`metric-delta ${results.metrics.national_revised_workload - results.metrics.national_baseline_workload > 0 ? 'positive' : 'negative'}`}>
                  {(results.metrics.national_revised_workload - results.metrics.national_baseline_workload > 0 ? '+' : '')}
                  {Number(results.metrics.national_revised_workload - results.metrics.national_baseline_workload).toLocaleString(undefined, {maximumFractionDigits: 4})} คะแนน
                </span>
              </div>
            </div>

            <WorkloadCharts results={results} selectedDept3={selectedDept3} />

            <div className="form-group" style={{marginTop: '24px', maxWidth: '320px', padding: '16px', backgroundColor: 'var(--bg-card)', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)'}}>
              <label style={{fontWeight: 'bold', display: 'block', marginBottom: '8px'}}>ตัวคูณร่วม X (Budget Multiplier)</label>
              <input 
                type="number" 
                value={budgetMultiplier} 
                onChange={e => setBudgetMultiplier(parseFloat(e.target.value) || 0)} 
                style={{width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid var(--border-color)', backgroundColor: 'var(--bg-app)', color: 'var(--text-main)'}}
              />
            </div>

            <Metrics results={results} />
            <DataTable results={results} />
            <FrameworkTable results={results} />
            <Charts results={results} />
            <WorkloadDetailTable results={results} />
            <SummaryAllDistrictsTable results={results} />
          </>
        )}
      </div>

      <ParameterModal 
        isOpen={isParamModalOpen}
        setIsOpen={setIsParamModalOpen}
        currentConfig={currentConfig}
        setCurrentConfig={setCurrentConfig}
        initData={initData}
        setWorkloadOverrides={setWorkloadOverrides}
      />
    </div>
  );
}

export default App;

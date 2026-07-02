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
      setBudgetMultiplier(res.data.default_budget_multiplier || 100.0);
      
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
      alert("Failed to connect to backend API. Is FastAPI running on port 8001?");
    });
  }, []);

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
        budget_multiplier: budgetMultiplier
      }).then(res => {
        setResults(res.data);
        setCalculating(false);
      }).catch(err => {
        console.error(err);
        setCalculating(false);
      });
    }, 500); // 500ms Debounce

    return () => clearTimeout(timeoutId);
  }, [selectedDept3, maxFactorUplift, useDamageProbability, workloadOverrides, quantityUpdates, currentConfig, budgetMultiplier]);

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
    <div className="app-container">
      <div className="main-content">
        <h1><Map style={{display: 'inline', verticalAlign: 'middle', marginRight: '12px', marginBottom: '4px'}}/> ระบบคำนวณงบประมาณ (Workload Cost)</h1>
        <p>แพลตฟอร์มปรับแก้ปริมาณงานและตัวแปรเพื่อจำลองผลกระทบต่องบประมาณแบบ Real-time</p>
        
        <div className="settings-panel" style={{marginTop: '24px', marginBottom: '24px', padding: '20px', backgroundColor: 'var(--bg-card)', borderRadius: 'var(--radius)', border: '1px solid var(--border-color)', display: 'flex', flexWrap: 'wrap', gap: '24px', alignItems: 'center'}}>
          <div className="form-group" style={{marginBottom: 0, minWidth: '180px'}}>
            <label>Use Damage Probability</label>
            <select value={useDamageProbability ? 'On' : 'Off'} onChange={e => setUseDamageProbability(e.target.value === 'On')}>
              <option value="On">On</option>
              <option value="Off">Off</option>
            </select>
          </div>

          <div className="form-group" style={{marginBottom: 0, minWidth: '220px'}}>
            <label>Max Factor Uplift ({maxFactorUplift.toFixed(2)})</label>
            <input 
              type="range" min="0" max="0.5" step="0.01" 
              value={maxFactorUplift} 
              onChange={e => setMaxFactorUplift(parseFloat(e.target.value))} 
            />
          </div>

          <div style={{marginLeft: 'auto'}}>
            <button className="btn" onClick={() => setIsParamModalOpen(true)}>
               ตั้งค่า Workload Parameter Grid
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
            <Charts results={results} />
            <DataTable results={results} />
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

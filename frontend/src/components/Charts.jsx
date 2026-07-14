import Plot from 'react-plotly.js';

export default function Charts({ results }) {
  if (!results) return null;

  const formatBaht = (val) => new Intl.NumberFormat('th-TH', { style: 'decimal', maximumFractionDigits: 0 }).format(val) + ' บาท';

  const sortedData = [...results.chart_data.all_districts_revised]
    .map((rev, index) => ({
      rev: rev,
      base: results.chart_data.all_districts_baseline[index]
    }))
    .sort((a, b) => b.rev.total_budget_model - a.rev.total_budget_model);

  const xSorted = sortedData.map(item => `${item.rev.dept3} - ${item.rev.district_name}`);
  const baseSorted = sortedData.map(item => item.base.total_budget_model);
  const revSorted = sortedData.map(item => item.rev.total_budget_model);

  const hasChanges = results.has_changes;

  const barData = [
    {
      x: ['Baseline'],
      y: [results.metrics.baseline_total],
      type: 'bar',
      text: [results.metrics.baseline_total].map(formatBaht),
      textposition: 'outside',
      marker: { color: '#94a3b8' }
    }
  ];
  if (hasChanges) {
    barData.push({
      x: ['Revised'],
      y: [results.metrics.revised_total],
      type: 'bar',
      text: [results.metrics.revised_total].map(formatBaht),
      textposition: 'outside',
      marker: { color: '#3b82f6' }
    });
  }

  const lineData = [
    {
      x: xSorted,
      y: baseSorted,
      type: 'scatter',
      mode: 'lines',
      name: 'Baseline',
      line: { color: '#94a3b8', width: 2, dash: 'dot' }
    }
  ];
  if (hasChanges) {
    lineData.push({
      x: xSorted,
      y: revSorted,
      type: 'scatter',
      mode: 'lines',
      name: 'Revised',
      line: { color: '#38bdf8', width: 3, shape: 'spline' },
      fill: 'tozeroy',
      fillcolor: 'rgba(56, 189, 248, 0.15)'
    });
  }

  return (
    <>
      <div className="chart-container">
        <Plot
          data={barData}
          layout={{
            title: hasChanges ? 'เปรียบเทียบงบประมาณของแขวงที่เลือก' : 'งบประมาณของแขวงที่เลือก (Baseline)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#f8fafc' },
            yaxis: { title: 'บาท', gridcolor: '#334155' },
            hoverlabel: {
              bgcolor: '#1e293b',
              font: { color: '#f8fafc' },
              bordercolor: '#334155'
            }
          }}
          useResizeHandler={true}
          style={{ width: '100%', height: '400px' }}
          config={{responsive: true}}
        />
      </div>

      <h2>{hasChanges ? 'เปรียบเทียบงบประมาณรวมทุกแขวง' : 'งบประมาณรวมทุกแขวง (Baseline)'}</h2>
      <div className="chart-container">
        <Plot
          data={lineData}
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
            hoverlabel: {
              bgcolor: '#1e293b',
              font: { color: '#f8fafc' },
              bordercolor: '#334155'
            },
            legend: { orientation: 'h', y: 1.1 }
          }}
          useResizeHandler={true}
          style={{ width: '100%', height: '560px' }}
          config={{responsive: true}}
        />
      </div>
    </>
  );
}

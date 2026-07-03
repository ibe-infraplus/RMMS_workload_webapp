import Plot from 'react-plotly.js';

export default function WorkloadCharts({ results, selectedDept3 }) {
  if (!results) return null;

  // Selected district bar chart data
  const baselineWorkload = results.metrics.baseline_workload_score;
  const revisedWorkload = results.metrics.revised_workload_score;

  // All districts line chart data
  const sortedData = [...results.chart_data.all_districts_revised]
    .map((rev, index) => ({
      rev: rev,
      base: results.chart_data.all_districts_baseline[index]
    }))
    .sort((a, b) => (b.rev.workload_score || 0) - (a.rev.workload_score || 0));

  const xSorted = sortedData.map(item => `${item.rev.dept3} - ${item.rev.district_name}`);
  const baseSorted = sortedData.map(item => item.base.workload_score || 0);
  const revSorted = sortedData.map(item => item.rev.workload_score || 0);
  const paveSorted = sortedData.map(item => item.rev.pavement_workload || 0);

  // Highlighting selected district point
  const highlightTraces = [];
  const selectedDistrictRow = sortedData.find(item => Number(item.rev.dept3) === Number(selectedDept3));
  if (selectedDistrictRow) {
    const selLabel = `${selectedDistrictRow.rev.dept3} - ${selectedDistrictRow.rev.district_name}`;
    const selBaseVal = selectedDistrictRow.base.workload_score || 0;
    const selRevVal = selectedDistrictRow.rev.workload_score || 0;

    const selPaveVal = selectedDistrictRow.rev.pavement_workload || 0;

    highlightTraces.push(
      {
        x: [selLabel],
        y: [selBaseVal],
        type: 'scatter',
        mode: 'markers+text',
        name: 'Selected (Baseline)',
        marker: { color: '#ef4444', size: 12, line: { color: '#ffffff', width: 2 } },
        text: [`Baseline: ${selBaseVal.toLocaleString(undefined, { maximumFractionDigits: 2 })}`],
        textposition: 'top center',
        showlegend: false
      },
      {
        x: [selLabel],
        y: [selRevVal],
        type: 'scatter',
        mode: 'markers+text',
        name: 'Selected (Revised)',
        marker: { color: '#b91c1c', size: 12, line: { color: '#ffffff', width: 2 } },
        text: [`Revised: ${selRevVal.toLocaleString(undefined, { maximumFractionDigits: 2 })}`],
        textposition: 'bottom center',
        showlegend: false
      },
      {
        x: [selLabel],
        y: [selPaveVal],
        type: 'scatter',
        mode: 'markers+text',
        name: 'Selected (ผิวจราจร)',
        marker: { color: '#ea580c', size: 12, line: { color: '#ffffff', width: 2 } },
        text: [`ผิวจราจร: ${selPaveVal.toLocaleString(undefined, { maximumFractionDigits: 2 })}`],
        textposition: 'bottom center',
        showlegend: false
      }
    );
  }

  return (
    <>
      <div className="chart-container" style={{ marginTop: '24px' }}>
        <Plot
          data={[{
            x: ['Baseline', 'Revised'],
            y: [baselineWorkload, revisedWorkload],
            type: 'bar',
            text: [baselineWorkload, revisedWorkload].map(val => Number(val).toFixed(4)),
            textposition: 'outside',
            marker: { color: ['#94a3b8', '#10b981'] }
          }]}
          layout={{
            title: 'เปรียบเทียบคะแนน Workload ของแขวงที่เลือก',
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#f8fafc' },
            yaxis: { title: 'คะแนน Workload', gridcolor: '#334155' },
            hoverlabel: {
              bgcolor: '#1e293b',
              font: { color: '#f8fafc' },
              bordercolor: '#334155'
            }
          }}
          useResizeHandler={true}
          style={{ width: '100%', height: '400px' }}
          config={{ responsive: true }}
        />
      </div>

      <div className="chart-container" style={{ marginTop: '24px' }}>
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
              line: { color: '#10b981', width: 3, shape: 'spline' },
              fill: 'tozeroy',
              fillcolor: 'rgba(16, 185, 129, 0.15)'
            },
            {
              x: xSorted,
              y: paveSorted,
              type: 'scatter',
              mode: 'lines',
              name: 'ผิวจราจร (Revised)',
              line: { color: '#f97316', width: 2, shape: 'spline' }
            },
            ...highlightTraces
          ]}
          layout={{
            title: 'เปรียบเทียบคะแนน Workload ทุกแขวง (Baseline vs Revised)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: { color: '#f8fafc', family: 'Inter' },
            yaxis: { 
              title: 'คะแนน Workload', 
              gridcolor: '#334155', 
              zerolinecolor: '#334155' 
            },
            xaxis: { 
              tickangle: -45, 
              gridcolor: 'transparent',
              tickfont: { size: 10 }
            },
            margin: { b: 140, t: 60, l: 80, r: 20 },
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
          config={{ responsive: true }}
        />
      </div>
    </>
  );
}

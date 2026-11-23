import React, { useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './style.css'

const percent = value => `${value.toFixed(2)}%`
const labels = ['Bust', 'Neutral', 'Boom']
const series = [['actual', 'Actual'], ['prediction', 'Regression'], ['baseline', 'Historical mean']]

function ReturnsChart({ rows, threshold, selected, setSelected }) {
  const bound = Math.ceil(Math.max(threshold, ...rows.flatMap(row =>
    series.map(([key]) => Math.abs(row[key])))) / 5) * 5
  const x = i => 60 + i * 790 / Math.max(rows.length - 1, 1)
  const y = value => 22 + (bound - value) * 244 / (2 * bound)
  const row = rows[selected]
  return <>
    <div className="legend">{series.map(([key, label]) =>
      <span key={key} className={key}>{label}</span>)}</div>
    <svg viewBox="0 0 880 305" role="img" aria-label="Actual and forecast three-month percentage returns">
      {[-bound, -threshold, 0, threshold, bound].filter((v, i, ticks) => ticks.indexOf(v) === i).map(value => <g key={value}>
        <line x1="60" x2="850" y1={y(value)} y2={y(value)} className="grid" strokeDasharray={Math.abs(value) === threshold ? '5 5' : undefined} />
        <text x="52" y={y(value) + 5} textAnchor="end">{value}%</text>
      </g>)}
      <line x1={x(selected)} x2={x(selected)} y1="22" y2="266" className="cursor" />
      {series.map(([key]) => <g key={key} className={key}>
        <polyline points={rows.map((r, i) => `${x(i)},${y(r[key])}`).join(' ')} />
        <circle cx={x(selected)} cy={y(row[key])} r="4" />
      </g>)}
      {rows.map((r, i) => r.month.endsWith('-01') &&
        <text key={r.month} x={x(i)} y="293" textAnchor="middle">{r.month.slice(0, 4)}</text>)}
    </svg>
    <label htmlFor="month">Forecast month <strong>{row.month}</strong></label>
    <input id="month" type="range" min="0" max={rows.length - 1}
      value={selected} aria-valuetext={row.month} onChange={e => setSelected(Number(e.target.value))} />
    <output htmlFor="month">{series.map(([key, label]) => <span key={key}>{label} <b>{percent(row[key])}</b></span>)}</output>
  </>
}

function Dashboard({ data }) {
  const [selected, setSelected] = useState(data.rows.length - 1)
  const maxWeight = Math.max(1, ...data.weights.map(item => Math.abs(item.weight)))
  return <>
    <div className="metrics">
      <div><span>Regression error</span><strong>{data.mae.toFixed(2)} pp</strong></div>
      <div><span>Historical mean error</span><strong>{data.baselineMae.toFixed(2)} pp</strong></div>
      <div><span>Latest model estimate · {data.forecast.end}</span><strong>{percent(data.forecast.return)}</strong><small>{data.forecast.origin} origin · {data.forecast.label}</small></div>
    </div>
    <section><h2>Actual vs. predicted returns</h2>
      <p>{data.horizon}-month returns across {data.rows.length} walk-forward forecasts. Dashed lines mark ±{data.threshold}%.</p>
      <ReturnsChart {...data} selected={selected} setSelected={setSelected} />
    </section>
    <div className="details">
      <section><h2>Boom and bust calls</h2>
        <table><thead><tr><th scope="col">Actual</th>{labels.map(label => <th scope="col" key={label}>{label}</th>)}</tr></thead>
          <tbody>{labels.map(actual => <tr key={actual}><th scope="row">{actual}</th>{labels.map(predicted =>
            <td key={predicted}>{data.rows.filter(r => r.actualLabel === actual && r.predictionLabel === predicted).length}</td>)}</tr>)}</tbody>
        </table><p>Columns show the model’s predicted labels.</p>
      </section>
      <section><h2>Learned weights</h2><p>Change in predicted return per standard deviation, in percentage points.</p>
        {data.weights.map(({ name, weight }) => <div className="weight" key={name}>
          <span>{name}</span><b>{weight.toFixed(2)}</b>
          <div className="track" aria-hidden="true"><div style={{ width: `${Math.abs(weight) / maxWeight * 50}%`, left: weight < 0 ? 'auto' : '50%', right: weight < 0 ? '50%' : 'auto' }} className={weight < 0 ? 'negative' : ''} /></div>
        </div>)}
      </section>
    </div>
    <footer>Source: FRED. Macro observations are lagged two months and may contain historical revisions.</footer>
  </>
}

function App() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    fetch('/api/backtest', { signal: controller.signal }).then(async response => {
      const payload = await response.json()
      if (!response.ok) throw new Error(payload.error)
      setData(payload)
    }).catch(err => { if (err.name !== 'AbortError') setError(err.message || 'Could not reach the API.') })
    return () => controller.abort()
  }, [attempt])
  return <main>
    <header><p>S&amp;P 500</p><h1>Market Regression Lab</h1><span>Linear regression and a historical-average baseline</span></header>
    {data ? <Dashboard data={data} /> : error ?
      <section role="alert"><p>{error}</p><button onClick={() => { setError(''); setAttempt(attempt + 1) }}>Retry</button></section> :
      <section role="status">Running the backtest…</section>}
  </main>
}

createRoot(document.getElementById('root')).render(<App />)

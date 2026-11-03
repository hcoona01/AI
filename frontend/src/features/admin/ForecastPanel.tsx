import React, { useState, useMemo } from 'react';
import {
  ResponsiveContainer,
  ComposedChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from 'recharts';
import { useForecasts, type ForecastRecord } from './api';

interface ForecastPanelProps {
  currentTerm: string;
}

export const ForecastPanel: React.FC<ForecastPanelProps> = ({ currentTerm }) => {
  const { data: forecasts, isLoading, isError, error } = useForecasts(currentTerm);
  const [scenarioMode, setScenarioMode] = useState<'p50' | 'p90'>('p50');
  const [searchTerm, setSearchTerm] = useState<string>('');

  // Filtered courses
  const filteredForecasts = useMemo(() => {
    if (!forecasts) return [];
    if (!searchTerm.trim()) return forecasts;
    const termLower = searchTerm.toLowerCase();
    return forecasts.filter(
      (f) =>
        f.course_code.toLowerCase().includes(termLower) ||
        f.course_id.toLowerCase().includes(termLower)
    );
  }, [forecasts, searchTerm]);

  // Aggregate Metrics
  const metrics = useMemo(() => {
    if (!forecasts || forecasts.length === 0) {
      return {
        totalDemandP50: 0,
        totalDemandP90: 0,
        totalSectionsP50: 0,
        totalSectionsP90: 0,
        surgeBufferSections: 0,
        highRiskCourseCount: 0,
      };
    }

    let totalDemandP50 = 0;
    let totalDemandP90 = 0;
    let totalSectionsP50 = 0;
    let totalSectionsP90 = 0;
    let highRiskCourseCount = 0;

    for (const f of forecasts) {
      totalDemandP50 += f.p50;
      totalDemandP90 += f.p90;
      totalSectionsP50 += f.n_sections;
      totalSectionsP90 += f.p90_risk_sections;

      // Volatility metric: P90 exceeds P50 by > 25% or risk sections > n_sections
      if (f.p90_risk_sections > f.n_sections || (f.p50 > 0 && f.p90 / f.p50 > 1.25)) {
        highRiskCourseCount++;
      }
    }

    return {
      totalDemandP50,
      totalDemandP90,
      totalSectionsP50,
      totalSectionsP90,
      surgeBufferSections: Math.max(0, totalSectionsP90 - totalSectionsP50),
      highRiskCourseCount,
    };
  }, [forecasts]);

  // Chart Data preparation
  const chartData = useMemo(() => {
    return filteredForecasts.map((f) => ({
      courseCode: f.course_code,
      p10: f.p10,
      p50: f.p50,
      p90: f.p90,
      uncertaintyBand: f.p90 - f.p10,
      sectionsP50: f.n_sections,
      sectionsP90: f.p90_risk_sections,
    }));
  }, [filteredForecasts]);

  if (isLoading) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-8 text-center text-slate-400 animate-pulse">
        <div className="h-6 w-48 bg-slate-800 rounded mx-auto mb-4" />
        <p className="text-sm">Loading LightGBM quantile demand forecasts for {currentTerm}...</p>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-rose-950/40 border border-rose-800/60 rounded-xl p-6 text-rose-300 text-sm">
        <h4 className="font-semibold text-rose-200 mb-1">Failed to Load Forecast Data</h4>
        <p>{(error as Error)?.message || 'An unexpected error occurred while fetching demand forecasts.'}</p>
      </div>
    );
  }

  if (!forecasts || forecasts.length === 0) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-12 text-center text-slate-400">
        <span className="text-4xl mb-3 block">📊</span>
        <h3 className="text-lg font-semibold text-white mb-1">No Forecast Data Available</h3>
        <p className="text-sm max-w-md mx-auto">
          No demand forecasts generated for <span className="font-semibold text-slate-200">{currentTerm}</span>.
          Generate forecasts or switch academic terms.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Banner & Scenario Mode Toggle */}
      <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded border border-blue-500/20">
              ML Quantile Forecasts
            </span>
            <span className="text-xs text-slate-400 font-mono">LightGBM (P10, P50, P90)</span>
          </div>
          <h2 className="text-lg font-bold text-white mt-1">Student Enrollment Demand Projections</h2>
          <p className="text-xs text-slate-400">
            Term: <strong className="text-slate-200">{currentTerm}</strong> • {forecasts.length} courses forecasted
          </p>
        </div>

        {/* P50 / P90 Scenario Mode Toggle */}
        <div className="flex items-center bg-slate-950 p-1 rounded-xl border border-slate-800">
          <button
            type="button"
            onClick={() => setScenarioMode('p50')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              scenarioMode === 'p50'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            P50 Expected Mode
          </button>
          <button
            type="button"
            onClick={() => setScenarioMode('p90')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              scenarioMode === 'p90'
                ? 'bg-amber-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            P90 Surge Stress Mode
          </button>
        </div>
      </div>

      {/* Aggregate Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">
            {scenarioMode === 'p50' ? 'Expected Enrollment (P50)' : 'Peak Enrollment (P90)'}
          </div>
          <div className="text-2xl font-bold stat-number text-white mt-1">
            {scenarioMode === 'p50' ? metrics.totalDemandP50 : metrics.totalDemandP90}
            <span className="text-xs font-normal text-slate-400 ml-1.5 font-sans">students</span>
          </div>
          <div className="text-xs text-slate-400 mt-2 font-mono">
            {scenarioMode === 'p50'
              ? `Surge Headroom: +${metrics.totalDemandP90 - metrics.totalDemandP50}`
              : `Baseline Delta: +${metrics.totalDemandP90 - metrics.totalDemandP50} vs P50`}
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">
            {scenarioMode === 'p50' ? 'Planned Sections (P50)' : 'Risk Sections (P90)'}
          </div>
          <div className="text-2xl font-bold stat-number text-white mt-1">
            {scenarioMode === 'p50' ? metrics.totalSectionsP50 : metrics.totalSectionsP90}
            <span className="text-xs font-normal text-slate-400 ml-1.5 font-sans">sections</span>
          </div>
          <div className="text-xs text-blue-400 mt-2 font-mono">
            {scenarioMode === 'p50' ? 'Target section plan' : `+${metrics.surgeBufferSections} buffer sections`}
          </div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Surge Capacity Buffer</div>
          <div className="text-2xl font-bold stat-number text-amber-400 mt-1">
            +{metrics.surgeBufferSections}
            <span className="text-xs font-normal text-slate-400 ml-1.5 font-sans">sections</span>
          </div>
          <div className="text-xs text-amber-500/80 mt-2 font-mono">P90 - P50 staffing delta</div>
        </div>

        <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Volatile Offerings</div>
          <div className="text-2xl font-bold stat-number text-rose-400 mt-1">
            {metrics.highRiskCourseCount}
            <span className="text-xs font-normal text-slate-400 ml-1.5 font-sans">/ {forecasts.length} courses</span>
          </div>
          <div className="text-xs text-slate-400 mt-2 font-mono">P90 &gt; 125% of P50 or extra section</div>
        </div>
      </div>

      {/* Uncertainty Band Chart */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <div>
            <h3 className="text-sm font-bold text-white uppercase tracking-wider">
              Course Demand & Uncertainty Bands (P10 &bull; P50 &bull; P90)
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              The spread between P10 (conservative) and P90 (surge) illustrates enrollment volatility.
            </p>
          </div>
          <div className="flex items-center gap-2">
            <input
              type="text"
              placeholder="Filter by course..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-slate-950 border border-slate-700 text-xs text-white rounded-lg px-2.5 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500 w-44"
            />
          </div>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 25 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e8ece0" opacity={0.9} />
              <XAxis
                dataKey="courseCode"
                tick={{ fill: '#5c634c', fontSize: 11 }}
                angle={-45}
                textAnchor="end"
                interval={0}
              />
              <YAxis
                tick={{ fill: '#5c634c', fontSize: 11 }}
                label={{ value: 'Students', angle: -90, position: 'insideLeft', fill: '#5c634c', fontSize: 11 }}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload as {
                      courseCode: string;
                      p10: number;
                      p50: number;
                      p90: number;
                      sectionsP50: number;
                      sectionsP90: number;
                    };
                    return (
                      <div className="bg-slate-950 border border-slate-700 p-3 rounded-lg shadow-xl text-xs space-y-1">
                        <div className="font-bold text-white text-sm border-b border-slate-800 pb-1 mb-1">
                          {data.courseCode}
                        </div>
                        <div className="text-slate-400 flex justify-between gap-4">
                          <span>Conservative (P10):</span>
                          <span className="font-mono text-slate-300 font-semibold">{data.p10}</span>
                        </div>
                        <div className="text-blue-400 flex justify-between gap-4">
                          <span>Median Demand (P50):</span>
                          <span className="font-mono font-semibold">{data.p50}</span>
                        </div>
                        <div className="text-amber-400 flex justify-between gap-4">
                          <span>Surge Demand (P90):</span>
                          <span className="font-mono font-semibold">{data.p90}</span>
                        </div>
                        <div className="text-purple-400 flex justify-between gap-4 border-t border-slate-800 pt-1 mt-1">
                          <span>Sections (P50 / P90):</span>
                          <span className="font-mono font-semibold">
                            {data.sectionsP50} / {data.sectionsP90}
                          </span>
                        </div>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Legend
                verticalAlign="top"
                align="right"
                wrapperStyle={{ paddingBottom: '10px', fontSize: '11px' }}
              />
              <Bar dataKey="p10" name="P10 (Floor)" fill="#cfd6c0" radius={[2, 2, 0, 0]} />
              <Bar dataKey="p50" name="P50 (Median)" fill="#4d6a10" radius={[2, 2, 0, 0]} />
              <Bar dataKey="p90" name="P90 (Surge)" fill="#b4cd52" radius={[2, 2, 0, 0]} />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Course Projections Detailed Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider">
            Course Section Requirements ({filteredForecasts.length})
          </h3>
          <span className="text-xs text-slate-400">
            Active Mode: <strong className="text-blue-400 uppercase">{scenarioMode}</strong>
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/60 text-slate-400 uppercase font-mono border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Course Code</th>
                <th className="py-3 px-4 text-center">P10 (Floor)</th>
                <th className="py-3 px-4 text-center bg-blue-950/20 text-blue-300">P50 (Expected)</th>
                <th className="py-3 px-4 text-center bg-amber-950/20 text-amber-300">P90 (Surge)</th>
                <th className="py-3 px-4 text-center">P90 - P10 Spread</th>
                <th className="py-3 px-4 text-center">Sections Needed</th>
                <th className="py-3 px-4 text-center">Risk Sections</th>
                <th className="py-3 px-4 text-right">Volatility Tag</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {filteredForecasts.map((f: ForecastRecord) => {
                const spread = f.p90 - f.p10;
                const isHighVolatility = f.p90_risk_sections > f.n_sections || (f.p50 > 0 && f.p90 / f.p50 > 1.25);
                const activeSections = scenarioMode === 'p50' ? f.n_sections : f.p90_risk_sections;

                return (
                  <tr key={f.course_id} className="hover:bg-slate-800/40 transition">
                    <td className="py-3 px-4 font-mono font-bold text-white">
                      {f.course_code}
                    </td>
                    <td className="py-3 px-4 text-center font-mono text-slate-400">{f.p10}</td>
                    <td className="py-3 px-4 text-center font-mono font-semibold text-blue-400 bg-blue-950/10">
                      {f.p50}
                    </td>
                    <td className="py-3 px-4 text-center font-mono font-semibold text-amber-400 bg-amber-950/10">
                      {f.p90}
                    </td>
                    <td className="py-3 px-4 text-center font-mono text-slate-400">&plusmn;{Math.round(spread / 2)}</td>
                    <td className="py-3 px-4 text-center">
                      <span className="font-mono font-bold text-white px-2 py-0.5 rounded bg-slate-800">
                        {activeSections}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span
                        className={`font-mono text-xs px-2 py-0.5 rounded ${
                          f.p90_risk_sections > f.n_sections
                            ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30 font-bold'
                            : 'text-slate-400'
                        }`}
                      >
                        {f.p90_risk_sections}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-right">
                      {isHighVolatility ? (
                        <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-rose-500/15 text-rose-400 border border-rose-500/30">
                          High Volatility
                        </span>
                      ) : (
                        <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                          Stable
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};


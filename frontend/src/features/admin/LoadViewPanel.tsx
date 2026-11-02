import React, { useMemo, useState } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
  ReferenceLine,
} from 'recharts';
import { useFairness } from './api';

interface LoadViewProps {
  currentTerm: string;
}

type LoadFilter = 'all' | 'over' | 'balanced' | 'under';

interface FacultyLoadChartItem {
  id: string;
  name: string;
  rank: string;
  assigned: number;
  maxLimit: number;
  ratio: number;
  status: 'over' | 'balanced' | 'under';
}

export const LoadViewPanel: React.FC<LoadViewProps> = ({ currentTerm }) => {
  const { data: fairness, isLoading, isError, error } = useFairness(currentTerm);
  const [filter, setFilter] = useState<LoadFilter>('all');

  // Prepare data with status tag and visual thresholds
  const chartData: FacultyLoadChartItem[] = useMemo(() => {
    if (!fairness?.faculty_loads) return [];

    return fairness.faculty_loads.map((item): FacultyLoadChartItem => {
      const assigned = item.assigned_contact_hours;
      const maxLimit = item.max_weekly_load_hours;
      const ratio = item.load_ratio;

      let status: 'over' | 'balanced' | 'under' = 'balanced';
      if (assigned > maxLimit) {
        status = 'over';
      } else if (ratio < 0.6) {
        status = 'under';
      }

      return {
        id: item.faculty_id,
        name: item.name,
        rank: item.rank,
        assigned,
        maxLimit,
        ratio: Math.round(ratio * 100),
        status,
      };
    });
  }, [fairness]);

  const filteredData = useMemo(() => {
    if (filter === 'all') return chartData;
    return chartData.filter((d: FacultyLoadChartItem) => d.status === filter);
  }, [chartData, filter]);

  // Color lookup based on workload state
  const getColor = (status: 'over' | 'balanced' | 'under') => {
    switch (status) {
      case 'over':
        return '#f43f5e'; // rose-500 (Overloaded)
      case 'balanced':
        return '#6f9a0c'; // olive green (Balanced)
      case 'under':
        return '#b4cd52'; // lime (Underloaded / Spare capacity)
    }
  };

  if (isLoading) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-8 text-center text-slate-400 animate-pulse">
        Loading faculty workload distributions for {currentTerm}...
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-rose-950/40 border border-rose-800/60 rounded-xl p-6 text-rose-300 text-sm">
        Failed to load workload distribution: {(error as Error)?.message}
      </div>
    );
  }

  if (!chartData || chartData.length === 0) {
    return (
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-12 text-center text-slate-400">
        No faculty workload assignments found for {currentTerm}. Run the optimizer to create assignments.
      </div>
    );
  }

  const overCount = chartData.filter((d: FacultyLoadChartItem) => d.status === 'over').length;
  const balancedCount = chartData.filter((d: FacultyLoadChartItem) => d.status === 'balanced').length;
  const underCount = chartData.filter((d: FacultyLoadChartItem) => d.status === 'under').length;

  return (
    <div className="space-y-6">
      {/* Header and Filter Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/90 border border-slate-800 rounded-xl p-4">
        <div>
          <h2 className="text-base font-bold text-white">Faculty Teaching Load Distribution</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Weekly contact hours compared against contractual limits ({currentTerm}).
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <button
            type="button"
            onClick={() => setFilter('all')}
            className={`px-3 py-1 rounded-lg text-xs font-medium transition cursor-pointer ${
              filter === 'all'
                ? 'bg-blue-600 text-white'
                : 'bg-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            All ({chartData.length})
          </button>
          <button
            type="button"
            onClick={() => setFilter('over')}
            className={`px-3 py-1 rounded-lg text-xs font-medium transition cursor-pointer ${
              filter === 'over'
                ? 'bg-rose-600 text-white'
                : 'bg-slate-800 text-rose-400 hover:bg-slate-700'
            }`}
          >
            Overloaded ({overCount})
          </button>
          <button
            type="button"
            onClick={() => setFilter('balanced')}
            className={`px-3 py-1 rounded-lg text-xs font-medium transition cursor-pointer ${
              filter === 'balanced'
                ? 'bg-emerald-600 text-white'
                : 'bg-slate-800 text-emerald-400 hover:bg-slate-700'
            }`}
          >
            Balanced ({balancedCount})
          </button>
          <button
            type="button"
            onClick={() => setFilter('under')}
            className={`px-3 py-1 rounded-lg text-xs font-medium transition cursor-pointer ${
              filter === 'under'
                ? 'bg-sky-600 text-white'
                : 'bg-slate-800 text-sky-400 hover:bg-slate-700'
            }`}
          >
            Underloaded ({underCount})
          </button>
        </div>
      </div>

      {/* Main Bar Chart */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6">
        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={filteredData}
              margin={{ top: 20, right: 30, left: 10, bottom: 40 }}
            >
              <XAxis
                dataKey="name"
                stroke="#8b9278"
                fontSize={11}
                tickLine={false}
                interval={0}
                angle={-45}
                textAnchor="end"
                height={60}
              />
              <YAxis
                stroke="#8b9278"
                fontSize={11}
                tickLine={false}
                label={{ value: 'Contact Hours / Week', angle: -90, position: 'insideLeft', fill: '#5c634c', fontSize: 11 }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#ffffff',
                  borderColor: '#e8ece0',
                  color: '#121410',
                  borderRadius: '0.5rem',
                  fontSize: '0.75rem',
                }}
                formatter={(value: unknown, name: unknown) => {
                  const val = typeof value === 'number' ? `${value} hrs` : String(value);
                  const lbl = name === 'assigned' ? 'Assigned Load' : 'Max Limit';
                  return [val, lbl];
                }}
              />
              <ReferenceLine y={12} stroke="#8b9278" strokeDasharray="3 3" label={{ value: 'Standard Cap (12h)', fill: '#5c634c', fontSize: 10 }} />
              <Bar dataKey="assigned" radius={[4, 4, 0, 0]}>
                {filteredData.map((entry: FacultyLoadChartItem) => (
                  <Cell key={`cell-${entry.id}`} fill={getColor(entry.status)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Legend Summary */}
        <div className="mt-4 pt-4 border-t border-slate-800 grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-xs bg-emerald-500 inline-block" />
            <span className="text-slate-300">
              Balanced: 60% – 100% of max capacity
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-xs bg-rose-500 inline-block" />
            <span className="text-slate-300">
              Overloaded: &gt; 100% limit (Violates HC-02)
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-xs bg-sky-400 inline-block" />
            <span className="text-slate-300">
              Underloaded: &lt; 60% capacity (Available slack)
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

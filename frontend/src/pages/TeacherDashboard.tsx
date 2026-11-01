import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { fetchHeatmap, fetchFlags, fetchErrorBreakdown, fetchStudents } from '../api/client';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';

const MASTERY_CELL: Record<string, string> = {
  at_risk: 'bg-red-500',
  struggling: 'bg-yellow-400',
  proficient: 'bg-blue-400',
  mastered: 'bg-green-500',
};

const PIE_COLORS = ['#ef4444', '#f97316', '#3b82f6'];

export function TeacherDashboard() {
  const [threshold, setThreshold] = useState<number>(0.4);
  const [selectedStudentId, setSelectedStudentId] = useState<number | null>(null);

  const { data: heatmap } = useQuery({ queryKey: ['heatmap'], queryFn: fetchHeatmap, refetchInterval: 10000 });
  const { data: flags }   = useQuery({ queryKey: ['flags', threshold], queryFn: () => fetchFlags(threshold) });
  const { data: students } = useQuery({ queryKey: ['students'], queryFn: fetchStudents });
  const { data: errors }  = useQuery({
    queryKey: ['errors', selectedStudentId],
    queryFn: () => fetchErrorBreakdown(selectedStudentId!),
    enabled: !!selectedStudentId,
  });

  const skillNames = Array.from(new Set(heatmap?.map(c => c.skill_name) ?? []));
  const studentNames = Array.from(new Set(heatmap?.map(c => c.student_name) ?? []));

  const pieData = errors ? [
    { name: 'Conceptual', value: errors.conceptual },
    { name: 'Careless', value: errors.careless },
    { name: 'Language Confusion', value: errors.language_confusion },
  ] : [];

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-800">🪐 CosmoTute — Teacher Dashboard</h1>
          <p className="text-gray-500 text-sm mt-1">Class 8 Math · BKT Mastery Tracker · India</p>
        </div>

        {/* Stats bar */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          {[
            { label: 'Students', value: students?.length ?? 0, icon: '👨‍🎓', color: 'bg-indigo-50 border-indigo-200 text-indigo-700' },
            { label: 'Skills Tracked', value: skillNames.length, icon: '📚', color: 'bg-blue-50 border-blue-200 text-blue-700' },
            { label: 'At-Risk Flags', value: flags?.length ?? 0, icon: '🚨', color: 'bg-red-50 border-red-200 text-red-700' },
            { label: 'Mastery Threshold', value: `${Math.round(threshold*100)}%`, icon: '🎯', color: 'bg-green-50 border-green-200 text-green-700' },
          ].map(s => (
            <div key={s.label} className={`rounded-xl border p-4 ${s.color}`}>
              <div className="text-2xl mb-1">{s.icon}</div>
              <div className="text-2xl font-bold">{s.value}</div>
              <div className="text-xs font-medium opacity-70">{s.label}</div>
            </div>
          ))}
        </div>

        {/* Heatmap */}
        <div className="bg-white rounded-2xl shadow-sm border p-5 mb-6 overflow-x-auto">
          <div className="flex items-center justify-between mb-4">
            <h2 className="font-bold text-gray-800">📊 Skill × Student Mastery Heatmap</h2>
            <div className="flex items-center gap-3 text-xs">
              {Object.entries(MASTERY_CELL).map(([label, cls]) => (
                <span key={label} className="flex items-center gap-1">
                  <span className={`w-3 h-3 rounded-sm inline-block ${cls}`}></span>
                  <span className="capitalize text-gray-500">{label.replace('_', ' ')}</span>
                </span>
              ))}
            </div>
          </div>
          <table className="min-w-full text-xs">
            <thead>
              <tr>
                <th className="text-left py-2 pr-4 text-gray-500 font-medium w-32">Skill</th>
                {studentNames.map(n => (
                  <th key={n} className="text-center py-2 px-2 text-gray-500 font-medium">{n.split(' ')[0]}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {skillNames.map((skill, si) => {
                const skillCells = heatmap?.filter(c => c.skill_name === skill) ?? [];
                return (
                  <tr key={si} className={si % 2 === 0 ? 'bg-gray-50/50' : ''}>
                    <td className="py-2 pr-4 text-gray-700 font-medium text-xs max-w-[130px] truncate" title={skill}>
                      {skill.split('–')[0].split('and')[0].trim()}
                    </td>
                    {studentNames.map(studentName => {
                      const cell = skillCells.find(c => c.student_name === studentName);
                      return (
                        <td key={studentName} className="py-2 px-2 text-center">
                          <div title={`${cell?.mastery !== undefined ? Math.round(cell.mastery*100) : '?'}%`}
                            className={`mx-auto w-8 h-8 rounded-md flex items-center justify-center text-white font-bold text-xs ${cell ? MASTERY_CELL[cell.mastery_label] : 'bg-gray-200'}`}>
                            {cell ? Math.round(cell.mastery*100) : '?'}
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="grid grid-cols-2 gap-6 mb-6">
          {/* Flagged Students */}
          <div className="bg-white rounded-2xl shadow-sm border p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-bold text-gray-800">🚨 At-Risk Students</h2>
              <div className="flex items-center gap-2">
                <label className="text-xs text-gray-500">Threshold:</label>
                <select value={threshold} onChange={e => setThreshold(Number(e.target.value))}
                  className="text-xs border rounded px-2 py-1">
                  {[0.3,0.4,0.5,0.6].map(t => <option key={t} value={t}>{Math.round(t*100)}%</option>)}
                </select>
              </div>
            </div>
            {flags?.length === 0 && <p className="text-sm text-gray-400 text-center py-4">🎉 No students below threshold!</p>}
            <div className="space-y-2 max-h-72 overflow-y-auto">
              {flags?.map((f, i) => (
                <div key={i} className="flex items-center gap-3 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold text-gray-800">{f.student_name}</p>
                    <p className="text-xs text-gray-500 truncate">{f.skill_name.split('–')[0].trim()}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-bold text-red-600">{Math.round(f.mastery*100)}%</span>
                    <p className="text-xs text-gray-400">{f.opportunities} attempts</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Error Breakdown */}
          <div className="bg-white rounded-2xl shadow-sm border p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-bold text-gray-800">🔍 Error Analysis</h2>
              <select value={selectedStudentId ?? ''} onChange={e => setSelectedStudentId(Number(e.target.value) || null)}
                className="text-xs border rounded px-2 py-1">
                <option value="">Select student…</option>
                {students?.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
            </div>
            {selectedStudentId && errors ? (
              errors.total_errors === 0 ? (
                <p className="text-sm text-gray-400 text-center py-8">No errors recorded yet! 🎉</p>
              ) : (
                <>
                  <ResponsiveContainer width="100%" height={180}>
                    <PieChart>
                      <Pie data={pieData.filter(d => d.value > 0)} cx="50%" cy="50%" outerRadius={70}
                        dataKey="value" label={({ name, percent }) => `${name}: ${(percent ? percent*100 : 0).toFixed(0)}%`}>
                        {pieData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i]} />)}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="grid grid-cols-3 gap-2 mt-2">
                    {[
                      { label: 'Conceptual', val: errors.conceptual, pct: errors.conceptual_pct, color: 'text-red-600' },
                      { label: 'Careless', val: errors.careless, pct: errors.careless_pct, color: 'text-orange-500' },
                      { label: 'Language', val: errors.language_confusion, pct: errors.language_confusion_pct, color: 'text-blue-600' },
                    ].map(e => (
                      <div key={e.label} className="text-center bg-gray-50 rounded-lg p-2">
                        <p className={`text-lg font-bold ${e.color}`}>{e.val}</p>
                        <p className="text-xs text-gray-500">{e.label}</p>
                        <p className="text-xs text-gray-400">{e.pct}%</p>
                      </div>
                    ))}
                  </div>
                </>
              )
            ) : (
              <div className="flex items-center justify-center h-48 text-gray-400 text-sm">Select a student to see error breakdown</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

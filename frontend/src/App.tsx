import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { StudentApp } from './pages/StudentApp';
import { TeacherDashboard } from './pages/TeacherDashboard';
import './index.css';

const queryClient = new QueryClient();

const STUDENTS = [
  { id: 1, name: 'Aarav Sharma', avatar: '🧑‍🎓' },
  { id: 2, name: 'Priya Nair', avatar: '👩‍🎓' },
  { id: 3, name: 'Rohan Mehta', avatar: '🧒' },
  { id: 4, name: 'Sneha Reddy', avatar: '👧' },
  { id: 5, name: 'Kiran Patel', avatar: '🧑' },
];

type View = 'select' | 'student' | 'teacher';

export default function App() {
  const [view, setView] = useState<View>('select');
  const [studentId, setStudentId] = useState<number>(1);
  const [studentName, setStudentName] = useState<string>('');

  if (view === 'student') {
    return (
      <QueryClientProvider client={queryClient}>
        <div>
          <div className="bg-white border-b px-4 py-2 flex items-center gap-3">
            <button onClick={() => setView('select')} className="text-indigo-600 text-sm font-medium hover:underline">← Back</button>
            <span className="text-gray-400 text-sm">Student View</span>
          </div>
          <StudentApp studentId={studentId} studentName={studentName} />
        </div>
      </QueryClientProvider>
    );
  }

  if (view === 'teacher') {
    return (
      <QueryClientProvider client={queryClient}>
        <div>
          <div className="bg-white border-b px-4 py-2 flex items-center gap-3">
            <button onClick={() => setView('select')} className="text-indigo-600 text-sm font-medium hover:underline">← Back</button>
            <span className="text-gray-400 text-sm">Teacher Dashboard</span>
          </div>
          <TeacherDashboard />
        </div>
      </QueryClientProvider>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-indigo-800 to-blue-900 flex items-center justify-center p-6">
        <div className="w-full max-w-lg">
          <div className="text-center mb-10">
            <h1 className="text-5xl font-black text-white mb-2">🪐 CosmoTute</h1>
            <p className="text-indigo-200 text-lg">Adaptive Learning Engine · Class 8 Math</p>
            <p className="text-indigo-300 text-sm mt-1">Bayesian Knowledge Tracing · India-focused</p>
          </div>

          {/* Student Cards */}
          <div className="bg-white/10 backdrop-blur rounded-2xl p-5 mb-4">
            <h2 className="text-white font-bold mb-3 text-sm uppercase tracking-wide">👨‍🎓 Login as Student</h2>
            <div className="grid grid-cols-1 gap-2">
              {STUDENTS.map(s => (
                <button key={s.id} onClick={() => { setStudentId(s.id); setStudentName(s.name); setView('student'); }}
                  className="flex items-center gap-3 bg-white/10 hover:bg-white/20 text-white rounded-xl px-4 py-2.5 transition-all text-left">
                  <span className="text-2xl">{s.avatar}</span>
                  <span className="font-semibold text-sm">{s.name}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Teacher */}
          <button onClick={() => setView('teacher')}
            className="w-full bg-white text-indigo-900 font-bold py-3 rounded-2xl hover:bg-indigo-50 transition-all flex items-center justify-center gap-2 text-sm">
            🏫 Open Teacher Dashboard
          </button>
        </div>
      </div>
    </QueryClientProvider>
  );
}

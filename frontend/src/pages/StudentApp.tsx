import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { fetchNextQuestion, submitAnswer, fetchStudentMastery, Question, AnswerResponse } from '../api/client';

type Mode = 'learn' | 'solve' | 'test';

const DIFFICULTY_LABEL: Record<number, string> = { 1: 'Easy', 2: 'Medium', 3: 'Hard' };
const MASTERY_COLOR: Record<string, string> = {
  at_risk: 'bg-red-100 text-red-700 border-red-300',
  struggling: 'bg-yellow-100 text-yellow-700 border-yellow-300',
  proficient: 'bg-blue-100 text-blue-700 border-blue-300',
  mastered: 'bg-green-100 text-green-700 border-green-300',
};
const MASTERY_BAR: Record<string, string> = {
  at_risk: 'bg-red-500', struggling: 'bg-yellow-400', proficient: 'bg-blue-500', mastered: 'bg-green-500'
};

interface Props { studentId: number; studentName: string; }

export function StudentApp({ studentId, studentName }: Props) {
  const [skillId, setSkillId] = useState<number>(1);
  const [mode, setMode] = useState<Mode>('solve');
  const [currentQuestion, setCurrentQuestion] = useState<Question | null>(null);
  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<AnswerResponse | null>(null);
  const [answered, setAnswered] = useState<boolean>(false);
  const queryClient = useQueryClient();

  const { data: mastery } = useQuery({ queryKey: ['mastery', studentId], queryFn: () => fetchStudentMastery(studentId), refetchInterval: 5000 });

  const { data: fetchedQ, isLoading: loadingQ, refetch: refetchQ } = useQuery<Question>({
    queryKey: ['nextQ', studentId, skillId, mode],
    queryFn: () => fetchNextQuestion(studentId, skillId, mode),
  });

  useEffect(() => {
    if (fetchedQ) {
      setCurrentQuestion(fetchedQ);
      setSelectedAnswer(null);
      setLastResult(null);
      setAnswered(false);
    }
  }, [fetchedQ]);

  const answerMutation = useMutation({
    mutationFn: () => submitAnswer(studentId, currentQuestion!.id, selectedAnswer!, mode),
    onSuccess: (res: AnswerResponse) => {
      setLastResult(res);
      setAnswered(true);
      queryClient.invalidateQueries({ queryKey: ['mastery', studentId] });
    },
  });

  const handleNext = () => {
    if (lastResult?.next_question) {
      setCurrentQuestion(lastResult.next_question);
    } else {
      setCurrentQuestion(null);
      refetchQ();
    }
    setSelectedAnswer(null);
    setLastResult(null);
    setAnswered(false);
  };

  const skillMastery = mastery?.find(m => m.skill_id === skillId);
  const q: Question | null = currentQuestion || fetchedQ || null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-blue-50 p-4">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-indigo-800">🪐 CosmoTute</h1>
            <p className="text-sm text-gray-500">Hello, <span className="font-semibold">{studentName}</span> 👋</p>
          </div>
          {/* Mode Selector */}
          <div className="flex gap-2 bg-white rounded-xl p-1 shadow-sm border">
            {(['learn', 'solve', 'test'] as Mode[]).map(m => (
              <button key={m} onClick={() => { setMode(m); setCurrentQuestion(null); }}
                className={`px-3 py-1.5 rounded-lg text-sm font-semibold capitalize transition-all ${mode === m ? 'bg-indigo-600 text-white shadow' : 'text-gray-500 hover:bg-gray-100'}`}>
                {m === 'learn' ? '📖 Learn' : m === 'solve' ? '✏️ Solve' : '🎯 Test'}
              </button>
            ))}
          </div>
        </div>

        {/* Skill Selector */}
        <div className="flex gap-2 flex-wrap mb-4">
          {[1,2,3,4,5,6,7,8].map(sid => {
            const sm = mastery?.find(m => m.skill_id === sid);
            return (
              <button key={sid} onClick={() => { setSkillId(sid); setCurrentQuestion(null); }}
                className={`px-3 py-1 rounded-full text-xs font-medium border transition-all ${skillId === sid ? 'bg-indigo-600 text-white border-indigo-600' : 'bg-white text-gray-600 border-gray-300 hover:border-indigo-400'}`}>
                {sm?.skill_name.split('–')[0].trim() || `Skill ${sid}`}
              </button>
            );
          })}
        </div>

        {/* Mastery Banner */}
        {skillMastery && (
          <div className={`rounded-xl p-3 mb-4 border flex items-center gap-3 ${MASTERY_COLOR[skillMastery.mastery_label]}`}>
            <div className="flex-1">
              <div className="flex justify-between text-xs font-semibold mb-1">
                <span>{skillMastery.skill_name}</span>
                <span>{Math.round(skillMastery.mastery * 100)}% Mastery</span>
              </div>
              <div className="w-full bg-white/60 rounded-full h-2">
                <div className={`h-2 rounded-full transition-all duration-700 ${MASTERY_BAR[skillMastery.mastery_label]}`}
                  style={{ width: `${skillMastery.mastery * 100}%` }} />
              </div>
            </div>
            <span className="text-xs capitalize font-bold px-2 py-0.5 bg-white/50 rounded-full">
              {skillMastery.mastery_label.replace('_', ' ')}
            </span>
          </div>
        )}

        {/* Question Card */}
        {loadingQ && !q ? (
          <div className="bg-white rounded-2xl shadow-md p-8 text-center text-gray-400">Loading question…</div>
        ) : q ? (
          <div className="bg-white rounded-2xl shadow-md p-6">
            <div className="flex items-center gap-2 mb-4">
              <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${q.difficulty === 1 ? 'bg-green-100 text-green-700' : q.difficulty === 2 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}`}>
                {DIFFICULTY_LABEL[q.difficulty]}
              </span>
              <span className="text-xs text-gray-400">Question #{q.id}</span>
            </div>

            <p className="text-lg font-semibold text-gray-800 mb-5 leading-relaxed">{q.text}</p>

            <div className="grid grid-cols-1 gap-2 mb-5">
              {q.options.map((opt: string, i: number) => {
                let style = 'bg-gray-50 border-gray-200 text-gray-700 hover:border-indigo-400 hover:bg-indigo-50';
                if (answered && lastResult) {
                  if (opt === lastResult.explanation.split('.')[0] || opt === selectedAnswer) {
                    if (opt === selectedAnswer && lastResult.correct) style = 'bg-green-100 border-green-500 text-green-800';
                    else if (opt === selectedAnswer && !lastResult.correct) style = 'bg-red-100 border-red-500 text-red-800';
                  }
                } else if (selectedAnswer === opt) {
                  style = 'bg-indigo-100 border-indigo-500 text-indigo-800';
                }
                return (
                  <button key={i} disabled={answered}
                    onClick={() => setSelectedAnswer(opt)}
                    className={`p-3 border-2 rounded-xl text-left text-sm font-medium transition-all ${style}`}>
                    <span className="font-bold mr-2">{String.fromCharCode(65+i)}.</span>{opt}
                  </button>
                );
              })}
            </div>

            {/* Answer Result */}
            {answered && lastResult && (
              <div className={`rounded-xl p-4 mb-4 ${lastResult.correct ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xl">{lastResult.correct ? '✅' : '❌'}</span>
                  <span className="font-bold text-sm">{lastResult.correct ? 'Correct!' : 'Incorrect'}</span>
                  {lastResult.error_type && (
                    <span className="ml-auto text-xs bg-orange-100 text-orange-700 px-2 py-0.5 rounded-full font-semibold">
                      {lastResult.error_type.replace('_', ' ')}
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-600 mt-1">{lastResult.explanation}</p>
                <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
                  <span>Mastery: {Math.round(lastResult.mastery_before*100)}% → <strong className="text-indigo-700">{Math.round(lastResult.mastery_after*100)}%</strong></span>
                  <span className="capitalize bg-white px-2 py-0.5 rounded-full border">{lastResult.mastery_label.replace('_',' ')}</span>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3">
              {!answered ? (
                <button onClick={() => answerMutation.mutate()} disabled={!selectedAnswer || answerMutation.isPending}
                  className="flex-1 bg-indigo-600 text-white py-2.5 rounded-xl font-semibold text-sm disabled:opacity-40 hover:bg-indigo-700 transition-all">
                  {answerMutation.isPending ? 'Submitting…' : 'Submit Answer'}
                </button>
              ) : (
                <button onClick={handleNext}
                  className="flex-1 bg-green-600 text-white py-2.5 rounded-xl font-semibold text-sm hover:bg-green-700 transition-all">
                  Next Question →
                </button>
              )}
            </div>
          </div>
        ) : null}

        {/* Mastery overview grid */}
        {mastery && (
          <div className="mt-6 bg-white rounded-2xl shadow-md p-5">
            <h3 className="text-sm font-bold text-gray-700 mb-3">📊 Your Skill Progress</h3>
            <div className="space-y-2">
              {mastery.map(m => (
                <div key={m.skill_id} className="flex items-center gap-2">
                  <span className="text-xs text-gray-600 w-48 truncate">{m.skill_name.split('–')[0].trim()}</span>
                  <div className="flex-1 bg-gray-100 rounded-full h-1.5">
                    <div className={`h-1.5 rounded-full ${MASTERY_BAR[m.mastery_label]}`} style={{ width: `${m.mastery * 100}%` }} />
                  </div>
                  <span className="text-xs text-gray-500 w-8 text-right">{Math.round(m.mastery*100)}%</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

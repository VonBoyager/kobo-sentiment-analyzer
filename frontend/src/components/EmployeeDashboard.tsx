import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { ClipboardList, CheckCircle, Clock, Calendar, Sparkles, Shield, TrendingUp } from 'lucide-react';

const submissionHistory = [
  { id: 1, date: '2024-11-15', status: 'completed', quarter: 'Q4 2024' },
  { id: 2, date: '2024-08-20', status: 'completed', quarter: 'Q3 2024' },
  { id: 3, date: '2024-05-10', status: 'completed', quarter: 'Q2 2024' },
];

export function EmployeeDashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();

  return (
    <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-12 gap-4 lg:gap-5">
        
        {/* Welcome Card */}
        <div className="sm:col-span-2 lg:col-span-8 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-3xl p-8 sm:p-10 text-white relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl"></div>
          <div className="relative z-10">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="w-5 h-5 text-blue-400" />
              <span className="text-sm text-blue-300 uppercase tracking-wider">Employee Dashboard</span>
            </div>
            <h1 className="text-3xl sm:text-4xl mb-3">Welcome, {user?.name}!</h1>
            <p className="text-slate-300 text-base sm:text-lg max-w-2xl">
              Your feedback helps us create a better workplace for everyone. 
              <span className="text-blue-400 font-semibold"> Anonymous & confidential.</span>
            </p>
          </div>
        </div>

        {/* Current Survey Status */}
        <div className="sm:col-span-2 lg:col-span-4 bg-gradient-to-br from-blue-600 to-blue-700 rounded-2xl p-6 text-white relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full blur-2xl"></div>
          <div className="relative z-10">
            <div className="flex items-center gap-2 mb-3">
              <Clock className="w-5 h-5 opacity-90" />
              <span className="text-sm text-blue-100 uppercase tracking-wider">Active Survey</span>
            </div>
            <h3 className="text-xl mb-2">Q4 2024</h3>
            <p className="text-sm text-blue-100 mb-4">Survey is now open</p>
            
            <button
              onClick={() => navigate('/questionnaire')}
              className="w-full px-4 py-3 bg-white text-blue-700 rounded-xl hover:bg-blue-50 transition-all shadow-lg hover:shadow-xl flex items-center justify-center gap-2 text-sm font-medium"
            >
              <ClipboardList className="w-4 h-4" />
              Start Questionnaire
            </button>
          </div>
        </div>

        {/* Submission History */}
        <div className="sm:col-span-2 lg:col-span-6 bg-gray-800 rounded-2xl p-6 border border-gray-700 hover:shadow-md transition-shadow">
          <div className="flex items-center gap-2 mb-5">
            <Calendar className="w-5 h-5 text-blue-400" />
            <h2 className="text-xl text-white">Submission History</h2>
          </div>
          <div className="space-y-3">
            {submissionHistory.map((submission) => (
              <div key={submission.id} className="flex items-center justify-between p-4 bg-gray-700/50 rounded-xl border border-gray-600">
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-emerald-400" />
                  <div>
                    <div className="text-sm font-medium text-white">{submission.quarter}</div>
                    <div className="text-xs text-gray-400">{submission.date}</div>
                  </div>
                </div>
                <span className="px-3 py-1 bg-emerald-900/30 text-emerald-300 text-xs font-medium rounded-lg border border-emerald-800">
                  {submission.status}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Privacy & Security */}
        <div className="sm:col-span-2 lg:col-span-6 bg-gray-800 rounded-2xl p-6 border border-gray-700 hover:shadow-md transition-shadow">
          <div className="flex items-center gap-2 mb-5">
            <Shield className="w-5 h-5 text-blue-400" />
            <h2 className="text-xl text-white">Privacy & Security</h2>
          </div>
          <div className="space-y-3">
            <div className="p-4 bg-blue-900/20 rounded-xl border border-blue-800">
              <div className="flex items-start gap-3">
                <CheckCircle className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
                <div>
                  <div className="text-sm font-medium text-white mb-1">Your responses are anonymous</div>
                  <div className="text-xs text-gray-400">All data is aggregated and cannot be traced back to you.</div>
                </div>
              </div>
            </div>
            <div className="p-4 bg-emerald-900/20 rounded-xl border border-emerald-800">
              <div className="flex items-start gap-3">
                <TrendingUp className="w-5 h-5 text-emerald-400 flex-shrink-0 mt-0.5" />
                <div>
                  <div className="text-sm font-medium text-white mb-1">Your feedback matters</div>
                  <div className="text-xs text-gray-400">Your responses help improve workplace conditions for everyone.</div>
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}


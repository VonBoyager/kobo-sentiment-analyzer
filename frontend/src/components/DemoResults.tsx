import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { Sparkles, MessageSquare, Award, ArrowLeft } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { STATIC_RESULTS_DATA } from '../data/staticDemoData';

interface ResultsData {
  count: number;
  results: Array<{
    id: string;
    submitted_at: string;
    review: string;
    sentiment: string;
  }>;
}

export function DemoResults() {
  const navigate = useNavigate();
  const [data, setData] = useState<ResultsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Use static data for demo
    setData(STATIC_RESULTS_DATA);
    setLoading(false);
  }, []);

  if (loading) {
    return <div className="text-center p-8 text-white">Loading demo results...</div>;
  }

  if (error) {
    return <div className="text-center p-8 text-red-500">Error: {error}</div>;
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Navigation Bar for Demo */}
      <nav className="bg-gray-800 border-b border-gray-700 px-4 py-3">
          <div className="max-w-[1400px] mx-auto flex justify-between items-center">
              <div className="flex items-center gap-2">
                  <span className="text-xl font-bold text-white">Kobo Demo Results</span>
                  <span className="px-2 py-0.5 bg-blue-900/50 text-blue-300 text-xs rounded-full border border-blue-800">Read Only</span>
              </div>
              <div className="flex gap-2">
                <button
                    onClick={() => navigate('/demo')}
                    className="flex items-center gap-2 px-4 py-2 text-sm text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
                >
                    <ArrowLeft className="w-4 h-4" />
                    Back to Dashboard
                </button>
              </div>
          </div>
      </nav>

      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        <div className="mb-6">
          <h1 className="text-3xl text-white mb-2">Analysis Results</h1>
          <p className="text-gray-400">
            Raw responses and sentiment analysis for the demo dataset.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-5">
          {/* Response List */}
          <div className="bg-gray-800 rounded-2xl p-6 sm:p-8 border border-gray-700 hover:shadow-md transition-shadow">
            <div className="flex items-center gap-2 mb-4">
              <MessageSquare className="w-4 h-4 text-blue-400" />
              <h2 className="text-white">Recent Responses ({data?.count || 0})</h2>
            </div>
            
            <div className="space-y-4">
              {data?.results && data.results.length > 0 ? (
                data.results.map((item) => (
                  <div key={item.id} className="p-4 bg-gray-700/30 rounded-xl border border-gray-700">
                    <div className="flex justify-between items-start mb-2">
                      <div className={`px-2 py-1 rounded text-xs font-semibold uppercase ${
                        item.sentiment === 'positive' ? 'bg-emerald-900/40 text-emerald-400 border border-emerald-800' :
                        item.sentiment === 'negative' ? 'bg-red-900/40 text-red-400 border border-red-800' :
                        'bg-yellow-900/40 text-yellow-400 border border-yellow-800'
                      }`}>
                        {item.sentiment}
                      </div>
                      <div className="text-xs text-gray-500">
                        {new Date(item.submitted_at).toLocaleDateString()}
                      </div>
                    </div>
                    <p className="text-gray-300 text-sm italic">"{item.review}"</p>
                  </div>
                ))
              ) : (
                <div className="text-gray-400 text-center py-8">
                  No responses found.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
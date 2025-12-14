import { useNavigate } from 'react-router-dom';
import { ClipboardList, Sparkles, TrendingUp, TrendingDown, LogIn, ArrowLeft } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, LineChart, Line, Tooltip } from 'recharts';
import { useEffect, useState } from 'react';
import { STATIC_DASHBOARD_DATA } from '../data/staticDemoData';

interface SentimentBreakdown {
  positive: number;
  neutral: number;
  negative: number;
}

interface CompanyPerformance {
  section_name: string;
  average_score: number;
}

interface Insight {
  section: string;
  keywords: string[];
}

interface SentimentTrend {
  month: string;
  avg_score: number;
}

interface DashboardData {
  total_responses: number;
  sentiment_breakdown: SentimentBreakdown;
  company_performance: CompanyPerformance[];
  generated_insights: {
    strengths: Insight[];
    weaknesses: Insight[];
  };
  sentiment_trend: SentimentTrend[];
  positive_correlations?: any[];
  negative_correlations?: any[];
}

export function DemoDashboard() {
  const navigate = useNavigate();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Use static data for demo
    setData(STATIC_DASHBOARD_DATA);
    setLoading(false);
  }, []);

  if (loading) {
    return <div className="text-center p-8 text-white">Loading demo...</div>;
  }

  if (error) {
    return (
        <div className="flex flex-col items-center justify-center min-h-screen p-4 text-center">
            <div className="text-red-500 mb-4">Error loading demo: {error}</div>
            <button 
                onClick={() => navigate('/login')}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
                Back to Login
            </button>
        </div>
    );
  }

  if (!data) {
    return <div className="text-center p-8 text-white">No data available</div>;
  }

  const { total_responses, sentiment_breakdown } = data;

  const totalSentiments = (sentiment_breakdown?.positive || 0) + (sentiment_breakdown?.neutral || 0) + (sentiment_breakdown?.negative || 0);

  const sentimentData = [
    { name: 'Positive', value: totalSentiments > 0 ? ((sentiment_breakdown.positive / totalSentiments) * 100) : 0, color: '#10b981' },
    { name: 'Neutral', value: totalSentiments > 0 ? ((sentiment_breakdown.neutral / totalSentiments) * 100) : 0, color: '#f59e0b' },
    { name: 'Negative', value: totalSentiments > 0 ? ((sentiment_breakdown.negative / totalSentiments) * 100) : 0, color: '#ef4444' }
  ];

  const trendData = data.sentiment_trend;

  return (
    <div className="min-h-screen bg-gray-900">
        {/* Navigation Bar for Demo */}
        <nav className="bg-gray-800 border-b border-gray-700 px-4 py-3">
            <div className="max-w-[1400px] mx-auto flex justify-between items-center">
                <div className="flex items-center gap-2">
                    <span className="text-xl font-bold text-white">Kobo Demo</span>
                    <span className="px-2 py-0.5 bg-blue-900/50 text-blue-300 text-xs rounded-full border border-blue-800">Read Only</span>
                </div>
                <button
                    onClick={() => navigate('/login')}
                    className="flex items-center gap-2 px-4 py-2 text-sm text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
                >
                    <ArrowLeft className="w-4 h-4" />
                    Back to Login
                </button>
            </div>
        </nav>

        <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-12 gap-4 lg:gap-5">
            
            {/* Welcome Card */}
            <div className="sm:col-span-2 lg:col-span-8 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-3xl p-8 sm:p-10 text-white relative overflow-hidden border border-gray-800">
            <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl"></div>
            <div className="relative z-10">
                <div className="flex items-center gap-2 mb-3">
                <Sparkles className="w-5 h-5 text-blue-400" />
                <span className="text-sm text-blue-300 uppercase tracking-wider">Demo Dashboard</span>
                </div>
                <h1 className="text-3xl sm:text-4xl mb-3">Welcome to the Live Demo</h1>
                <p className="text-slate-300 text-base sm:text-lg max-w-2xl">
                This shows the sentiment analysis capabilities of Kobo using a sample dataset.
                We've analyzed <span className="text-blue-400 font-semibold">{total_responses} responses</span>.
                </p>
            </div>
            </div>

            {/* Quick Actions - Read Only */}
            <div className="sm:col-span-2 lg:col-span-4 grid grid-cols-1 gap-4">
                <button
                    onClick={() => navigate('/demo/results')}
                    className="group bg-gray-800 hover:bg-gray-700 rounded-2xl p-6 border border-gray-700 hover:border-purple-600 transition-all duration-300 hover:shadow-lg text-left flex items-center justify-between"
                >
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 bg-purple-900/30 group-hover:bg-purple-900/50 rounded-xl flex items-center justify-center transition-colors">
                            <ClipboardList className="w-6 h-6 text-purple-400" />
                        </div>
                        <div>
                            <div className="text-xs text-gray-400 mb-1">View</div>
                            <div className="font-semibold text-white">Full Results</div>
                        </div>
                    </div>
                    <div className="text-purple-400 text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                        View List →
                    </div>
                </button>

                <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700">
                    <h3 className="text-white font-semibold mb-2">Demo Mode Limitations</h3>
                    <ul className="text-sm text-gray-400 space-y-2">
                        <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-yellow-500"></span> Read-only access</li>
                        <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-yellow-500"></span> Upload disabled</li>
                        <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-yellow-500"></span> Model training disabled</li>
                    </ul>
                    <button
                        onClick={() => navigate('/login')}
                        className="mt-4 w-full py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2"
                    >
                        <LogIn className="w-4 h-4" />
                        Login for Full Access
                    </button>
                </div>
            </div>

            {/* Key Metrics */}
            <div className="sm:col-span-1 lg:col-span-3 bg-gray-800 rounded-2xl p-6 border border-gray-700">
            <div className="text-xs uppercase tracking-wider text-gray-400 mb-3">Total Responses</div>
            <div className="text-4xl font-bold text-white mb-2">{total_responses}</div>
            </div>

            <div className="sm:col-span-1 lg:col-span-5 bg-gray-800 rounded-2xl p-6 border border-gray-700">
            <div className="text-xs uppercase tracking-wider text-gray-400 mb-4">Sentiment Breakdown</div>
            <div className="flex items-center gap-6">
                <div className="w-28 h-28 flex-shrink-0">
                <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                    <Pie data={sentimentData} cx="50%" cy="50%" innerRadius={32} outerRadius={48} paddingAngle={3} dataKey="value">
                        {sentimentData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                    </Pie>
                    </PieChart>
                </ResponsiveContainer>
                </div>
                <div className="flex-1 space-y-2.5">
                {sentimentData.map((item) => (
                    <div key={item.name} className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                        <div className="w-3 h-3 rounded-full shadow-sm" style={{ backgroundColor: item.color }} />
                        <span className="text-sm font-medium text-gray-300">{item.name}</span>
                    </div>
                    <span className="text-sm font-semibold text-white">{item.value.toFixed(1)}%</span>
                    </div>
                ))}
                </div>
            </div>
            </div>

            <div className="sm:col-span-2 lg:col-span-4 bg-gray-800 rounded-2xl p-6 border border-gray-700">
            <div className="flex items-center justify-between mb-4">
                <div className="text-xs uppercase tracking-wider text-gray-400">Sentiment Trend</div>
            </div>
            <div style={{ width: '100%', height: '100px' }}>
                <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trendData}>
                    <Line type="monotone" dataKey="avg_score" stroke="#3b82f6" strokeWidth={3} dot={true} strokeLinecap="round" />
                    <Tooltip 
                    contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: '8px', fontSize: '12px', color: '#f3f4f6' }}
                    />
                </LineChart>
                </ResponsiveContainer>
            </div>
            </div>

            {/* Correlations - Using data from public API if available */}
            {data.positive_correlations && data.positive_correlations.length > 0 && (
                <div className="sm:col-span-2 lg:col-span-6 bg-gray-800 rounded-2xl p-6 border border-gray-700">
                    <div className="text-xs uppercase tracking-wider text-gray-400 mb-4">Top Positive Correlations</div>
                    <div className="space-y-3">
                        {data.positive_correlations.map((corr: any, idx: number) => (
                            <div key={idx} className="flex items-center justify-between p-3 bg-gray-700/30 rounded-lg">
                                <div>
                                    <div className="text-sm font-medium text-white">{corr.section_name}</div>
                                    <div className="text-xs text-gray-400">{corr.topic_name}</div>
                                </div>
                                <div className="text-emerald-400 font-bold text-sm">
                                    +{(corr.correlation_score * 100).toFixed(0)}%
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
            
            {data.negative_correlations && data.negative_correlations.length > 0 && (
                <div className="sm:col-span-2 lg:col-span-6 bg-gray-800 rounded-2xl p-6 border border-gray-700">
                    <div className="text-xs uppercase tracking-wider text-gray-400 mb-4">Top Negative Correlations</div>
                    <div className="space-y-3">
                        {data.negative_correlations.map((corr: any, idx: number) => (
                            <div key={idx} className="flex items-center justify-between p-3 bg-gray-700/30 rounded-lg">
                                <div>
                                    <div className="text-sm font-medium text-white">{corr.section_name}</div>
                                    <div className="text-xs text-gray-400">{corr.topic_name}</div>
                                </div>
                                <div className="text-red-400 font-bold text-sm">
                                    {(corr.correlation_score * 100).toFixed(0)}%
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

        </div>
        </div>
    </div>
  );
}
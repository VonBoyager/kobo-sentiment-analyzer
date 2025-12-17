import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { ClipboardList, Upload, Brain, TrendingUp, TrendingDown, Sparkles, Loader2 } from 'lucide-react';
import { PieChart, Pie, Cell, ResponsiveContainer, LineChart, Line, Tooltip, ReferenceDot, Label } from 'recharts';
import { useEffect, useState } from 'react';
import { toast } from 'sonner';

interface SentimentBreakdown {
  positive: number;
  neutral: number;
  negative: number;
}

interface CompanyPerformance {
  section__name: string;
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

interface UserSubmission {
  date: string;
  quarter: string;
  review: string;
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
  user_latest_submission?: UserSubmission;
  confidence_rating?: string;
}

export function Dashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [trainingModels, setTrainingModels] = useState(false);
  const [trainingProgress, setTrainingProgress] = useState<string>('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/api/ml/dashboard-stats/');
        if (!response.ok) {
          throw new Error('Failed to fetch dashboard data');
        }
        const result = await response.json();
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An unknown error occurred');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const [showTrainingModal, setShowTrainingModal] = useState(false);
  const [trainingPercent, setTrainingPercent] = useState(0);

  const handleTestModels = async () => {
    if (trainingModels) return;
    
    setTrainingModels(true);
    setShowTrainingModal(true);
    setTrainingPercent(0);
    setTrainingProgress('Initializing...');
    
    try {
      // 1. Start the training
      const response = await fetch('/api/ml/test-models/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      
      if (!response.ok) {
        throw new Error('Failed to start model training');
      }
      
      // 2. Poll for status
      const pollInterval = setInterval(async () => {
        try {
          const statusRes = await fetch('/api/ml/training-status/');
          const statusData = await statusRes.json();
          
          setTrainingPercent(statusData.progress || 0);
          setTrainingProgress(statusData.message || 'Processing...');
          
          if (statusData.status === 'completed') {
            clearInterval(pollInterval);
            setTrainingPercent(100);
            setTrainingProgress('Complete!');
            
            toast.success('Model Training Completed!', {
              description: 'Dashboard insights have been updated.',
            });
            
            // Wait a moment then reload
            setTimeout(() => {
              window.location.reload();
            }, 1000);
          } else if (statusData.status === 'error') {
            clearInterval(pollInterval);
            throw new Error(statusData.message || 'Training failed');
          }
        } catch (err) {
          // If polling fails, don't crash, just wait
          console.error("Polling error:", err);
        }
      }, 2000); // Poll every 2 seconds
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error occurred';
      toast.error('Model Training Failed', { description: errorMessage });
      setTrainingModels(false);
      setShowTrainingModal(false);
    }
  };

  if (loading) {
    return <div className="text-center p-8 text-white">Loading dashboard...</div>;
  }

  if (error) {
    return <div className="text-center p-8 text-red-500">Error: {error}</div>;
  }

  if (!data) {
    return <div className="text-center p-8 text-white">No data available</div>;
  }

  const { total_responses, sentiment_breakdown, company_performance, generated_insights, sentiment_trend, user_latest_submission, confidence_rating } = data;

  const totalSentiments = (sentiment_breakdown?.positive || 0) + (sentiment_breakdown?.neutral || 0) + (sentiment_breakdown?.negative || 0);

  const sentimentData = [
    { name: 'Positive', value: totalSentiments > 0 ? ((sentiment_breakdown.positive / totalSentiments) * 100) : 0, color: '#10b981' },
    { name: 'Neutral', value: totalSentiments > 0 ? ((sentiment_breakdown.neutral / totalSentiments) * 100) : 0, color: '#f59e0b' },
    { name: 'Negative', value: totalSentiments > 0 ? ((sentiment_breakdown.negative / totalSentiments) * 100) : 0, color: '#ef4444' }
  ];

  const strengths = company_performance?.filter(p => p.average_score >= 4.0) || [];
  const weaknesses = company_performance?.filter(p => p.average_score < 3.0) || [];
  
  // Format trend data with better labels and calculate percentage change
  const trendData = sentiment_trend?.map(d => {
    // Parse quarter label (e.g., "2024-Q1" -> "2024 Q1")
    const quarterLabel = d.month.replace('-', ' ');
    return { 
      month: d.month, 
      label: quarterLabel,
      score: d.avg_score 
    };
  }) || [];
  
  // Calculate percentage change from previous quarter to most recent
  let percentageChange = null;
  let changeLabel = '';
  if (trendData.length >= 2) {
    const currentQuarter = trendData[trendData.length - 1];
    const previousQuarter = trendData[trendData.length - 2];
    const change = currentQuarter.score - previousQuarter.score;
    const percentChange = previousQuarter.score !== 0 
      ? (change / Math.abs(previousQuarter.score)) * 100 
      : 0;
    percentageChange = {
      value: percentChange,
      isPositive: change >= 0,
      current: currentQuarter.score,
      previous: previousQuarter.score,
      currentLabel: currentQuarter.label,
      previousLabel: previousQuarter.label
    };
    changeLabel = `${percentageChange.isPositive ? '+' : ''}${percentChange.toFixed(1)}%`;
  }

  // Find user submission point for the chart
  const userSubmissionPoint = user_latest_submission && trendData.find(d => d.month === user_latest_submission.quarter);

  return (
    <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-12 gap-4 lg:gap-5">
        
        {/* Welcome Card */}
        <div className="sm:col-span-2 lg:col-span-8 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 rounded-3xl p-8 sm:p-10 text-white relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/10 rounded-full blur-3xl"></div>
          <div className="relative z-10">
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="w-5 h-5 text-blue-400" />
              <span className="text-sm text-blue-300 uppercase tracking-wider">Dashboard</span>
            </div>
            <h1 className="text-3xl sm:text-4xl mb-3">Welcome back, {user?.username}!</h1>
            <p className="text-slate-300 text-base sm:text-lg max-w-2xl">
              Your team sentiment analysis is ready. 
              We've analyzed <span className="text-blue-400 font-semibold">{total_responses} responses</span> and identified key areas for focus.
            </p>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="sm:col-span-2 lg:col-span-4 grid grid-cols-3 sm:grid-cols-3 lg:grid-cols-1 gap-4">
          <button
            onClick={() => navigate('/upload')}
            className="group bg-gray-800 hover:bg-gray-700 rounded-2xl p-6 border border-gray-700 hover:border-blue-600 transition-all duration-300 hover:shadow-lg text-left"
          >
            <div className="w-12 h-12 bg-blue-900/30 group-hover:bg-blue-900/50 rounded-xl flex items-center justify-center mb-4 transition-colors">
              <Upload className="w-6 h-6 text-blue-400" />
            </div>
            <div className="text-xs text-gray-400 mb-1">Upload</div>
            <div className="font-semibold text-white">Data</div>
          </button>

          <button
            onClick={() => navigate('/results')}
            className="group bg-gray-800 hover:bg-gray-700 rounded-2xl p-6 border border-gray-700 hover:border-purple-600 transition-all duration-300 hover:shadow-lg text-left"
          >
            <div className="w-12 h-12 bg-purple-900/30 group-hover:bg-purple-900/50 rounded-xl flex items-center justify-center mb-4 transition-colors">
              <ClipboardList className="w-6 h-6 text-purple-400" />
            </div>
            <div className="text-xs text-gray-400 mb-1">View</div>
            <div className="font-semibold text-white">Results</div>
          </button>

          <button
            onClick={handleTestModels}
            disabled={trainingModels}
            className={`group bg-gradient-to-br from-emerald-900/20 to-teal-900/20 rounded-2xl p-6 border border-emerald-800 text-left transition-all ${
              trainingModels 
                ? 'opacity-75 cursor-not-allowed' 
                : 'hover:from-emerald-900/30 hover:to-teal-900/30 hover:border-emerald-700'
            }`}
          >
            <div className="w-12 h-12 bg-gray-800 rounded-xl flex items-center justify-center mb-4 shadow-sm">
              {trainingModels ? (
                <Loader2 className="w-6 h-6 text-emerald-400 animate-spin" />
              ) : (
                <Brain className="w-6 h-6 text-emerald-400" />
              )}
            </div>
            <div className="text-xs text-emerald-300 mb-1">ML Model</div>
            <div className="font-semibold text-white">Test Models</div>
            {trainingModels && (
              <div className="text-xs text-emerald-400 mt-2">
                Starting...
              </div>
            )}
          </button>
        </div>

        {/* Key Metrics */}
        <div className="sm:col-span-1 lg:col-span-3 bg-gray-800 rounded-2xl p-6 border border-gray-700 hover:shadow-md transition-shadow">
          <div className="text-xs uppercase tracking-wider text-gray-400 mb-3">Total Responses</div>
          <div className="text-4xl font-bold text-white mb-2">{total_responses}</div>
          {confidence_rating && (
             <div className="flex items-center gap-2 mt-2">
                <span className={`text-xs px-2 py-1 rounded-full border ${
                  confidence_rating === 'High'
                    ? 'bg-emerald-900/30 text-emerald-400 border-emerald-800'
                    : confidence_rating === 'Medium'
                    ? 'bg-yellow-900/30 text-yellow-400 border-yellow-800'
                    : 'bg-red-900/30 text-red-400 border-red-800'
                }`}>
                  {confidence_rating} Confidence
                </span>
             </div>
          )}
        </div>

        <div className="sm:col-span-1 lg:col-span-5 bg-gray-800 rounded-2xl p-6 border border-gray-700 hover:shadow-md transition-shadow">
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

        <div className="sm:col-span-2 lg:col-span-4 bg-gray-800 rounded-2xl p-6 border border-gray-700 hover:shadow-md transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <div className="text-xs uppercase tracking-wider text-gray-400">Sentiment Trend (by Quarter)</div>
            {percentageChange && (
              <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg ${
                percentageChange.isPositive 
                  ? 'bg-emerald-900/20 text-emerald-300 border border-emerald-800' 
                  : 'bg-red-900/20 text-red-300 border border-red-800'
              }`}>
                {percentageChange.isPositive ? (
                  <TrendingUp className="w-3 h-3" />
                ) : (
                  <TrendingDown className="w-3 h-3" />
                )}
                <span className="text-xs font-semibold">{changeLabel}</span>
                <span className="text-xs opacity-75 ml-1">vs previous</span>
              </div>
            )}
          </div>
          <div style={{ width: '100%', height: '100px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData}>
                <Line type="monotone" dataKey="score" stroke="#3b82f6" strokeWidth={3} dot={true} strokeLinecap="round" />
                <Tooltip 
                  contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: '8px', fontSize: '12px', color: '#f3f4f6' }}
                  labelFormatter={(value, payload) => {
                    // Recharts passes the data point in payload array
                    if (payload && payload.length > 0 && payload[0].payload) {
                      const dataPoint = payload[0].payload;
                      // Format: "2024 Q1" instead of "2024-Q1"
                      const quarterLabel = dataPoint.label || dataPoint.month?.replace('-', ' ') || value;
                      return `Quarter: ${quarterLabel}`;
                    }
                    // Fallback: format the value if it's a string
                    if (typeof value === 'string') {
                      return `Quarter: ${value.replace('-', ' ')}`;
                    }
                    return `Quarter: ${value}`;
                  }}
                  formatter={(value: number) => [`${value.toFixed(2)}`, 'Avg Score']}
                />
                {userSubmissionPoint && (
                  <ReferenceDot
                    x={userSubmissionPoint.month}
                    y={userSubmissionPoint.score}
                    r={6}
                    fill="#3b82f6"
                    stroke="#1f2937"
                    strokeWidth={2}
                    isFront={true}
                  >
                    <Label
                      value="You"
                      position="top"
                      offset={10}
                      fill="#3b82f6"
                      fontSize={12}
                      fontWeight="bold"
                    />
                  </ReferenceDot>
                )}
              </LineChart>
            </ResponsiveContainer>
          </div>
          {user_latest_submission && (
            <div className="mt-2 text-xs text-blue-400 text-center font-medium">
              Your latest submission: {new Date(user_latest_submission.date).toLocaleDateString()} ({user_latest_submission.quarter})
            </div>
          )}
          {percentageChange && (
            <div className="mt-2 text-xs text-gray-500 text-center">
              {percentageChange.previousLabel}: {percentageChange.previous.toFixed(2)} → {percentageChange.currentLabel}: {percentageChange.current.toFixed(2)}
            </div>
          )}
        </div>

        {/* Company Performance - Shows numerical ratings */}
        <div className="sm:col-span-2 lg:col-span-7 bg-gray-800 rounded-2xl p-6 sm:p-7 border border-gray-700 hover:shadow-md transition-shadow">
          <div className="text-xs uppercase tracking-wider text-gray-400 mb-5">Company Performance</div>
          <div className="space-y-5">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <TrendingUp className="w-4 h-4 text-emerald-400" />
                <span className="text-sm font-semibold text-gray-300">Strengths</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {strengths.length > 0 ? strengths.map(s => (
                  <div key={s.section__name} className="px-4 py-2.5 bg-emerald-900/20 text-emerald-300 rounded-xl border border-emerald-800 text-sm font-medium">
                    {s.section__name}: {s.average_score.toFixed(2)}/5.0
                  </div>
                )) : (
                  <div className="text-gray-400 text-sm">No strengths identified yet</div>
                )}
              </div>
            </div>
            <div>
              <div className="flex items-center gap-2 mb-3">
                <TrendingDown className="w-4 h-4 text-red-400" />
                <span className="text-sm font-semibold text-gray-300">Areas for Improvement</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {weaknesses.length > 0 ? weaknesses.map(w => (
                  <div key={w.section__name} className="px-4 py-2.5 bg-red-900/20 text-red-300 rounded-xl border border-red-800 text-sm font-medium">
                    {w.section__name}: {w.average_score.toFixed(2)}/5.0
                  </div>
                )) : (
                  <div className="text-gray-400 text-sm">No areas for improvement identified yet</div>
                )}
              </div>
            </div>
            {/* All sections with numerical ratings */}
            {company_performance && company_performance.length > 0 && (
              <div className="mt-4 pt-4 border-t border-gray-700">
                <div className="text-xs uppercase tracking-wider text-gray-400 mb-3">All Categories</div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {company_performance.map(perf => (
                    <div key={perf.section__name} className="flex items-center justify-between px-3 py-2 bg-gray-700/50 rounded-lg">
                      <span className="text-sm text-gray-300">{perf.section__name}</span>
                      <span className="text-sm font-semibold text-white">{perf.average_score.toFixed(2)}/5.0</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Generated Insights - Changed from "AI Generated Insights" */}
        <div className="sm:col-span-2 lg:col-span-5 bg-gradient-to-br from-blue-900/20 to-indigo-900/20 rounded-2xl p-6 sm:p-7 border border-blue-800">
          <div className="flex items-center gap-2 mb-5">
            <Sparkles className="w-4 h-4 text-blue-400" />
            <div className="text-xs uppercase tracking-wider text-blue-300">Generated Insights</div>
          </div>
          <div className="space-y-2.5 max-h-72 overflow-y-auto pr-2">
            {generated_insights?.strengths && generated_insights.strengths.length > 0 ? (
              generated_insights.strengths.map((insight, index) => (
                <div key={`s-${index}`} className="p-4 bg-gray-800 rounded-xl border border-gray-700 text-sm hover:shadow-sm transition-shadow">
                  <div className="flex gap-3">
                    <span className="text-lg flex-shrink-0">🟢</span>
                    <p className="text-gray-300 leading-relaxed">
                      <strong>{insight.section}:</strong> praised for "{insight.keywords?.join(', ') || 'positive feedback'}".
                    </p>
                  </div>
                </div>
              ))
            ) : (
              <div className="text-gray-400 text-sm p-4">No strength insights available yet. Upload data and train models to generate insights.</div>
            )}
            {generated_insights?.weaknesses && generated_insights.weaknesses.length > 0 ? (
              generated_insights.weaknesses.map((insight, index) => (
                <div key={`w-${index}`} className="p-4 bg-gray-800 rounded-xl border border-gray-700 text-sm hover:shadow-sm transition-shadow">
                  <div className="flex gap-3">
                    <span className="text-lg flex-shrink-0">🔴</span>
                    <p className="text-gray-300 leading-relaxed">
                      <strong>{insight.section}:</strong> needs improvement regarding "{insight.keywords?.join(', ') || 'identified areas'}".
                    </p>
                  </div>
                </div>
              ))
            ) : (
              generated_insights?.strengths && generated_insights.strengths.length === 0 && (
                <div className="text-gray-400 text-sm p-4">No weakness insights available yet. Upload data and train models to generate insights.</div>
              )
            )}
          </div>
        </div>

      </div>

      {/* Training Progress Modal */}
      {showTrainingModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-gray-800 rounded-2xl p-8 max-w-md w-full border border-gray-700 shadow-2xl relative overflow-hidden">
            {/* Background Glow */}
            <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/10 rounded-full blur-2xl"></div>
            
            <div className="relative z-10 flex flex-col items-center text-center">
              <div className="w-16 h-16 bg-blue-900/30 rounded-2xl flex items-center justify-center mb-6">
                <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
              </div>
              
              <h3 className="text-xl font-bold text-white mb-2">Training AI Models</h3>
              <p className="text-gray-400 text-sm mb-8">
                Please wait while we analyze the data and generate insights. This process may take a few minutes.
              </p>
              
              {/* Progress Bar */}
              <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden mb-3">
                <div
                  className="h-full bg-blue-500 transition-all duration-500 ease-out rounded-full relative"
                  style={{ width: `${trainingPercent}%` }}
                >
                  <div className="absolute inset-0 bg-white/20 animate-[shimmer_2s_infinite]"></div>
                </div>
              </div>
              
              <div className="flex justify-between w-full text-xs">
                <span className="text-blue-400 font-medium">{trainingProgress}</span>
                <span className="text-gray-500">{trainingPercent}%</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


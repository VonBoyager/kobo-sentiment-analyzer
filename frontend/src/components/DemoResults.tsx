import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown, Sparkles, MessageSquare, Award, Search, Filter, ZoomIn, ZoomOut, RotateCcw, ArrowLeft } from 'lucide-react';
import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { STATIC_RESULTS_DATA } from '../data/staticDemoData';

interface ResultsData {
  overall_company_score: number;
  section_importance: Array<{
    section: string;
    importance: number;
    sample_size: number;
  }>;
  trending_words: Array<{
    word: string;
    count: number;
    sentiment: string;
    sentiment_ratio: number;
    positive_count: number;
    negative_count: number;
    neutral_count: number;
  }>;
}

export function DemoResults() {
  const navigate = useNavigate();
  const [data, setData] = useState<ResultsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sentimentFilter, setSentimentFilter] = useState<'all' | 'positive' | 'negative' | 'neutral'>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const containerRef = useRef<HTMLDivElement>(null);

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
  
  // Prepare feature importance data (already normalized from API)
  const featureImportance = data?.section_importance.map(item => ({
    feature: item.section,
    importance: item.importance,
  })) || [];

  // Ensure total is exactly 100%
  const totalImportance = featureImportance.reduce((sum, item) => sum + item.importance, 0);
  let normalizedFeatureImportance = featureImportance;
  if (totalImportance > 0 && Math.abs(totalImportance - 1.0) > 0.0001) {
    const normalizationFactor = 1.0 / totalImportance;
    normalizedFeatureImportance = featureImportance.map(item => ({
      ...item,
      importance: item.importance * normalizationFactor,
    }));
  }
  
  // Get trending words with sentiments - filtered
  const allTrendingWords = data?.trending_words || [];
  const filteredWords = allTrendingWords.filter(word => {
    const matchesSentiment = sentimentFilter === 'all' || word.sentiment === sentimentFilter;
    const matchesSearch = searchQuery === '' || word.word.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSentiment && matchesSearch;
  });

  // Handle zoom
  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.2, 2));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.2, 0.5));
  const handleReset = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  // Handle drag/pan
  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // Handle wheel zoom
  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? -0.1 : 0.1;
    setZoom(prev => Math.max(0.5, Math.min(2, prev + delta)));
  };

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
            Deep insights into employee satisfaction across all categories
            </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
            
            {/* Overall Company Score */}
            <div className="lg:col-span-2 bg-gradient-to-br from-blue-900/20 to-indigo-900/20 rounded-2xl p-6 sm:p-8 border border-blue-800 hover:shadow-md transition-shadow">
            <div className="flex items-center gap-3 mb-4">
                <Award className="w-5 h-5 text-blue-400" />
                <div className="text-xs uppercase tracking-wider text-blue-300">Overall Company Score</div>
            </div>
            {data?.overall_company_score !== undefined ? (
                <div className="flex items-baseline gap-4">
                <div className="text-6xl font-bold text-white">
                    {data.overall_company_score.toFixed(2)}
                </div>
                <div className="text-2xl text-gray-400">/ 5.0</div>
                <div className="ml-auto">
                    <div className={`text-lg font-semibold ${
                    data.overall_company_score >= 4.0 ? 'text-emerald-400' :
                    data.overall_company_score >= 3.0 ? 'text-yellow-400' :
                    'text-red-400'
                    }`}>
                    {data.overall_company_score >= 4.0 ? 'Excellent' :
                    data.overall_company_score >= 3.0 ? 'Good' :
                    'Needs Improvement'}
                    </div>
                    <div className="text-sm text-gray-500 mt-1">Based on all section averages</div>
                </div>
                </div>
            ) : (
                <div className="text-gray-400 text-center py-8">
                No company score available.
                </div>
            )}
            </div>

            {/* ML Feature Importance - Normalized to 100% */}
            <div className="bg-gray-800 rounded-2xl p-6 sm:p-8 border border-gray-700 hover:shadow-md transition-shadow">
            <div className="flex items-center gap-2 mb-4">
                <Sparkles className="w-4 h-4 text-blue-400" />
                <h2 className="text-white">ML Feature Importance</h2>
            </div>
            <p className="text-gray-400 mb-6 text-sm">
                Factors that most influence overall employee satisfaction (normalized to 100%)
            </p>
            {normalizedFeatureImportance.length > 0 ? (
                <>
                <div style={{ width: '100%', height: '300px' }}>
                    <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={normalizedFeatureImportance} layout="vertical">
                        <XAxis 
                        type="number" 
                        domain={[0, 1]} 
                        tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
                        tick={{ fill: '#9ca3af', fontSize: 12 }}
                        stroke="#4b5563"
                        />
                        <YAxis 
                        type="category" 
                        dataKey="feature" 
                        width={110} 
                        tick={{ fill: '#d1d5db', fontSize: 12 }}
                        stroke="#4b5563"
                        />
                        <Tooltip 
                        formatter={(value: number) => `${(value * 100).toFixed(1)}%`}
                        contentStyle={{
                            backgroundColor: '#1f2937',
                            border: '1px solid #374151',
                            borderRadius: '8px',
                            color: '#f3f4f6'
                        }}
                        />
                        <Bar dataKey="importance" fill="#3b82f6" radius={[0, 8, 8, 0]} />
                    </BarChart>
                    </ResponsiveContainer>
                </div>
                <div className="mt-4 text-xs text-gray-400 text-center">
                    Total: {normalizedFeatureImportance.reduce((sum, item) => sum + item.importance, 0).toFixed(1)}%
                </div>
                </>
            ) : (
                <div className="text-gray-400 text-center py-12">
                No feature importance data available.
                </div>
            )}
            </div>

            {/* Trending Words with Sentiments - Interactive Circular Blobs Design */}
            <div className="bg-gray-800 rounded-2xl p-6 sm:p-8 border border-gray-700 hover:shadow-md transition-shadow">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-blue-400" />
                <h2 className="text-white">Trending Words</h2>
                </div>
                <div className="flex items-center gap-2">
                <button
                    onClick={handleZoomIn}
                    className="p-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
                    title="Zoom In"
                >
                    <ZoomIn className="w-4 h-4 text-gray-300" />
                </button>
                <button
                    onClick={handleZoomOut}
                    className="p-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
                    title="Zoom Out"
                >
                    <ZoomOut className="w-4 h-4 text-gray-300" />
                </button>
                <button
                    onClick={handleReset}
                    className="p-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
                    title="Reset View"
                >
                    <RotateCcw className="w-4 h-4 text-gray-300" />
                </button>
                </div>
            </div>
            
            {/* Search and Filter Controls */}
            <div className="flex flex-col sm:flex-row gap-3 mb-4">
                <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                    type="text"
                    placeholder="Search words..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 bg-gray-700 border border-gray-600 text-white placeholder-gray-500 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent"
                />
                </div>
                <div className="flex items-center gap-2">
                <Filter className="w-4 h-4 text-gray-400" />
                <select
                    value={sentimentFilter}
                    onChange={(e) => setSentimentFilter(e.target.value as any)}
                    className="px-4 py-2 bg-gray-700 border border-gray-600 text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent"
                >
                    <option value="all">All Sentiments</option>
                    <option value="positive">Positive</option>
                    <option value="negative">Negative</option>
                    <option value="neutral">Neutral</option>
                </select>
                </div>
            </div>

            <p className="text-gray-400 mb-4 text-sm">
                {filteredWords.length} of {allTrendingWords.length} words • Drag to pan • Scroll to zoom
            </p>
            
            {filteredWords.length > 0 ? (
                <>
                <div
                    ref={containerRef}
                    className="relative h-96 bg-gradient-to-br from-gray-700/50 to-gray-700/30 rounded-xl overflow-hidden border border-gray-600 cursor-move"
                    onMouseDown={handleMouseDown}
                    onMouseMove={handleMouseMove}
                    onMouseUp={handleMouseUp}
                    onMouseLeave={handleMouseUp}
                    onWheel={handleWheel}
                    style={{ userSelect: 'none' }}
                >
                    <div
                    className="absolute inset-0 flex flex-wrap items-center justify-center gap-3 p-6"
                    style={{
                        transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
                        transformOrigin: 'center center',
                        transition: isDragging ? 'none' : 'transform 0.1s ease-out',
                    }}
                    >
                    {filteredWords.map((wordData, idx) => {
                        // Calculate size based on count (larger count = larger bubble)
                        const maxCount = Math.max(...filteredWords.map(w => w.count));
                        const minCount = Math.min(...filteredWords.map(w => w.count));
                        const countRange = maxCount - minCount || 1;
                        const normalizedCount = (wordData.count - minCount) / countRange;
                        const size = Math.max(60, Math.min(150, 60 + (normalizedCount * 90)));
                        
                        const sentimentColor =
                        wordData.sentiment === 'positive'
                            ? 'bg-emerald-900/40 text-emerald-300 border-emerald-700 hover:bg-emerald-900/60'
                            : wordData.sentiment === 'negative'
                            ? 'bg-red-900/40 text-red-300 border-red-700 hover:bg-red-900/60'
                            : 'bg-gray-700/40 text-gray-300 border-gray-600 hover:bg-gray-700/60';

                        return (
                        <div
                            key={idx}
                            className={`rounded-full border-2 flex flex-col items-center justify-center transition-all hover:scale-125 cursor-pointer shadow-lg ${sentimentColor}`}
                            style={{
                            width: `${size}px`,
                            height: `${size}px`,
                            fontSize: `${Math.max(10, Math.min(16, size / 8))}px`,
                            pointerEvents: 'auto',
                            }}
                            title={`${wordData.word}: ${wordData.count} mentions\n${wordData.positive_count} positive, ${wordData.negative_count} negative, ${wordData.neutral_count} neutral`}
                            onClick={(e) => {
                            e.stopPropagation();
                            }}
                        >
                            <div className="font-semibold text-center px-2 break-words">{wordData.word}</div>
                            <div className="text-xs opacity-75 mt-1">{wordData.count}</div>
                        </div>
                        );
                    })}
                    </div>
                </div>

                <div className="flex items-center justify-center gap-6 mt-6">
                    <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded-full bg-emerald-900/40 border-2 border-emerald-700" />
                    <span className="text-sm text-gray-300">Positive</span>
                    </div>
                    <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded-full bg-red-900/40 border-2 border-red-700" />
                    <span className="text-sm text-gray-300">Negative</span>
                    </div>
                    <div className="flex items-center gap-2">
                    <div className="w-4 h-4 rounded-full bg-gray-700/40 border-2 border-gray-600" />
                    <span className="text-sm text-gray-300">Neutral</span>
                    </div>
                </div>
                </>
            ) : (
                <div className="text-gray-400 text-center py-12">
                {allTrendingWords.length === 0 
                    ? 'No word data available.'
                    : 'No words match your search or filter criteria.'}
                </div>
            )}
            </div>

        </div>
        </div>
    </div>
  );
}
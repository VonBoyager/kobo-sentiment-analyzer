export const STATIC_DASHBOARD_DATA = {
  total_responses: 1250,
  sentiment_breakdown: {
    positive: 750,
    neutral: 300,
    negative: 200
  },
  company_performance: [
    { section_name: "Management", average_score: 4.2 },
    { section_name: "Work-Life Balance", average_score: 3.8 },
    { section_name: "Compensation", average_score: 3.5 },
    { section_name: "Culture", average_score: 4.5 }
  ],
  generated_insights: {
    strengths: [
      { section: "Culture", keywords: ["collaborative", "friendly", "supportive"] },
      { section: "Management", keywords: ["transparent", "approachable"] }
    ],
    weaknesses: [
      { section: "Compensation", keywords: ["below market", "benefits"] },
      { section: "Workload", keywords: ["high volume", "stress"] }
    ]
  },
  sentiment_trend: [
    { month: '2024-01', avg_score: 3.2 },
    { month: '2024-02', avg_score: 3.4 },
    { month: '2024-03', avg_score: 3.1 },
    { month: '2024-04', avg_score: 3.5 },
  ]
};

export const STATIC_RESULTS_DATA = {
  overall_company_score: 4.15,
  section_importance: [
    { section: "Management", importance: 0.35, sample_size: 1250 },
    { section: "Culture", importance: 0.25, sample_size: 1250 },
    { section: "Compensation", importance: 0.20, sample_size: 1250 },
    { section: "Work-Life Balance", importance: 0.15, sample_size: 1250 },
    { section: "Career Growth", importance: 0.05, sample_size: 1250 }
  ],
  trending_words: [
    { word: "Supportive", count: 120, sentiment: "positive", sentiment_ratio: 0.9, positive_count: 108, negative_count: 2, neutral_count: 10 },
    { word: "Flexible", count: 95, sentiment: "positive", sentiment_ratio: 0.85, positive_count: 80, negative_count: 5, neutral_count: 10 },
    { word: "Salary", count: 85, sentiment: "neutral", sentiment_ratio: 0.4, positive_count: 20, negative_count: 30, neutral_count: 35 },
    { word: "Overtime", count: 70, sentiment: "negative", sentiment_ratio: 0.2, positive_count: 5, negative_count: 55, neutral_count: 10 },
    { word: "Team", count: 150, sentiment: "positive", sentiment_ratio: 0.95, positive_count: 140, negative_count: 2, neutral_count: 8 },
    { word: "Benefits", count: 60, sentiment: "neutral", sentiment_ratio: 0.5, positive_count: 20, negative_count: 20, neutral_count: 20 },
    { word: "Communication", count: 90, sentiment: "negative", sentiment_ratio: 0.3, positive_count: 15, negative_count: 60, neutral_count: 15 },
    { word: "Growth", count: 50, sentiment: "positive", sentiment_ratio: 0.8, positive_count: 35, negative_count: 5, neutral_count: 10 },
    { word: "Tools", count: 40, sentiment: "neutral", sentiment_ratio: 0.6, positive_count: 15, negative_count: 10, neutral_count: 15 },
    { word: "Management", count: 110, sentiment: "positive", sentiment_ratio: 0.75, positive_count: 70, negative_count: 20, neutral_count: 20 }
  ]
};
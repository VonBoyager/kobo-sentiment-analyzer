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
  ],
  positive_correlations: [
    { section_name: "Culture", topic_name: "Team Events", correlation_score: 0.85 },
    { section_name: "Management", topic_name: "Communication", correlation_score: 0.78 }
  ],
  negative_correlations: [
    { section_name: "Work-Life Balance", topic_name: "Overtime", correlation_score: 0.92 },
    { section_name: "Compensation", topic_name: "Salary", correlation_score: 0.88 }
  ]
};

export const STATIC_RESULTS_DATA = {
  count: 5,
  results: [
    {
      id: "1",
      submitted_at: "2024-04-15T10:30:00Z",
      review: "Great work environment and supportive team. I really enjoy coming to work every day.",
      sentiment: "positive",
      confidence: 0.95
    },
    {
      id: "2",
      submitted_at: "2024-04-14T14:20:00Z",
      review: "The workload is manageable, but the benefits package could be better compared to other companies.",
      sentiment: "neutral",
      confidence: 0.78
    },
    {
      id: "3",
      submitted_at: "2024-04-12T09:15:00Z",
      review: "I feel undervalued and the management does not listen to our feedback.",
      sentiment: "negative",
      confidence: 0.92
    },
    {
      id: "4",
      submitted_at: "2024-04-10T16:45:00Z",
      review: "Fantastic company culture! The regular team building events are a blast.",
      sentiment: "positive",
      confidence: 0.98
    },
    {
      id: "5",
      submitted_at: "2024-04-08T11:00:00Z",
      review: "Communication from upper management is often unclear and causes confusion.",
      sentiment: "negative",
      confidence: 0.85
    }
  ]
};
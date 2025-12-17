# Plan: Highlight Latest Submission on Sentiment Trend Chart

## Objective
The user wants to see a dot (marker) on the Sentiment Trend chart in the dashboard that corresponds to their specific questionnaire submission date/quarter. Currently, the chart shows aggregated trends, but individual user context is missing.

## Current Architecture
- **Backend**: `DashboardStatsView` in `sentiment_analyzer/api/views.py` calculates `sentiment_trend` by aggregating all responses by quarter.
- **Frontend**: `Dashboard.tsx` renders a `LineChart` using `recharts` with the aggregated trend data.
- **Data Flow**: `QuestionnaireResponse` -> `DashboardStatsView` -> `Dashboard.tsx`

## Analysis
1.  **Backend (`DashboardStatsView`)**:
    - Currently returns `sentiment_trend` as a list of `{ month: "YYYY-QX", avg_score: number }`.
    - It does *not* explicitly identify which data point (quarter) corresponds to the user's latest submission.
    - We need to find the latest `QuestionnaireResponse` for the current user, determine its quarter ("YYYY-QX"), and pass this information to the frontend.

2.  **Frontend (`Dashboard.tsx`)**:
    - Receives `sentiment_trend` and renders a `LineChart`.
    - The `LineChart` uses `data={trendData}`.
    - We need to overlay a "dot" or specific marker on the data point that matches the user's submission quarter.
    - `recharts` supports custom dots or reference dots. Since the user wants "a dot should appear on the sentiment trend", highlighting the specific data point on the line chart is the most intuitive approach.

## Proposed Changes

### Backend Changes (`sentiment_analyzer/api/views.py`)
1.  In `DashboardStatsView.get`:
    - Fetch the user's latest *completed* `QuestionnaireResponse`.
    - Extract its `submitted_at` date.
    - Calculate the quarter string (e.g., "2024-Q1") for this submission.
    - Add a new field `user_latest_submission` to the response payload:
      ```json
      {
        ...,
        "user_latest_submission": {
          "date": "2024-03-15",
          "quarter": "2024-Q1",
          "score": 0.5 // Optional, if we want to show their specific score vs average
        }
      }
      ```

### Frontend Changes (`frontend/src/components/Dashboard.tsx`)
1.  Update `DashboardData` interface to include `user_latest_submission`.
2.  In the `LineChart` component:
    - We can use a `ReferenceDot` or `ReferenceLine` if we want to point to it.
    - OR, simply customize the `activeDot` or `dot` prop of the `Line` component to highlight the specific point.
    - A `ReferenceDot` is probably best to clearly mark "Your Submission".
    - Logic:
      - Check if `user_latest_submission` exists.
      - Find the data point in `trendData` that matches `user_latest_submission.quarter`.
      - If found, render a `ReferenceDot` at that x-axis value (quarter) and y-axis value (avg_score).
      - Add a label "You" or "Your Submission" to the dot.

## Detailed Steps

### Step 1: Backend Update
- Modify `sentiment_analyzer/api/views.py`:
  - Inside `DashboardStatsView`, after fetching `responses`.
  - Get `latest_user_response = QuestionnaireResponse.objects.filter(user=request.user, is_complete=True).order_by('-submitted_at').first()` (if user is authenticated).
  - If found:
    - `quarter = f"{latest_user_response.submitted_at.year}-Q{(latest_user_response.submitted_at.month-1)//3 + 1}"`
    - Add to response.

### Step 2: Frontend Update
- Modify `frontend/src/components/Dashboard.tsx`:
  - Update interfaces.
  - Inside `Dashboard` component, destructure `user_latest_submission`.
  - In `LineChart`:
    - Add `<ReferenceDot x={userQuarter} y={avgScoreOfThatQuarter} r={6} fill="red" stroke="none" />`
    - Alternatively, since the X-axis is categorical (strings), we need to match the string exactly.

### Step 3: Verification
- Submit a questionnaire.
- Go to Dashboard.
- Verify the dot appears on the correct quarter.

## Todo List
- [ ] Modify `sentiment_analyzer/api/views.py`: `DashboardStatsView` to return `user_latest_submission`.
- [ ] Modify `frontend/src/components/Dashboard.tsx`: Add `ReferenceDot` to `LineChart` for the user's submission quarter.
- [ ] Verify the fix by submitting a new questionnaire and checking the dashboard.
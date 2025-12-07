# Metrics Source Documentation

## Dashboard Page - Generated Insights Cards

### Location: `frontend/src/components/Dashboard.tsx` (lines 263-301)

**Data Source:** `/api/ml/dashboard-stats/` endpoint
- **API View:** `DashboardStatsView` in `api/views.py` (lines 313-464)
- **Expected Data Structure:**
  ```typescript
  {
    generated_insights: {
      strengths: [{ section: string, keywords: string[] }],
      weaknesses: [{ section: string, keywords: string[] }]
    }
  }
  ```

**How It's Generated:**
1. **Primary Source:** Feature Importance Data
   - From `MLPipeline.section_feature_importance` (loaded from database)
   - Positive feature importance → Strengths
   - Negative feature importance → Weaknesses
   - Location: `api/views.py` lines 376-399

2. **Fallback Source:** Section Topic Correlations
   - From `SectionTopicCorrelation` model
   - Positive correlations (correlation_score > 0) → Strengths
   - Negative correlations (correlation_score < 0) → Weaknesses
   - Location: `api/views.py` lines 401-427

**Current Status:** 
- ❌ No data available (models not trained yet)
- ✅ Will populate after clicking "Test Models" button

---

## Results Page - Empty Cards

### 1. Category Scores Card
**Location:** `frontend/src/components/Results.tsx` (lines 123-141)

**Data Source:** `/api/ml/results-data/` endpoint
- **API View:** `ResultsDataView` in `api/views.py` (lines 466-490)
- **Expected Data:** `SectionTopicCorrelation` filtered for:
  - `topic_name` contains 'General Topics' OR 'Overall Rating'
- **Current Status:** ❌ No correlations exist (0 records)

### 2. ML Feature Importance Chart
**Location:** `frontend/src/components/Results.tsx` (lines 143-193)

**Data Source:** `/api/ml/results-data/` endpoint
- **Expected Data:** `SectionTopicCorrelation` filtered for:
  - `topic_name` contains 'Feature Importance'
- **Normalization:** Values are normalized to sum to exactly 100%
- **Current Status:** ❌ No feature importance data (models not trained)

### 3. Trending Topics (Topic Bubbles)
**Location:** `frontend/src/components/Results.tsx` (lines 195-250)

**Data Source:** `/api/ml/results-data/` endpoint
- **Expected Data:** `SectionTopicCorrelation` filtered to exclude:
  - `topic_name` contains 'Feature Importance'
- **Current Status:** ❌ No topic data (models not trained)

---

## How to Populate the Data

### Step 1: Train the Models
Click the **"Test Models"** button in the Dashboard (ML Ready card)
- **Endpoint:** `POST /api/ml/test-models/`
- **API View:** `TestModelsView` in `api/views.py` (lines 492-510)
- **What It Does:**
  1. Calls `MLPipeline().train_all_models()`
  2. Trains correlation analyzer → Creates `SectionTopicCorrelation` records
  3. Trains section feature importance → Saves to database
  4. Generates topic correlations with keywords

### Step 2: Data Generation Flow

**Correlation Training:**
- **Service:** `SectionCorrelationAnalyzer.train_model()` 
- **Location:** `ml_analysis/services.py` (lines 624-707)
- **Saves:** `SectionCorrelationAnalyzer.save_correlations()`
- **Location:** `ml_analysis/services.py` (lines 937-984)
- **Creates:** `SectionTopicCorrelation` records with:
  - `section_name`
  - `topic_name` (includes "Feature Importance" variants)
  - `correlation_score`
  - `negative_correlation` (boolean)
  - `keywords` (dict with word: score)
  - `sample_size`

**Feature Importance Training:**
- **Service:** `MLPipeline.train_section_feature_importance()`
- **Location:** `ml_analysis/services.py` (lines 1200-1417)
- **Saves:** `_save_section_feature_importance_to_db()`
- **Location:** `ml_analysis/services.py` (lines 1150-1198)
- **Creates:** Feature importance data stored in database
- **Used By:** Dashboard Insights (primary source)

---

## Database Models

### SectionTopicCorrelation
**Location:** `ml_analysis/models.py`
- `section_name`: Name of the questionnaire section
- `topic_name`: Name of the topic (includes "Feature Importance" variants)
- `correlation_score`: Correlation value (-1 to 1)
- `negative_correlation`: Boolean flag
- `keywords`: JSON field with word: score pairs
- `sample_size`: Number of samples used

### Current Count: 0 (needs model training)

---

## Summary

**Empty Cards Reason:**
- Models haven't been trained yet
- No `SectionTopicCorrelation` records exist
- No feature importance data exists

**Solution:**
1. Click "Test Models" button in Dashboard
2. Wait for training to complete (may take a few minutes)
3. Refresh the pages
4. Cards will populate with:
   - Generated Insights (strengths/weaknesses)
   - Category Scores
   - ML Feature Importance chart
   - Trending Topics bubbles

**Data Flow:**
```
CSV Upload → QuestionnaireResponse + SectionScore
    ↓
Train Models (Test Models button)
    ↓
SectionCorrelationAnalyzer.train_model()
    ↓
SectionTopicCorrelation records created
    ↓
API endpoints return correlation data
    ↓
Frontend displays in cards/charts
```


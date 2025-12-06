# Kobo Sentiment Analyzer

A comprehensive Django-based sentiment analysis platform with multi-tenancy support, machine learning capabilities, and a modern frontend interface.

## Features

### Core Functionality
- **Sentiment Analysis**: VADER-based sentiment analysis with confidence scoring
- **Topic Modeling**: BERTopic integration for automatic topic discovery
- **Correlation Analysis**: Statistical correlation between topics and questionnaire sections
- **Multi-tenancy**: Isolated data and models per tenant
- **REST API**: Comprehensive API with Django REST Framework
- **Modern Frontend**: Vite-powered frontend with responsive design

### Machine Learning
- **Sentiment Classification**: Naive Bayes and VADER sentiment analysis
- **Topic Discovery**: BERTopic for automatic topic modeling
- **Model Management**: Train, store, and version ML models
- **Performance Tracking**: Accuracy, precision, recall, and F1 score monitoring
- **Feedback Loop**: User feedback integration for model improvement

### Multi-tenancy
- **Tenant Isolation**: Separate databases and file storage per tenant
- **User Management**: Role-based access control within tenants
- **File Management**: Tenant-specific file uploads and processing
- **Model Isolation**: Tenant-specific ML models and training data

## Project Structure

```
Kobo/
├── api/                          # REST API application
│   ├── models.py                 # API-specific models
│   ├── serializers.py           # DRF serializers
│   ├── views.py                 # API views and viewsets
│   └── urls.py                  # API URL routing
├── frontend/                     # Frontend application
│   ├── src/                     # Source files
│   │   ├── main.js             # Main entry point
│   │   ├── app.js              # Application logic
│   │   ├── api/                # API client
│   │   ├── components/         # UI components
│   │   ├── utils/              # Utility functions
│   │   └── styles/             # CSS styles
│   ├── package.json            # Frontend dependencies
│   └── vite.config.js          # Vite configuration
├── sentiment_analyzer/          # Main Django project
│   ├── frontend/               # Frontend Django app
│   ├── ml_analysis/            # ML analysis app
│   ├── tenants/                # Multi-tenancy app
│   └── sentiment_analyzer/     # Project settings
├── requirements.txt            # Python dependencies
├── env.example                 # Environment variables template
└── README.md                   # This file
```

## Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL 12+
- Redis (optional, for caching)

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Kobo
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Set up database**
   ```bash
   python sentiment_analyzer/manage.py migrate
   python sentiment_analyzer/manage.py createsuperuser
   ```

6. **Load sample data (optional)**
   ```bash
   python sentiment_analyzer/manage.py loaddata sample_data.json
   ```

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```

## Usage

### Development

1. **Start Django development server**
   ```bash
   cd sentiment_analyzer
   python manage.py runserver
   ```

2. **Start frontend development server** (in another terminal)
   ```bash
   cd frontend
   npm run dev
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Django Admin: http://localhost:8000/admin/
   - API: http://localhost:8000/api/

### Production

1. **Build frontend**
   ```bash
   cd frontend
   npm run build
   ```

2. **Collect static files**
   ```bash
   cd sentiment_analyzer
   python manage.py collectstatic
   ```

3. **Run with Gunicorn**
   ```bash
   gunicorn sentiment_analyzer.wsgi:application
   ```

## API Documentation

### Authentication
- **Token-based**: Use API tokens for authentication
- **Session-based**: Use Django sessions for web interface

### Endpoints

#### Questionnaire
- `GET /api/questionnaire-responses/` - List responses
- `GET /api/questionnaire-responses/{id}/` - Get specific response
- `GET /api/questionnaire-responses/{id}/complete_analysis/` - Get complete analysis

#### Analysis
- `GET /api/sentiment-analysis/` - List sentiment analyses
- `GET /api/topic-analysis/` - List topic analyses
- `GET /api/correlations/` - List correlations

#### ML Models
- `GET /api/ml-models/` - List ML models
- `GET /api/training-data/` - List training data
- `POST /api/feedback/` - Submit feedback

#### Tenants
- `GET /api/tenants/` - List accessible tenants
- `GET /api/tenant-files/` - List tenant files
- `GET /api/tenant-models/` - List tenant models

#### Statistics
- `GET /api/stats/` - API statistics
- `GET /api/ml-stats/` - ML analysis statistics

### Example API Usage

```javascript
// Using the API client
import { api } from './api/client.js'

// Get questionnaire responses
const responses = await api.questionnaire.getResponses()

// Get complete analysis for a response
const analysis = await api.questionnaire.getCompleteAnalysis(responseId)

// Submit feedback
await api.ml.submitFeedback({
  response: responseId,
  feedback_type: 'helpful',
  sentiment_accuracy: true
})
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key | Required |
| `DEBUG` | Debug mode | `True` |
| `DB_NAME` | Database name | `sentiment_analyzer` |
| `DB_USER` | Database user | `postgres` |
| `DB_PASSWORD` | Database password | Required |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `5432` |
| `REDIS_URL` | Redis URL | `redis://localhost:6379/0` |

### Django Settings

Key settings can be found in `sentiment_analyzer/sentiment_analyzer/settings.py`:

- **Database**: PostgreSQL configuration
- **Media Files**: File upload settings
- **Static Files**: Frontend asset serving
- **API**: REST Framework configuration
- **Security**: CSRF, CORS, and authentication settings

## Machine Learning

### Models

1. **Sentiment Analysis**
   - VADER sentiment analyzer
   - Naive Bayes classifier
   - Custom trained models

2. **Topic Modeling**
   - BERTopic for topic discovery
   - UMAP for dimensionality reduction
   - HDBSCAN for clustering

3. **Correlation Analysis**
   - Statistical correlation between topics and questionnaire sections
   - Pearson correlation coefficients
   - Significance testing

### Training

```bash
# Train models
python sentiment_analyzer/manage.py train_models

# Load training data
python sentiment_analyzer/manage.py load_dataset --file data.csv
```

## Multi-tenancy

### Tenant Management

1. **Create Tenant**
   ```python
   from tenants.models import Tenant
   tenant = Tenant.objects.create(
       name="Company ABC",
       owner=user,
       description="Sentiment analysis for Company ABC"
   )
   ```

2. **Add Users to Tenant**
   ```python
   from tenants.models import TenantUser
   TenantUser.objects.create(
       tenant=tenant,
       user=user,
       role='admin'
   )
   ```

### Tenant Isolation

- **Database**: Each tenant can have separate database
- **Files**: Tenant-specific file storage
- **Models**: Isolated ML models per tenant
- **Data**: Complete data isolation

## Frontend Development

### Technologies

- **Vite**: Build tool and development server
- **Vanilla JavaScript**: No framework dependencies
- **CSS3**: Modern styling with CSS variables
- **Axios**: HTTP client for API communication

### Development Commands

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint

# Format code
npm run format
```

### Component Structure

- **Components**: Reusable UI components
- **Utils**: Utility functions and helpers
- **API**: API client and endpoints
- **Styles**: CSS and styling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the documentation

## Changelog

### Version 1.0.0
- Initial release
- Sentiment analysis functionality
- Topic modeling with BERTopic
- Multi-tenancy support
- REST API
- Modern frontend interface
- ML model management
- User feedback system

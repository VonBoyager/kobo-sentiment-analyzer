// API client configuration and utilities
import axios from 'axios'

// Create axios instance with default configuration
const apiClient = axios.create({
  baseURL: '/api',
  timeout: 60000, // Increased to 60s for large uploads/ML processing
  headers: {
    'Content-Type': 'application/json',
  }
})

// Helper to get cookie value
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

// Request interceptor for authentication
apiClient.interceptors.request.use(
  (config) => {
    // Add CSRF token if available
    let csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value
    if (!csrfToken) {
      csrfToken = getCookie('csrftoken');
    }
    
    if (csrfToken) {
      config.headers['X-CSRFToken'] = csrfToken
    }
    
    // Add API token if available
    const apiToken = localStorage.getItem('api_token')
    if (apiToken) {
      config.headers['Authorization'] = `Token ${apiToken}`
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      console.warn('Unauthorized access - redirecting to login')
      window.location.href = '/login/'
    } else if (error.response?.status === 403) {
      // Handle forbidden access
      console.error('Forbidden access')
      showNotification('Access denied', 'error')
    } else if (error.response?.status >= 500) {
      // Handle server errors
      console.error('Server error:', error.response.data)
      showNotification('Server error occurred', 'error')
    }
    
    return Promise.reject(error)
  }
)

// API endpoints
export const apiEndpoints = {
  // Authentication
  login: '/auth/login/',
  logout: '/auth/logout/',
  register: '/auth/register/',
  
  // Questionnaire
  questionnaireResponses: '/questionnaire-responses/',
  questionnaireSections: '/questionnaire-sections/',
  questionnaireQuestions: '/questionnaire-questions/',
  
  // Analysis
  sentimentAnalysis: '/sentiment-analysis/',
  topicAnalysis: '/topic-analysis/',
  correlations: '/correlations/',
  
  // ML Models
  mlModels: '/ml-models/',
  trainingData: '/training-data/',
  
  // Feedback
  feedback: '/feedback/',
  
  // Tenants
  tenants: '/tenants/',
  tenantFiles: '/tenant-files/',
  tenantModels: '/tenant-models/',
  
  // Statistics
  apiStats: '/stats/',
  mlStats: '/ml-stats/',
  
  // Utility
  health: '/health/',
  version: '/version/'
}

// API methods
export const api = {
  // Generic CRUD operations
  get: (endpoint, config = {}) => apiClient.get(endpoint, config),
  post: (endpoint, data = {}, config = {}) => apiClient.post(endpoint, data, config),
  put: (endpoint, data = {}, config = {}) => apiClient.put(endpoint, data, config),
  patch: (endpoint, data = {}, config = {}) => apiClient.patch(endpoint, data, config),
  delete: (endpoint, config = {}) => apiClient.delete(endpoint, config),
  
  // Specific API calls
  auth: {
    login: (credentials) => apiClient.post(apiEndpoints.login, credentials),
    logout: () => apiClient.post(apiEndpoints.logout),
    register: (userData) => apiClient.post(apiEndpoints.register, userData),
  },
  
  questionnaire: {
    getResponses: (params = {}) => apiClient.get(apiEndpoints.questionnaireResponses, { params }),
    getResponse: (id) => apiClient.get(`${apiEndpoints.questionnaireResponses}${id}/`),
    getCompleteAnalysis: (id) => apiClient.get(`${apiEndpoints.questionnaireResponses}${id}/complete_analysis/`),
    createResponse: (data) => apiClient.post(apiEndpoints.questionnaireResponses, data),
  },
  
  analysis: {
    getSentimentAnalysis: (params = {}) => apiClient.get(apiEndpoints.sentimentAnalysis, { params }),
    getTopicAnalysis: (params = {}) => apiClient.get(apiEndpoints.topicAnalysis, { params }),
    getCorrelations: (params = {}) => apiClient.get(apiEndpoints.correlations, { params }),
  },
  
  ml: {
    getModels: (params = {}) => apiClient.get(apiEndpoints.mlModels, { params }),
    getTrainingData: (params = {}) => apiClient.get(apiEndpoints.trainingData, { params }),
    submitFeedback: (data) => apiClient.post(apiEndpoints.feedback, data),
  },
  
  tenants: {
    getTenants: (params = {}) => apiClient.get(apiEndpoints.tenants, { params }),
    getTenantFiles: (params = {}) => apiClient.get(apiEndpoints.tenantFiles, { params }),
    getTenantModels: (params = {}) => apiClient.get(apiEndpoints.tenantModels, { params }),
  },
  
  stats: {
    getAPIStats: () => apiClient.get(apiEndpoints.apiStats),
    getMLStats: () => apiClient.get(apiEndpoints.mlStats),
  },
  
  utility: {
    healthCheck: () => apiClient.get(apiEndpoints.health),
    getVersion: () => apiClient.get(apiEndpoints.version),
  }
}

// Setup function
export function setupAPI() {
  console.log('Setting up API client...')
  
  // Test API connection
  api.utility.healthCheck()
    .then(response => {
      console.log('API health check passed:', response.data)
    })
    .catch(error => {
      console.warn('API health check failed:', error.message)
    })
}

// Utility function for notifications
function showNotification(message, type = 'info') {
  // Simple notification system - can be enhanced with a proper notification library
  const notification = document.createElement('div')
  notification.className = `notification notification-${type}`
  notification.textContent = message
  
  // Add to page
  document.body.appendChild(notification)
  
  // Remove after 5 seconds
  setTimeout(() => {
    if (notification.parentNode) {
      notification.parentNode.removeChild(notification)
    }
  }, 5000)
}

export default apiClient

// Main application logic
import { setupEventListeners } from './utils/eventListeners'
import { initializeComponents } from './components/componentManager'
import { setupNavigation } from './utils/navigation'
import { setupFormHandlers } from './utils/formHandlers'

export function initApp() {
  console.log('Initializing Kobo Sentiment Analyzer Frontend...')
  
  try {
    // Setup navigation
    setupNavigation()
    
    // Initialize components
    initializeComponents()
    
    // Setup event listeners
    setupEventListeners()
    
    // Setup form handlers
    setupFormHandlers()
    
    console.log('Frontend application initialized successfully')
  } catch (error) {
    console.error('Error initializing frontend application:', error)
  }
}

// Global error handler
window.addEventListener('error', (event) => {
  console.error('Global error:', event.error)
})

// Handle unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection:', event.reason)
})

// Main entry point for the frontend application
import './styles/main.css'
import { initApp } from './app'
import { setupAPI } from './api/client'

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
  // Setup API client
  setupAPI()
  
  // Initialize the main app
  initApp()
})

// Export for use in other modules
export { initApp, setupAPI }

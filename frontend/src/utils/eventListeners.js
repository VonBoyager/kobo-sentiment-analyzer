// Event listeners setup
export function setupEventListeners() {
  console.log('Setting up event listeners...')
  
  // Form submission handlers
  setupFormSubmissionListeners()
  
  // Navigation handlers
  setupNavigationListeners()
  
  // Modal handlers
  setupModalListeners()
  
  // Chart handlers
  setupChartListeners()
  
  console.log('Event listeners setup complete')
}

function setupFormSubmissionListeners() {
  // Handle all form submissions
  document.addEventListener('submit', (event) => {
    const form = event.target
    if (form.tagName === 'FORM') {
      handleFormSubmission(form, event)
    }
  })
  
  // Handle file uploads
  document.addEventListener('change', (event) => {
    if (event.target.type === 'file') {
      handleFileUpload(event.target)
    }
  })
}

function setupNavigationListeners() {
  // Handle navigation clicks
  document.addEventListener('click', (event) => {
    const link = event.target.closest('a[data-navigation]')
    if (link) {
      event.preventDefault()
      handleNavigation(link)
    }
  })
  
  // Handle back button
  window.addEventListener('popstate', (event) => {
    handlePopState(event)
  })
}

function setupModalListeners() {
  // Handle modal triggers
  document.addEventListener('click', (event) => {
    const modalTrigger = event.target.closest('[data-modal]')
    if (modalTrigger) {
      event.preventDefault()
      openModal(modalTrigger.dataset.modal)
    }
    
    // Handle modal close
    const modalClose = event.target.closest('[data-modal-close]')
    if (modalClose) {
      event.preventDefault()
      closeModal(modalClose.dataset.modalClose)
    }
  })
  
  // Close modal on escape key
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      closeAllModals()
    }
  })
}

function setupChartListeners() {
  // Handle chart interactions
  document.addEventListener('click', (event) => {
    const chartElement = event.target.closest('[data-chart]')
    if (chartElement) {
      handleChartInteraction(chartElement, event)
    }
  })
}

// Form handling functions
function handleFormSubmission(form, event) {
  const formData = new FormData(form)
  const action = form.action || window.location.href
  const method = form.method || 'POST'
  
  // Show loading state
  showFormLoading(form, true)
  
  // Submit form data
  fetch(action, {
    method: method,
    body: formData,
    headers: {
      'X-CSRFToken': getCSRFToken()
    }
  })
  .then(response => {
    if (response.ok) {
      return response.json()
    }
    throw new Error('Form submission failed')
  })
  .then(data => {
    showFormLoading(form, false)
    handleFormSuccess(form, data)
  })
  .catch(error => {
    showFormLoading(form, false)
    handleFormError(form, error)
  })
}

function handleFileUpload(input) {
  const files = Array.from(input.files)
  const maxSize = 5 * 1024 * 1024 // 5MB
  
  files.forEach(file => {
    if (file.size > maxSize) {
      showNotification(`File ${file.name} is too large. Maximum size is 5MB.`, 'error')
      input.value = ''
      return
    }
  })
  
  // Show file preview if supported
  if (files.length > 0 && files[0].type.startsWith('image/')) {
    showImagePreview(files[0])
  }
}

// Navigation functions
function handleNavigation(link) {
  const target = link.dataset.navigation
  const url = link.href
  
  // Update URL without page reload
  history.pushState({}, '', url)
  
  // Load content
  loadPageContent(target, url)
}

function handlePopState(event) {
  const url = window.location.href
  loadPageContent(null, url)
}

// Modal functions
function openModal(modalId) {
  const modal = document.getElementById(modalId)
  if (modal) {
    modal.classList.add('active')
    document.body.classList.add('modal-open')
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId)
  if (modal) {
    modal.classList.remove('active')
    document.body.classList.remove('modal-open')
  }
}

function closeAllModals() {
  const modals = document.querySelectorAll('.modal.active')
  modals.forEach(modal => {
    modal.classList.remove('active')
  })
  document.body.classList.remove('modal-open')
}

// Chart functions
function handleChartInteraction(element, event) {
  const chartType = element.dataset.chart
  const chartData = element.dataset.chartData
  
  if (chartData) {
    try {
      const data = JSON.parse(chartData)
      // Handle chart interaction based on type
      console.log('Chart interaction:', chartType, data)
    } catch (error) {
      console.error('Error parsing chart data:', error)
    }
  }
}

// Utility functions
function getCSRFToken() {
  const token = document.querySelector('[name=csrfmiddlewaretoken]')
  return token ? token.value : ''
}

function showFormLoading(form, isLoading) {
  const submitButton = form.querySelector('button[type="submit"]')
  if (submitButton) {
    if (isLoading) {
      submitButton.disabled = true
      submitButton.innerHTML = '<span class="spinner"></span> Processing...'
    } else {
      submitButton.disabled = false
      submitButton.innerHTML = submitButton.dataset.originalText || 'Submit'
    }
  }
}

function handleFormSuccess(form, data) {
  showNotification('Form submitted successfully!', 'success')
  
  // Reset form if needed
  if (form.dataset.resetOnSuccess !== 'false') {
    form.reset()
  }
  
  // Redirect if specified
  if (data.redirect) {
    window.location.href = data.redirect
  }
}

function handleFormError(form, error) {
  showNotification('Error submitting form: ' + error.message, 'error')
  console.error('Form submission error:', error)
}

function loadPageContent(target, url) {
  // Show loading indicator
  showPageLoading(true)
  
  fetch(url, {
    headers: {
      'X-Requested-With': 'XMLHttpRequest'
    }
  })
  .then(response => response.text())
  .then(html => {
    // Update page content
    if (target) {
      const targetElement = document.getElementById(target)
      if (targetElement) {
        targetElement.innerHTML = html
      }
    } else {
      // Full page reload
      document.documentElement.innerHTML = html
    }
    showPageLoading(false)
  })
  .catch(error => {
    console.error('Error loading page content:', error)
    showPageLoading(false)
    showNotification('Error loading page content', 'error')
  })
}

function showPageLoading(isLoading) {
  const loader = document.getElementById('page-loader')
  if (loader) {
    loader.style.display = isLoading ? 'block' : 'none'
  }
}

function showImagePreview(file) {
  const reader = new FileReader()
  reader.onload = (e) => {
    const preview = document.getElementById('image-preview')
    if (preview) {
      preview.src = e.target.result
      preview.style.display = 'block'
    }
  }
  reader.readAsDataURL(file)
}

function showNotification(message, type = 'info') {
  // Create notification element
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

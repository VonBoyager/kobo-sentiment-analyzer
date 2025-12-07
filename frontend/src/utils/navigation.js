// Navigation utilities
export function setupNavigation() {
  console.log('Setting up navigation...')
  
  // Initialize navigation state
  initializeNavigationState()
  
  // Setup navigation event listeners
  setupNavigationEventListeners()
  
  // Setup breadcrumb navigation
  setupBreadcrumbNavigation()
  
  console.log('Navigation setup complete')
}

function initializeNavigationState() {
  // Set initial active navigation item
  const currentPath = window.location.pathname
  setActiveNavigationItem(currentPath)
  
  // Initialize navigation history
  if (!window.navigationHistory) {
    window.navigationHistory = [currentPath]
  }
}

function setupNavigationEventListeners() {
  // Handle navigation clicks
  document.addEventListener('click', (event) => {
    const navLink = event.target.closest('a[data-nav]')
    if (navLink) {
      event.preventDefault()
      handleNavigationClick(navLink)
    }
  })
  
  // Handle browser back/forward buttons
  window.addEventListener('popstate', (event) => {
    handlePopState(event)
  })
  
  // Handle keyboard navigation
  document.addEventListener('keydown', (event) => {
    handleKeyboardNavigation(event)
  })
}

function setupBreadcrumbNavigation() {
  // Generate breadcrumbs based on current path
  const breadcrumbs = generateBreadcrumbs(window.location.pathname)
  updateBreadcrumbDisplay(breadcrumbs)
}

// Navigation handling functions
function handleNavigationClick(link) {
  const href = link.getAttribute('href')
  const target = link.dataset.target || '_self'
  const method = link.dataset.method || 'GET'
  
  // Add to navigation history
  addToNavigationHistory(href)
  
  // Update active navigation item
  setActiveNavigationItem(href)
  
  // Handle different navigation methods
  switch (method) {
    case 'ajax':
      navigateAjax(href, link)
      break
    case 'replace':
      navigateReplace(href)
      break
    case 'new':
      window.open(href, target)
      break
    default:
      navigateDefault(href)
  }
}

function handlePopState(event) {
  const href = window.location.pathname
  
  // Update active navigation item
  setActiveNavigationItem(href)
  
  // Update breadcrumbs
  const breadcrumbs = generateBreadcrumbs(href)
  updateBreadcrumbDisplay(breadcrumbs)
  
  // Load content if needed
  loadPageContent(href)
}

function handleKeyboardNavigation(event) {
  // Handle keyboard shortcuts for navigation
  if (event.ctrlKey || event.metaKey) {
    switch (event.key) {
      case 'h':
        event.preventDefault()
        navigateToHome()
        break
      case 'd':
        event.preventDefault()
        navigateToDashboard()
        break
      case 'a':
        event.preventDefault()
        navigateToAnalysis()
        break
      case 's':
        event.preventDefault()
        navigateToSettings()
        break
    }
  }
  
  // Handle arrow key navigation in menus
  if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    handleArrowKeyNavigation(event)
  }
}

// Navigation methods
function navigateAjax(href, link) {
  // Show loading indicator
  showNavigationLoading(true)
  
  // Update URL without page reload
  history.pushState({}, '', href)
  
  // Load content via AJAX
  fetch(href, {
    headers: {
      'X-Requested-With': 'XMLHttpRequest'
    }
  })
  .then(response => response.text())
  .then(html => {
    // Update main content area
    const mainContent = document.getElementById('main-content')
    if (mainContent) {
      mainContent.innerHTML = html
    }
    
    // Update page title
    updatePageTitle(html)
    
    // Update breadcrumbs
    const breadcrumbs = generateBreadcrumbs(href)
    updateBreadcrumbDisplay(breadcrumbs)
    
    showNavigationLoading(false)
  })
  .catch(error => {
    console.error('Navigation error:', error)
    showNavigationLoading(false)
    showNotification('Error loading page', 'error')
  })
}

function navigateReplace(href) {
  window.location.replace(href)
}

function navigateDefault(href) {
  window.location.href = href
}

// Navigation utility functions
function setActiveNavigationItem(path) {
  // Remove active class from all navigation items
  const navItems = document.querySelectorAll('.nav-item, .nav-link')
  navItems.forEach(item => {
    item.classList.remove('active')
  })
  
  // Add active class to current item
  const currentItem = document.querySelector(`a[href="${path}"]`)
  if (currentItem) {
    currentItem.classList.add('active')
    
    // Also activate parent items
    const parentItem = currentItem.closest('.nav-item')
    if (parentItem) {
      parentItem.classList.add('active')
    }
  }
}

function addToNavigationHistory(href) {
  if (!window.navigationHistory) {
    window.navigationHistory = []
  }
  
  // Add to history if not already the current page
  if (window.navigationHistory[window.navigationHistory.length - 1] !== href) {
    window.navigationHistory.push(href)
    
    // Limit history size
    if (window.navigationHistory.length > 50) {
      window.navigationHistory.shift()
    }
  }
}

function generateBreadcrumbs(path) {
  const segments = path.split('/').filter(segment => segment !== '')
  const breadcrumbs = [
    { name: 'Home', href: '/', active: false }
  ]
  
  let currentPath = ''
  segments.forEach((segment, index) => {
    currentPath += '/' + segment
    const isLast = index === segments.length - 1
    
    breadcrumbs.push({
      name: formatBreadcrumbName(segment),
      href: currentPath,
      active: isLast
    })
  })
  
  return breadcrumbs
}

function formatBreadcrumbName(segment) {
  // Convert URL segment to readable name
  return segment
    .split('-')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

function updateBreadcrumbDisplay(breadcrumbs) {
  const breadcrumbContainer = document.getElementById('breadcrumb-container')
  if (!breadcrumbContainer) return
  
  const breadcrumbHTML = breadcrumbs.map((crumb, index) => {
    const separator = index > 0 ? '<span class="breadcrumb-separator">/</span>' : ''
    const linkClass = crumb.active ? 'breadcrumb-item active' : 'breadcrumb-item'
    
    return `${separator}<span class="${linkClass}">
      ${crumb.active ? crumb.name : `<a href="${crumb.href}">${crumb.name}</a>`}
    </span>`
  }).join('')
  
  breadcrumbContainer.innerHTML = breadcrumbHTML
}

function updatePageTitle(html) {
  // Extract title from HTML
  const titleMatch = html.match(/<title>(.*?)<\/title>/i)
  if (titleMatch) {
    document.title = titleMatch[1]
  }
}

function loadPageContent(href) {
  // This function can be overridden by specific pages
  // to handle custom content loading
  console.log('Loading content for:', href)
}

// Keyboard navigation shortcuts
function navigateToHome() {
  const homeLink = document.querySelector('a[href="/"]')
  if (homeLink) {
    homeLink.click()
  }
}

function navigateToDashboard() {
  const dashboardLink = document.querySelector('a[href="/dashboard/"]')
  if (dashboardLink) {
    dashboardLink.click()
  }
}

function navigateToAnalysis() {
  const analysisLink = document.querySelector('a[href="/sentiment-analysis/"]')
  if (analysisLink) {
    analysisLink.click()
  }
}

function navigateToSettings() {
  const settingsLink = document.querySelector('a[href="/accounts-settings/"]')
  if (settingsLink) {
    settingsLink.click()
  }
}

function handleArrowKeyNavigation(event) {
  const menu = event.target.closest('.nav-menu, .dropdown-menu')
  if (!menu) return
  
  const menuItems = Array.from(menu.querySelectorAll('a, button'))
  const currentIndex = menuItems.indexOf(event.target)
  
  if (currentIndex === -1) return
  
  let nextIndex
  if (event.key === 'ArrowDown') {
    nextIndex = (currentIndex + 1) % menuItems.length
  } else if (event.key === 'ArrowUp') {
    nextIndex = currentIndex === 0 ? menuItems.length - 1 : currentIndex - 1
  }
  
  if (nextIndex !== undefined) {
    event.preventDefault()
    menuItems[nextIndex].focus()
  }
}

function showNavigationLoading(isLoading) {
  const loader = document.getElementById('navigation-loader')
  if (loader) {
    loader.style.display = isLoading ? 'block' : 'none'
  }
}

function showNotification(message, type = 'info') {
  // Simple notification system
  const notification = document.createElement('div')
  notification.className = `notification notification-${type}`
  notification.textContent = message
  
  document.body.appendChild(notification)
  
  setTimeout(() => {
    if (notification.parentNode) {
      notification.parentNode.removeChild(notification)
    }
  }, 5000)
}

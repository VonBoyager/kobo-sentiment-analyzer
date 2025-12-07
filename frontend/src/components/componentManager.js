// Component manager for initializing and managing frontend components
export function initializeComponents() {
  console.log('Initializing components...')
  
  // Initialize all components
  initializeCharts()
  initializeModals()
  initializeDropdowns()
  initializeTabs()
  initializeAccordions()
  initializeTooltips()
  initializeProgressBars()
  initializeDataTables()
  initializeFilters()
  
  console.log('Components initialized successfully')
}

// Chart components
function initializeCharts() {
  const chartElements = document.querySelectorAll('[data-chart]')
  
  chartElements.forEach(element => {
    const chartType = element.dataset.chart
    const chartData = element.dataset.chartData
    
    if (chartData) {
      try {
        const data = JSON.parse(chartData)
        createChart(element, chartType, data)
      } catch (error) {
        console.error('Error parsing chart data:', error)
      }
    }
  })
}

function createChart(element, type, data) {
  // Simple chart implementation - can be enhanced with Chart.js or D3.js
  const canvas = document.createElement('canvas')
  element.appendChild(canvas)
  
  const ctx = canvas.getContext('2d')
  const width = element.offsetWidth
  const height = element.offsetHeight
  
  canvas.width = width
  canvas.height = height
  
  switch (type) {
    case 'bar':
      drawBarChart(ctx, data, width, height)
      break
    case 'line':
      drawLineChart(ctx, data, width, height)
      break
    case 'pie':
      drawPieChart(ctx, data, width, height)
      break
    case 'doughnut':
      drawDoughnutChart(ctx, data, width, height)
      break
    default:
      console.warn('Unknown chart type:', type)
  }
}

function drawBarChart(ctx, data, width, height) {
  const { labels, datasets } = data
  const maxValue = Math.max(...datasets[0].data)
  const barWidth = width / labels.length * 0.8
  const barSpacing = width / labels.length * 0.2
  
  ctx.fillStyle = '#2563eb'
  
  labels.forEach((label, index) => {
    const barHeight = (datasets[0].data[index] / maxValue) * height * 0.8
    const x = index * (barWidth + barSpacing) + barSpacing / 2
    const y = height - barHeight - 20
    
    ctx.fillRect(x, y, barWidth, barHeight)
    
    // Draw label
    ctx.fillStyle = '#64748b'
    ctx.font = '12px Arial'
    ctx.textAlign = 'center'
    ctx.fillText(label, x + barWidth / 2, height - 5)
  })
}

function drawLineChart(ctx, data, width, height) {
  const { labels, datasets } = data
  const maxValue = Math.max(...datasets[0].data)
  const minValue = Math.min(...datasets[0].data)
  const valueRange = maxValue - minValue
  
  ctx.strokeStyle = '#2563eb'
  ctx.lineWidth = 2
  ctx.beginPath()
  
  labels.forEach((label, index) => {
    const x = (index / (labels.length - 1)) * width
    const y = height - ((datasets[0].data[index] - minValue) / valueRange) * height * 0.8 - 20
    
    if (index === 0) {
      ctx.moveTo(x, y)
    } else {
      ctx.lineTo(x, y)
    }
  })
  
  ctx.stroke()
}

function drawPieChart(ctx, data, width, height) {
  const { labels, datasets } = data
  const total = datasets[0].data.reduce((sum, value) => sum + value, 0)
  const centerX = width / 2
  const centerY = height / 2
  const radius = Math.min(width, height) / 2 - 20
  
  let currentAngle = 0
  const colors = ['#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
  
  labels.forEach((label, index) => {
    const value = datasets[0].data[index]
    const sliceAngle = (value / total) * 2 * Math.PI
    
    ctx.fillStyle = colors[index % colors.length]
    ctx.beginPath()
    ctx.moveTo(centerX, centerY)
    ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle)
    ctx.closePath()
    ctx.fill()
    
    currentAngle += sliceAngle
  })
}

function drawDoughnutChart(ctx, data, width, height) {
  // Similar to pie chart but with a hole in the center
  drawPieChart(ctx, data, width, height)
  
  // Draw inner circle to create doughnut effect
  const centerX = width / 2
  const centerY = height / 2
  const innerRadius = Math.min(width, height) / 4
  
  ctx.fillStyle = '#ffffff'
  ctx.beginPath()
  ctx.arc(centerX, centerY, innerRadius, 0, 2 * Math.PI)
  ctx.fill()
}

// Modal components
function initializeModals() {
  const modalTriggers = document.querySelectorAll('[data-modal]')
  
  modalTriggers.forEach(trigger => {
    trigger.addEventListener('click', (event) => {
      event.preventDefault()
      const modalId = trigger.dataset.modal
      openModal(modalId)
    })
  })
  
  // Close modal on backdrop click
  document.addEventListener('click', (event) => {
    if (event.target.classList.contains('modal')) {
      closeModal(event.target.id)
    }
  })
  
  // Close modal on escape key
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      closeAllModals()
    }
  })
}

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

// Dropdown components
function initializeDropdowns() {
  const dropdowns = document.querySelectorAll('.dropdown')
  
  dropdowns.forEach(dropdown => {
    const toggle = dropdown.querySelector('.dropdown-toggle')
    const menu = dropdown.querySelector('.dropdown-menu')
    
    if (toggle && menu) {
      toggle.addEventListener('click', (event) => {
        event.preventDefault()
        event.stopPropagation()
        toggleDropdown(dropdown)
      })
    }
  })
  
  // Close dropdowns when clicking outside
  document.addEventListener('click', (event) => {
    if (!event.target.closest('.dropdown')) {
      closeAllDropdowns()
    }
  })
}

function toggleDropdown(dropdown) {
  const isOpen = dropdown.classList.contains('open')
  
  closeAllDropdowns()
  
  if (!isOpen) {
    dropdown.classList.add('open')
  }
}

function closeAllDropdowns() {
  const dropdowns = document.querySelectorAll('.dropdown.open')
  dropdowns.forEach(dropdown => {
    dropdown.classList.remove('open')
  })
}

// Tab components
function initializeTabs() {
  const tabContainers = document.querySelectorAll('.tabs')
  
  tabContainers.forEach(container => {
    const tabs = container.querySelectorAll('.tab')
    const panels = container.querySelectorAll('.tab-panel')
    
    tabs.forEach(tab => {
      tab.addEventListener('click', (event) => {
        event.preventDefault()
        const targetPanel = tab.dataset.tab
        
        // Remove active class from all tabs and panels
        tabs.forEach(t => t.classList.remove('active'))
        panels.forEach(p => p.classList.remove('active'))
        
        // Add active class to clicked tab and corresponding panel
        tab.classList.add('active')
        const panel = container.querySelector(`[data-panel="${targetPanel}"]`)
        if (panel) {
          panel.classList.add('active')
        }
      })
    })
  })
}

// Accordion components
function initializeAccordions() {
  const accordions = document.querySelectorAll('.accordion')
  
  accordions.forEach(accordion => {
    const headers = accordion.querySelectorAll('.accordion-header')
    
    headers.forEach(header => {
      header.addEventListener('click', () => {
        const panel = header.nextElementSibling
        const isOpen = panel.classList.contains('active')
        
        // Close all panels in this accordion
        accordion.querySelectorAll('.accordion-panel').forEach(p => {
          p.classList.remove('active')
        })
        
        // Toggle current panel
        if (!isOpen) {
          panel.classList.add('active')
        }
      })
    })
  })
}

// Tooltip components
function initializeTooltips() {
  const tooltipElements = document.querySelectorAll('[data-tooltip]')
  
  tooltipElements.forEach(element => {
    element.addEventListener('mouseenter', (event) => {
      showTooltip(event.target, event.target.dataset.tooltip)
    })
    
    element.addEventListener('mouseleave', () => {
      hideTooltip()
    })
  })
}

function showTooltip(element, text) {
  const tooltip = document.createElement('div')
  tooltip.className = 'tooltip'
  tooltip.textContent = text
  
  document.body.appendChild(tooltip)
  
  const rect = element.getBoundingClientRect()
  tooltip.style.left = rect.left + rect.width / 2 - tooltip.offsetWidth / 2 + 'px'
  tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px'
}

function hideTooltip() {
  const tooltip = document.querySelector('.tooltip')
  if (tooltip) {
    tooltip.remove()
  }
}

// Progress bar components
function initializeProgressBars() {
  const progressBars = document.querySelectorAll('.progress-bar')
  
  progressBars.forEach(bar => {
    const value = bar.dataset.value || 0
    const max = bar.dataset.max || 100
    const percentage = (value / max) * 100
    
    bar.style.width = percentage + '%'
  })
}

// Data table components
function initializeDataTables() {
  const tables = document.querySelectorAll('.data-table')
  
  tables.forEach(table => {
    if (table.dataset.sortable === 'true') {
      setupTableSorting(table)
    }
    
    if (table.dataset.searchable === 'true') {
      setupTableSearch(table)
    }
    
    if (table.dataset.paginated === 'true') {
      setupTablePagination(table)
    }
  })
}

function setupTableSorting(table) {
  const headers = table.querySelectorAll('th[data-sortable]')
  
  headers.forEach(header => {
    header.addEventListener('click', () => {
      const column = header.dataset.sortable
      const currentOrder = header.dataset.sortOrder || 'asc'
      const newOrder = currentOrder === 'asc' ? 'desc' : 'asc'
      
      // Update sort indicators
      headers.forEach(h => h.classList.remove('sort-asc', 'sort-desc'))
      header.classList.add(`sort-${newOrder}`)
      header.dataset.sortOrder = newOrder
      
      // Sort table data
      sortTable(table, column, newOrder)
    })
  })
}

function sortTable(table, column, order) {
  const tbody = table.querySelector('tbody')
  const rows = Array.from(tbody.querySelectorAll('tr'))
  
  rows.sort((a, b) => {
    const aValue = a.querySelector(`[data-column="${column}"]`).textContent
    const bValue = b.querySelector(`[data-column="${column}"]`).textContent
    
    if (order === 'asc') {
      return aValue.localeCompare(bValue)
    } else {
      return bValue.localeCompare(aValue)
    }
  })
  
  rows.forEach(row => tbody.appendChild(row))
}

function setupTableSearch(table) {
  const searchInput = table.parentNode.querySelector('.table-search')
  if (!searchInput) return
  
  searchInput.addEventListener('input', () => {
    const searchTerm = searchInput.value.toLowerCase()
    const rows = table.querySelectorAll('tbody tr')
    
    rows.forEach(row => {
      const text = row.textContent.toLowerCase()
      const matches = text.includes(searchTerm)
      row.style.display = matches ? '' : 'none'
    })
  })
}

function setupTablePagination(table) {
  const rowsPerPage = parseInt(table.dataset.rowsPerPage) || 10
  const rows = Array.from(table.querySelectorAll('tbody tr'))
  const totalPages = Math.ceil(rows.length / rowsPerPage)
  
  if (totalPages <= 1) return
  
  // Create pagination controls
  const pagination = document.createElement('div')
  pagination.className = 'pagination'
  
  // Add pagination to table container
  table.parentNode.appendChild(pagination)
  
  // Show first page
  showTablePage(table, rows, 1, rowsPerPage, pagination, totalPages)
}

function showTablePage(table, rows, page, rowsPerPage, pagination, totalPages) {
  const start = (page - 1) * rowsPerPage
  const end = start + rowsPerPage
  const pageRows = rows.slice(start, end)
  
  // Hide all rows
  rows.forEach(row => row.style.display = 'none')
  
  // Show page rows
  pageRows.forEach(row => row.style.display = '')
  
  // Update pagination controls
  updatePaginationControls(pagination, page, totalPages)
}

function updatePaginationControls(pagination, currentPage, totalPages) {
  pagination.innerHTML = ''
  
  // Previous button
  const prevButton = document.createElement('button')
  prevButton.textContent = 'Previous'
  prevButton.disabled = currentPage === 1
  prevButton.addEventListener('click', () => {
    if (currentPage > 1) {
      showTablePage(table, rows, currentPage - 1, rowsPerPage, pagination, totalPages)
    }
  })
  pagination.appendChild(prevButton)
  
  // Page numbers
  for (let i = 1; i <= totalPages; i++) {
    const pageButton = document.createElement('button')
    pageButton.textContent = i
    pageButton.className = i === currentPage ? 'active' : ''
    pageButton.addEventListener('click', () => {
      showTablePage(table, rows, i, rowsPerPage, pagination, totalPages)
    })
    pagination.appendChild(pageButton)
  }
  
  // Next button
  const nextButton = document.createElement('button')
  nextButton.textContent = 'Next'
  nextButton.disabled = currentPage === totalPages
  nextButton.addEventListener('click', () => {
    if (currentPage < totalPages) {
      showTablePage(table, rows, currentPage + 1, rowsPerPage, pagination, totalPages)
    }
  })
  pagination.appendChild(nextButton)
}

// Filter components
function initializeFilters() {
  const filterContainers = document.querySelectorAll('.filter-container')
  
  filterContainers.forEach(container => {
    const filterInputs = container.querySelectorAll('.filter-input')
    const targetElement = document.querySelector(container.dataset.target)
    
    if (targetElement) {
      filterInputs.forEach(input => {
        input.addEventListener('input', () => {
          applyFilters(targetElement, filterInputs)
        })
      })
    }
  })
}

function applyFilters(targetElement, filterInputs) {
  const filters = {}
  
  filterInputs.forEach(input => {
    if (input.value) {
      filters[input.dataset.filter] = input.value.toLowerCase()
    }
  })
  
  const items = targetElement.querySelectorAll('[data-filter-item]')
  
  items.forEach(item => {
    let matches = true
    
    Object.entries(filters).forEach(([key, value]) => {
      const itemValue = item.dataset[key] || item.querySelector(`[data-${key}]`)?.textContent || ''
      if (!itemValue.toLowerCase().includes(value)) {
        matches = false
      }
    })
    
    item.style.display = matches ? '' : 'none'
  })
}

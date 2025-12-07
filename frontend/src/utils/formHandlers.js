// Form handling utilities
export function setupFormHandlers() {
  console.log('Setting up form handlers...')
  
  // Setup form validation
  setupFormValidation()
  
  // Setup form submission handlers
  setupFormSubmissionHandlers()
  
  // Setup form field handlers
  setupFormFieldHandlers()
  
  console.log('Form handlers setup complete')
}

function setupFormValidation() {
  // Add validation to all forms
  const forms = document.querySelectorAll('form[data-validate]')
  forms.forEach(form => {
    setupFormValidationForElement(form)
  })
  
  // Setup real-time validation
  setupRealTimeValidation()
}

function setupFormValidationForElement(form) {
  const fields = form.querySelectorAll('input, select, textarea')
  
  fields.forEach(field => {
    // Add validation attributes
    addValidationAttributes(field)
    
    // Setup field validation
    setupFieldValidation(field)
  })
}

function addValidationAttributes(field) {
  const fieldType = field.type
  const fieldName = field.name
  
  // Add required validation
  if (field.hasAttribute('required')) {
    field.setAttribute('data-required', 'true')
  }
  
  // Add type-specific validation
  switch (fieldType) {
    case 'email':
      field.setAttribute('data-email', 'true')
      break
    case 'url':
      field.setAttribute('data-url', 'true')
      break
    case 'tel':
      field.setAttribute('data-phone', 'true')
      break
    case 'number':
      field.setAttribute('data-number', 'true')
      break
  }
  
  // Add length validation
  if (field.hasAttribute('maxlength')) {
    field.setAttribute('data-max-length', field.getAttribute('maxlength'))
  }
  if (field.hasAttribute('minlength')) {
    field.setAttribute('data-min-length', field.getAttribute('minlength'))
  }
  
  // Add pattern validation
  if (field.hasAttribute('pattern')) {
    field.setAttribute('data-pattern', field.getAttribute('pattern'))
  }
}

function setupFieldValidation(field) {
  // Validate on blur
  field.addEventListener('blur', () => {
    validateField(field)
  })
  
  // Validate on input (for real-time feedback)
  field.addEventListener('input', () => {
    if (field.dataset.validateOnInput !== 'false') {
      validateField(field)
    }
  })
  
  // Clear validation on focus
  field.addEventListener('focus', () => {
    clearFieldValidation(field)
  })
}

function setupRealTimeValidation() {
  // Setup global validation event listeners
  document.addEventListener('input', (event) => {
    if (event.target.matches('input, select, textarea')) {
      validateFieldRealTime(event.target)
    }
  })
}

function setupFormSubmissionHandlers() {
  // Handle form submissions
  document.addEventListener('submit', (event) => {
    const form = event.target
    if (form.tagName === 'FORM') {
      handleFormSubmission(form, event)
    }
  })
}

function setupFormFieldHandlers() {
  // Handle field-specific interactions
  setupFileUploadHandlers()
  setupDatePickerHandlers()
  setupSelectHandlers()
  setupCheckboxHandlers()
  setupRadioHandlers()
}

function setupFileUploadHandlers() {
  const fileInputs = document.querySelectorAll('input[type="file"]')
  
  fileInputs.forEach(input => {
    input.addEventListener('change', (event) => {
      handleFileUpload(event.target)
    })
    
    // Add drag and drop support
    input.addEventListener('dragover', (event) => {
      event.preventDefault()
      input.classList.add('drag-over')
    })
    
    input.addEventListener('dragleave', (event) => {
      event.preventDefault()
      input.classList.remove('drag-over')
    })
    
    input.addEventListener('drop', (event) => {
      event.preventDefault()
      input.classList.remove('drag-over')
      
      const files = event.dataTransfer.files
      input.files = files
      
      // Trigger change event
      input.dispatchEvent(new Event('change'))
    })
  })
}

function setupDatePickerHandlers() {
  const dateInputs = document.querySelectorAll('input[type="date"], input[type="datetime-local"]')
  
  dateInputs.forEach(input => {
    // Add date validation
    input.addEventListener('change', () => {
      validateDateField(input)
    })
  })
}

function setupSelectHandlers() {
  const selects = document.querySelectorAll('select')
  
  selects.forEach(select => {
    // Add change validation
    select.addEventListener('change', () => {
      validateField(select)
    })
    
    // Add search functionality for large selects
    if (select.dataset.searchable === 'true') {
      setupSelectSearch(select)
    }
  })
}

function setupCheckboxHandlers() {
  const checkboxes = document.querySelectorAll('input[type="checkbox"]')
  
  checkboxes.forEach(checkbox => {
    // Handle checkbox groups
    if (checkbox.name.endsWith('[]')) {
      checkbox.addEventListener('change', () => {
        validateCheckboxGroup(checkbox)
      })
    }
  })
}

function setupRadioHandlers() {
  const radioGroups = document.querySelectorAll('input[type="radio"]')
  
  // Group radios by name
  const radioGroupsMap = new Map()
  radioGroups.forEach(radio => {
    if (!radioGroupsMap.has(radio.name)) {
      radioGroupsMap.set(radio.name, [])
    }
    radioGroupsMap.get(radio.name).push(radio)
  })
  
  // Add validation to each group
  radioGroupsMap.forEach((radios, name) => {
    radios.forEach(radio => {
      radio.addEventListener('change', () => {
        validateRadioGroup(radios)
      })
    })
  })
}

// Validation functions
function validateField(field) {
  const value = field.value.trim()
  const fieldName = field.name
  const fieldType = field.type
  
  // Clear previous validation
  clearFieldValidation(field)
  
  // Required validation
  if (field.dataset.required === 'true' && !value) {
    showFieldError(field, `${getFieldLabel(field)} is required`)
    return false
  }
  
  // Skip other validations if field is empty and not required
  if (!value && field.dataset.required !== 'true') {
    return true
  }
  
  // Type-specific validation
  switch (fieldType) {
    case 'email':
      if (!isValidEmail(value)) {
        showFieldError(field, 'Please enter a valid email address')
        return false
      }
      break
    case 'url':
      if (!isValidUrl(value)) {
        showFieldError(field, 'Please enter a valid URL')
        return false
      }
      break
    case 'tel':
      if (!isValidPhone(value)) {
        showFieldError(field, 'Please enter a valid phone number')
        return false
      }
      break
    case 'number':
      if (!isValidNumber(value)) {
        showFieldError(field, 'Please enter a valid number')
        return false
      }
      break
  }
  
  // Length validation
  if (field.dataset.minLength && value.length < parseInt(field.dataset.minLength)) {
    showFieldError(field, `Minimum length is ${field.dataset.minLength} characters`)
    return false
  }
  
  if (field.dataset.maxLength && value.length > parseInt(field.dataset.maxLength)) {
    showFieldError(field, `Maximum length is ${field.dataset.maxLength} characters`)
    return false
  }
  
  // Pattern validation
  if (field.dataset.pattern) {
    const pattern = new RegExp(field.dataset.pattern)
    if (!pattern.test(value)) {
      showFieldError(field, 'Please enter a valid format')
      return false
    }
  }
  
  // Custom validation
  if (field.dataset.validate) {
    const validationResult = validateCustom(field, value)
    if (!validationResult.valid) {
      showFieldError(field, validationResult.message)
      return false
    }
  }
  
  return true
}

function validateFieldRealTime(field) {
  // Only validate if field has been touched
  if (field.dataset.touched !== 'true') {
    return
  }
  
  validateField(field)
}

function validateDateField(field) {
  const value = field.value
  if (!value) return true
  
  const date = new Date(value)
  const now = new Date()
  
  // Check if date is in the future (if not allowed)
  if (field.dataset.noFuture === 'true' && date > now) {
    showFieldError(field, 'Date cannot be in the future')
    return false
  }
  
  // Check if date is in the past (if not allowed)
  if (field.dataset.noPast === 'true' && date < now) {
    showFieldError(field, 'Date cannot be in the past')
    return false
  }
  
  return true
}

function validateCheckboxGroup(checkbox) {
  const groupName = checkbox.name.replace('[]', '')
  const groupCheckboxes = document.querySelectorAll(`input[name="${checkbox.name}"]`)
  const checkedBoxes = document.querySelectorAll(`input[name="${checkbox.name}"]:checked`)
  
  // Check minimum required
  const minRequired = parseInt(checkbox.dataset.minRequired) || 0
  if (checkedBoxes.length < minRequired) {
    showGroupError(groupCheckboxes, `Please select at least ${minRequired} options`)
    return false
  }
  
  // Check maximum allowed
  const maxAllowed = parseInt(checkbox.dataset.maxAllowed) || Infinity
  if (checkedBoxes.length > maxAllowed) {
    showGroupError(groupCheckboxes, `Please select no more than ${maxAllowed} options`)
    return false
  }
  
  clearGroupError(groupCheckboxes)
  return true
}

function validateRadioGroup(radios) {
  const checkedRadio = document.querySelector(`input[name="${radios[0].name}"]:checked`)
  
  if (!checkedRadio && radios[0].dataset.required === 'true') {
    showGroupError(radios, 'Please select an option')
    return false
  }
  
  clearGroupError(radios)
  return true
}

// Validation helper functions
function isValidEmail(email) {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

function isValidUrl(url) {
  try {
    new URL(url)
    return true
  } catch {
    return false
  }
}

function isValidPhone(phone) {
  const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/
  return phoneRegex.test(phone.replace(/[\s\-\(\)]/g, ''))
}

function isValidNumber(number) {
  return !isNaN(number) && isFinite(number)
}

function validateCustom(field, value) {
  // This can be extended with custom validation functions
  const validator = field.dataset.validate
  const validatorFunction = window[validator]
  
  if (typeof validatorFunction === 'function') {
    return validatorFunction(value, field)
  }
  
  return { valid: true }
}

// Error handling functions
function showFieldError(field, message) {
  clearFieldValidation(field)
  
  field.classList.add('error')
  
  const errorElement = document.createElement('div')
  errorElement.className = 'field-error'
  errorElement.textContent = message
  
  field.parentNode.appendChild(errorElement)
}

function clearFieldValidation(field) {
  field.classList.remove('error')
  
  const errorElement = field.parentNode.querySelector('.field-error')
  if (errorElement) {
    errorElement.remove()
  }
}

function showGroupError(fields, message) {
  fields.forEach(field => {
    field.classList.add('error')
  })
  
  // Show error message for the group
  const firstField = fields[0]
  const groupError = document.createElement('div')
  groupError.className = 'group-error'
  groupError.textContent = message
  
  const fieldContainer = firstField.closest('.form-group, .field-group')
  if (fieldContainer) {
    fieldContainer.appendChild(groupError)
  }
}

function clearGroupError(fields) {
  fields.forEach(field => {
    field.classList.remove('error')
  })
  
  const firstField = fields[0]
  const fieldContainer = firstField.closest('.form-group, .field-group')
  if (fieldContainer) {
    const groupError = fieldContainer.querySelector('.group-error')
    if (groupError) {
      groupError.remove()
    }
  }
}

function getFieldLabel(field) {
  const label = field.parentNode.querySelector('label')
  if (label) {
    return label.textContent.replace('*', '').trim()
  }
  
  return field.name.replace(/[_-]/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

// Form submission handling
function handleFormSubmission(form, event) {
  // Mark all fields as touched
  const fields = form.querySelectorAll('input, select, textarea')
  fields.forEach(field => {
    field.dataset.touched = 'true'
  })
  
  // Validate all fields
  const isValid = validateForm(form)
  
  if (!isValid) {
    event.preventDefault()
    showNotification('Please fix the errors in the form', 'error')
    return false
  }
  
  // Show loading state
  showFormLoading(form, true)
  
  return true
}

function validateForm(form) {
  const fields = form.querySelectorAll('input, select, textarea')
  let isValid = true
  
  fields.forEach(field => {
    if (!validateField(field)) {
      isValid = false
    }
  })
  
  return isValid
}

function showFormLoading(form, isLoading) {
  const submitButton = form.querySelector('button[type="submit"]')
  if (submitButton) {
    if (isLoading) {
      submitButton.disabled = true
      submitButton.dataset.originalText = submitButton.textContent
      submitButton.innerHTML = '<span class="spinner"></span> Processing...'
    } else {
      submitButton.disabled = false
      submitButton.textContent = submitButton.dataset.originalText || 'Submit'
    }
  }
}

// File upload handling
function handleFileUpload(input) {
  const files = Array.from(input.files)
  const maxSize = parseInt(input.dataset.maxSize) || 5 * 1024 * 1024 // 5MB default
  const allowedTypes = input.dataset.allowedTypes ? input.dataset.allowedTypes.split(',') : []
  
  files.forEach(file => {
    // Check file size
    if (file.size > maxSize) {
      showNotification(`File ${file.name} is too large. Maximum size is ${formatFileSize(maxSize)}.`, 'error')
      input.value = ''
      return
    }
    
    // Check file type
    if (allowedTypes.length > 0 && !allowedTypes.includes(file.type)) {
      showNotification(`File ${file.name} is not allowed. Allowed types: ${allowedTypes.join(', ')}`, 'error')
      input.value = ''
      return
    }
  })
  
  // Show file preview
  if (files.length > 0) {
    showFilePreview(files[0], input)
  }
}

function showFilePreview(file, input) {
  const previewContainer = input.parentNode.querySelector('.file-preview')
  if (!previewContainer) return
  
  if (file.type.startsWith('image/')) {
    const reader = new FileReader()
    reader.onload = (e) => {
      previewContainer.innerHTML = `<img src="${e.target.result}" alt="Preview" style="max-width: 200px; max-height: 200px;">`
    }
    reader.readAsDataURL(file)
  } else {
    previewContainer.innerHTML = `<div class="file-info">
      <strong>${file.name}</strong><br>
      <small>${formatFileSize(file.size)}</small>
    </div>`
  }
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes'
  
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// Select search functionality
function setupSelectSearch(select) {
  const wrapper = document.createElement('div')
  wrapper.className = 'select-search-wrapper'
  
  const searchInput = document.createElement('input')
  searchInput.type = 'text'
  searchInput.className = 'select-search-input'
  searchInput.placeholder = 'Search options...'
  
  const optionsContainer = document.createElement('div')
  optionsContainer.className = 'select-options'
  
  // Move select inside wrapper
  select.parentNode.insertBefore(wrapper, select)
  wrapper.appendChild(select)
  wrapper.appendChild(searchInput)
  wrapper.appendChild(optionsContainer)
  
  // Populate options
  populateSelectOptions(select, optionsContainer)
  
  // Setup search
  searchInput.addEventListener('input', () => {
    filterSelectOptions(optionsContainer, searchInput.value)
  })
}

function populateSelectOptions(select, container) {
  const options = Array.from(select.options)
  
  options.forEach(option => {
    const optionElement = document.createElement('div')
    optionElement.className = 'select-option'
    optionElement.textContent = option.textContent
    optionElement.dataset.value = option.value
    
    optionElement.addEventListener('click', () => {
      select.value = option.value
      select.dispatchEvent(new Event('change'))
      container.style.display = 'none'
    })
    
    container.appendChild(optionElement)
  })
}

function filterSelectOptions(container, searchTerm) {
  const options = container.querySelectorAll('.select-option')
  
  options.forEach(option => {
    const text = option.textContent.toLowerCase()
    const matches = text.includes(searchTerm.toLowerCase())
    
    option.style.display = matches ? 'block' : 'none'
  })
}

function showNotification(message, type = 'info') {
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

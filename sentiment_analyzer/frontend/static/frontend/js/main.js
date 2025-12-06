// Main JavaScript file for the Django frontend application

console.log('Django frontend application loaded!');

// Simple navigation functionality
document.addEventListener('DOMContentLoaded', function() {
    // Add click handlers for navigation links
    const navLinks = document.querySelectorAll('nav a');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Let Django handle the navigation
            console.log('Navigating to:', this.getAttribute('href'));
        });
    });
    
    // Example function to make API calls to Django backend
    window.fetchData = async function() {
        try {
            const response = await fetch('/api/data/'); // Adjust this URL to match your Django API
            const data = await response.json();
            console.log('Data from Django API:', data);
            return data;
        } catch (error) {
            console.error('Error fetching data:', error);
            return null;
        }
    };
    
    // Example function to show current time
    window.updateTime = function() {
        const now = new Date();
        const timeElement = document.querySelector('.current-time');
        if (timeElement) {
            timeElement.textContent = now.toLocaleString();
        }
    };
    
    // Update time every second
    setInterval(window.updateTime, 1000);
});

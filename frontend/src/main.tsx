import { createRoot } from 'react-dom/client';
import App from './App';
import './styles/main.css';

// Load CSV on launch if no data exists
async function loadCSVOnLaunch() {
  try {
    // Check if CSV data already exists
    const response = await fetch('/api/ml/dashboard-stats/');
    if (response.ok) {
      const data = await response.json();
      if (data.total_responses === 0) {
        // No data exists, try to load default CSV from the project root
        try {
          // Try to fetch the CSV file from the backend static files or public directory
          const csvPath = '/employee_feedback_dataset.csv';
          const csvResponse = await fetch(csvPath);
          if (csvResponse.ok) {
            const csvBlob = await csvResponse.blob();
            const formData = new FormData();
            formData.append('csv_file', csvBlob, 'employee_feedback_dataset.csv');
            
            // Upload CSV
            const uploadResponse = await fetch('/api/upload/', {
              method: 'POST',
              body: formData,
            });
            
            if (uploadResponse.ok) {
              console.log('CSV loaded successfully on launch');
            }
          }
        } catch (csvError) {
          console.log('CSV file not found in public directory. Please upload manually.');
        }
      } else {
        console.log(`Data already exists: ${data.total_responses} responses`);
      }
    }
  } catch (error) {
    console.log('CSV auto-load skipped:', error);
  }
}

// Load CSV when app starts (non-blocking)
loadCSVOnLaunch();

const root = createRoot(document.getElementById('root')!);
root.render(<App />);


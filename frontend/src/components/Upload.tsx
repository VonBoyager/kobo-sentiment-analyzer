import { useState, useRef } from 'react';
import { Upload as UploadIcon, FileSpreadsheet, CheckCircle2, XCircle, AlertCircle, Sparkles, Database } from 'lucide-react';
import { api } from '../api/client';

const requiredColumns = [
  { name: 'uid', description: 'Unique identifier for the response.' },
  { name: 'review_date', description: 'Date of the review (e.g., YYYY-MM-DD). Required for trend analysis.' },
  { name: 'salary_fairness', description: 'Rating (1-5) for "I believe my salary is fair."' },
  { name: 'compensation_competitiveness', description: 'Rating (1-5) for "Our compensation is competitive."' },
  { name: 'benefits_adequacy', description: 'Rating (1-5) for "Our benefits are adequate for my needs."' },
  { name: 'workload_balance', description: 'Rating (1-5) for "I have a manageable workload."' },
  { name: 'schedule_flexibility', description: 'Rating (1-5) for "I have flexibility in my schedule."' },
  { name: 'leave_policies_adequacy', description: 'Rating (1-5) for "Our leave policies are adequate."' },
  { name: 'workplace_safety_comfort', description: 'Rating (1-5) for "My workplace is safe and comfortable."' },
  { name: 'positive_inclusive_culture', description: 'Rating (1-5) for "We have a positive and inclusive culture."' },
  { name: 'access_to_tools_resources', description: 'Rating (1-5) for "I have the tools and resources I need."' },
  { name: 'professional_growth_opportunities', description: 'Rating (1-5) for "There are opportunities for professional growth."' },
  { name: 'training_skill_development', description: 'Rating (1-5) for "The training I receive is valuable."' },
  { name: 'clear_career_paths', description: 'Rating (1-5) for "There is a clear path for career advancement."' },
  { name: 'manager_communication_clarity', description: 'Rating (1-5) for "My manager communicates clearly."' },
  { name: 'raising_concerns_comfortability', description: 'Rating (1-5) for "I am comfortable raising concerns."' },
  { name: 'manager_support_for_employees', description: 'Rating (1-5) for "My manager supports me."' },
  { name: 'job_security_feeling', description: 'Rating (1-5) for "I feel my job is secure."' },
  { name: 'organizational_financial_stability', description: 'Rating (1-5) for "I believe the company is financially stable."' },
  { name: 'open_communication_on_changes', description: 'Rating (1-5) for "Changes are communicated openly."' },
  { name: 'team_collaboration_effectiveness', description: 'Rating (1-5) for "My team collaborates effectively."' },
  { name: 'colleague_respect_support', description: 'Rating (1-5) for "I feel respected by my colleagues."' },
  { name: 'constructive_conflict_management', description: 'Rating (1-5) for "Conflicts are managed constructively."' },
  { name: 'clear_job_responsibilities', description: 'Rating (1-5) for "My job responsibilities are clear."' },
  { name: 'autonomy_in_role', description: 'Rating (1-5) for "I have autonomy in my role."' },
  { name: 'role_alignment_with_skills', description: 'Rating (1-5) for "My role aligns with my skills."' },
  { name: 'acknowledgement_of_contributions', description: 'Rating (1-5) for "My contributions are acknowledged."' },
  { name: 'fair_performance_evaluations', description: 'Rating (1-5) for "Performance evaluations are fair."' },
  { name: 'fair_rewards_for_effort', description: 'Rating (1-5) for "We are fairly rewarded for our efforts."' },
  { name: 'mission_values_meaningful', description: 'Rating (1-5) for "The company\'s mission is meaningful to me."' },
  { name: 'encouragement_of_innovation', description: 'Rating (1-5) for "Innovation is encouraged."' },
  { name: 'Company_acts_ethically', description: 'Rating (1-5) for "The company acts ethically."' },
  { name: 'free_text_box', description: 'Open-ended feedback text. This column should contain employee comments and feedback.' },
  { name: 'sentiment_label', description: 'Sentiment of the feedback (Positive, Neutral, Negative). Optional - will be auto-detected if missing.' },
];

type UploadStatus = 'idle' | 'uploading' | 'processing' | 'success' | 'error';

export function Upload() {
  const [status, setStatus] = useState<UploadStatus>('idle');
  const [fileName, setFileName] = useState('');
  const [logs, setLogs] = useState<string[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const addLog = (message: string) => {
    setLogs(prev => [...prev, `${new Date().toLocaleTimeString()}: ${message}`]);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = async (file: File) => {
    setFileName(file.name);
    setStatus('uploading');
    setLogs([]);
    
    addLog('File selected: ' + file.name);
    addLog('File size: ' + (file.size / 1024 / 1024).toFixed(2) + ' MB');
    
    const formData = new FormData();
    formData.append('csv_file', file);
    
    try {
        addLog('Uploading file to server...');
        // Don't set Content-Type manually for FormData - axios/browser does it with boundary
        const response = await api.post('/upload/', formData);

        addLog('Upload complete. Processing data...');
        setStatus('processing');
        
        const result = response.data;
        addLog(result.message || 'Processing complete');
        addLog('Data has been loaded into the system.');
        addLog('You can now view results in the Dashboard and Results pages.');
        setStatus('success');

    } catch (error) {
        addLog('An error occurred: ' + (error instanceof Error ? error.message : 'Unknown error'));
        setStatus('error');
    }
  };

  const handleReset = () => {
    setStatus('idle');
    setFileName('');
    setLogs([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-3">
          <Database className="w-5 h-5 text-blue-400" />
          <span className="text-sm text-gray-400 uppercase tracking-wider">Data Management</span>
        </div>
        <h1 className="text-3xl text-white mb-2">Upload Employee Data</h1>
        <p className="text-gray-400">
          Import employee feedback data from CSV files for analysis. The system will automatically process the data and run ML analysis.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        
        {/* Upload Zone */}
        <div className="lg:col-span-2">
          <div className="bg-gray-800 rounded-2xl p-8 border border-gray-700">
            {status === 'idle' && (
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-2xl p-12 text-center transition-all ${
                  dragActive
                    ? 'border-blue-500 bg-blue-900/20'
                    : 'border-gray-600 hover:border-gray-500 bg-gray-700/30'
                }`}
              >
                <div className="w-20 h-20 bg-blue-900/30 rounded-2xl flex items-center justify-center mx-auto mb-6">
                  <UploadIcon className="w-10 h-10 text-blue-400" />
                </div>
                <h3 className="text-xl text-white mb-2">Drop your CSV file here</h3>
                <p className="text-gray-400 mb-6">or click to browse</p>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv"
                  onChange={handleChange}
                  className="hidden"
                  id="file-upload"
                />
                <label
                  htmlFor="file-upload"
                  className="inline-block px-8 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-all shadow-lg hover:shadow-xl cursor-pointer font-medium"
                >
                  Select CSV File
                </label>
              </div>
            )}

            {status !== 'idle' && (
              <div>
                <div className="flex items-center gap-4 mb-6 pb-6 border-b border-gray-700">
                  <div className="w-14 h-14 bg-blue-900/30 rounded-xl flex items-center justify-center flex-shrink-0">
                    <FileSpreadsheet className="w-7 h-7 text-blue-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-white font-medium truncate">{fileName}</div>
                    <div className="text-sm text-gray-400 mt-1">
                      {status === 'uploading' && 'Uploading...'}
                      {status === 'processing' && 'Processing...'}
                      {status === 'success' && 'Complete'}
                      {status === 'error' && 'Error'}
                    </div>
                  </div>
                  {status === 'success' && (
                    <div className="w-12 h-12 bg-emerald-900/30 rounded-xl flex items-center justify-center flex-shrink-0">
                      <CheckCircle2 className="w-7 h-7 text-emerald-400" />
                    </div>
                  )}
                  {status === 'error' && (
                    <div className="w-12 h-12 bg-red-900/30 rounded-xl flex items-center justify-center flex-shrink-0">
                      <XCircle className="w-7 h-7 text-red-400" />
                    </div>
                  )}
                </div>

                {/* Progress Logs */}
                <div className="bg-slate-950 rounded-xl p-4 mb-6 border border-gray-700">
                  <div className="text-xs text-emerald-400 font-mono space-y-1.5 max-h-64 overflow-y-auto">
                    {logs.map((log, index) => (
                      <div key={index} className="leading-relaxed">{log}</div>
                    ))}
                  </div>
                </div>

                {status === 'success' && (
                  <button
                    onClick={handleReset}
                    className="w-full px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-all shadow-lg hover:shadow-xl font-medium"
                  >
                    Upload Another File
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Requirements Card - Detailed Instructions */}
        <div className="lg:col-span-1">
          <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700 lg:sticky lg:top-24">
            <div className="flex items-center gap-2 mb-5">
              <AlertCircle className="w-5 h-5 text-blue-400" />
              <h3 className="text-white font-semibold">CSV Requirements</h3>
            </div>
            
            <p className="text-sm text-gray-400 mb-5">
              Your CSV file must include the following columns with their respective questions:
            </p>

            <div className="space-y-3 max-h-96 overflow-y-auto pr-2">
              {requiredColumns.map((col) => (
                <div key={col.name} className="pb-3 border-b border-gray-700 last:border-0">
                  <div className="text-sm mb-1 font-mono text-blue-300 break-all">{col.name}</div>
                  <div className="text-xs text-gray-400">{col.description}</div>
                </div>
              ))}
            </div>

            <div className="mt-6 p-4 bg-blue-900/20 rounded-xl border border-blue-800">
              <div className="flex items-start gap-2">
                <Sparkles className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-blue-300">
                  <strong>Important:</strong> All score columns should contain numeric values from 1 to 5. The system will automatically detect sentiment from the free_text_box column if sentiment_label is not provided.
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}


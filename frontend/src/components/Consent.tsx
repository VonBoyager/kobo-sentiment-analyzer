import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck, ArrowRight, FileText } from 'lucide-react';

export function Consent() {
  const navigate = useNavigate();
  const [agreed, setAgreed] = useState(false);

  const handleStart = () => {
    if (agreed) {
      // In a real app, we might save this consent state
      localStorage.setItem('questionnaire_consent', 'true');
      navigate('/questionnaire/start');
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full bg-gray-800 rounded-3xl p-8 border border-gray-700 shadow-xl">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-900/30 rounded-2xl mb-4 text-blue-400">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">Employee Feedback Questionnaire</h1>
          <p className="text-gray-400">Your voice matters. Help us improve our workplace.</p>
        </div>

        <div className="space-y-6 mb-8">
          <div className="bg-gray-700/30 rounded-xl p-6 border border-gray-600/50">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <FileText className="w-5 h-5 text-blue-400" />
              Consent & Privacy Policy
            </h3>
            <div className="space-y-4 text-gray-300 text-sm leading-relaxed">
              <p>
                <strong>Purpose:</strong> This questionnaire is designed to gather feedback on employee satisfaction, 
                workplace culture, and areas for improvement. Your responses will be used to enhance our working environment.
              </p>
              <p>
                <strong>Confidentiality:</strong> Your responses will be processed anonymously where possible. 
                Individual responses will be aggregated for analysis. We are committed to protecting your privacy 
                and ensuring that your feedback is used constructively.
              </p>
              <p>
                <strong>Voluntary Participation:</strong> Participation in this survey is voluntary. 
                You may choose not to answer specific questions or discontinue the survey at any time.
              </p>
              <p>
                <strong>Data Usage:</strong> The data collected will be analyzed using statistical methods 
                and machine learning to identify trends and insights.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3 p-4 bg-blue-900/10 rounded-xl border border-blue-900/30">
            <div className="flex items-center h-5 mt-0.5">
              <input
                id="consent-checkbox"
                type="checkbox"
                checked={agreed}
                onChange={(e) => setAgreed(e.target.checked)}
                className="w-5 h-5 text-blue-600 bg-gray-700 border-gray-600 rounded focus:ring-blue-600 ring-offset-gray-800 focus:ring-2"
              />
            </div>
            <label htmlFor="consent-checkbox" className="text-sm text-gray-300 cursor-pointer select-none">
              I have read and understood the information above. I agree to participate in this questionnaire 
              and consent to the processing of my feedback as described.
            </label>
          </div>
        </div>

        <button
          onClick={handleStart}
          disabled={!agreed}
          className={`w-full py-4 rounded-xl font-semibold text-lg flex items-center justify-center gap-2 transition-all ${
            agreed
              ? 'bg-blue-600 hover:bg-blue-700 text-white shadow-lg hover:shadow-blue-500/25'
              : 'bg-gray-700 text-gray-500 cursor-not-allowed'
          }`}
        >
          Start Questionnaire
          <ArrowRight className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}
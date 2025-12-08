import { useState } from 'react';
import { Copy, Lock, Unlock, Eye, Link as LinkIcon, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';

export function AdminQuestionnaires() {
  const [isLocked, setIsLocked] = useState(false);
  
  // In a real app, this would come from the backend
  const questionnaireLink = `${window.location.origin}/questionnaire`;

  const copyLink = async () => {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(questionnaireLink);
        toast.success('Link copied to clipboard');
      } else {
        // Fallback for non-secure context (HTTP)
        const textArea = document.createElement("textarea");
        textArea.value = questionnaireLink;
        textArea.style.position = "fixed";
        textArea.style.left = "-9999px";
        textArea.style.top = "0";
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        try {
          document.execCommand('copy');
          toast.success('Link copied to clipboard');
        } catch (err) {
          console.error('Fallback: Oops, unable to copy', err);
          toast.error('Failed to copy link');
        }
        document.body.removeChild(textArea);
      }
    } catch (err) {
      console.error('Failed to copy: ', err);
      toast.error('Failed to copy link');
    }
  };

  const toggleLock = () => {
    setIsLocked(!isLocked);
    toast.success(isLocked ? 'Questionnaire unlocked' : 'Questionnaire locked');
  };

  return (
    <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
      <div className="bg-gray-800 rounded-3xl p-8 border border-gray-700 shadow-xl">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 mb-8">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2">Questionnaire Management</h1>
            <p className="text-gray-400">Manage access and settings for employee questionnaires</p>
          </div>
          <div className="flex gap-3">
            <a
              href="/questionnaire"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-gray-200 rounded-xl transition-colors font-medium border border-gray-600"
            >
              <Eye className="w-4 h-4" />
              Preview
            </a>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Share Link Card */}
          <div className="bg-gray-700/30 rounded-2xl p-6 border border-gray-600/50">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-blue-900/30 rounded-xl flex items-center justify-center">
                <LinkIcon className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white">Shareable Link</h3>
                <p className="text-sm text-gray-400">Direct link for employees to access the questionnaire</p>
              </div>
            </div>
            
            <div className="flex gap-2">
              <div className="flex-1 bg-gray-900/50 border border-gray-600 rounded-xl px-4 py-3 text-gray-300 font-mono text-sm truncate">
                {questionnaireLink}
              </div>
              <button
                onClick={copyLink}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl transition-colors flex items-center gap-2"
              >
                <Copy className="w-4 h-4" />
                <span className="hidden sm:inline">Copy</span>
              </button>
            </div>
          </div>

          {/* Access Control Card */}
          <div className="bg-gray-700/30 rounded-2xl p-6 border border-gray-600/50">
            <div className="flex items-center gap-3 mb-4">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                isLocked ? 'bg-red-900/30' : 'bg-emerald-900/30'
              }`}>
                {isLocked ? (
                  <Lock className="w-5 h-5 text-red-400" />
                ) : (
                  <Unlock className="w-5 h-5 text-emerald-400" />
                )}
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white">Access Control</h3>
                <p className="text-sm text-gray-400">
                  {isLocked 
                    ? 'Questionnaire is currently locked (not accepting responses)' 
                    : 'Questionnaire is active and accepting responses'}
                </p>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <span className={`text-sm font-medium ${
                isLocked ? 'text-red-400' : 'text-emerald-400'
              }`}>
                Status: {isLocked ? 'Locked' : 'Active'}
              </span>
              <button
                onClick={toggleLock}
                className={`px-6 py-2 rounded-xl text-sm font-medium transition-colors border ${
                  isLocked
                    ? 'bg-emerald-600 hover:bg-emerald-700 text-white border-transparent'
                    : 'bg-red-600 hover:bg-red-700 text-white border-transparent'
                }`}
              >
                {isLocked ? 'Unlock Questionnaire' : 'Lock Questionnaire'}
              </button>
            </div>
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-8 bg-blue-900/10 border border-blue-900/30 rounded-2xl p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <CheckCircle2 className="w-5 h-5 text-blue-400" />
            Workflow Instructions
          </h3>
          <ul className="space-y-3 text-gray-300 text-sm">
            <li className="flex gap-3">
              <span className="w-6 h-6 bg-blue-900/30 rounded-full flex items-center justify-center text-blue-400 font-bold text-xs flex-shrink-0">1</span>
              <span>Copy the shareable link above and distribute it to employees via email or internal communication channels.</span>
            </li>
            <li className="flex gap-3">
              <span className="w-6 h-6 bg-blue-900/30 rounded-full flex items-center justify-center text-blue-400 font-bold text-xs flex-shrink-0">2</span>
              <span>Employees will be directed to a landing page where they must provide consent before starting the questionnaire.</span>
            </li>
            <li className="flex gap-3">
              <span className="w-6 h-6 bg-blue-900/30 rounded-full flex items-center justify-center text-blue-400 font-bold text-xs flex-shrink-0">3</span>
              <span>Use the Lock/Unlock toggle to control when responses can be submitted (e.g., close the survey after a deadline).</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
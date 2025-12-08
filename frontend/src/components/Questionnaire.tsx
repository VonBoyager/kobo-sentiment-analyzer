import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { api } from '../api/client';

interface Section {
  id: number;
  name: string;
  description: string;
  order: number;
}

interface Question {
  id: number;
  section: {
    id: number;
    name: string;
  };
  text: string;
  order: number;
}

export function Questionnaire() {
  const navigate = useNavigate();
  const [sections, setSections] = useState<Section[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [answers, setAnswers] = useState<{ [key: number]: number }>({});
  const [review, setReview] = useState('');
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [sectionsRes, questionsRes] = await Promise.all([
          api.get('/questionnaire-sections/'),
          api.get('/questionnaire-questions/')
        ]);
        
        // Sort sections by order
        const sortedSections = (sectionsRes.data.results || sectionsRes.data || []).sort(
          (a: Section, b: Section) => a.order - b.order
        );
        
        setSections(sortedSections);
        setQuestions(questionsRes.data.results || questionsRes.data || []);
      } catch (err) {
        console.error("Failed to load questionnaire:", err);
        setError("Failed to load questionnaire data. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleScoreChange = (questionId: number, score: number) => {
    setAnswers(prev => ({
      ...prev,
      [questionId]: score
    }));
  };

  const handleSubmit = async () => {
    // Validation
    const unansweredCount = questions.length - Object.keys(answers).length;
    if (unansweredCount > 0) {
      setError(`Please answer all questions. (${unansweredCount} remaining)`);
      window.scrollTo(0, 0);
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const payload = {
        review: review,
        answers: Object.entries(answers).map(([qId, score]) => ({
          question_id: parseInt(qId),
          score: score
        }))
      };

      await api.post('/questionnaire-responses/', payload);
      setSubmitted(true);
      setTimeout(() => {
        navigate('/dashboard');
      }, 3000);
    } catch (err) {
      console.error("Submission error:", err);
      setError("Failed to submit questionnaire. Please try again.");
      window.scrollTo(0, 0);
    } finally {
      setSubmitting(false);
    }
  };

  const getQuestionsBySection = (sectionId: number) => {
    return questions
      .filter(q => q.section.id === sectionId)
      .sort((a, b) => a.order - b.order);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  if (submitted) {
    return (
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        <div className="bg-gray-800 rounded-2xl p-8 text-center border border-gray-700">
          <CheckCircle2 className="w-16 h-16 text-emerald-400 mx-auto mb-4" />
          <h2 className="text-2xl text-white mb-2">Thank you!</h2>
          <p className="text-gray-400">Your response has been submitted successfully.</p>
          <p className="text-gray-500 text-sm mt-4">Redirecting to dashboard...</p>
        </div>
      </div>
    );
  }

  if (sections.length === 0) {
     return (
        <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
          <div className="bg-gray-800 rounded-2xl p-8 text-center">
            <AlertCircle className="w-16 h-16 text-yellow-400 mx-auto mb-4" />
            <h2 className="text-2xl text-white mb-2">No Questions Found</h2>
            <p className="text-gray-400">The questionnaire has not been set up yet.</p>
          </div>
        </div>
     );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Employee Questionnaire</h1>
        <p className="text-gray-400">Your feedback helps us improve our workplace. All responses are confidential.</p>
      </div>

      {error && (
        <div className="bg-red-900/50 border border-red-500 text-red-200 px-4 py-3 rounded-xl mb-6 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 mt-0.5 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      <div className="space-y-8">
        {sections.map(section => {
            const sectionQuestions = getQuestionsBySection(section.id);
            if (sectionQuestions.length === 0) return null;

            return (
                <div key={section.id} className="bg-gray-800 rounded-2xl p-6 border border-gray-700">
                    <h2 className="text-xl font-semibold text-white mb-1">{section.name}</h2>
                    {section.description && <p className="text-gray-400 text-sm mb-6">{section.description}</p>}
                    
                    <div className="space-y-8">
                        {sectionQuestions.map(q => (
                            <div key={q.id} className="border-b border-gray-700 last:border-0 pb-6 last:pb-0">
                                <p className="text-white mb-4 text-base">{q.text}</p>
                                <div className="flex flex-wrap gap-2 sm:gap-4 justify-between sm:justify-start">
                                    {[1, 2, 3, 4, 5].map(score => (
                                        <button
                                            key={score}
                                            onClick={() => handleScoreChange(q.id, score)}
                                            className={`
                                                w-10 h-10 sm:w-12 sm:h-12 rounded-full flex items-center justify-center text-sm font-medium transition-all
                                                ${answers[q.id] === score 
                                                    ? 'bg-blue-600 text-white shadow-lg scale-110' 
                                                    : 'bg-gray-700 text-gray-300 hover:bg-gray-600 hover:scale-105'
                                                }
                                            `}
                                        >
                                            {score}
                                        </button>
                                    ))}
                                </div>
                                <div className="flex justify-between text-xs text-gray-500 mt-2 px-1 max-w-sm">
                                    <span>Strongly Disagree</span>
                                    <span>Strongly Agree</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            );
        })}

        {/* Free Text Review */}
        <div className="bg-gray-800 rounded-2xl p-6 border border-gray-700">
            <h2 className="text-xl font-semibold text-white mb-2">Additional Feedback</h2>
            <p className="text-gray-400 text-sm mb-4">Please share any other thoughts or suggestions you have.</p>
            <textarea
                value={review}
                onChange={(e) => setReview(e.target.value)}
                className="w-full bg-gray-900 border border-gray-600 rounded-xl p-4 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors h-32"
                placeholder="Type your feedback here..."
            />
        </div>

        <div className="flex justify-end pt-4 pb-12">
            <button
                onClick={handleSubmit}
                disabled={submitting}
                className={`
                    px-8 py-4 bg-blue-600 text-white rounded-xl font-medium text-lg shadow-lg hover:bg-blue-700 transition-all transform hover:-translate-y-1
                    ${submitting ? 'opacity-70 cursor-not-allowed' : ''}
                `}
            >
                {submitting ? (
                    <span className="flex items-center gap-2">
                        <Loader2 className="w-5 h-5 animate-spin" />
                        Submitting...
                    </span>
                ) : (
                    'Submit Questionnaire'
                )}
            </button>
        </div>
      </div>
    </div>
  );
}

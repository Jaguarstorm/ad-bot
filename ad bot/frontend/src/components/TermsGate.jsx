import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { CheckCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';
import { api } from '../utils/api';
import toast from 'react-hot-toast';

const TermsGate = ({ onAgreed }) => {
  const [hasRead, setHasRead] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleAgree = async () => {
    if (!hasRead) {
      toast.error('Please read the terms and conditions first');
      return;
    }

    setIsSubmitting(true);
    try {
      await api.post('/auth/agree-terms');
      toast.success('Terms accepted successfully');
      onAgreed();
    } catch (error) {
      toast.error('Failed to accept terms. Please try again.');
      console.error('Terms agreement error:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 bg-black bg-opacity-90 z-50 flex items-center justify-center p-4"
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        className="bg-gray-800 rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden shadow-2xl"
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-purple-600 to-blue-600 p-6">
          <div className="flex items-center space-x-3">
            <ExclamationTriangleIcon className="h-8 w-8 text-white" />
            <div>
              <h1 className="text-2xl font-bold text-white">Terms & Conditions</h1>
              <p className="text-purple-100">AdForgeAI - Jaguar Storm</p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 max-h-[60vh] overflow-y-auto">
          <div className="space-y-6 text-gray-300">
            <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-4">
              <h2 className="text-lg font-semibold text-red-400 mb-2">
                ⚠️ Use at Your Own Risk
              </h2>
              <p className="text-sm">
                You acknowledge that any use of this application is done entirely at your own risk. 
                The developer (Jaguar Storm) holds <strong>zero responsibility</strong> for what you post, 
                how you use the app, or any consequences that arise from its use.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-white mb-3">This includes but is not limited to:</h3>
              <ul className="space-y-2 text-sm">
                <li className="flex items-start space-x-2">
                  <span className="text-red-400 mt-1">•</span>
                  <span>Platform bans or suspensions from social media sites</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="text-red-400 mt-1">•</span>
                  <span>Data loss or unauthorized access to your accounts</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="text-red-400 mt-1">•</span>
                  <span>Incorrect posting or scheduling errors</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="text-red-400 mt-1">•</span>
                  <span>Violation of other platform rules and guidelines</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="text-red-400 mt-1">•</span>
                  <span>Any financial losses or damages</span>
                </li>
              </ul>
            </div>

            <div className="bg-gray-700/50 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-white mb-2">No Warranties</h3>
              <p className="text-sm">
                This software is provided <strong>"as is"</strong> with <strong>no warranty</strong> of any kind. 
                You are responsible for securing your own login credentials and managing your own data.
              </p>
            </div>

            <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-blue-400 mb-2">Your Responsibilities</h3>
              <ul className="text-sm space-y-1">
                <li>• You are solely responsible for all content you create and post</li>
                <li>• You must comply with all platform terms of service</li>
                <li>• You are responsible for managing your own social media accounts</li>
                <li>• You must ensure you have proper rights to any content you use</li>
              </ul>
            </div>

            <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-green-400 mb-2">Privacy & Data</h3>
              <p className="text-sm">
                We implement encryption and security measures, but you acknowledge that no system is 100% secure. 
                Your OAuth tokens are encrypted and stored securely, but you remain responsible for your account security.
              </p>
            </div>

            <div className="text-center text-sm text-gray-400">
              <p>
                By clicking "I Agree and Understand", you accept the full 
                <strong> Privacy Policy</strong> and <strong>Terms & Conditions</strong> 
                and waive any claim against the developer.
              </p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="bg-gray-700 p-6 border-t border-gray-600">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <input
                type="checkbox"
                id="hasRead"
                checked={hasRead}
                onChange={(e) => setHasRead(e.target.checked)}
                className="w-5 h-5 text-purple-600 bg-gray-700 border-gray-500 rounded focus:ring-purple-500 focus:ring-2"
              />
              <label htmlFor="hasRead" className="text-sm text-gray-300">
                I have read and understand the terms and conditions
              </label>
            </div>

            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleAgree}
              disabled={!hasRead || isSubmitting}
              className={`
                flex items-center space-x-2 px-6 py-3 rounded-lg font-semibold transition-all duration-200
                ${hasRead && !isSubmitting
                  ? 'bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white shadow-lg'
                  : 'bg-gray-600 text-gray-400 cursor-not-allowed'
                }
              `}
            >
              {isSubmitting ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  <CheckCircleIcon className="h-5 w-5" />
                  <span>✅ I Agree and Understand</span>
                </>
              )}
            </motion.button>
          </div>
        </div>
      </motion.div>
    </motion.div>
  );
};

export default TermsGate; 
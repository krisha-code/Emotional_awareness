import React from 'react';
import { ShieldAlert, Smile, Frown, Angry, AlertCircle, Info, Zap, Camera, MessageSquare, Mic } from 'lucide-react';

export default function FusionResult({ result }) {
  if (!result) return null;

  const { fusedEmotion, severity, conflictDetected, modalities, xaiExplanation } = result;

  const getEmotionIcon = (emotion) => {
    switch (emotion?.toLowerCase()) {
      case 'happy':
      case 'joy':
        return <Smile size={48} className="text-green-500" />;
      case 'sad':
      case 'sadness':
        return <Frown size={48} className="text-blue-500" />;
      case 'angry':
      case 'anger':
        return <Angry size={48} className="text-red-500" />;
      default:
        return <Info size={48} className="text-indigo-500" />;
    }
  };

  const getSeverityBadge = (level) => {
    const levels = {
      Low: 'bg-green-100 text-green-800 border-green-200',
      Moderate: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      High: 'bg-orange-100 text-orange-800 border-orange-200',
      Critical: 'bg-red-100 text-red-800 border-red-200 animate-pulse',
    };
    
    return (
      <span className={`px-3 py-1 rounded-full text-xs font-bold border ${levels[level] || 'bg-gray-100 text-gray-800'}`}>
        {level} Severity
      </span>
    );
  };

  return (
    <div className="w-full bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden mb-8">
      {/* Header section with Fused Emotion */}
      <div className="p-6 bg-gradient-to-r from-indigo-50 to-white border-b border-gray-100">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-4">Analysis Result</h2>
        
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-6">
            <div className="bg-white p-4 rounded-xl shadow-sm border border-indigo-50">
              {getEmotionIcon(fusedEmotion)}
            </div>
            <div>
              <p className="text-sm text-gray-500 mb-1">Fused Emotion Profile</p>
              <h3 className="text-3xl font-bold text-gray-900 capitalize">{fusedEmotion || 'Unknown'}</h3>
            </div>
          </div>
          
          <div className="flex flex-col items-end gap-3">
            {severity && getSeverityBadge(severity)}
            {conflictDetected && (
              <div className="flex items-center gap-1.5 text-xs font-medium text-orange-600 bg-orange-50 px-2 py-1 rounded-md">
                <AlertCircle size={14} />
                <span>Modalities Conflict</span>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
          <Zap size={20} className="text-indigo-600" />
          Modality Breakdown
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          {/* Face */}
          <div className="p-4 rounded-xl bg-gray-50 border border-gray-100 flex flex-col items-center text-center">
            <Camera size={24} className="text-gray-400 mb-2" />
            <span className="text-xs text-gray-500 uppercase tracking-wide font-semibold">Face</span>
            <span className="text-lg font-bold text-gray-800 capitalize mt-1">
              {modalities?.face?.emotion || 'N/A'}
            </span>
            <span className="text-xs text-gray-400 mt-1">Confidence: {modalities?.face?.confidence || '0%'}</span>
          </div>
          
          {/* Text */}
          <div className="p-4 rounded-xl bg-gray-50 border border-gray-100 flex flex-col items-center text-center">
            <MessageSquare size={24} className="text-gray-400 mb-2" />
            <span className="text-xs text-gray-500 uppercase tracking-wide font-semibold">Text</span>
            <span className="text-lg font-bold text-gray-800 capitalize mt-1">
              {modalities?.text?.emotion || 'N/A'}
            </span>
            <span className="text-xs text-gray-400 mt-1">Confidence: {modalities?.text?.confidence || '0%'}</span>
          </div>
          
          {/* Audio */}
          <div className="p-4 rounded-xl bg-gray-50 border border-gray-100 flex flex-col items-center text-center">
            <Mic size={24} className="text-gray-400 mb-2" />
            <span className="text-xs text-gray-500 uppercase tracking-wide font-semibold">Speech</span>
            <span className="text-lg font-bold text-gray-800 capitalize mt-1">
              {modalities?.audio?.emotion || 'N/A'}
            </span>
            <span className="text-xs text-gray-400 mt-1">Confidence: {modalities?.audio?.confidence || '0%'}</span>
          </div>
        </div>

        {/* XAI Explanation */}
        {xaiExplanation && (
          <div className="bg-blue-50 border border-blue-100 rounded-xl p-5">
            <h4 className="text-sm font-semibold text-blue-900 mb-2 flex items-center gap-2">
              <ShieldAlert size={16} />
              AI Explanation (XAI)
            </h4>
            <p className="text-sm text-blue-800 leading-relaxed">
              {xaiExplanation}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

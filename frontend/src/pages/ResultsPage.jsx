import React, { useEffect } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { Activity, ShieldAlert, CheckCircle, AlertTriangle, ArrowLeft, Download, RefreshCw, FileText, Mic, Camera, Brain, Heart, Sparkles } from 'lucide-react';
import toast from 'react-hot-toast';

export default function ResultsPage() {
  const location = useLocation();
  const navigate = useNavigate();

  // Retrieve result from navigation state or fallback to localStorage
  const stateData = location.state || {};
  let result = stateData.result;
  let inputs = stateData.inputs || {};

  if (!result) {
    try {
      const stored = localStorage.getItem('last_fusion_result');
      if (stored) {
        const parsed = JSON.parse(stored);
        result = parsed.result;
        inputs = parsed.inputs || {};
      }
    } catch (e) {
      console.error('Error loading stored result', e);
    }
  }

  useEffect(() => {
    if (result) {
      // Save history record automatically
      try {
        const historyList = JSON.parse(localStorage.getItem('emotion_history') || '[]');
        const newRecord = {
          id: 'rec-' + Date.now(),
          timestamp: new Date().toISOString(),
          fusedEmotion: result.fusedEmotion,
          severity: result.severity,
          confidence: result.confidence || '94%',
          conflictDetected: result.conflictDetected || false,
          modalities: result.modalities || {}
        };
        // Avoid duplicate saves within 5 seconds
        if (!historyList.length || (Date.now() - new Date(historyList[0].timestamp).getTime() > 5000)) {
          historyList.unshift(newRecord);
          localStorage.setItem('emotion_history', JSON.stringify(historyList.slice(0, 50)));
        }
      } catch (e) {
        console.error('Failed to save to history', e);
      }
    }
  }, [result]);

  if (!result) {
    return (
      <div className="max-w-4xl mx-auto p-8 text-center glass-card border border-[rgba(255,255,255,0.12)] my-12">
        <div className="w-16 h-16 bg-[rgba(108,99,255,0.2)] text-[#6C63FF] rounded-full flex items-center justify-center mx-auto mb-4">
          <Activity size={32} />
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">No Recent Analysis Found</h2>
        <p className="text-[#8888AA] mb-6">
          You haven't run a multimodal AI fusion check-in yet, or your previous session expired.
        </p>
        <Link
          to="/analyze"
          className="inline-flex items-center gap-2 px-8 py-3.5 bg-gradient-to-r from-[#6C63FF] to-[#4fc3f7] text-white font-bold rounded-xl hover:brightness-110 transition-all shadow-[0_4px_20px_rgba(108,99,255,0.4)]"
        >
          <ArrowLeft size={18} />
          Go to Multi-Modal Capture Page
        </Link>
      </div>
    );
  }

  // Determine theme colors based on fused emotion and severity
  const getThemeConfig = (emotion = '', severity = 'Low') => {
    const e = emotion.toLowerCase();
    if (severity === 'Critical' || e.includes('crisis') || e.includes('hopeless')) {
      return {
        bgGradient: 'from-red-600/30 via-red-900/20 to-[#0a0a0f]',
        borderClass: 'border-red-500/60 shadow-[0_0_50px_rgba(255,71,87,0.3)]',
        badgeColor: 'bg-red-500/20 text-red-400 border-red-500/40',
        textColor: 'text-red-400',
        ringColor: '#FF4757',
        icon: <ShieldAlert size={40} className="text-red-500 animate-pulse" />
      };
    }
    if (e.includes('happy') || e.includes('joy') || e.includes('excited') || e.includes('positive')) {
      return {
        bgGradient: 'from-green-500/25 via-emerald-900/15 to-[#0a0a0f]',
        borderClass: 'border-green-500/50 shadow-[0_0_50px_rgba(67,233,123,0.25)]',
        badgeColor: 'bg-green-500/20 text-green-300 border-green-500/40',
        textColor: 'text-[#43E97B]',
        ringColor: '#43E97B',
        icon: <Sparkles size={40} className="text-[#43E97B]" />
      };
    }
    if (e.includes('anxious') || e.includes('stress') || e.includes('fear') || e.includes('overwhelmed') || severity === 'High') {
      return {
        bgGradient: 'from-amber-500/25 via-orange-900/15 to-[#0a0a0f]',
        borderClass: 'border-amber-500/50 shadow-[0_0_50px_rgba(255,184,0,0.25)]',
        badgeColor: 'bg-amber-500/20 text-amber-300 border-amber-500/40',
        textColor: 'text-amber-400',
        ringColor: '#FFB800',
        icon: <AlertTriangle size={40} className="text-amber-400 animate-bounce" />
      };
    }
    if (e.includes('sad') || e.includes('depress') || e.includes('melancholy') || e.includes('lonely')) {
      return {
        bgGradient: 'from-purple-600/30 via-indigo-900/20 to-[#0a0a0f]',
        borderClass: 'border-purple-500/50 shadow-[0_0_50px_rgba(108,99,255,0.3)]',
        badgeColor: 'bg-purple-500/20 text-purple-300 border-purple-500/40',
        textColor: 'text-[#9c88ff]',
        ringColor: '#6C63FF',
        icon: <Heart size={40} className="text-[#9c88ff]" />
      };
    }
    return {
      bgGradient: 'from-blue-600/25 via-cyan-900/15 to-[#0a0a0f]',
      borderClass: 'border-cyan-500/50 shadow-[0_0_50px_rgba(0,242,254,0.25)]',
      badgeColor: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40',
      textColor: 'text-cyan-400',
      ringColor: '#00F2FE',
      icon: <Brain size={40} className="text-cyan-400" />
    };
  };

  const theme = getThemeConfig(result.fusedEmotion, result.severity);

  const handleDownloadReport = () => {
    toast.success('Generating Full Clinical PDF / JSON Report...');
    const reportObj = {
      timestamp: new Date().toLocaleString(),
      diagnosis: result.fusedEmotion,
      confidence: result.confidence || '94%',
      severityTier: result.severity,
      conflictDetected: result.conflictDetected,
      xaiReasoning: result.xaiExplanation || 'Modalities converged on consistent emotional valence.',
      modalities: result.modalities
    };
    const blob = new Blob([JSON.stringify(reportObj, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `MindSense_Report_${result.fusedEmotion}_${Date.now()}.json`;
    a.click();
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-fade-in pb-16">
      {/* Top Header Back Button */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => navigate('/analyze')}
          className="flex items-center gap-2 text-sm font-bold text-[#8888AA] hover:text-white transition-colors bg-[rgba(255,255,255,0.05)] px-4 py-2.5 rounded-xl border border-[rgba(255,255,255,0.1)]"
        >
          <ArrowLeft size={18} />
          Back to Capture Page
        </button>
        <span className="text-xs text-[#8888AA] font-mono">
          Analysis ID: #{Math.floor(100000 + Math.random() * 900000)}
        </span>
      </div>

      {/* Hero Holistic Diagnosis Card */}
      <div className={`p-8 sm:p-12 rounded-3xl bg-gradient-to-br ${theme.bgGradient} border ${theme.borderClass} flex flex-col md:flex-row items-center justify-between gap-8 relative overflow-hidden`}>
        <div className="flex flex-col items-center md:items-start text-center md:text-left z-10 max-w-xl">
          <div className="flex items-center gap-3 mb-4 flex-wrap justify-center md:justify-start">
            <span className={`px-4 py-1.5 rounded-full text-xs font-bold border uppercase tracking-wider ${theme.badgeColor}`}>
              Severity Tier: {result.severity}
            </span>
            {result.conflictDetected && (
              <span className="px-3 py-1.5 rounded-full text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 flex items-center gap-1.5">
                <AlertTriangle size={14} /> Modality Conflict Masking
              </span>
            )}
          </div>

          <h1 className="text-4xl sm:text-5xl font-black text-white tracking-tight mb-4 capitalize flex items-center gap-4">
            {theme.icon}
            <span>{result.fusedEmotion}</span>
          </h1>

          <p className="text-[#dcdce6] text-base sm:text-lg leading-relaxed mb-6 font-medium">
            {result.xaiExplanation || "Our multimodal fusion neural network cross-analyzed your facial expressions, vocal tone changes, and linguistic semantics to formulate this holistic assessment."}
          </p>

          <div className="flex flex-wrap gap-4">
            <button
              onClick={handleDownloadReport}
              className="flex items-center gap-2 px-6 py-3 bg-white text-black font-extrabold rounded-xl hover:bg-gray-200 transition-all shadow-lg"
            >
              <Download size={18} />
              Export Clinical Report
            </button>
            <Link
              to="/journal"
              className="flex items-center gap-2 px-6 py-3 bg-[rgba(255,255,255,0.1)] text-white font-bold rounded-xl hover:bg-[rgba(255,255,255,0.2)] transition-all border border-[rgba(255,255,255,0.2)]"
            >
              <FileText size={18} />
              View Journal & History
            </Link>
          </div>
        </div>

        {/* Confidence Gauge Box */}
        <div className="flex flex-col items-center justify-center p-6 bg-[#0a0a0f]/80 rounded-2xl border border-[rgba(255,255,255,0.15)] shadow-2xl z-10 min-w-[220px]">
          <div className="relative w-36 h-36 flex items-center justify-center mb-3">
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="42" stroke="rgba(255,255,255,0.1)" strokeWidth="10" fill="transparent" />
              <circle
                cx="50" cy="50" r="42"
                stroke={theme.ringColor}
                strokeWidth="10"
                strokeDasharray="264"
                strokeDashoffset={264 - (264 * parseInt(result.confidence || '92%')) / 100}
                strokeLinecap="round"
                fill="transparent"
                className="transition-all duration-1000 ease-out"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-3xl font-black text-white font-mono">{result.confidence || '94%'}</span>
              <span className="text-[10px] text-[#8888AA] uppercase font-bold tracking-widest mt-0.5">Confidence</span>
            </div>
          </div>
          <span className="text-xs font-semibold text-[#8888AA]">Multi-Modal Consensus</span>
        </div>
      </div>

      {/* Modality Breakdown Section */}
      <div>
        <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2.5">
          <Activity size={24} className="text-[#6C63FF]" />
          Individual Modality Breakdown
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Face Box */}
          <div className="glass-card p-6 flex flex-col justify-between border border-[rgba(255,255,255,0.1)] hover:border-[rgba(108,99,255,0.4)] transition-all">
            <div>
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-[rgba(255,255,255,0.08)]">
                <span className="font-bold text-white flex items-center gap-2">
                  <Camera size={18} className="text-[#6C63FF]" />
                  Facial / Video
                </span>
                <span className="text-xs font-mono bg-[rgba(255,255,255,0.08)] px-2.5 py-1 rounded text-[#8888AA]">
                  Weight: 45%
                </span>
              </div>
              <p className="text-sm text-[#8888AA] mb-4 leading-relaxed">
                Visual micro-expressions and muscle tension around eyes and jawline.
              </p>
            </div>
            <div className="mt-auto pt-3 bg-[#0d0d14] p-4 rounded-xl border border-[rgba(255,255,255,0.06)] flex items-center justify-between">
              <div>
                <span className="text-xs text-[#8888AA] block uppercase font-semibold">Detected Emotion</span>
                <span className="text-lg font-bold text-white capitalize">{result.modalities?.face?.emotion || 'Neutral'}</span>
              </div>
              <span className="badge badge-low bg-indigo-500/20 text-indigo-300 font-mono">
                {result.modalities?.face?.confidence || '88%'}
              </span>
            </div>
          </div>

          {/* Voice Box */}
          <div className="glass-card p-6 flex flex-col justify-between border border-[rgba(255,255,255,0.1)] hover:border-[rgba(108,99,255,0.4)] transition-all">
            <div>
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-[rgba(255,255,255,0.08)]">
                <span className="font-bold text-white flex items-center gap-2">
                  <Mic size={18} className="text-[#43E97B]" />
                  Vocal Tone
                </span>
                <span className="text-xs font-mono bg-[rgba(255,255,255,0.08)] px-2.5 py-1 rounded text-[#8888AA]">
                  Weight: 30%
                </span>
              </div>
              <p className="text-sm text-[#8888AA] mb-4 leading-relaxed">
                Acoustic pitch jitter, speaking cadence variations, and energy modulation.
              </p>
            </div>
            <div className="mt-auto pt-3 bg-[#0d0d14] p-4 rounded-xl border border-[rgba(255,255,255,0.06)] flex items-center justify-between">
              <div>
                <span className="text-xs text-[#8888AA] block uppercase font-semibold">Detected Tone</span>
                <span className="text-lg font-bold text-white capitalize">{result.modalities?.audio?.emotion || 'Calm'}</span>
              </div>
              <span className="badge badge-low bg-green-500/20 text-green-300 font-mono">
                {result.modalities?.audio?.confidence || '82%'}
              </span>
            </div>
          </div>

          {/* Text Box */}
          <div className="glass-card p-6 flex flex-col justify-between border border-[rgba(255,255,255,0.1)] hover:border-[rgba(108,99,255,0.4)] transition-all">
            <div>
              <div className="flex items-center justify-between mb-4 pb-3 border-b border-[rgba(255,255,255,0.08)]">
                <span className="font-bold text-white flex items-center gap-2">
                  <FileText size={18} className="text-[#FF6584]" />
                  Linguistic Semantics
                </span>
                <span className="text-xs font-mono bg-[rgba(255,255,255,0.08)] px-2.5 py-1 rounded text-[#8888AA]">
                  Weight: 25%
                </span>
              </div>
              <p className="text-sm text-[#8888AA] mb-4 leading-relaxed">
                Contextual sentiment, lexical intensity, and emotional word choice.
              </p>
            </div>
            <div className="mt-auto pt-3 bg-[#0d0d14] p-4 rounded-xl border border-[rgba(255,255,255,0.06)] flex items-center justify-between">
              <div>
                <span className="text-xs text-[#8888AA] block uppercase font-semibold">Detected Semantics</span>
                <span className="text-lg font-bold text-white capitalize">{result.modalities?.text?.emotion || 'Positive'}</span>
              </div>
              <span className="badge badge-low bg-pink-500/20 text-pink-300 font-mono">
                {result.modalities?.text?.confidence || '95%'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Tailored Clinical & Actionable Recommendations Card */}
      <div className="glass-card p-8 border border-[rgba(255,255,255,0.12)]">
        <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
          <Brain size={22} className="text-[#6C63FF]" />
          Personalized Actionable Recommendations
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-4">
          <div className="p-5 rounded-2xl bg-[rgba(255,255,255,0.03)] border border-[rgba(255,255,255,0.08)]">
            <h4 className="font-bold text-white mb-2 flex items-center gap-2 text-base">
              <CheckCircle size={18} className="text-[#43E97B]" />
              Immediate Regulation Strategy
            </h4>
            <p className="text-sm text-[#8888AA] leading-relaxed">
              {result.severity === 'Critical' ? (
                "Please connect immediately with our 24/7 Crisis Support team via the Emergency Help button on the bottom right. Take slow, deliberate 4-7-8 breaths while help is arranged."
              ) : result.severity === 'High' || result.fusedEmotion.toLowerCase().includes('anx') || result.fusedEmotion.toLowerCase().includes('stress') ? (
                "Engage the physiological sigh: Take two quick inhalations through the nose, followed by a long, slow exhalation through the mouth. Repeat 4 times to immediately reset autonomic nervous arousal."
              ) : result.fusedEmotion.toLowerCase().includes('sad') || result.fusedEmotion.toLowerCase().includes('depress') ? (
                "Try gentle behavioral activation: Step outside into natural sunlight for 10 minutes or play a familiar comforting instrumental song to stimulate dopamine release."
              ) : (
                "Your emotional balance is healthy right now! Capitalize on this positive state by focusing on high-creativity tasks or sharing appreciation with a peer or loved one."
              )}
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-[rgba(255,255,255,0.03)] border border-[rgba(255,255,255,0.08)]">
            <h4 className="font-bold text-white mb-2 flex items-center gap-2 text-base">
              <RefreshCw size={18} className="text-[#6C63FF]" />
              Longitudinal Wellness Tip
            </h4>
            <p className="text-sm text-[#8888AA] leading-relaxed">
              Consistent multi-modal check-ins enable MindSense to map how your vocal cadence and facial tension fluctuate before emotional burnout occurs. Schedule your next check-in tomorrow morning.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

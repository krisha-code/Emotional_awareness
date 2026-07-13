import React from 'react';
import { Link } from 'react-router-dom';
import { Brain, Sparkles, Shield, Activity } from 'lucide-react';

export default function Home() {
  return (
    <div className="flex flex-col items-center max-w-5xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
      {/* Hero Section */}
      <div className="text-center w-full max-w-3xl mb-16">
        <div className="inline-flex items-center justify-center p-3 bg-indigo-100 rounded-full mb-6 text-indigo-600">
          <Brain size={48} />
        </div>
        <h1 className="text-4xl sm:text-5xl font-extrabold text-white tracking-tight mb-6">
          Understand Your Emotions <br className="hidden sm:block" />
          <span className="text-[#6C63FF]">With Multimodal AI</span>
        </h1>
        <p className="text-xl text-[#8888AA] mb-8 leading-relaxed">
          MindSense analyzes your facial expressions, voice tone, and words to provide a holistic view of your emotional well-being.
        </p>
        <Link 
          to="/analyze" 
          className="inline-flex items-center justify-center gap-2 px-8 py-4 text-lg font-bold text-white bg-[#6C63FF] rounded-full hover:bg-[#5a52e0] transition-all shadow-lg hover:shadow-[0_0_24px_rgba(108,99,255,0.5)] transform hover:-translate-y-1"
        >
          <Sparkles size={24} />
          Start Analysis
        </Link>
      </div>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 w-full mt-8">
        <div className="glass-card p-8 flex flex-col items-center text-center">
          <div className="w-12 h-12 bg-blue-500/20 text-blue-400 rounded-xl flex items-center justify-center mb-4">
            <Activity size={24} />
          </div>
          <h3 className="text-xl font-bold text-white mb-3">Multimodal Fusion</h3>
          <p className="text-[#8888AA]">
            Combines data from multiple sources (face, speech, text) for highly accurate emotion detection.
          </p>
        </div>

        <div className="glass-card p-8 flex flex-col items-center text-center">
          <div className="w-12 h-12 bg-green-500/20 text-green-400 rounded-xl flex items-center justify-center mb-4">
            <Shield size={24} />
          </div>
          <h3 className="text-xl font-bold text-white mb-3">Crisis Detection</h3>
          <p className="text-[#8888AA]">
            Proactive alerts for potential crises, ensuring timely support and interventions when needed most.
          </p>
        </div>

        <div className="glass-card p-8 flex flex-col items-center text-center">
          <div className="w-12 h-12 bg-purple-500/20 text-purple-400 rounded-xl flex items-center justify-center mb-4">
            <Brain size={24} />
          </div>
          <h3 className="text-xl font-bold text-white mb-3">Explainable AI</h3>
          <p className="text-[#8888AA]">
            Understand why the system reached its conclusion with transparent XAI explanations.
          </p>
        </div>
      </div>
    </div>
  );
}

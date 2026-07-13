import React, { useState } from 'react';
import { Send, AlertTriangle, MessageSquare } from 'lucide-react';

export default function TextInput({ onTextChange, onCapture, result, onSubmit, disabled }) {
  const [text, setText] = useState('');
  const maxLength = 500;

  const handleChange = (e) => {
    const newText = e.target.value;
    if (newText.length <= maxLength) {
      setText(newText);
      if (onTextChange) {
        onTextChange(newText);
      }
      if (onCapture) {
        onCapture(newText);
      }
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (text.trim()) {
      if (onSubmit) onSubmit(text);
      if (onCapture) onCapture(text);
      if (onTextChange) onTextChange(text);
    }
  };

  return (
    <div className="flex flex-col w-full glass-card p-6 border border-[rgba(255,255,255,0.12)] hover:border-[rgba(108,99,255,0.4)] transition-all">
      <div className="flex items-center justify-between w-full mb-4 border-b border-[rgba(255,255,255,0.08)] pb-3">
        <h3 className="text-lg font-bold text-white flex items-center gap-2.5">
          <MessageSquare size={20} className="text-[#6C63FF]" />
          Text Emotion Analysis
        </h3>
        {text.trim().length > 0 ? (
          <span className="badge badge-low bg-green-500/20 text-green-300 border-green-500/40">
            ✓ Text Entered
          </span>
        ) : (
          <span className="badge badge-neutral text-xs">Waiting for Text</span>
        )}
      </div>

      {result && result.sarcasmDetected && (
        <div className="mb-4 p-3.5 bg-amber-500/20 border border-amber-500/40 text-amber-200 rounded-xl flex items-start gap-3 text-sm shadow-md" role="alert">
          <AlertTriangle size={20} className="mt-0.5 flex-shrink-0 text-amber-400" />
          <div>
            <span className="font-bold block">Sarcasm Detected</span>
            <span className="block mt-1 text-xs">The literal meaning may differ from the emotional undertone.</span>
          </div>
        </div>
      )}

      {result && result.crisisDetected && (
        <div className="mb-4 p-3.5 bg-red-500/20 border border-red-500/40 text-red-200 rounded-xl flex items-start gap-3 text-sm shadow-md animate-pulse" role="alert">
          <AlertTriangle size={20} className="mt-0.5 flex-shrink-0 text-red-400" />
          <div>
            <span className="font-bold block">Crisis Alert</span>
            <span className="block mt-1 text-xs">Distressing content detected. If you need urgent support, please reach out to emergency services or a crisis helpline right away.</span>
          </div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex flex-col flex-1">
        <div className="relative flex-1 flex flex-col mb-4">
          <textarea
            value={text}
            onChange={handleChange}
            placeholder="Type or paste what's on your mind... (e.g. 'I felt really overwhelmed at work today, but talking to my friend helped relax me.')"
            className="w-full flex-1 min-h-[170px] p-4 input-field resize-none rounded-xl text-white font-sans leading-relaxed"
            aria-label="Text emotion input"
            disabled={disabled}
          />
          <div className="absolute bottom-3 right-3 text-xs text-[#8888AA] bg-[#12121c]/90 px-2 py-1 rounded-md border border-[rgba(255,255,255,0.08)]">
            {text.length}/{maxLength} chars
          </div>
        </div>

        <div className="flex flex-col gap-3 mt-auto">
          <button
            type="button"
            onClick={() => {
              if (onTextChange) onTextChange(text);
              if (onCapture) onCapture(text);
              if (onSubmit) onSubmit(text);
              const btn = document.getElementById('run-analysis-btn');
              if (btn) btn.scrollIntoView({ behavior: 'smooth' });
            }}
            disabled={disabled || text.trim().length === 0}
            className="w-full flex items-center justify-center gap-2 py-3 px-4 bg-gradient-to-r from-[#6C63FF] to-[#4fc3f7] text-white rounded-xl font-bold hover:brightness-110 disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-[0_4px_15px_rgba(108,99,255,0.35)]"
          >
            <Send size={18} />
            Confirm & Use Text →
          </button>
        </div>
      </form>

      {result && result.modalities && result.modalities.text && (
        <div className="mt-4 p-3.5 w-full bg-[rgba(108,99,255,0.15)] text-white border border-[rgba(108,99,255,0.3)] rounded-xl text-sm flex justify-between items-center">
          <span className="font-semibold text-[#8888AA]">Detected Text Emotion:</span>
          <span className="font-bold capitalize bg-[#6C63FF] px-3 py-1 rounded-full text-white shadow-md">{result.modalities.text.emotion} ({result.modalities.text.confidence})</span>
        </div>
      )}
    </div>
  );
}


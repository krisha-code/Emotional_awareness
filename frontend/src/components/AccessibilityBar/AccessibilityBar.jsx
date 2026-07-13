import React, { useState } from 'react';
import { Mic, Volume2, Vibrate, Type, Moon, HelpCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import CrisisPanel from '../CrisisPanel';

const AccessibilityBar = () => {
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [hapticEnabled, setHapticEnabled] = useState(true);
  const [isCrisisOpen, setIsCrisisOpen] = useState(false);
  
  // For the demo we just toggle state, real implementation would call the accessibility/ hooks
  const toggleVoice = () => {
    setVoiceEnabled(!voiceEnabled);
    if (!voiceEnabled) {
      window.speechSynthesis.speak(new SpeechSynthesisUtterance("Voice commands activated. Say 'Help' for options."));
    }
  };

  return (
    <>
      <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40" role="region" aria-label="Accessibility Controls">
        <div className="glass-card flex items-center gap-2 p-2 rounded-full shadow-2xl border border-[rgba(255,255,255,0.1)] backdrop-blur-xl">
          
          <button 
            onClick={toggleVoice}
            className={`p-3 rounded-full transition-colors flex items-center justify-center relative ${voiceEnabled ? 'bg-[rgba(108,99,255,0.2)] text-[#6C63FF]' : 'hover:bg-[rgba(255,255,255,0.1)] text-[#8888AA]'}`}
            aria-pressed={voiceEnabled}
            aria-label="Toggle Voice Commands"
            title="Voice Commands"
          >
            <Mic size={20} />
            {voiceEnabled && (
              <span className="absolute top-1 right-1 w-2 h-2 rounded-full bg-[#43E97B] animate-pulse"></span>
            )}
          </button>
          
          <div className="w-px h-6 bg-[rgba(255,255,255,0.1)] mx-1"></div>
          
          <button 
            onClick={() => setAudioEnabled(!audioEnabled)}
            className={`p-3 rounded-full transition-colors ${audioEnabled ? 'bg-[rgba(108,99,255,0.2)] text-[#6C63FF]' : 'hover:bg-[rgba(255,255,255,0.1)] text-[#8888AA]'}`}
            aria-pressed={audioEnabled}
            aria-label="Toggle Audio Feedback"
            title="Audio Earcons"
          >
            <Volume2 size={20} />
          </button>
          
          <button 
            onClick={() => setHapticEnabled(!hapticEnabled)}
            className={`p-3 rounded-full transition-colors ${hapticEnabled ? 'bg-[rgba(108,99,255,0.2)] text-[#6C63FF]' : 'hover:bg-[rgba(255,255,255,0.1)] text-[#8888AA]'}`}
            aria-pressed={hapticEnabled}
            aria-label="Toggle Haptic Feedback"
            title="Haptic Alerts"
          >
            <Vibrate size={20} />
          </button>
          
          <div className="w-px h-6 bg-[rgba(255,255,255,0.1)] mx-1"></div>
          
          <button 
            onClick={() => setIsCrisisOpen(true)}
            className="p-3 pr-4 rounded-full bg-[rgba(255,71,87,0.1)] text-[#FF4757] hover:bg-[#FF4757] hover:text-white transition-colors flex items-center gap-2 font-bold ml-1"
            aria-label="Open Crisis Help"
          >
            <HelpCircle size={20} />
            <span className="hidden sm:inline">Crisis Help</span>
          </button>
          
        </div>
      </div>
      
      <CrisisPanel isOpen={isCrisisOpen} onClose={() => setIsCrisisOpen(false)} />
    </>
  );
};

export default AccessibilityBar;

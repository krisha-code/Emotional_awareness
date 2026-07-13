import React, { useEffect, useState } from 'react';
import { Phone, Heart, AlertTriangle, X, Link as LinkIcon, Info } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const RESOURCES = [
  { name: 'National Suicide Prevention Lifeline', phone: '988', desc: 'Available 24/7 in English and Spanish (US)', type: 'phone' },
  { name: 'Crisis Text Line', phone: 'Text HOME to 741741', desc: 'Connect with a volunteer Crisis Counselor 24/7 (US/UK/Canada)', type: 'text' },
  { name: 'iCall (India)', phone: '9152987821', desc: 'Professional counseling via telephone and email (India)', type: 'phone' },
  { name: 'Vandrevala Foundation', phone: '1860-2662-345', desc: 'Mental health crisis intervention (India)', type: 'phone' },
  { name: 'NHS Mental Health (UK)', phone: '111', desc: 'NHS 111 mental health services', type: 'phone' },
  { name: 'Find A Helpline', link: 'https://findahelpline.com/', desc: 'Search for crisis support by country', type: 'link' }
];

const CrisisPanel = ({ isOpen, onClose, allowClose = true }) => {
  const [phase, setPhase] = useState(0); // For breathing widget

  useEffect(() => {
    let interval;
    if (isOpen) {
      // Breathing animation: 4s inhale, 7s hold, 8s exhale
      const runBreathing = () => {
        setPhase(1); // Inhale
        setTimeout(() => {
          setPhase(2); // Hold
          setTimeout(() => {
            setPhase(3); // Exhale
          }, 7000);
        }, 4000);
      };
      
      runBreathing();
      interval = setInterval(runBreathing, 19000);
      
      // Auto-announce for screen readers
      const utterance = new SpeechSynthesisUtterance("Crisis support panel opened. You are not alone. Help is available.");
      window.speechSynthesis.speak(utterance);
    }
    return () => clearInterval(interval);
  }, [isOpen]);

  const handleClose = () => {
    if (!allowClose) return;
    if (window.confirm("Are you sure you want to close the crisis resources?")) {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-8 bg-black/90 backdrop-blur-xl overflow-y-auto"
        role="dialog"
        aria-modal="true"
        aria-labelledby="crisis-title"
      >
        <div className="w-full max-w-5xl mx-auto flex flex-col lg:flex-row gap-8 relative min-h-[80vh] items-stretch">
          
          {allowClose && (
            <button 
              onClick={handleClose}
              className="absolute top-0 right-0 p-4 text-[#8888AA] hover:text-white z-10"
              aria-label="Close crisis panel"
            >
              <X size={32} />
            </button>
          )}

          {/* Left Column: Resources */}
          <div className="flex-1 flex flex-col border border-[rgba(255,255,255,0.1)] rounded-3xl bg-[rgba(255,0,0,0.05)] overflow-hidden">
            <div className="bg-[#FF4757] text-white p-8">
              <h2 id="crisis-title" className="text-3xl font-bold mb-2 flex items-center gap-3">
                <AlertTriangle size={36} /> You're not alone.
              </h2>
              <p className="text-lg opacity-90">Help is available right now. Please reach out to one of these free, confidential resources.</p>
            </div>
            
            <div className="p-8 flex-1 overflow-y-auto" role="list">
              {RESOURCES.map((r, idx) => (
                <div key={idx} className="mb-6 last:mb-0 p-4 border border-[rgba(255,255,255,0.1)] bg-[rgba(255,255,255,0.02)] rounded-xl hover:bg-[rgba(255,255,255,0.05)] transition-colors" role="listitem">
                  <h3 className="text-xl font-bold text-[#F0F0FF] mb-1">{r.name}</h3>
                  <p className="text-sm text-[#8888AA] mb-4">{r.desc}</p>
                  
                  {r.type === 'phone' && (
                    <a href={`tel:${r.phone.replace(/\D/g,'')}`} className="btn btn-primary bg-[#FF4757] hover:bg-[#ff2e43] border-none flex items-center gap-2 inline-flex w-full sm:w-auto justify-center">
                      <Phone size={18} /> {r.phone}
                    </a>
                  )}
                  {r.type === 'text' && (
                    <div className="btn bg-white text-black font-bold flex items-center gap-2 inline-flex w-full sm:w-auto justify-center cursor-default">
                      <Info size={18} /> {r.phone}
                    </div>
                  )}
                  {r.type === 'link' && (
                    <a href={r.link} target="_blank" rel="noreferrer" className="btn btn-secondary flex items-center gap-2 inline-flex w-full sm:w-auto justify-center">
                      <LinkIcon size={18} /> Visit Website
                    </a>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Right Column: Grounding Exercise */}
          <div className="flex-1 flex flex-col justify-center items-center p-8 border border-[rgba(255,255,255,0.1)] rounded-3xl bg-[rgba(255,255,255,0.02)]">
            <h3 className="text-2xl font-semibold mb-2">Grounding Exercise</h3>
            <p className="text-[#8888AA] text-center mb-12">Breathe in sync with the circle. Focus only on the movement.</p>
            
            <div className="relative w-64 h-64 flex items-center justify-center">
              <motion.div 
                className="absolute w-12 h-12 bg-[#6C63FF] rounded-full blur-sm opacity-50"
                animate={
                  phase === 1 ? { scale: 5, opacity: 0.8 } : 
                  phase === 2 ? { scale: 5, opacity: 0.8 } : 
                  { scale: 1, opacity: 0.5 }
                }
                transition={{
                  duration: phase === 1 ? 4 : phase === 2 ? 7 : 8,
                  ease: "easeInOut"
                }}
              />
              <motion.div 
                className="relative z-10 w-24 h-24 bg-gradient-to-tr from-[#6C63FF] to-[#43E97B] rounded-full shadow-[0_0_40px_rgba(108,99,255,0.5)] flex items-center justify-center text-white font-bold text-xl"
                animate={
                  phase === 1 ? { scale: 2.2 } : 
                  phase === 2 ? { scale: 2.2 } : 
                  { scale: 1 }
                }
                transition={{
                  duration: phase === 1 ? 4 : phase === 2 ? 7 : 8,
                  ease: "easeInOut"
                }}
              >
                <motion.span
                  key={phase}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="absolute"
                >
                  {phase === 1 ? 'Inhale' : phase === 2 ? 'Hold' : 'Exhale'}
                </motion.span>
              </motion.div>
            </div>
            
            <div className="mt-16 text-center text-[#8888AA] max-w-sm">
              <Heart size={24} className="mx-auto mb-4 text-[#FF6584] opacity-50" />
              <p>This feeling will pass. Focus on your breath. Keep yourself safe.</p>
            </div>
          </div>
          
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export default CrisisPanel;

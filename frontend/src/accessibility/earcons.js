let audioCtx = null;
let enabled = true;

const initAudio = () => {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  }
  if (audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
};

export const setEarconsEnabled = (val) => {
  enabled = val;
};

// Play a short distinct synthesized tone for different emotions
export const playEarcon = (emotion) => {
  if (!enabled) return;
  initAudio();
  
  const osc = audioCtx.createOscillator();
  const gain = audioCtx.createGain();
  
  osc.connect(gain);
  gain.connect(audioCtx.destination);
  
  const now = audioCtx.currentTime;
  
  switch (emotion?.toLowerCase()) {
    case 'happy':
    case 'joy':
      // Bright major chord arpeggio (C5 - E5 - G5)
      osc.type = 'sine';
      osc.frequency.setValueAtTime(523.25, now);
      osc.frequency.setValueAtTime(659.25, now + 0.1);
      osc.frequency.setValueAtTime(783.99, now + 0.2);
      gain.gain.setValueAtTime(0, now);
      gain.gain.linearRampToValueAtTime(0.3, now + 0.05);
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.4);
      osc.start(now);
      osc.stop(now + 0.4);
      break;
      
    case 'sad':
    case 'sadness':
      // Descending minor interval
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(440, now); // A4
      osc.frequency.linearRampToValueAtTime(349.23, now + 0.5); // F4
      gain.gain.setValueAtTime(0, now);
      gain.gain.linearRampToValueAtTime(0.2, now + 0.1);
      gain.gain.linearRampToValueAtTime(0.01, now + 0.6);
      osc.start(now);
      osc.stop(now + 0.6);
      break;
      
    case 'angry':
    case 'anger':
      // Sharp, loud, dissonant burst
      osc.type = 'sawtooth';
      osc.frequency.setValueAtTime(150, now);
      osc.frequency.linearRampToValueAtTime(100, now + 0.2);
      gain.gain.setValueAtTime(0, now);
      gain.gain.linearRampToValueAtTime(0.5, now + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.01, now + 0.2);
      osc.start(now);
      osc.stop(now + 0.2);
      break;
      
    case 'fear':
    case 'fearful':
      // Tremolo high pitch
      osc.type = 'sine';
      osc.frequency.setValueAtTime(800, now);
      
      // Tremolo effect using another oscillator modulating gain
      const lfo = audioCtx.createOscillator();
      lfo.type = 'sine';
      lfo.frequency.value = 10;
      
      const tremoloGain = audioCtx.createGain();
      tremoloGain.gain.value = 0.5;
      lfo.connect(tremoloGain.gain);
      lfo.start();
      
      osc.disconnect();
      osc.connect(tremoloGain);
      tremoloGain.connect(gain);
      
      gain.gain.setValueAtTime(0, now);
      gain.gain.linearRampToValueAtTime(0.3, now + 0.1);
      gain.gain.linearRampToValueAtTime(0.01, now + 0.6);
      
      osc.start(now);
      osc.stop(now + 0.6);
      setTimeout(() => lfo.stop(), 600);
      break;
      
    case 'distress':
    case 'critical':
      // Alarm-like pattern (two rapid beeps)
      osc.type = 'square';
      osc.frequency.setValueAtTime(880, now);
      gain.gain.setValueAtTime(0, now);
      gain.gain.linearRampToValueAtTime(0.3, now + 0.01);
      gain.gain.setValueAtTime(0.3, now + 0.1);
      gain.gain.setValueAtTime(0, now + 0.11);
      
      gain.gain.setValueAtTime(0, now + 0.2);
      gain.gain.linearRampToValueAtTime(0.3, now + 0.21);
      gain.gain.setValueAtTime(0.3, now + 0.3);
      gain.gain.linearRampToValueAtTime(0.01, now + 0.35);
      
      osc.start(now);
      osc.stop(now + 0.4);
      break;
      
    default: // neutral
      osc.type = 'sine';
      osc.frequency.setValueAtTime(440, now);
      gain.gain.setValueAtTime(0, now);
      gain.gain.linearRampToValueAtTime(0.2, now + 0.05);
      gain.gain.linearRampToValueAtTime(0.01, now + 0.3);
      osc.start(now);
      osc.stop(now + 0.3);
      break;
  }
};

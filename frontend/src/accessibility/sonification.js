let audioCtx = null;

export const speakSummary = (text) => {
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel(); // stop previous
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.9;
    window.speechSynthesis.speak(utterance);
  }
};

export const sonifyTrends = (sessions, durationMs = 5000) => {
  return new Promise((resolve) => {
    if (!sessions || sessions.length === 0) {
      resolve();
      return;
    }

    if (!audioCtx) {
      audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioCtx.state === 'suspended') {
      audioCtx.resume();
    }

    // Valence mapping (happy=high pitch, sad=low pitch, angry=dissonant mid)
    const emotionToFreq = {
      happy: 659.25, // E5
      joy: 659.25,
      sad: 220.00,   // A3
      sadness: 220.00,
      angry: 311.13, // Eb4 (dissonant to C)
      anger: 311.13,
      fear: 880.00,  // A5
      distress: 987.77, // B5
      critical: 1046.50, // C6
      neutral: 440.00, // A4
    };

    const timePerSession = (durationMs / 1000) / sessions.length;
    const now = audioCtx.currentTime;

    sessions.forEach((session, i) => {
      const startTime = now + (i * timePerSession);
      const label = (session.fused_label || 'neutral').toLowerCase();
      const freq = emotionToFreq[label] || 440.0;
      const severityScore = session.conflict_score || 0.1; // mapping intensity
      
      const osc = audioCtx.createOscillator();
      const gain = audioCtx.createGain();
      
      osc.connect(gain);
      gain.connect(audioCtx.destination);
      
      // Tone shape
      if (['angry', 'anger', 'distress', 'critical'].includes(label)) {
        osc.type = 'sawtooth';
      } else if (['sad', 'sadness'].includes(label)) {
        osc.type = 'triangle';
      } else {
        osc.type = 'sine';
      }
      
      osc.frequency.value = freq;
      
      // Volume envelope
      const maxVol = 0.1 + (severityScore * 0.2); // louder for higher severity
      gain.gain.setValueAtTime(0, startTime);
      gain.gain.linearRampToValueAtTime(maxVol, startTime + 0.05);
      gain.gain.exponentialRampToValueAtTime(0.01, startTime + timePerSession - 0.05);
      
      osc.start(startTime);
      osc.stop(startTime + timePerSession);
    });

    // Resolve when done playing
    setTimeout(() => {
      resolve();
    }, durationMs + 200);
  });
};

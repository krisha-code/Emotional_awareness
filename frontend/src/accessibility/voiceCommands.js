export const initVoiceCommands = (navigate, actions) => {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  
  if (!SpeechRecognition) {
    console.warn("Speech recognition not supported in this browser.");
    return {
      start: () => {},
      stop: () => {},
      isSupported: false
    };
  }

  const recognition = new SpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = false;
  recognition.lang = 'en-US';

  const COMMANDS = {
    'go to analyze': () => navigate('/analyze'),
    'start analysis': () => navigate('/analyze'),
    'go to history': () => navigate('/history'),
    'open history': () => navigate('/history'),
    'open journal': () => navigate('/journal'),
    'go to settings': () => navigate('/settings'),
    'read results': () => { if(actions.readResults) actions.readResults(); },
    'crisis help': () => { if(actions.openCrisis) actions.openCrisis(); },
    'help me': () => { if(actions.openCrisis) actions.openCrisis(); },
    'start recording': () => { if(actions.startRecording) actions.startRecording(); },
    'stop recording': () => { if(actions.stopRecording) actions.stopRecording(); },
    'capture face': () => { if(actions.captureFace) actions.captureFace(); },
    'analyze': () => { if(actions.analyze) actions.analyze(); },
  };

  recognition.onresult = (event) => {
    const lastResultIndex = event.results.length - 1;
    const transcript = event.results[lastResultIndex][0].transcript.toLowerCase().trim();
    
    console.log("Heard:", transcript);
    
    // Simple command matching
    for (const [cmd, action] of Object.entries(COMMANDS)) {
      if (transcript.includes(cmd)) {
        action();
        
        // Announce the action
        const utterance = new SpeechSynthesisUtterance(`Executing command: ${cmd}`);
        window.speechSynthesis.speak(utterance);
        break;
      }
    }
  };

  recognition.onerror = (event) => {
    console.error("Speech recognition error", event.error);
  };

  return {
    start: () => {
      try {
        recognition.start();
      } catch (e) {
        // Already started
      }
    },
    stop: () => recognition.stop(),
    isSupported: true
  };
};

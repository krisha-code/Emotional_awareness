import React, { useState } from 'react';
import { User, Bell, Lock, Download, Trash2, Eye, Mic, Vibrate, Shield, AlertTriangle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const Settings = () => {
  const { user, updateConsent } = useAuth();
  const [consent, setConsent] = useState({
    camera: user?.consent_camera || false,
    microphone: user?.consent_microphone || false,
    wearable: user?.consent_wearable || false,
    emergency: user?.consent_emergency || false,
  });

  const handleToggle = (key) => {
    const newConsent = { ...consent, [key]: !consent[key] };
    setConsent(newConsent);
    // In a real app, update API here
    if (updateConsent) {
      updateConsent(newConsent);
    }
  };

  return (
    <div className="max-w-4xl mx-auto pb-24 animate-fadeIn">
      <h2 className="text-3xl font-bold mb-8">Settings</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        
        {/* Left Nav (Simulated) */}
        <div className="col-span-1 flex flex-col gap-2">
          <button className="flex items-center gap-3 p-3 rounded-xl bg-[rgba(108,99,255,0.2)] text-[#6C63FF] font-medium border-l-4 border-[#6C63FF]">
            <User size={18} /> Profile
          </button>
          <button className="flex items-center gap-3 p-3 rounded-xl text-[#8888AA] hover:bg-[rgba(255,255,255,0.05)] hover:text-white transition-colors">
            <Shield size={18} /> Privacy & Consent
          </button>
          <button className="flex items-center gap-3 p-3 rounded-xl text-[#8888AA] hover:bg-[rgba(255,255,255,0.05)] hover:text-white transition-colors">
            <Bell size={18} /> Notifications
          </button>
        </div>

        {/* Content */}
        <div className="col-span-1 md:col-span-2 flex flex-col gap-8">
          
          {/* Profile Section */}
          <section className="glass-card p-8 rounded-3xl">
            <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
              <User size={20} className="text-[#6C63FF]" /> Profile Information
            </h3>
            
            <div className="flex flex-col gap-4">
              <div>
                <label className="block text-sm text-[#8888AA] mb-1">Username</label>
                <input type="text" value={user?.username || 'Demo User'} disabled className="input-field w-full opacity-70" />
              </div>
              <div>
                <label className="block text-sm text-[#8888AA] mb-1">Email</label>
                <input type="email" value={user?.email || 'demo@mindsense.app'} disabled className="input-field w-full opacity-70" />
              </div>
              <button className="btn btn-secondary self-start">Change Password</button>
            </div>
          </section>

          {/* Privacy & Consent Section */}
          <section className="glass-card p-8 rounded-3xl border border-[rgba(67,233,123,0.2)]">
            <h3 className="text-xl font-bold mb-2 flex items-center gap-2">
              <Shield size={20} className="text-[#43E97B]" /> Privacy & Consent
            </h3>
            <p className="text-[#8888AA] text-sm mb-6">Manage what data MindSense is allowed to collect and analyze. You can revoke this at any time.</p>
            
            <div className="flex flex-col gap-4">
              
              <div className="flex items-center justify-between p-4 bg-[rgba(255,255,255,0.02)] rounded-xl border border-[rgba(255,255,255,0.05)]">
                <div className="flex gap-4 items-center">
                  <div className="p-3 bg-[rgba(255,255,255,0.05)] rounded-lg"><Eye size={20} className="text-[#6C63FF]" /></div>
                  <div>
                    <h4 className="font-bold">Camera (Facial Analysis)</h4>
                    <p className="text-xs text-[#8888AA]">Allow capturing frames for emotion detection. Frames are not saved.</p>
                  </div>
                </div>
                <button 
                  onClick={() => handleToggle('camera')}
                  className={`w-14 h-7 rounded-full transition-colors relative ${consent.camera ? 'bg-[#43E97B]' : 'bg-[rgba(255,255,255,0.2)]'}`}
                  aria-pressed={consent.camera}
                >
                  <span className={`absolute top-1 w-5 h-5 bg-white rounded-full transition-transform ${consent.camera ? 'left-8' : 'left-1'}`}></span>
                </button>
              </div>

              <div className="flex items-center justify-between p-4 bg-[rgba(255,255,255,0.02)] rounded-xl border border-[rgba(255,255,255,0.05)]">
                <div className="flex gap-4 items-center">
                  <div className="p-3 bg-[rgba(255,255,255,0.05)] rounded-lg"><Mic size={20} className="text-[#6C63FF]" /></div>
                  <div>
                    <h4 className="font-bold">Microphone (Speech Analysis)</h4>
                    <p className="text-xs text-[#8888AA]">Allow recording audio for prosody analysis. Audio is not saved.</p>
                  </div>
                </div>
                <button 
                  onClick={() => handleToggle('microphone')}
                  className={`w-14 h-7 rounded-full transition-colors relative ${consent.microphone ? 'bg-[#43E97B]' : 'bg-[rgba(255,255,255,0.2)]'}`}
                  aria-pressed={consent.microphone}
                >
                  <span className={`absolute top-1 w-5 h-5 bg-white rounded-full transition-transform ${consent.microphone ? 'left-8' : 'left-1'}`}></span>
                </button>
              </div>

              <div className="flex items-center justify-between p-4 bg-[rgba(255,255,255,0.02)] rounded-xl border border-[rgba(255,255,255,0.05)]">
                <div className="flex gap-4 items-center">
                  <div className="p-3 bg-[rgba(255,255,255,0.05)] rounded-lg"><AlertTriangle size={20} className="text-[#FF4757]" /></div>
                  <div>
                    <h4 className="font-bold">Emergency Contact Sync</h4>
                    <p className="text-xs text-[#8888AA]">Allow notifying a trusted contact if critical distress is detected.</p>
                  </div>
                </div>
                <button 
                  onClick={() => handleToggle('emergency')}
                  className={`w-14 h-7 rounded-full transition-colors relative ${consent.emergency ? 'bg-[#FF4757]' : 'bg-[rgba(255,255,255,0.2)]'}`}
                  aria-pressed={consent.emergency}
                >
                  <span className={`absolute top-1 w-5 h-5 bg-white rounded-full transition-transform ${consent.emergency ? 'left-8' : 'left-1'}`}></span>
                </button>
              </div>

            </div>
          </section>

          {/* Data Management */}
          <section className="glass-card p-8 rounded-3xl border border-[rgba(255,71,87,0.2)]">
            <h3 className="text-xl font-bold mb-2 flex items-center gap-2 text-[#FF4757]">
              <Lock size={20} /> Data Management
            </h3>
            <p className="text-[#8888AA] text-sm mb-6">Download your data or permanently delete your account.</p>
            
            <div className="flex gap-4">
              <button className="btn btn-secondary flex items-center gap-2">
                <Download size={18} /> Export All Data
              </button>
              <button className="btn bg-[rgba(255,71,87,0.1)] text-[#FF4757] hover:bg-[#FF4757] hover:text-white flex items-center gap-2 border border-[#FF4757]">
                <Trash2 size={18} /> Delete Account
              </button>
            </div>
          </section>

        </div>
      </div>
    </div>
  );
};

export default Settings;

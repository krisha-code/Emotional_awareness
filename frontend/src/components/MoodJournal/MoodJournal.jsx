import React, { useState } from 'react';
import { Download, Search, Plus, Calendar, Tag } from 'lucide-react';
import { motion } from 'framer-motion';

const MOODS = [
  { id: 'happy', emoji: '😊', label: 'Happy', color: 'text-[#43E97B]' },
  { id: 'sad', emoji: '😢', label: 'Sad', color: 'text-[#6C63FF]' },
  { id: 'angry', emoji: '😤', label: 'Angry', color: 'text-[#FF6584]' },
  { id: 'fearful', emoji: '😨', label: 'Fearful', color: 'text-[#FFB347]' },
  { id: 'neutral', emoji: '😐', label: 'Neutral', color: 'text-[#8888AA]' },
  { id: 'distressed', emoji: '💔', label: 'Distressed', color: 'text-[#FF4757]' },
];

const MoodJournal = () => {
  const [entries, setEntries] = useState([
    { id: 1, date: '2026-07-13T10:00:00Z', mood: 'happy', content: 'Had a great morning walk.', tags: ['exercise', 'morning'] },
    { id: 2, date: '2026-07-12T19:30:00Z', mood: 'sad', content: 'Feeling a bit overwhelmed with work today.', tags: ['work', 'stress'] }
  ]);
  const [isAdding, setIsAdding] = useState(false);
  const [newEntry, setNewEntry] = useState({ mood: 'neutral', content: '', tags: '' });
  const [searchTerm, setSearchTerm] = useState('');

  const handleExport = () => {
    // API call would go here
    const utterance = new SpeechSynthesisUtterance("Downloading journal export.");
    window.speechSynthesis.speak(utterance);
  };

  const handleAdd = (e) => {
    e.preventDefault();
    const entry = {
      id: Date.now(),
      date: new Date().toISOString(),
      mood: newEntry.mood,
      content: newEntry.content,
      tags: newEntry.tags.split(',').map(t => t.trim()).filter(Boolean)
    };
    setEntries([entry, ...entries]);
    setIsAdding(false);
    setNewEntry({ mood: 'neutral', content: '', tags: '' });
  };

  const filteredEntries = entries.filter(e => 
    e.content.toLowerCase().includes(searchTerm.toLowerCase()) || 
    e.tags.some(t => t.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div className="w-full max-w-4xl mx-auto flex flex-col gap-6">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-bold mb-2">Mood Journal</h2>
          <p className="text-[#8888AA]">Track your feelings and thoughts over time.</p>
        </div>
        <button onClick={handleExport} className="btn btn-secondary flex items-center gap-2 px-4 py-2" aria-label="Export Journal">
          <Download size={18} /> Export
        </button>
      </div>

      {/* Controls */}
      <div className="flex gap-4 items-center">
        <div className="relative flex-grow">
          <Search size={18} className="absolute left-4 top-1/2 -translate-y-1/2 text-[#8888AA]" />
          <input 
            type="text" 
            placeholder="Search entries or tags..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input-field pl-12 w-full py-3"
            aria-label="Search journal"
          />
        </div>
        <button 
          onClick={() => setIsAdding(!isAdding)} 
          className="btn btn-primary px-6 py-3 flex items-center gap-2"
          aria-expanded={isAdding}
        >
          <Plus size={18} /> New Entry
        </button>
      </div>

      {/* Add Entry Form */}
      {isAdding && (
        <motion.form 
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          onSubmit={handleAdd}
          className="glass-card p-6 flex flex-col gap-4 overflow-hidden"
        >
          <div className="flex gap-4 justify-between items-center mb-2">
            <h3 className="font-semibold text-lg">How are you feeling?</h3>
            <div className="flex gap-2" role="radiogroup" aria-label="Select mood">
              {MOODS.map(m => (
                <button
                  key={m.id}
                  type="button"
                  role="radio"
                  aria-checked={newEntry.mood === m.id}
                  onClick={() => setNewEntry({...newEntry, mood: m.id})}
                  className={`text-2xl p-2 rounded-full transition-all ${newEntry.mood === m.id ? 'bg-[rgba(255,255,255,0.1)] scale-110' : 'opacity-50 hover:opacity-100'}`}
                  title={m.label}
                >
                  {m.emoji}
                </button>
              ))}
            </div>
          </div>
          
          <textarea
            required
            placeholder="Write your thoughts here..."
            value={newEntry.content}
            onChange={(e) => setNewEntry({...newEntry, content: e.target.value})}
            className="input-field w-full min-h-[120px] resize-none"
            aria-label="Journal entry content"
          />
          
          <div className="flex gap-4 items-center">
            <Tag size={18} className="text-[#8888AA]" />
            <input 
              type="text"
              placeholder="Tags (comma separated)... e.g. work, family"
              value={newEntry.tags}
              onChange={(e) => setNewEntry({...newEntry, tags: e.target.value})}
              className="input-field flex-grow py-2"
              aria-label="Tags"
            />
            <button type="submit" className="btn btn-primary px-6">Save</button>
          </div>
        </motion.form>
      )}

      {/* List */}
      <div className="flex flex-col gap-4" role="list">
        {filteredEntries.map(entry => {
          const moodObj = MOODS.find(m => m.id === entry.mood);
          return (
            <div key={entry.id} className="glass-card p-6 flex gap-6 hover:bg-[rgba(255,255,255,0.08)] transition-colors" role="listitem">
              <div className="flex flex-col items-center justify-start gap-2 pt-1 w-16 flex-shrink-0">
                <span className="text-4xl" aria-hidden="true">{moodObj?.emoji}</span>
                <span className={`text-xs font-medium uppercase ${moodObj?.color}`}>{moodObj?.label}</span>
              </div>
              <div className="flex-grow border-l border-[rgba(255,255,255,0.1)] pl-6">
                <div className="flex items-center gap-2 mb-3 text-[#8888AA] text-sm">
                  <Calendar size={14} />
                  <time dateTime={entry.date}>
                    {new Date(entry.date).toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                  </time>
                </div>
                <p className="text-[#F0F0FF] leading-relaxed mb-4 whitespace-pre-wrap">{entry.content}</p>
                {entry.tags.length > 0 && (
                  <div className="flex gap-2 flex-wrap">
                    {entry.tags.map(t => (
                      <span key={t} className="px-3 py-1 bg-[rgba(255,255,255,0.1)] rounded-full text-xs text-[#8888AA]">#{t}</span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}
        {filteredEntries.length === 0 && (
          <div className="text-center p-12 text-[#8888AA]">
            No journal entries found.
          </div>
        )}
      </div>
    </div>
  );
};

export default MoodJournal;

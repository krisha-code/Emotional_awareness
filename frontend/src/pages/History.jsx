import React, { useState, useEffect } from 'react';
import Dashboard from '../components/Dashboard';
import { Clock, Tag } from 'lucide-react';

export default function History() {
  const [sessions, setSessions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Simulate fetching history
    setTimeout(() => {
      setSessions([
        { id: 1, date: '2026-07-13T10:30:00Z', fusedEmotion: 'happy', severity: 'Low' },
        { id: 2, date: '2026-07-12T15:45:00Z', fusedEmotion: 'anxious', severity: 'Moderate' },
        { id: 3, date: '2026-07-11T09:15:00Z', fusedEmotion: 'neutral', severity: 'Low' },
        { id: 4, date: '2026-07-10T18:20:00Z', fusedEmotion: 'sad', severity: 'Moderate' },
        { id: 5, date: '2026-07-09T14:10:00Z', fusedEmotion: 'angry', severity: 'High' },
      ]);
      setIsLoading(false);
    }, 1000);
  }, []);

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('en-US', {
      weekday: 'short', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit'
    });
  };

  const getSeverityColor = (severity) => {
    switch(severity) {
      case 'Low': return 'bg-green-100 text-green-800';
      case 'Moderate': return 'bg-yellow-100 text-yellow-800';
      case 'High': return 'bg-orange-100 text-orange-800';
      case 'Critical': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-10">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Overview</h2>
        <Dashboard sessions={sessions} />
      </div>

      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Session History</h2>
        
        {isLoading ? (
          <div className="flex justify-center p-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <ul className="divide-y divide-gray-200">
              {sessions.map((session) => (
                <li key={session.id} className="p-4 sm:p-6 hover:bg-gray-50 transition-colors">
                  <div className="flex items-center justify-between">
                    <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-6">
                      <div className="flex items-center text-sm text-gray-500 gap-2">
                        <Clock size={16} />
                        {formatDate(session.date)}
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="font-bold text-lg text-gray-900 capitalize">
                          {session.fusedEmotion}
                        </span>
                        <span className={`text-xs font-medium px-2.5 py-0.5 rounded-full ${getSeverityColor(session.severity)}`}>
                          {session.severity}
                        </span>
                      </div>
                    </div>
                    <button className="text-indigo-600 hover:text-indigo-800 text-sm font-medium">
                      View Details
                    </button>
                  </div>
                </li>
              ))}
              {sessions.length === 0 && (
                <li className="p-8 text-center text-gray-500">
                  No sessions recorded yet. Start an analysis to see your history.
                </li>
              )}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

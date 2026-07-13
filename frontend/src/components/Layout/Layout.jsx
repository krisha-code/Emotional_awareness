import React, { useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { Brain, Home, Activity, History as HistoryIcon, User, LogOut, Menu, X, Bell, Settings, Accessibility } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import AccessibilityBar from '../AccessibilityBar';

export default function Layout({ children }) {
  const { user, logout } = useAuth() || { user: { username: 'Guest' }, logout: () => {} };
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showAccessibility, setShowAccessibility] = useState(true);
  const location = useLocation();

  const navItems = [
    { name: 'Home', path: '/', icon: <Home size={20} /> },
    { name: 'Analyze', path: '/analyze', icon: <Activity size={20} /> },
    { name: 'History', path: '/history', icon: <HistoryIcon size={20} /> },
    { name: 'Journal', path: '/journal', icon: <Brain size={20} /> },
    { name: 'Settings', path: '/settings', icon: <Settings size={20} /> },
  ];

  const getPageTitle = () => {
    switch (location.pathname) {
      case '/': return 'Dashboard';
      case '/analyze': return 'Emotion Analysis';
      case '/history': return 'Analysis History';
      case '/journal': return 'Mood Journal';
      case '/settings': return 'Settings';
      default: return 'MindSense';
    }
  };

  return (
    <div className="app-wrapper">
      {/* Mobile sidebar overlay */}
      {mobileMenuOpen && (
        <div 
          className="fixed inset-0 z-20 bg-black bg-opacity-70 lg:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`sidebar-container ${mobileMenuOpen ? 'fixed left-0 top-0 z-50' : 'hidden lg:flex'}`}>
        <div className="flex flex-col h-full">
          <div className="flex items-center justify-between h-16 px-6 border-b border-[rgba(255,255,255,0.08)]">
            <div className="flex items-center gap-2 text-[#6C63FF]">
              <Brain size={28} />
              <span className="text-xl font-bold tracking-tight text-white">MindSense</span>
            </div>
            <button className="lg:hidden text-[#8888AA]" onClick={() => setMobileMenuOpen(false)}>
              <X size={24} />
            </button>
          </div>

          <nav className="flex-1 px-4 py-6 space-y-2 overflow-y-auto" aria-label="Main Navigation">
            {navItems.map((item) => (
              <NavLink
                key={item.name}
                to={item.path}
                className={({ isActive }) => `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-semibold transition-all ${
                  isActive ? 'bg-[rgba(108,99,255,0.25)] text-[#6C63FF] border border-[rgba(108,99,255,0.4)] shadow-[0_0_15px_rgba(108,99,255,0.2)]' : 'text-[#8888AA] hover:bg-[rgba(255,255,255,0.05)] hover:text-white'
                }`}
                onClick={() => setMobileMenuOpen(false)}
              >
                {item.icon}
                {item.name}
              </NavLink>
            ))}
          </nav>

          <div className="p-4 border-t border-[rgba(255,255,255,0.08)]">
            <div className="flex items-center justify-between mb-4 bg-[rgba(255,255,255,0.03)] p-3 rounded-xl border border-[rgba(255,255,255,0.05)]">
               <div className="flex items-center gap-3">
                 <div className="w-9 h-9 rounded-full bg-gradient-to-br from-[#6C63FF] to-[#FF6584] flex items-center justify-center text-white font-bold shadow-md">
                   {user?.username?.charAt(0)?.toUpperCase() || 'U'}
                 </div>
                 <div className="flex flex-col">
                   <span className="text-sm font-bold text-white">{user?.username || 'Guest'}</span>
                   <span className="text-xs text-[#43E97B] font-medium">● Active Plan</span>
                 </div>
               </div>
               <button 
                 onClick={logout} 
                 className="p-2 text-[#8888AA] hover:text-[#FF4757] hover:bg-[rgba(255,71,87,0.15)] rounded-lg transition-colors"
                 aria-label="Logout"
                 title="Log Out"
               >
                 <LogOut size={18} />
               </button>
            </div>
            
            <button 
              onClick={() => setShowAccessibility(!showAccessibility)}
              className={`flex items-center justify-center w-full gap-2 px-3 py-2.5 text-sm font-semibold rounded-xl transition-all border ${
                showAccessibility 
                  ? 'bg-[rgba(108,99,255,0.2)] text-[#6C63FF] border-[rgba(108,99,255,0.4)]' 
                  : 'text-[#8888AA] bg-[rgba(255,255,255,0.02)] border-[rgba(255,255,255,0.08)] hover:bg-[rgba(255,255,255,0.05)] hover:text-white'
              }`}
              aria-label="Toggle Accessibility Mode"
            >
              <Accessibility size={16} />
              <span>Accessibility: {showAccessibility ? 'ON' : 'OFF'}</span>
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="main-container">
        <header className="header-bar">
          <div className="flex items-center gap-4">
            <button 
              className="p-2 text-[#8888AA] rounded-lg lg:hidden hover:bg-[rgba(255,255,255,0.05)] hover:text-white focus:outline-none"
              onClick={() => setMobileMenuOpen(true)}
              aria-label="Open sidebar"
            >
              <Menu size={24} />
            </button>
            <h1 className="text-xl font-bold text-white tracking-wide">{getPageTitle()}</h1>
          </div>
          
          <div className="flex items-center gap-4">
            <button className="p-2.5 text-[#8888AA] rounded-xl bg-[rgba(255,255,255,0.03)] border border-[rgba(255,255,255,0.08)] hover:bg-[rgba(255,255,255,0.08)] hover:text-white transition-all" aria-label="Notifications">
              <Bell size={18} />
            </button>
          </div>
        </header>

        <main className="content-area" role="main">
          {children || <Outlet />}
        </main>

        {showAccessibility && <AccessibilityBar />}
      </div>
    </div>
  );
}

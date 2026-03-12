import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, PlusCircle, BarChart3, Users, Info, Mail, Menu, X } from 'lucide-react';

const NAV_LINKS = [
  { to: '/', label: 'Home', icon: Home },
  { to: '/analyzer', label: 'Analyzer', icon: BarChart3 },
  { to: '/new-company', label: 'New Analysis', icon: PlusCircle },
  { to: '/about', label: 'About', icon: Info },
  { to: '/team', label: 'Team', icon: Users },
  { to: '/contact', label: 'Contact', icon: Mail },
];

function LeafLogo({ className = "h-8 w-8" }) {
  return (
    <svg viewBox="0 0 64 64" className={className} fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="lg1" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#102a43"/>
          <stop offset="100%" stopColor="#3b82f6"/>
        </linearGradient>
        <linearGradient id="lg2" x1="0%" y1="100%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#2563eb"/>
          <stop offset="100%" stopColor="#60a5fa"/>
        </linearGradient>
      </defs>
      <path d="M32 4 C12 18 8 38 32 60 C56 38 52 18 32 4Z" fill="url(#lg1)" opacity="0.9"/>
      <circle cx="32" cy="18" r="3" fill="url(#lg2)"/>
      <circle cx="22" cy="30" r="2.5" fill="url(#lg2)"/>
      <circle cx="42" cy="30" r="2.5" fill="url(#lg2)"/>
      <circle cx="27" cy="42" r="2.5" fill="url(#lg2)"/>
      <circle cx="37" cy="42" r="2.5" fill="url(#lg2)"/>
      <circle cx="32" cy="52" r="2" fill="url(#lg2)"/>
      <line x1="32" y1="18" x2="22" y2="30" stroke="#93c5fd" strokeWidth="1" opacity="0.7"/>
      <line x1="32" y1="18" x2="42" y2="30" stroke="#93c5fd" strokeWidth="1" opacity="0.7"/>
      <line x1="22" y1="30" x2="27" y2="42" stroke="#93c5fd" strokeWidth="1" opacity="0.7"/>
      <line x1="42" y1="30" x2="37" y2="42" stroke="#93c5fd" strokeWidth="1" opacity="0.7"/>
      <line x1="22" y1="30" x2="42" y2="30" stroke="#93c5fd" strokeWidth="0.8" opacity="0.5"/>
      <line x1="27" y1="42" x2="37" y2="42" stroke="#93c5fd" strokeWidth="0.8" opacity="0.5"/>
      <line x1="27" y1="42" x2="32" y2="52" stroke="#93c5fd" strokeWidth="1" opacity="0.7"/>
      <line x1="37" y1="42" x2="32" y2="52" stroke="#93c5fd" strokeWidth="1" opacity="0.7"/>
    </svg>
  );
}

export default function Layout({ children }) {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const isActive = (path) => {
    if (path === '/') return location.pathname === '/';
    return location.pathname.startsWith(path);
  };

  return (
    <div className="min-h-screen bg-navy-50 flex flex-col">
      {/* Top Bar */}
      <div className="bg-navy-950 text-navy-300 text-xs py-1.5 px-4 flex justify-between items-center">
        <span className="flex items-center space-x-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-blue-400 animate-pulse"></span>
          <span>Corporate Credit Decisioning Engine</span>
        </span>
        <span>AI-Powered &bull; RBI Compliant</span>
      </div>

      {/* Main Navigation */}
      <nav className="gradient-bg text-white shadow-lg sticky top-0 z-50 border-b border-navy-700/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center space-x-3 group">
              <LeafLogo className="h-9 w-9 group-hover:scale-110 transition-transform" />
              <div className="flex flex-col">
                <span className="text-lg font-bold tracking-tight leading-none bg-gradient-to-r from-blue-300 to-white bg-clip-text text-transparent">
                  Intelli-Credit
                </span>
                <span className="text-[10px] text-blue-300/70 font-medium tracking-wider uppercase">
                  AI Credit Platform
                </span>
              </div>
            </Link>

            {/* Desktop Nav */}
            <div className="hidden md:flex items-center space-x-1">
              {NAV_LINKS.map(({ to, label, icon: Icon }) => (
                <Link
                  key={to}
                  to={to}
                  className={`flex items-center space-x-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    isActive(to)
                      ? 'bg-blue-500/20 text-blue-200 shadow-sm ring-1 ring-blue-500/30'
                      : 'text-navy-300 hover:bg-white/10 hover:text-white'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{label}</span>
                </Link>
              ))}
            </div>

            {/* Mobile Toggle */}
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="md:hidden p-2 rounded-lg text-navy-200 hover:bg-white/10 transition"
            >
              {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Nav */}
        {mobileOpen && (
          <div className="md:hidden border-t border-navy-700/30 pb-3">
            {NAV_LINKS.map(({ to, label, icon: Icon }) => (
              <Link
                key={to}
                to={to}
                onClick={() => setMobileOpen(false)}
                className={`flex items-center space-x-2 px-4 py-2.5 text-sm font-medium transition ${
                  isActive(to)
                    ? 'bg-blue-500/20 text-blue-200'
                    : 'text-navy-200 hover:bg-white/10 hover:text-white'
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{label}</span>
              </Link>
            ))}
          </div>
        )}
      </nav>

      {/* Main Content */}
      <main className="flex-1">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-navy-950 text-navy-400 mt-auto border-t border-navy-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-2">
            <div className="flex items-center space-x-2">
              <LeafLogo className="h-4 w-4" />
              <span className="text-blue-200 text-sm font-semibold">Intelli-Credit</span>
              <span className="text-navy-600 text-xs">|</span>
              <span className="text-xs text-navy-500">AI-Powered Credit Decisioning Engine</span>
            </div>
            <div className="flex items-center space-x-4 text-xs">
              <Link to="/about" className="hover:text-blue-300 transition">About</Link>
              <Link to="/analyzer" className="hover:text-blue-300 transition">Analyzer</Link>
              <Link to="/team" className="hover:text-blue-300 transition">Team</Link>
              <Link to="/contact" className="hover:text-blue-300 transition">Contact</Link>
              <span className="text-navy-600">|</span>
              <span className="text-navy-500">&copy; {new Date().getFullYear()} Intelli-Credit</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

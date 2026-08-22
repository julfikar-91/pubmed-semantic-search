import React, { useState, useEffect, useRef } from 'react';
import { 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  RotateCw, 
  Server, 
  Database, 
  BookOpen, 
  Cpu, 
  Zap, 
  ChevronDown,
  Globe
} from 'lucide-react';
import { fetchSystemHealth, SystemHealthStatus } from '../api/searchApi';

export const SystemStatusBadge: React.FC = () => {
  const [health, setHealth] = useState<SystemHealthStatus>({
    status: 'healthy',
    backend: 'Connecting...',
    ncbi_status: 'Checking...',
    mesh_status: 'Checking...',
    llm_provider: 'Checking...',
    ping_ms: 0
  });
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const checkHealth = async () => {
    setIsRefreshing(true);
    try {
      const data = await fetchSystemHealth();
      setHealth(data);
    } catch (err) {
      console.error("Health check error:", err);
      setHealth({
        status: 'offline',
        backend: 'Disconnected',
        ncbi_status: 'Unreachable',
        mesh_status: 'Offline',
        llm_provider: 'Offline',
        ping_ms: 0
      });
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    checkHealth();
    // Poll every 30 seconds
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const isHealthy = health.status === 'healthy';
  const isDegraded = health.status === 'degraded';

  return (
    <div className="relative inline-block" ref={dropdownRef}>
      {/* Light Indicator Link / Button in Navbar */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold border transition-all cursor-pointer shadow-sm ${
          isHealthy
            ? 'bg-emerald-50 text-emerald-800 border-emerald-200 hover:bg-emerald-100'
            : isDegraded
            ? 'bg-amber-50 text-amber-800 border-amber-200 hover:bg-amber-100'
            : 'bg-red-50 text-red-800 border-red-200 hover:bg-red-100'
        }`}
        title="Click to view full System & API connection status"
      >
        <span className="relative flex h-2.5 w-2.5">
          <span
            className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
              isHealthy ? 'bg-emerald-400' : isDegraded ? 'bg-amber-400' : 'bg-red-400'
            }`}
          ></span>
          <span
            className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
              isHealthy ? 'bg-emerald-500' : isDegraded ? 'bg-amber-500' : 'bg-red-500'
            }`}
          ></span>
        </span>

        <span className="hidden sm:inline">
          {isHealthy ? 'All Systems Operational' : isDegraded ? 'Degraded Service' : 'Backend Offline'}
        </span>
        <span className="sm:hidden">
          {isHealthy ? 'Live' : isDegraded ? 'Slow' : 'Down'}
        </span>

        {health.ping_ms ? (
          <span className="text-[10px] opacity-75 font-mono">
            {health.ping_ms}ms
          </span>
        ) : null}

        <ChevronDown size={12} className={`transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {/* Floating Status Dropdown Modal */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 sm:w-96 bg-white rounded-2xl shadow-2xl border border-slate-200 p-4 z-50 animate-in fade-in slide-in-from-top-2 duration-150 text-slate-800">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <div className={`p-1.5 rounded-lg ${isHealthy ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>
                {isHealthy ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
              </div>
              <div>
                <h4 className="text-xs font-bold text-slate-900">System Connection Status</h4>
                <p className="text-[11px] text-slate-500">Live health monitor for all subsystem APIs</p>
              </div>
            </div>

            <button
              type="button"
              onClick={checkHealth}
              disabled={isRefreshing}
              className="p-1.5 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors cursor-pointer"
              title="Refresh connection status"
            >
              <RotateCw size={14} className={isRefreshing ? 'animate-spin text-blue-600' : ''} />
            </button>
          </div>

          <div className="py-3 space-y-2.5">
            {/* 1. FastAPI Backend */}
            <div className="flex items-center justify-between text-xs p-2 rounded-xl bg-slate-50 border border-slate-100">
              <div className="flex items-center gap-2">
                <Server size={15} className="text-blue-600" />
                <span className="font-semibold text-slate-700">FastAPI Backend</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className={`h-2 w-2 rounded-full ${health.backend === 'Disconnected' ? 'bg-red-500' : 'bg-emerald-500'}`}></span>
                <span className="font-medium text-slate-900 capitalize">{health.backend || 'Operational'}</span>
              </div>
            </div>

            {/* 2. NCBI PubMed API */}
            <div className="flex items-center justify-between text-xs p-2 rounded-xl bg-slate-50 border border-slate-100">
              <div className="flex items-center gap-2">
                <Globe size={15} className="text-emerald-600" />
                <span className="font-semibold text-slate-700">NCBI E-Utilities API</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className={`h-2 w-2 rounded-full ${health.ncbi_status === 'Operational' ? 'bg-emerald-500' : 'bg-amber-500'}`}></span>
                <span className="font-medium text-slate-900">{health.ncbi_status || 'Operational'}</span>
              </div>
            </div>

            {/* 3. MeSH 2026 Engine */}
            <div className="flex items-center justify-between text-xs p-2 rounded-xl bg-slate-50 border border-slate-100">
              <div className="flex items-center gap-2">
                <BookOpen size={15} className="text-indigo-600" />
                <span className="font-semibold text-slate-700">MeSH 2026 Dictionary</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className={`h-2 w-2 rounded-full ${health.mesh_status.includes('Loaded') || health.mesh_status === 'Operational' ? 'bg-emerald-500' : 'bg-amber-500'}`}></span>
                <span className="font-medium text-slate-900">{health.mesh_status || 'Ready'}</span>
              </div>
            </div>

            {/* 4. Vector Store */}
            <div className="flex items-center justify-between text-xs p-2 rounded-xl bg-slate-50 border border-slate-100">
              <div className="flex items-center gap-2">
                <Database size={15} className="text-purple-600" />
                <span className="font-semibold text-slate-700">Vector Embeddings (Dense)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-emerald-500"></span>
                <span className="font-medium text-slate-900">{health.embedding_model || 'MiniLM-L6 (384d)'}</span>
              </div>
            </div>

            {/* 5. LLM Provider */}
            <div className="flex items-center justify-between text-xs p-2 rounded-xl bg-slate-50 border border-slate-100">
              <div className="flex items-center gap-2">
                <Cpu size={15} className="text-amber-600" />
                <span className="font-semibold text-slate-700">LLM Query Expansion</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-emerald-500"></span>
                <span className="font-medium text-slate-900 capitalize">{health.llm_provider || 'Mock / Gemini'}</span>
              </div>
            </div>
          </div>

          <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
            <span className="flex items-center gap-1">
              <Zap size={11} className="text-amber-500" /> Roundtrip Ping: {health.ping_ms || 0}ms
            </span>
            <span>Version {health.version || '1.0.0'}</span>
          </div>
        </div>
      )}
    </div>
  );
};

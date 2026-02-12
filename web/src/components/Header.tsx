import { Shield, Activity } from 'lucide-react';
import { useHealth } from '../hooks/useApi';

export default function Header() {
  const { data: health } = useHealth();

  return (
    <header className="h-14 bg-navy-800 border-b border-navy-600 flex items-center justify-between px-6 shrink-0">
      <div className="flex items-center gap-3">
        <Shield className="w-6 h-6 text-accent" />
        <h1 className="text-lg font-semibold tracking-wide">
          <span className="text-accent">OSINT</span>
          <span className="text-gray-300 ml-1.5">Intelligence Platform</span>
        </h1>
      </div>
      <div className="flex items-center gap-4 text-sm">
        {health && (
          <>
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-safe" />
              <span className="text-gray-400">
                {health.providers_available} providers online
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-safe animate-pulse" />
              <span className="text-gray-500 font-mono text-xs">v{health.version}</span>
            </div>
          </>
        )}
      </div>
    </header>
  );
}

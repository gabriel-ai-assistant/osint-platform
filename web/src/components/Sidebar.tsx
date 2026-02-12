import { Search, Radar, Server, Crosshair } from 'lucide-react';
import type { NavPage } from '../types';

interface Props {
  active: NavPage;
  onNavigate: (page: NavPage) => void;
}

const navItems: { id: NavPage; label: string; icon: React.ElementType }[] = [
  { id: 'investigation', label: 'Investigation', icon: Crosshair },
  { id: 'lookup', label: 'Quick Lookup', icon: Search },
  { id: 'providers', label: 'Providers', icon: Server },
];

export default function Sidebar({ active, onNavigate }: Props) {
  return (
    <nav className="w-56 bg-navy-800 border-r border-navy-600 flex flex-col shrink-0">
      <div className="px-4 py-5">
        <div className="flex items-center gap-2 mb-1">
          <Radar className="w-5 h-5 text-accent" />
          <span className="text-xs font-semibold uppercase tracking-widest text-accent">
            Modules
          </span>
        </div>
      </div>

      <div className="flex-1 px-2 space-y-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = active === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`
                w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium
                transition-all duration-200 cursor-pointer
                ${isActive
                  ? 'bg-accent/10 text-accent border border-accent/20'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-navy-700 border border-transparent'
                }
              `}
            >
              <Icon className="w-4 h-4" />
              {item.label}
            </button>
          );
        })}
      </div>

      <div className="p-4 border-t border-navy-600">
        <p className="text-xs text-gray-600 text-center">
          Enterprise Intelligence Suite
        </p>
      </div>
    </nav>
  );
}

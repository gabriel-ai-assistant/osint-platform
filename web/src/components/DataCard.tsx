import { useState } from 'react';
import { motion } from 'framer-motion';
import { ChevronDown, ChevronUp } from 'lucide-react';

interface Props {
  title: string;
  icon: React.ReactNode;
  count?: number;
  children: React.ReactNode;
  index?: number;
  accentColor?: string;
  defaultExpanded?: boolean;
}

export default function DataCard({
  title,
  icon,
  count,
  children,
  index = 0,
  accentColor = 'accent',
  defaultExpanded = true,
}: Props) {
  const [expanded, setExpanded] = useState(defaultExpanded);

  const colorMap: Record<string, string> = {
    accent: 'border-accent/20 hover:border-accent/40',
    threat: 'border-threat/20 hover:border-threat/40',
    safe: 'border-safe/20 hover:border-safe/40',
    warning: 'border-warning/20 hover:border-warning/40',
  };

  const badgeMap: Record<string, string> = {
    accent: 'bg-accent/20 text-accent',
    threat: 'bg-threat/20 text-threat',
    safe: 'bg-safe/20 text-safe',
    warning: 'bg-warning/20 text-warning',
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, duration: 0.4, ease: 'easeOut' }}
      className={`bg-navy-800 border rounded-xl overflow-hidden transition-colors duration-200 ${colorMap[accentColor] || colorMap.accent}`}
    >
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 px-5 py-4 text-left cursor-pointer"
      >
        <div className="text-gray-400">{icon}</div>
        <h3 className="text-sm font-semibold text-gray-200 flex-1">{title}</h3>
        {count !== undefined && count > 0 && (
          <span className={`text-xs font-mono px-2 py-0.5 rounded-full ${badgeMap[accentColor] || badgeMap.accent}`}>
            {count}
          </span>
        )}
        {expanded ? (
          <ChevronUp className="w-4 h-4 text-gray-500" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-500" />
        )}
      </button>
      <motion.div
        initial={false}
        animate={{ height: expanded ? 'auto' : 0, opacity: expanded ? 1 : 0 }}
        transition={{ duration: 0.2 }}
        className="overflow-hidden"
      >
        <div className="px-5 pb-5">
          {children}
        </div>
      </motion.div>
    </motion.div>
  );
}

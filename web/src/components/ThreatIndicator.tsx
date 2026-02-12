import { motion } from 'framer-motion';
import type { ThreatInfo } from '../types';

interface Props {
  threat: ThreatInfo;
  size?: number;
}

export default function ThreatIndicator({ threat, size = 120 }: Props) {
  const radius = (size - 12) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = (threat.score / 100) * circumference;
  const center = size / 2;

  const getColor = () => {
    if (threat.score >= 75) return '#ff3b3b';
    if (threat.score >= 50) return '#ffaa00';
    if (threat.score >= 25) return '#00d4ff';
    return '#00ff88';
  };

  const getLabel = () => {
    if (threat.level === 'critical') return 'CRITICAL';
    if (threat.level === 'high') return 'HIGH';
    if (threat.level === 'medium') return 'MEDIUM';
    return 'LOW';
  };

  const color = getColor();

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          {/* Background ring */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="#1c2647"
            strokeWidth="6"
          />
          {/* Progress ring */}
          <motion.circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth="6"
            strokeLinecap="round"
            strokeDasharray={circumference}
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: circumference - progress }}
            transition={{ duration: 1.2, ease: 'easeOut' }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <motion.span
            className="text-2xl font-bold font-mono"
            style={{ color }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            {Math.round(threat.score)}
          </motion.span>
          <span className="text-xs text-gray-500 uppercase">Threat</span>
        </div>
      </div>
      <span
        className="text-xs font-bold uppercase tracking-wider px-3 py-1 rounded-full"
        style={{ color, backgroundColor: `${color}20` }}
      >
        {getLabel()}
      </span>
    </div>
  );
}

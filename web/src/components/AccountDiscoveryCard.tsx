import { ShieldCheck, CheckCircle2 } from 'lucide-react';
import { motion } from 'framer-motion';
import DataCard from './DataCard';

interface Props {
  services: string[];
  email?: string;
  index?: number;
}

export default function AccountDiscoveryCard({ services, email, index = 0 }: Props) {
  return (
    <DataCard
      title="Account Discovery"
      icon={<ShieldCheck className="w-5 h-5" />}
      count={services.length}
      index={index}
      accentColor="warning"
    >
      <div className="space-y-3">
        {/* Header */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold bg-warning/20 text-warning px-3 py-1 rounded-full">
            Registered on {services.length} service{services.length !== 1 ? 's' : ''}
          </span>
          {email && (
            <span className="text-xs font-mono text-gray-500 truncate">
              {email}
            </span>
          )}
        </div>

        {/* Services list */}
        <div className="space-y-1 max-h-64 overflow-y-auto">
          {services.map((service, i) => (
            <motion.div
              key={service}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.03, duration: 0.2 }}
              className="flex items-center gap-2 bg-navy-700/50 rounded-lg px-3 py-2"
            >
              <CheckCircle2 className="w-4 h-4 text-safe shrink-0" />
              <span className="text-sm text-gray-300">{service}</span>
            </motion.div>
          ))}
        </div>

        {services.length === 0 && (
          <p className="text-sm text-gray-600">No registered accounts discovered</p>
        )}
      </div>
    </DataCard>
  );
}

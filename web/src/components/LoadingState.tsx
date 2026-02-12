import { motion } from 'framer-motion';

interface Props {
  count?: number;
  className?: string;
}

export function SkeletonCard({ className = '' }: { className?: string }) {
  return (
    <div className={`bg-navy-800 border border-navy-600 rounded-xl p-5 ${className}`}>
      <div className="flex items-center gap-3 mb-4">
        <div className="skeleton-pulse w-8 h-8 rounded-lg" />
        <div className="skeleton-pulse h-4 w-32 rounded" />
        <div className="skeleton-pulse h-5 w-8 rounded-full ml-auto" />
      </div>
      <div className="space-y-3">
        <div className="skeleton-pulse h-3 w-full rounded" />
        <div className="skeleton-pulse h-3 w-3/4 rounded" />
        <div className="skeleton-pulse h-3 w-1/2 rounded" />
      </div>
    </div>
  );
}

export default function LoadingState({ count = 6 }: Props) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4"
    >
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} />
      ))}
    </motion.div>
  );
}

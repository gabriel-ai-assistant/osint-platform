import { Users, ExternalLink } from 'lucide-react';
import { motion } from 'framer-motion';
import DataCard from './DataCard';
import type { SocialPresenceProfile } from '../types';

interface Props {
  profiles: SocialPresenceProfile[];
  index?: number;
}

const CATEGORY_COLORS: Record<string, string> = {
  social: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
  dating: 'bg-pink-500/20 text-pink-400 border-pink-500/30',
  coding: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
  music: 'bg-purple-500/20 text-purple-400 border-purple-500/30',
  video: 'bg-red-500/20 text-red-400 border-red-500/30',
  photo: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
  gaming: 'bg-indigo-500/20 text-indigo-400 border-indigo-500/30',
  forum: 'bg-teal-500/20 text-teal-400 border-teal-500/30',
  blog: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
};

const DEFAULT_COLOR = 'bg-gray-500/20 text-gray-400 border-gray-500/30';

function getCategoryStyle(category?: string): string {
  if (!category) return DEFAULT_COLOR;
  return CATEGORY_COLORS[category.toLowerCase()] || DEFAULT_COLOR;
}

function getCategoryDot(category?: string): string {
  const dotColors: Record<string, string> = {
    social: 'bg-blue-400',
    dating: 'bg-pink-400',
    coding: 'bg-emerald-400',
    music: 'bg-purple-400',
    video: 'bg-red-400',
    photo: 'bg-amber-400',
    gaming: 'bg-indigo-400',
    forum: 'bg-teal-400',
    blog: 'bg-orange-400',
  };
  if (!category) return 'bg-gray-400';
  return dotColors[category.toLowerCase()] || 'bg-gray-400';
}

export default function SocialPresenceCard({ profiles, index = 0 }: Props) {
  // Deduplicate by platform+url
  const seen = new Set<string>();
  const unique = profiles.filter((p) => {
    const key = `${p.platform}:${p.url}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });

  // Group by category
  const categories = new Map<string, SocialPresenceProfile[]>();
  for (const p of unique) {
    const cat = p.category || 'other';
    if (!categories.has(cat)) categories.set(cat, []);
    categories.get(cat)!.push(p);
  }

  return (
    <DataCard
      title="Social Media Presence"
      icon={<Users className="w-5 h-5" />}
      count={unique.length}
      index={index}
      accentColor="accent"
    >
      <div className="space-y-4">
        {/* Summary badge */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold bg-accent/20 text-accent px-3 py-1 rounded-full">
            Found on {unique.length} platform{unique.length !== 1 ? 's' : ''}
          </span>
          {/* Provider badges */}
          {[...new Set(unique.map((p) => p.provider))].map((prov) => (
            <span
              key={prov}
              className="text-xs font-mono bg-navy-700 text-gray-500 px-2 py-0.5 rounded"
            >
              via {prov}
            </span>
          ))}
        </div>

        {/* Profile grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {unique.map((profile, i) => (
            <motion.a
              key={`${profile.platform}-${profile.url}`}
              href={profile.url}
              target="_blank"
              rel="noopener noreferrer"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: i * 0.03, duration: 0.25, ease: 'easeOut' }}
              className={`group relative flex items-center gap-2 rounded-lg border px-3 py-2 transition-all duration-200 hover:scale-[1.02] hover:shadow-lg ${getCategoryStyle(profile.category)}`}
            >
              {/* Category dot */}
              <span className={`w-2 h-2 rounded-full shrink-0 ${getCategoryDot(profile.category)}`} />
              {/* Platform name */}
              <span className="text-xs font-medium truncate flex-1">
                {profile.platform}
              </span>
              {/* External link icon */}
              <ExternalLink className="w-3 h-3 opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
            </motion.a>
          ))}
        </div>

        {/* Category legend */}
        {categories.size > 1 && (
          <div className="flex flex-wrap gap-2 pt-2 border-t border-navy-700">
            {Array.from(categories.entries()).map(([cat, items]) => (
              <span key={cat} className="flex items-center gap-1 text-xs text-gray-500">
                <span className={`w-2 h-2 rounded-full ${getCategoryDot(cat)}`} />
                {cat} ({items.length})
              </span>
            ))}
          </div>
        )}
      </div>
    </DataCard>
  );
}

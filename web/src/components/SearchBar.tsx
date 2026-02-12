import { useState } from 'react';
import { Search, Loader2 } from 'lucide-react';

interface Props {
  onSearch: (query: string, queryType?: string) => void;
  loading?: boolean;
  placeholder?: string;
}

function detectType(query: string): string | undefined {
  const q = query.trim();
  if (/^\d{1,3}(\.\d{1,3}){3}$/.test(q)) return 'ip';
  if (q.includes('@') && q.includes('.')) return 'email';
  if (q.startsWith('http://') || q.startsWith('https://')) return 'url';
  const stripped = q.replace(/[-() ]/g, '');
  if (stripped.startsWith('+') && /^\d{10,}$/.test(stripped.slice(1))) return 'phone';
  if (q.includes('.') && !q.includes(' ')) return 'domain';
  return undefined;
}

export default function SearchBar({ onSearch, loading, placeholder }: Props) {
  const [query, setQuery] = useState('');
  const detectedType = query ? detectType(query) : undefined;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim(), detectedType);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative">
      <div className="flex items-center gap-2 bg-navy-800 border border-navy-600 rounded-xl px-4 py-3 focus-within:border-accent/50 focus-within:glow-accent transition-all duration-200">
        {loading ? (
          <Loader2 className="w-5 h-5 text-accent animate-spin" />
        ) : (
          <Search className="w-5 h-5 text-gray-500" />
        )}
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder={placeholder || 'Search IP, domain, email, phone, or URL...'}
          className="flex-1 bg-transparent text-gray-100 placeholder-gray-600 outline-none text-sm font-mono"
        />
        {detectedType && (
          <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-accent/20 text-accent">
            {detectedType}
          </span>
        )}
        <button
          type="submit"
          disabled={!query.trim() || loading}
          className="px-4 py-1.5 bg-accent/10 text-accent border border-accent/20 rounded-lg text-sm font-semibold hover:bg-accent/20 disabled:opacity-30 disabled:cursor-not-allowed transition-all cursor-pointer"
        >
          Search
        </button>
      </div>
    </form>
  );
}

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search, Plus, Eye, RefreshCw, Archive, Loader2, FolderOpen,
  Clock, User, ChevronRight,
} from 'lucide-react';
import { api } from '../api/client';
import type { InvestigationSummary } from '../types';

interface Props {
  onOpen: (id: string) => void;
  onNew: () => void;
}

type StatusFilter = 'all' | 'active' | 'archived';

export default function InvestigationsList({ onOpen, onNew }: Props) {
  const [items, setItems] = useState<InvestigationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState<StatusFilter>('all');
  const [rerunningId, setRerunningId] = useState<string | null>(null);

  const fetchList = useCallback(async () => {
    setLoading(true);
    try {
      const status = filter === 'all' ? undefined : filter;
      const data = await api.listInvestigations(status, search || undefined);
      setItems(data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [filter, search]);

  useEffect(() => {
    fetchList();
  }, [fetchList]);

  const handleRerun = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    setRerunningId(id);
    try {
      await api.rerunInvestigation(id);
      fetchList();
    } catch {
      // ignore
    } finally {
      setRerunningId(null);
    }
  };

  const handleArchive = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    try {
      await api.deleteInvestigation(id);
      fetchList();
    } catch {
      // ignore
    }
  };

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString('en-US', {
      month: 'short', day: 'numeric', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  };

  const statusBadge = (status: string) => {
    const colours: Record<string, string> = {
      active: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/20',
      archived: 'bg-gray-500/15 text-gray-400 border-gray-500/20',
      closed: 'bg-red-500/15 text-red-400 border-red-500/20',
    };
    return colours[status] || colours.active;
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-100">Investigations</h2>
          <p className="text-xs text-gray-500 mt-0.5">
            {items.length} investigation{items.length !== 1 ? 's' : ''}
          </p>
        </div>
        <button
          onClick={onNew}
          className="flex items-center gap-2 px-4 py-2 bg-accent/10 text-accent border border-accent/20 rounded-lg text-sm font-semibold hover:bg-accent/20 transition-all cursor-pointer"
        >
          <Plus className="w-4 h-4" />
          New Investigation
        </button>
      </div>

      {/* Search & Filter */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name, email, phone..."
            className="w-full bg-navy-800 border border-navy-600 rounded-lg pl-10 pr-4 py-2 text-sm text-gray-200 placeholder-gray-600 focus:border-accent/50 focus:outline-none transition-colors"
          />
        </div>
        <div className="flex bg-navy-800 border border-navy-600 rounded-lg overflow-hidden">
          {(['all', 'active', 'archived'] as StatusFilter[]).map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-2 text-xs font-medium capitalize transition-colors cursor-pointer ${
                filter === f
                  ? 'bg-accent/10 text-accent'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-navy-700'
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-6 h-6 text-accent animate-spin" />
        </div>
      ) : items.length === 0 ? (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-navy-800 border border-navy-600 rounded-xl p-12 text-center"
        >
          <FolderOpen className="w-12 h-12 text-gray-600 mx-auto mb-3" />
          <h3 className="text-gray-300 font-medium mb-1">No investigations yet</h3>
          <p className="text-sm text-gray-500 mb-4">Start your first one.</p>
          <button
            onClick={onNew}
            className="inline-flex items-center gap-2 px-4 py-2 bg-accent/10 text-accent border border-accent/20 rounded-lg text-sm font-semibold hover:bg-accent/20 transition-all cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            New Investigation
          </button>
        </motion.div>
      ) : (
        <div className="space-y-2">
          <AnimatePresence mode="popLayout">
            {items.map((item) => (
              <motion.div
                key={item.id}
                layout
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                onClick={() => onOpen(item.id)}
                className="bg-navy-800 border border-navy-600 rounded-xl p-4 flex items-center gap-4 hover:border-accent/30 transition-all cursor-pointer group"
              >
                {/* Icon */}
                <div className="w-10 h-10 rounded-lg bg-navy-700 flex items-center justify-center shrink-0">
                  <User className="w-5 h-5 text-gray-400" />
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-sm font-semibold text-gray-200 truncate">
                      {item.name || item.subject_name || 'Unnamed Investigation'}
                    </span>
                    <span className={`text-[10px] font-medium uppercase px-1.5 py-0.5 rounded border ${statusBadge(item.status)}`}>
                      {item.status}
                    </span>
                    {item.has_results && (
                      <span className="text-[10px] font-medium text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded">
                        Results ✓
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 text-xs text-gray-500">
                    {item.subject_name && item.name && (
                      <span>Subject: {item.subject_name}</span>
                    )}
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {formatDate(item.updated_at)}
                    </span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={(e) => { e.stopPropagation(); onOpen(item.id); }}
                    className="p-1.5 rounded-lg hover:bg-navy-700 text-gray-400 hover:text-accent transition-colors cursor-pointer"
                    title="View"
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                  <button
                    onClick={(e) => handleRerun(e, item.id)}
                    disabled={rerunningId === item.id}
                    className="p-1.5 rounded-lg hover:bg-navy-700 text-gray-400 hover:text-accent transition-colors cursor-pointer disabled:opacity-40"
                    title="Re-run"
                  >
                    <RefreshCw className={`w-4 h-4 ${rerunningId === item.id ? 'animate-spin' : ''}`} />
                  </button>
                  {item.status !== 'archived' && (
                    <button
                      onClick={(e) => handleArchive(e, item.id)}
                      className="p-1.5 rounded-lg hover:bg-navy-700 text-gray-400 hover:text-red-400 transition-colors cursor-pointer"
                      title="Archive"
                    >
                      <Archive className="w-4 h-4" />
                    </button>
                  )}
                </div>

                <ChevronRight className="w-4 h-4 text-gray-600 group-hover:text-gray-400 transition-colors shrink-0" />
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}

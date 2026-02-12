import { useState } from 'react';
import { motion } from 'framer-motion';
import { Crosshair, User, Mail, Phone, Globe, Building2, Wifi, Loader2 } from 'lucide-react';
import { useInvestigate } from '../hooks/useApi';
import ResultsMatrix from './ResultsMatrix';
import LoadingState from './LoadingState';
import type { InvestigateRequest, InvestigateResponse } from '../types';

const fields = [
  { key: 'name', label: 'Full Name', icon: User, placeholder: 'John Doe' },
  { key: 'email', label: 'Email', icon: Mail, placeholder: 'john@example.com' },
  { key: 'phone', label: 'Phone', icon: Phone, placeholder: '+1234567890' },
  { key: 'ip', label: 'IP Address', icon: Wifi, placeholder: '8.8.8.8' },
  { key: 'domain', label: 'Domain', icon: Globe, placeholder: 'example.com' },
  { key: 'company', label: 'Company', icon: Building2, placeholder: 'Acme Corp' },
] as const;

export default function InvestigationPanel() {
  const [form, setForm] = useState<InvestigateRequest>({});
  const investigate = useInvestigate();
  const [results, setResults] = useState<InvestigateResponse | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Check at least one field
    const hasValue = Object.values(form).some((v) => v && v.trim());
    if (!hasValue) return;

    investigate.mutate(form, {
      onSuccess: (data) => setResults(data),
    });
  };

  const updateField = (key: string, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value || undefined }));
  };

  return (
    <div className="space-y-6">
      {/* Investigation Form */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-navy-800 border border-navy-600 rounded-xl p-6"
      >
        <div className="flex items-center gap-3 mb-6">
          <Crosshair className="w-5 h-5 text-accent" />
          <h2 className="text-lg font-semibold text-gray-100">New Investigation</h2>
          <span className="text-xs text-gray-500">Enter any combination of identifiers</span>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {fields.map(({ key, label, icon: Icon, placeholder }) => (
              <div key={key}>
                <label className="flex items-center gap-2 text-xs font-medium text-gray-400 mb-1.5">
                  <Icon className="w-3.5 h-3.5" />
                  {label}
                </label>
                <input
                  type="text"
                  value={(form as any)[key] || ''}
                  onChange={(e) => updateField(key, e.target.value)}
                  placeholder={placeholder}
                  className="w-full bg-navy-900 border border-navy-600 rounded-lg px-3 py-2 text-sm font-mono text-gray-200 placeholder-gray-700 focus:border-accent/50 focus:outline-none transition-colors"
                />
              </div>
            ))}
          </div>

          <div className="flex items-center gap-4 mt-6">
            <button
              type="submit"
              disabled={investigate.isPending}
              className="flex items-center gap-2 px-6 py-2.5 bg-accent/10 text-accent border border-accent/20 rounded-lg text-sm font-semibold hover:bg-accent/20 disabled:opacity-40 disabled:cursor-not-allowed transition-all cursor-pointer"
            >
              {investigate.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Crosshair className="w-4 h-4" />
              )}
              {investigate.isPending ? 'Investigating...' : 'Launch Investigation'}
            </button>
            {investigate.isPending && (
              <span className="text-xs text-gray-500 animate-pulse">
                Querying all providers concurrently...
              </span>
            )}
          </div>
        </form>

        {investigate.isError && (
          <div className="mt-4 bg-threat/10 border border-threat/20 rounded-lg p-3 text-sm text-threat">
            Error: {(investigate.error as Error).message}
          </div>
        )}
      </motion.div>

      {/* Results */}
      {investigate.isPending && <LoadingState count={8} />}
      {results && !investigate.isPending && <ResultsMatrix data={results} />}
    </div>
  );
}

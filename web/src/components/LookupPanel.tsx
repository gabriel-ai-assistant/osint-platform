import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import SearchBar from './SearchBar';
import { useLookup } from '../hooks/useApi';
import type { LookupResponse } from '../types';

export default function LookupPanel() {
  const lookup = useLookup();
  const [results, setResults] = useState<LookupResponse | null>(null);

  const handleSearch = (query: string, queryType?: string) => {
    lookup.mutate(
      { query, query_type: queryType },
      { onSuccess: (data) => setResults(data) }
    );
  };

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h2 className="text-lg font-semibold text-gray-100 mb-4">Quick Lookup</h2>
        <SearchBar onSearch={handleSearch} loading={lookup.isPending} />
      </motion.div>

      {lookup.isError && (
        <div className="bg-threat/10 border border-threat/20 rounded-lg p-3 text-sm text-threat">
          Error: {(lookup.error as Error).message}
        </div>
      )}

      <AnimatePresence>
        {results && !lookup.isPending && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="space-y-4"
          >
            {/* Summary */}
            <div className="bg-navy-800 border border-navy-600 rounded-xl p-5">
              <div className="flex items-center gap-4 mb-3">
                <span className="font-mono text-accent text-sm">{results.query}</span>
                <span className="text-xs bg-accent/20 text-accent px-2 py-0.5 rounded-full">
                  {results.query_type}
                </span>
                <span className="text-xs text-gray-500">
                  {results.providers_queried.length} providers
                </span>
              </div>
              {results.providers_failed.length > 0 && (
                <div className="text-xs text-threat mb-2">
                  Failed: {results.providers_failed.join(', ')}
                </div>
              )}
            </div>

            {/* Reports */}
            {results.reports.map((report: any, i: number) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className="bg-navy-800 border border-navy-600 rounded-xl p-5"
              >
                <div className="flex items-center gap-3 mb-3">
                  <span className="text-xs font-semibold uppercase tracking-wider text-accent">
                    {report.provider}
                  </span>
                  {report.reputation_score != null && (
                    <span className="text-xs font-mono text-gray-500">
                      Rep: {(report.reputation_score * 100).toFixed(0)}%
                    </span>
                  )}
                </div>

                {/* Dynamic rendering based on report type */}
                <div className="space-y-2 text-sm">
                  {/* IP Report */}
                  {report.ip && (
                    <>
                      <div className="font-mono text-gray-300">{report.ip}</div>
                      {report.hostnames?.length > 0 && (
                        <div className="text-xs text-gray-500">
                          Hostnames: {report.hostnames.join(', ')}
                        </div>
                      )}
                      {report.geo && (
                        <div className="text-xs text-gray-400">
                          📍 {[report.geo.city, report.geo.country].filter(Boolean).join(', ')}
                          {report.geo.org && ` — ${report.geo.org}`}
                        </div>
                      )}
                      {report.ports?.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {report.ports.slice(0, 20).map((p: any, j: number) => (
                            <span key={j} className="text-xs font-mono bg-navy-900 text-gray-400 px-2 py-0.5 rounded">
                              {p.port}/{p.protocol}
                            </span>
                          ))}
                        </div>
                      )}
                      {report.vulns?.length > 0 && (
                        <div className="mt-2">
                          <span className="text-xs text-threat">
                            ⚠ {report.vulns.length} vulnerabilities
                          </span>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {report.vulns.slice(0, 10).map((v: any, j: number) => (
                              <span key={j} className="text-xs font-mono bg-threat/10 text-threat px-2 py-0.5 rounded">
                                {v.cve_id}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </>
                  )}

                  {/* Domain Report */}
                  {report.domain && !report.ip && (
                    <>
                      <div className="font-mono text-safe">{report.domain}</div>
                      {report.organization && (
                        <div className="text-xs text-gray-400">Org: {report.organization}</div>
                      )}
                      {report.emails?.length > 0 && (
                        <div className="mt-2 space-y-1">
                          <div className="text-xs text-gray-500 mb-1">
                            {report.emails.length} emails found
                          </div>
                          {report.emails.slice(0, 5).map((e: any, j: number) => (
                            <div key={j} className="text-xs font-mono text-gray-400">
                              {e.email}
                              {e.confidence != null && (
                                <span className="text-gray-600 ml-2">({e.confidence}%)</span>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                      {report.technologies?.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {report.technologies.map((t: string, j: number) => (
                            <span key={j} className="text-xs bg-navy-900 text-gray-400 px-1.5 py-0.5 rounded">
                              {t}
                            </span>
                          ))}
                        </div>
                      )}
                    </>
                  )}

                  {/* Email Report */}
                  {report.email && !report.domain && (
                    <>
                      <div className="font-mono text-warning">{report.email}</div>
                      {report.deliverable !== null && (
                        <span className={`text-xs ${report.deliverable ? 'text-safe' : 'text-threat'}`}>
                          {report.deliverable ? '✓ Deliverable' : '✗ Undeliverable'}
                        </span>
                      )}
                      {report.disposable && (
                        <span className="text-xs text-threat ml-2">⚠ Disposable</span>
                      )}
                    </>
                  )}

                  {/* URL Report */}
                  {report.url && (
                    <>
                      <div className="font-mono text-gray-300 break-all">{report.url}</div>
                      {report.malicious !== null && (
                        <span className={`text-xs ${report.malicious ? 'text-threat' : 'text-safe'}`}>
                          {report.malicious ? '⚠ MALICIOUS' : '✓ Clean'}
                        </span>
                      )}
                    </>
                  )}

                  {/* Raw data toggle */}
                  {report.raw && Object.keys(report.raw).length > 0 && (
                    <details className="mt-3">
                      <summary className="text-xs text-gray-600 cursor-pointer hover:text-gray-400">
                        Show raw data
                      </summary>
                      <pre className="mt-2 text-xs font-mono text-gray-500 bg-navy-900 rounded-lg p-3 overflow-x-auto max-h-60">
                        {JSON.stringify(report.raw, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              </motion.div>
            ))}

            {results.reports.length === 0 && (
              <div className="bg-navy-800 border border-navy-600 rounded-xl p-8 text-center text-gray-500">
                No results found. The query may not match any provider's supported types, or all providers failed.
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

import { motion } from 'framer-motion';
import { Server, CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import { useProviders } from '../hooks/useApi';

const providerIcons: Record<string, string> = {
  shodan: '🔍',
  hunter: '📧',
  virustotal: '🛡️',
  otx: '🌐',
  abuseipdb: '⚠️',
  urlscan: '🔗',
  ipinfo: '📍',
  numverify: '📱',
  opencorporates: '🏢',
};

const providerDescriptions: Record<string, string> = {
  shodan: 'Internet-wide scanning — hosts, ports, services, vulnerabilities',
  hunter: 'Email discovery and verification for domains',
  virustotal: 'File, URL, domain, and IP reputation analysis',
  otx: 'Open Threat Exchange — indicators of compromise',
  abuseipdb: 'IP address abuse and blacklist checking',
  urlscan: 'URL scanning and website analysis',
  ipinfo: 'IP geolocation, ASN, and company data',
  numverify: 'Phone number validation and carrier lookup',
  opencorporates: 'Company and corporate entity search',
};

export default function ProvidersPanel() {
  const { data, isLoading, error } = useProviders();

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 text-gray-400">
        <Loader2 className="w-4 h-4 animate-spin" />
        Loading providers...
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-threat/10 border border-threat/20 rounded-lg p-3 text-sm text-threat">
        Failed to load providers: {(error as Error).message}
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center gap-3"
      >
        <Server className="w-5 h-5 text-accent" />
        <h2 className="text-lg font-semibold text-gray-100">Intelligence Providers</h2>
        <span className="text-xs bg-safe/20 text-safe px-2 py-0.5 rounded-full">
          {data.available}/{data.total} online
        </span>
      </motion.div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {data.providers.map((provider, i) => (
          <motion.div
            key={provider.name}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className={`bg-navy-800 border rounded-xl p-5 transition-colors duration-200 ${
              provider.available
                ? 'border-safe/20 hover:border-safe/40'
                : 'border-navy-600 opacity-60'
            }`}
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-3">
                <span className="text-xl">{providerIcons[provider.name] || '🔧'}</span>
                <div>
                  <h3 className="font-semibold text-gray-200 capitalize">{provider.name}</h3>
                  <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">
                    {providerDescriptions[provider.name] || 'OSINT data provider'}
                  </p>
                </div>
              </div>
              {provider.available ? (
                <CheckCircle2 className="w-5 h-5 text-safe shrink-0" />
              ) : (
                <XCircle className="w-5 h-5 text-gray-600 shrink-0" />
              )}
            </div>

            <div className="flex flex-wrap gap-1.5 mb-3">
              {provider.supported_types.map((type) => (
                <span
                  key={type}
                  className="text-xs font-mono bg-navy-900 text-gray-400 px-2 py-0.5 rounded"
                >
                  {type}
                </span>
              ))}
            </div>

            {provider.rate_limit && Object.keys(provider.rate_limit).length > 0 && (
              <div className="text-xs text-gray-600">
                Rate: {provider.rate_limit.rate} req/s
                {provider.rate_limit.capacity && ` (burst: ${provider.rate_limit.capacity})`}
              </div>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  );
}

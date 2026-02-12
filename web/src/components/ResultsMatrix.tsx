import {
  Globe, Mail, Phone, MapPin, Link2, AlertTriangle, Building2, Network,
} from 'lucide-react';
import DataCard from './DataCard';
import ThreatIndicator from './ThreatIndicator';
import GeoMap from './GeoMap';
import NetworkGraph from './NetworkGraph';
import type { InvestigateResponse } from '../types';
import { motion } from 'framer-motion';

interface Props {
  data: InvestigateResponse;
}

export default function ResultsMatrix({ data }: Props) {
  const { identity, network, threats, geo, email_intel, phone_intel, domain_intel, organization, relationships } = data;

  return (
    <div className="space-y-6">
      {/* Subject Summary */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-navy-800 border border-navy-600 rounded-xl p-6 flex flex-col md:flex-row items-center gap-6"
      >
        {/* Avatar placeholder */}
        <div className="w-20 h-20 rounded-full bg-navy-700 border-2 border-accent/30 flex items-center justify-center text-2xl text-accent shrink-0">
          {identity.name ? identity.name.charAt(0).toUpperCase() : '?'}
        </div>
        <div className="flex-1 min-w-0">
          <h2 className="text-xl font-bold text-gray-100">
            {identity.name || 'Unknown Subject'}
          </h2>
          <div className="flex flex-wrap gap-2 mt-2">
            {identity.emails.slice(0, 3).map((e) => (
              <span key={e} className="text-xs font-mono bg-navy-700 text-gray-400 px-2 py-1 rounded">
                {e}
              </span>
            ))}
            {identity.ips.slice(0, 3).map((ip) => (
              <span key={ip} className="text-xs font-mono bg-navy-700 text-accent px-2 py-1 rounded">
                {ip}
              </span>
            ))}
            {identity.domains.slice(0, 3).map((d) => (
              <span key={d} className="text-xs font-mono bg-navy-700 text-safe px-2 py-1 rounded">
                {d}
              </span>
            ))}
          </div>
          <div className="flex gap-4 mt-3 text-xs text-gray-500">
            <span>{data.providers_queried.length} providers queried</span>
            <span>{data.query_count} queries executed</span>
            {data.providers_failed.length > 0 && (
              <span className="text-threat">{data.providers_failed.length} failed</span>
            )}
          </div>
        </div>
        <ThreatIndicator threat={threats} />
      </motion.div>

      {/* Intel Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
        {/* Network Intelligence */}
        <DataCard
          title="Network Intelligence"
          icon={<Globe className="w-5 h-5" />}
          count={network.ips.length + network.ports.length}
          index={0}
        >
          {network.ips.length > 0 ? (
            <div className="space-y-2">
              {network.ips.map((ip: any, i: number) => (
                <div key={i} className="bg-navy-700/50 rounded-lg p-3">
                  <div className="font-mono text-sm text-accent">{ip.ip}</div>
                  {ip.hostnames?.length > 0 && (
                    <div className="text-xs text-gray-500 mt-1">
                      {ip.hostnames.join(', ')}
                    </div>
                  )}
                  {ip.os && <div className="text-xs text-gray-500">OS: {ip.os}</div>}
                </div>
              ))}
              {network.ports.length > 0 && (
                <div className="mt-2">
                  <div className="text-xs text-gray-500 mb-1">Open Ports</div>
                  <div className="flex flex-wrap gap-1.5">
                    {network.ports.slice(0, 20).map((p: any, i: number) => (
                      <span key={i} className="text-xs font-mono bg-navy-900 text-gray-400 px-2 py-0.5 rounded">
                        {p.port}/{p.protocol}
                        {p.service && ` (${p.service})`}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-gray-600">No network data collected</p>
          )}
        </DataCard>

        {/* Email Intelligence */}
        <DataCard
          title="Email Intelligence"
          icon={<Mail className="w-5 h-5" />}
          count={email_intel.emails.length + email_intel.verified.length}
          index={1}
          accentColor="warning"
        >
          {email_intel.emails.length > 0 || email_intel.verified.length > 0 ? (
            <div className="space-y-2">
              {email_intel.verified.map((v: any, i: number) => (
                <div key={`v-${i}`} className="bg-navy-700/50 rounded-lg p-3">
                  <div className="font-mono text-sm text-warning">{v.email}</div>
                  <div className="flex gap-2 mt-1 text-xs">
                    {v.deliverable !== null && (
                      <span className={v.deliverable ? 'text-safe' : 'text-threat'}>
                        {v.deliverable ? '✓ Deliverable' : '✗ Undeliverable'}
                      </span>
                    )}
                    {v.disposable && <span className="text-threat">⚠ Disposable</span>}
                    {v.confidence != null && (
                      <span className="text-gray-500">Confidence: {v.confidence}%</span>
                    )}
                  </div>
                  {(v.first_name || v.last_name) && (
                    <div className="text-xs text-gray-400 mt-1">
                      {[v.first_name, v.last_name].filter(Boolean).join(' ')}
                      {v.organization && ` @ ${v.organization}`}
                    </div>
                  )}
                </div>
              ))}
              {email_intel.emails.slice(0, 10).map((e: any, i: number) => (
                <div key={`e-${i}`} className="bg-navy-700/50 rounded-lg p-3">
                  <div className="font-mono text-sm text-gray-300">{e.email}</div>
                  <div className="text-xs text-gray-500 mt-1">
                    {[e.first_name, e.last_name].filter(Boolean).join(' ')}
                    {e.position && ` — ${e.position}`}
                    {e.department && ` (${e.department})`}
                  </div>
                  {e.confidence != null && (
                    <div className="text-xs text-gray-600 mt-0.5">
                      Confidence: {e.confidence}%
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-600">No email data collected</p>
          )}
        </DataCard>

        {/* Phone Intelligence */}
        <DataCard
          title="Phone Intelligence"
          icon={<Phone className="w-5 h-5" />}
          count={phone_intel.numbers.length}
          index={2}
        >
          {phone_intel.numbers.length > 0 ? (
            <div className="space-y-2">
              {phone_intel.numbers.map((p: any, i: number) => (
                <div key={i} className="bg-navy-700/50 rounded-lg p-3">
                  <div className="font-mono text-sm text-accent">{p.number || p.phone}</div>
                  {p.carrier && <div className="text-xs text-gray-500">Carrier: {p.carrier}</div>}
                  {p.line_type && <div className="text-xs text-gray-500">Type: {p.line_type}</div>}
                  {p.country_name && <div className="text-xs text-gray-500">Country: {p.country_name}</div>}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-600">No phone data collected</p>
          )}
        </DataCard>

        {/* Geolocation */}
        <DataCard
          title="Geolocation"
          icon={<MapPin className="w-5 h-5" />}
          count={geo.locations.length}
          index={3}
          accentColor="safe"
        >
          <GeoMap locations={geo.locations} />
          {geo.locations.length > 0 && (
            <div className="mt-3 space-y-1">
              {geo.locations.map((loc, i) => (
                <div key={i} className="flex items-center gap-2 text-xs text-gray-400">
                  <span className="font-mono text-accent">{loc.ip}</span>
                  <span>→</span>
                  <span>{[loc.city, loc.country].filter(Boolean).join(', ')}</span>
                  {loc.org && <span className="text-gray-600">({loc.org})</span>}
                </div>
              ))}
            </div>
          )}
        </DataCard>

        {/* Domain Intelligence */}
        <DataCard
          title="Domain Intelligence"
          icon={<Link2 className="w-5 h-5" />}
          count={domain_intel.domains.length + domain_intel.subdomains.length}
          index={4}
          accentColor="safe"
        >
          {domain_intel.domains.length > 0 ? (
            <div className="space-y-2">
              {domain_intel.domains.map((d: any, i: number) => (
                <div key={i} className="bg-navy-700/50 rounded-lg p-3">
                  <div className="font-mono text-sm text-safe">{d.domain}</div>
                  {d.organization && (
                    <div className="text-xs text-gray-500 mt-1">Org: {d.organization}</div>
                  )}
                  {d.technologies?.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {d.technologies.map((t: string, j: number) => (
                        <span key={j} className="text-xs bg-navy-900 text-gray-400 px-1.5 py-0.5 rounded">
                          {t}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              {Object.keys(domain_intel.dns_records).length > 0 && (
                <div className="mt-2">
                  <div className="text-xs text-gray-500 mb-1">DNS Records</div>
                  {Object.entries(domain_intel.dns_records).map(([type, records]) => (
                    <div key={type} className="text-xs font-mono text-gray-400">
                      <span className="text-accent">{type}:</span> {records.join(', ')}
                    </div>
                  ))}
                </div>
              )}
              {domain_intel.subdomains.length > 0 && (
                <div className="mt-2">
                  <div className="text-xs text-gray-500 mb-1">Subdomains</div>
                  <div className="flex flex-wrap gap-1">
                    {domain_intel.subdomains.slice(0, 15).map((s, i) => (
                      <span key={i} className="text-xs font-mono bg-navy-900 text-gray-400 px-1.5 py-0.5 rounded">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-gray-600">No domain data collected</p>
          )}
        </DataCard>

        {/* Threat Assessment */}
        <DataCard
          title="Threat Assessment"
          icon={<AlertTriangle className="w-5 h-5" />}
          count={threats.vulnerabilities.length + threats.indicators.length}
          index={5}
          accentColor="threat"
        >
          <div className="space-y-3">
            <div className="flex gap-4 text-xs">
              <div className={`flex items-center gap-1 ${threats.malware_detected ? 'text-threat' : 'text-safe'}`}>
                {threats.malware_detected ? '⚠ Malware Detected' : '✓ No Malware'}
              </div>
              <div className={`flex items-center gap-1 ${threats.phishing_detected ? 'text-threat' : 'text-safe'}`}>
                {threats.phishing_detected ? '⚠ Phishing Detected' : '✓ No Phishing'}
              </div>
            </div>
            {threats.indicators.length > 0 && (
              <div className="space-y-1">
                {threats.indicators.map((ind, i) => (
                  <div key={i} className="text-xs text-warning bg-warning/10 px-2 py-1 rounded">
                    {ind}
                  </div>
                ))}
              </div>
            )}
            {threats.vulnerabilities.length > 0 && (
              <div>
                <div className="text-xs text-gray-500 mb-1">Vulnerabilities</div>
                <div className="space-y-1 max-h-40 overflow-y-auto">
                  {threats.vulnerabilities.map((v: any, i: number) => (
                    <div key={i} className="text-xs font-mono bg-navy-900 rounded px-2 py-1 flex justify-between">
                      <span className="text-threat">{v.cve_id}</span>
                      {v.cvss != null && (
                        <span className={v.cvss >= 7 ? 'text-threat' : v.cvss >= 4 ? 'text-warning' : 'text-gray-400'}>
                          CVSS {v.cvss}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
            {threats.vulnerabilities.length === 0 && threats.indicators.length === 0 && (
              <p className="text-sm text-gray-600">No threats detected</p>
            )}
          </div>
        </DataCard>

        {/* Organization */}
        <DataCard
          title="Organization"
          icon={<Building2 className="w-5 h-5" />}
          count={organization.companies.length}
          index={6}
        >
          {organization.companies.length > 0 ? (
            <div className="space-y-2">
              {organization.companies.map((c: any, i: number) => (
                <div key={i} className="bg-navy-700/50 rounded-lg p-3">
                  <div className="font-semibold text-sm text-gray-200">{c.name}</div>
                  {c.domain && <div className="text-xs text-gray-500 font-mono">{c.domain}</div>}
                  {c.source && <div className="text-xs text-gray-600">Source: {c.source}</div>}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-600">No organization data collected</p>
          )}
        </DataCard>

        {/* Relationship Graph */}
        <DataCard
          title="Relationship Graph"
          icon={<Network className="w-5 h-5" />}
          count={relationships.length}
          index={7}
          accentColor="accent"
        >
          <NetworkGraph relationships={relationships} />
        </DataCard>
      </div>
    </div>
  );
}

import {
  Globe, Mail, Phone, MapPin, Link2, AlertTriangle, Building2, Network,
  Fingerprint, ExternalLink,
} from 'lucide-react';
import DataCard from './DataCard';
import ThreatIndicator from './ThreatIndicator';
import GeoMap from './GeoMap';
import NetworkGraph from './NetworkGraph';
import SocialPresenceCard from './SocialPresenceCard';
import AccountDiscoveryCard from './AccountDiscoveryCard';
import { api } from '../api/client';
import type { InvestigateResponse } from '../types';
import { motion } from 'framer-motion';

interface Props {
  data: InvestigateResponse;
}

/* ─── Social media icon/label helpers ─────────────────────── */

const SOCIAL_LABELS: Record<string, { label: string; color: string; urlPrefix?: string }> = {
  twitter: { label: 'Twitter/X', color: 'text-sky-400', urlPrefix: 'https://x.com/' },
  facebook: { label: 'Facebook', color: 'text-blue-500', urlPrefix: 'https://facebook.com/' },
  linkedin: { label: 'LinkedIn', color: 'text-blue-400', urlPrefix: 'https://linkedin.com/in/' },
  instagram: { label: 'Instagram', color: 'text-pink-400', urlPrefix: 'https://instagram.com/' },
  tiktok: { label: 'TikTok', color: 'text-gray-300', urlPrefix: 'https://tiktok.com/@' },
  reddit: { label: 'Reddit', color: 'text-orange-400', urlPrefix: 'https://reddit.com/user/' },
  github: { label: 'GitHub', color: 'text-gray-300', urlPrefix: 'https://github.com/' },
};

function makeSocialUrl(platform: string, handle: string): string {
  // If it's already a URL, use as-is
  if (handle.startsWith('http://') || handle.startsWith('https://')) return handle;
  const info = SOCIAL_LABELS[platform];
  const cleanHandle = handle.replace(/^@/, '').replace(/^u\//, '');
  return info?.urlPrefix ? `${info.urlPrefix}${cleanHandle}` : handle;
}

export default function ResultsMatrix({ data }: Props) {
  const { identity, network, threats, geo, email_intel, phone_intel, domain_intel, organization, digital_footprint, social_presence, registered_services, relationships } = data;

  const socialMedia = digital_footprint.social_media ?? {};
  const hasSocial = Object.keys(socialMedia).length > 0;

  return (
    <div className="space-y-6">
      {/* ── Subject Summary / Identity Profile ── */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-navy-800 border border-navy-600 rounded-xl p-6 flex flex-col md:flex-row items-start gap-6"
      >
        {/* Avatar */}
        <div className="shrink-0">
          {identity.photo_ids && identity.photo_ids.length > 0 ? (
            <img
              src={api.getPhotoUrl(identity.photo_ids[0])}
              alt="Subject"
              className="w-20 h-20 rounded-full object-cover border-2 border-accent/30"
            />
          ) : (
            <div className="w-20 h-20 rounded-full bg-navy-700 border-2 border-accent/30 flex items-center justify-center text-2xl text-accent">
              {identity.name ? identity.name.charAt(0).toUpperCase() : '?'}
            </div>
          )}
        </div>

        <div className="flex-1 min-w-0">
          <h2 className="text-xl font-bold text-gray-100">
            {identity.name || 'Unknown Subject'}
          </h2>

          {/* Aliases */}
          {identity.aliases && identity.aliases.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-1">
              <span className="text-xs text-gray-500">aka</span>
              {identity.aliases.map((a) => (
                <span key={a} className="text-xs font-mono bg-accent/10 text-accent px-2 py-0.5 rounded-full">
                  {a}
                </span>
              ))}
            </div>
          )}

          {/* Key identity facts */}
          <div className="flex flex-wrap gap-x-4 gap-y-1 mt-2 text-xs text-gray-400">
            {identity.date_of_birth && (
              <span>DOB: <span className="text-gray-300">{identity.date_of_birth}</span></span>
            )}
            {identity.age_range && (
              <span>Age: <span className="text-gray-300">{identity.age_range}</span></span>
            )}
            {identity.gender && (
              <span>Gender: <span className="text-gray-300">{identity.gender}</span></span>
            )}
            {identity.nationality && (
              <span>Nationality: <span className="text-gray-300">{identity.nationality}</span></span>
            )}
            {identity.location && (
              <span><MapPin className="w-3 h-3 inline" /> <span className="text-gray-300">{identity.location}</span></span>
            )}
            {identity.employer && (
              <span>Employer: <span className="text-gray-300">{identity.employer}</span></span>
            )}
            {identity.occupation && (
              <span>Title: <span className="text-gray-300">{identity.occupation}</span></span>
            )}
            {identity.education && (
              <span>Education: <span className="text-gray-300">{identity.education}</span></span>
            )}
          </div>

          {/* Identifiers chips */}
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

          {/* Social media links */}
          {hasSocial && (
            <div className="flex flex-wrap gap-2 mt-2">
              {Object.entries(socialMedia).map(([platform, handle]) => {
                const info = SOCIAL_LABELS[platform] || { label: platform, color: 'text-gray-400' };
                return (
                  <a
                    key={platform}
                    href={makeSocialUrl(platform, handle)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={`text-xs flex items-center gap-1 bg-navy-700 px-2 py-1 rounded hover:bg-navy-600 transition-colors ${info.color}`}
                  >
                    {info.label}
                    <ExternalLink className="w-3 h-3" />
                  </a>
                );
              })}
            </div>
          )}

          {/* Physical description */}
          {identity.physical_description && (
            <p className="text-xs text-gray-500 mt-2 italic">{identity.physical_description}</p>
          )}

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

        {/* ── Social Media Presence (Sherlock / Maigret) ── */}
        {social_presence && social_presence.length > 0 && (
          <SocialPresenceCard profiles={social_presence} index={0} />
        )}

        {/* ── Account Discovery (Holehe) ── */}
        {registered_services && registered_services.length > 0 && (
          <AccountDiscoveryCard
            services={registered_services}
            email={identity.emails?.[0]}
            index={1}
          />
        )}

        {/* ── Digital Footprint / Social Media ── */}
        {(hasSocial || digital_footprint.sources.length > 0 || digital_footprint.urls.length > 0) && (
          <DataCard
            title="Digital Footprint"
            icon={<Fingerprint className="w-5 h-5" />}
            count={Object.keys(socialMedia).length + digital_footprint.sources.length + digital_footprint.urls.length}
            index={0}
            accentColor="accent"
          >
            <div className="space-y-3">
              {hasSocial && (
                <div>
                  <div className="text-xs text-gray-500 mb-2">Social Media Profiles</div>
                  <div className="space-y-1.5">
                    {Object.entries(socialMedia).map(([platform, handle]) => {
                      const info = SOCIAL_LABELS[platform] || { label: platform, color: 'text-gray-400' };
                      return (
                        <a
                          key={platform}
                          href={makeSocialUrl(platform, handle)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-2 bg-navy-700/50 rounded-lg px-3 py-2 hover:bg-navy-700 transition-colors"
                        >
                          <span className={`text-xs font-semibold w-20 ${info.color}`}>{info.label}</span>
                          <span className="text-sm font-mono text-gray-300 flex-1 truncate">{handle}</span>
                          <ExternalLink className="w-3.5 h-3.5 text-gray-600" />
                        </a>
                      );
                    })}
                  </div>
                </div>
              )}
              {digital_footprint.sources.length > 0 && (
                <div>
                  <div className="text-xs text-gray-500 mb-1">Discovered Sources</div>
                  <div className="flex flex-wrap gap-1.5">
                    {digital_footprint.sources.map((s, i) => (
                      <span key={i} className="text-xs bg-navy-900 text-gray-400 px-2 py-0.5 rounded font-mono">
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {digital_footprint.urls.length > 0 && (
                <div>
                  <div className="text-xs text-gray-500 mb-1">URLs</div>
                  {digital_footprint.urls.map((u: any, i: number) => (
                    <div key={i} className="bg-navy-700/50 rounded-lg px-3 py-2 mb-1">
                      <a
                        href={u.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="font-mono text-xs text-accent hover:underline"
                      >
                        {u.url}
                      </a>
                      {u.malicious && (
                        <span className="text-xs text-threat ml-2">⚠ Malicious</span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </DataCard>
        )}

        {/* Network Intelligence */}
        <DataCard
          title="Network Intelligence"
          icon={<Globe className="w-5 h-5" />}
          count={network.ips.length + network.ports.length}
          index={1}
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
          index={2}
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
          index={3}
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
          index={4}
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
          index={5}
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
          index={6}
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
          index={7}
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
          index={8}
          accentColor="accent"
        >
          <NetworkGraph relationships={relationships} />
        </DataCard>
      </div>
    </div>
  );
}

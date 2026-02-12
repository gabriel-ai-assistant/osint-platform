/* ── API Response Types ─────────────────────────────────── */

export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
  providers_available: number;
}

export interface ProviderInfo {
  name: string;
  available: boolean;
  supported_types: string[];
  rate_limit: Record<string, number>;
}

export interface ProvidersResponse {
  providers: ProviderInfo[];
  total: number;
  available: number;
}

export interface LookupRequest {
  query: string;
  query_type?: string;
}

export interface LookupResponse {
  query: string;
  query_type: string;
  reports: Record<string, any>[];
  confidence: number;
  providers_queried: string[];
  providers_failed: string[];
  timestamp: string;
}

export interface InvestigateRequest {
  name?: string;
  email?: string;
  phone?: string;
  ip?: string;
  domain?: string;
  company?: string;
}

export interface ThreatInfo {
  score: number;
  level: string;
  abuse_reports: Record<string, any>[];
  malware_detected: boolean;
  phishing_detected: boolean;
  vulnerabilities: Record<string, any>[];
  indicators: string[];
}

export interface GeoLocation {
  ip?: string;
  country?: string;
  country_code?: string;
  city?: string;
  latitude?: number;
  longitude?: number;
  asn?: string;
  org?: string;
}

export interface GeoInfo {
  locations: GeoLocation[];
}

export interface NetworkInfo {
  ips: Record<string, any>[];
  ports: Record<string, any>[];
  services: Record<string, any>[];
  hostnames: string[];
}

export interface EmailContact {
  email: string;
  first_name?: string;
  last_name?: string;
  position?: string;
  department?: string;
  confidence?: number;
}

export interface EmailInfo {
  emails: EmailContact[];
  verified: Record<string, any>[];
}

export interface PhoneInfo {
  numbers: Record<string, any>[];
}

export interface DomainInfo {
  domains: Record<string, any>[];
  dns_records: Record<string, string[]>;
  subdomains: string[];
  technologies: string[];
}

export interface OrganizationInfo {
  companies: Record<string, any>[];
}

export interface IdentityInfo {
  name?: string;
  emails: string[];
  phones: string[];
  ips: string[];
  domains: string[];
  companies: string[];
}

export interface DigitalFootprint {
  sources: string[];
  urls: Record<string, any>[];
}

export interface RelationshipEdge {
  source: string;
  target: string;
  relationship: string;
  source_type: string;
  target_type: string;
}

export interface InvestigateResponse {
  identity: IdentityInfo;
  network: NetworkInfo;
  threats: ThreatInfo;
  geo: GeoInfo;
  email_intel: EmailInfo;
  phone_intel: PhoneInfo;
  domain_intel: DomainInfo;
  organization: OrganizationInfo;
  digital_footprint: DigitalFootprint;
  relationships: RelationshipEdge[];
  providers_queried: string[];
  providers_failed: string[];
  query_count: number;
  timestamp: string;
}

export type NavPage = 'investigation' | 'lookup' | 'providers';

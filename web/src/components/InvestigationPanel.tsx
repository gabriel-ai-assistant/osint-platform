import { useState, useRef, useCallback, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Crosshair, User, Mail, Phone, Globe, Building2, Wifi, Loader2,
  ChevronDown, ChevronUp, MapPin, Camera, FileText, Car, Briefcase,
  GraduationCap, X, Hash, Fingerprint, RefreshCw, MessageSquarePlus,
  Check, Clock, StickyNote, Play, Edit3,
} from 'lucide-react';
import { useInvestigate } from '../hooks/useApi';
import { api } from '../api/client';
import ResultsMatrix from './ResultsMatrix';
import LoadingState from './LoadingState';
import type {
  InvestigateRequest,
  InvestigateResponse,
  InvestigationCreateRequest,
  InvestigationFull,
  PhotoUploadResponse,
  TimelineEvent,
} from '../types';

/* ─── Props ───────────────────────────────────────────────── */

interface PanelProps {
  loadInvestigationId?: string | null;
  onClearLoad?: () => void;
}

/* ─── Collapsible Section ─────────────────────────────────── */

interface SectionProps {
  title: string;
  icon: React.ReactNode;
  defaultOpen?: boolean;
  badge?: string | number;
  children: React.ReactNode;
}

function Section({ title, icon, defaultOpen = false, badge, children }: SectionProps) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className="border-b border-navy-600/50 last:border-b-0">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-3 py-3 px-1 text-left cursor-pointer group"
      >
        <span className="text-gray-500 group-hover:text-accent transition-colors">{icon}</span>
        <span className="text-sm font-semibold text-gray-300 flex-1">{title}</span>
        {badge !== undefined && badge !== 0 && badge !== '' && (
          <span className="text-xs font-mono bg-accent/15 text-accent px-2 py-0.5 rounded-full">
            {badge}
          </span>
        )}
        {open ? (
          <ChevronUp className="w-4 h-4 text-gray-600" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-600" />
        )}
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            key="content"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: 'easeInOut' }}
            className="overflow-hidden"
          >
            <div className="pb-4 px-1">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ─── Tag Input (for aliases) ─────────────────────────────── */

interface TagInputProps {
  tags: string[];
  onChange: (tags: string[]) => void;
  placeholder?: string;
}

function TagInput({ tags, onChange, placeholder }: TagInputProps) {
  const [input, setInput] = useState('');

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && input.trim()) {
      e.preventDefault();
      if (!tags.includes(input.trim())) {
        onChange([...tags, input.trim()]);
      }
      setInput('');
    } else if (e.key === 'Backspace' && !input && tags.length > 0) {
      onChange(tags.slice(0, -1));
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-1.5 bg-navy-900 border border-navy-600 rounded-lg px-3 py-2 min-h-[38px] focus-within:border-accent/50 transition-colors">
      {tags.map((tag) => (
        <span
          key={tag}
          className="flex items-center gap-1 text-xs font-mono bg-accent/15 text-accent px-2 py-0.5 rounded-full"
        >
          {tag}
          <button
            type="button"
            onClick={() => onChange(tags.filter((t) => t !== tag))}
            className="hover:text-white transition-colors cursor-pointer"
          >
            <X className="w-3 h-3" />
          </button>
        </span>
      ))}
      <input
        type="text"
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={tags.length === 0 ? placeholder : ''}
        className="flex-1 min-w-[80px] bg-transparent text-sm font-mono text-gray-200 placeholder-gray-700 focus:outline-none"
      />
    </div>
  );
}

/* ─── Shared Input Components ─────────────────────────────── */

function FieldLabel({ icon: Icon, label }: { icon: React.FC<{ className?: string }>; label: string }) {
  return (
    <label className="flex items-center gap-2 text-xs font-medium text-gray-400 mb-1.5">
      <Icon className="w-3.5 h-3.5" />
      {label}
    </label>
  );
}

const inputClass =
  'w-full bg-navy-900 border border-navy-600 rounded-lg px-3 py-2 text-sm font-mono text-gray-200 placeholder-gray-700 focus:border-accent/50 focus:outline-none transition-colors';

const selectClass =
  'w-full bg-navy-900 border border-navy-600 rounded-lg px-3 py-2 text-sm text-gray-200 focus:border-accent/50 focus:outline-none transition-colors appearance-none cursor-pointer';

const textareaClass =
  'w-full bg-navy-900 border border-navy-600 rounded-lg px-3 py-2 text-sm font-mono text-gray-200 placeholder-gray-700 focus:border-accent/50 focus:outline-none transition-colors resize-y min-h-[60px]';

/* ─── Photo Upload ────────────────────────────────────────── */

interface UploadedPhoto {
  id: string;
  filename: string;
  url: string;
}

interface PhotoUploadProps {
  photos: UploadedPhoto[];
  onAdd: (photo: UploadedPhoto) => void;
  onRemove: (id: string) => void;
}

function PhotoUpload({ photos, onAdd, onRemove }: PhotoUploadProps) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const doUpload = useCallback(
    async (file: File) => {
      setError(null);
      setUploading(true);
      try {
        const resp: PhotoUploadResponse = await api.uploadPhoto(file);
        onAdd({ id: resp.id, filename: resp.filename, url: api.getPhotoUrl(resp.id) });
      } catch (err: any) {
        setError(err.detail || err.message || 'Upload failed');
      } finally {
        setUploading(false);
      }
    },
    [onAdd],
  );

  const handleFiles = useCallback(
    (files: FileList | null) => {
      if (!files) return;
      for (const f of Array.from(files)) {
        if (['image/jpeg', 'image/png', 'image/webp'].includes(f.type)) {
          doUpload(f);
        }
      }
    },
    [doUpload],
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles],
  );

  const handleRemove = useCallback(
    async (id: string) => {
      try {
        await api.deletePhoto(id);
      } catch {
        // ignore — still remove from local state
      }
      onRemove(id);
    },
    [onRemove],
  );

  return (
    <div className="space-y-3">
      {/* Upload area */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => fileRef.current?.click()}
        className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
          dragOver
            ? 'border-accent bg-accent/5'
            : 'border-navy-600 hover:border-accent/40 hover:bg-navy-900/50'
        }`}
      >
        <input
          ref={fileRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          multiple
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
        {uploading ? (
          <Loader2 className="w-8 h-8 mx-auto text-accent animate-spin" />
        ) : (
          <Camera className="w-8 h-8 mx-auto text-gray-600" />
        )}
        <p className="text-xs text-gray-500 mt-2">
          {uploading ? 'Uploading...' : 'Drag & drop photos or click to browse'}
        </p>
        <p className="text-xs text-gray-700 mt-1">JPEG, PNG, WebP — max 10 MB</p>
      </div>

      {error && (
        <div className="text-xs text-threat bg-threat/10 px-3 py-1.5 rounded">{error}</div>
      )}

      {/* Badge */}
      <div className="flex items-center gap-2 text-xs text-gray-500">
        <Camera className="w-3.5 h-3.5" />
        <span>For future facial recognition</span>
      </div>

      {/* Thumbnails */}
      {photos.length > 0 && (
        <div className="grid grid-cols-3 gap-2">
          {photos.map((p) => (
            <div key={p.id} className="relative group rounded-lg overflow-hidden bg-navy-900 aspect-square">
              <img
                src={p.url}
                alt={p.filename}
                className="w-full h-full object-cover"
              />
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  handleRemove(p.id);
                }}
                className="absolute top-1 right-1 w-5 h-5 rounded-full bg-navy-900/80 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer hover:bg-threat/80"
              >
                <X className="w-3 h-3 text-white" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ─── Social Media Grid ───────────────────────────────────── */

const socialPlatforms = [
  { key: 'twitter', label: 'Twitter / X', placeholder: '@handle' },
  { key: 'facebook', label: 'Facebook', placeholder: 'URL or username' },
  { key: 'linkedin', label: 'LinkedIn', placeholder: 'Profile URL' },
  { key: 'instagram', label: 'Instagram', placeholder: '@handle' },
  { key: 'tiktok', label: 'TikTok', placeholder: '@handle' },
  { key: 'reddit', label: 'Reddit', placeholder: 'u/username' },
  { key: 'github', label: 'GitHub', placeholder: 'username' },
] as const;

/* ─── Timeline Component ──────────────────────────────────── */

function TimelineView({ events }: { events: TimelineEvent[] }) {
  if (events.length === 0) return null;

  const iconFor = (type: string) => {
    switch (type) {
      case 'created': return <Play className="w-3 h-3" />;
      case 'updated': return <Edit3 className="w-3 h-3" />;
      case 'rerun': return <RefreshCw className="w-3 h-3" />;
      case 'note_added': return <StickyNote className="w-3 h-3" />;
      default: return <Clock className="w-3 h-3" />;
    }
  };

  const colorFor = (type: string) => {
    switch (type) {
      case 'created': return 'text-emerald-400 bg-emerald-500/15 border-emerald-500/30';
      case 'rerun': return 'text-blue-400 bg-blue-500/15 border-blue-500/30';
      case 'note_added': return 'text-yellow-400 bg-yellow-500/15 border-yellow-500/30';
      case 'updated': return 'text-purple-400 bg-purple-500/15 border-purple-500/30';
      default: return 'text-gray-400 bg-gray-500/15 border-gray-500/30';
    }
  };

  const formatTime = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleString('en-US', {
      month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  };

  return (
    <div className="relative pl-6 space-y-4">
      {/* Vertical line */}
      <div className="absolute left-[11px] top-2 bottom-2 w-px bg-navy-600" />
      {events.map((ev) => (
        <div key={ev.id} className="relative flex items-start gap-3">
          <div className={`absolute left-[-13px] w-6 h-6 rounded-full border flex items-center justify-center ${colorFor(ev.event_type)}`}>
            {iconFor(ev.event_type)}
          </div>
          <div className="ml-4">
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-gray-400 capitalize">
                {ev.event_type.replace('_', ' ')}
              </span>
              <span className="text-[10px] text-gray-600">{formatTime(ev.timestamp)}</span>
            </div>
            {ev.description && (
              <p className="text-xs text-gray-500 mt-0.5">{ev.description}</p>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}

/* ─── Main Component ──────────────────────────────────────── */

const AGE_RANGES = ['', 'Under 18', '18-25', '25-35', '35-45', '45-55', '55-65', '65+'];
const GENDERS = ['', 'Male', 'Female', 'Non-binary', 'Unknown'];

export default function InvestigationPanel({ loadInvestigationId }: PanelProps) {
  const [form, setForm] = useState<InvestigateRequest>({});
  const [caseName, setCaseName] = useState('');
  const [aliases, setAliases] = useState<string[]>([]);
  const [socialMedia, setSocialMedia] = useState<Record<string, string>>({});
  const [photos, setPhotos] = useState<UploadedPhoto[]>([]);
  const investigate = useInvestigate();
  const [results, setResults] = useState<InvestigateResponse | null>(null);
  const [savedId, setSavedId] = useState<string | null>(null);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [rerunning, setRerunning] = useState(false);
  const [showNoteInput, setShowNoteInput] = useState(false);
  const [noteText, setNoteText] = useState('');
  const [addingNote, setAddingNote] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  // Load an existing investigation when loadInvestigationId changes
  useEffect(() => {
    if (!loadInvestigationId) return;
    let cancelled = false;

    (async () => {
      try {
        const inv: InvestigationFull = await api.getInvestigation(loadInvestigationId);
        if (cancelled) return;

        setCaseName(inv.name || '');
        setForm({
          name: inv.subject_name || undefined,
          email: inv.email || undefined,
          phone: inv.phone || undefined,
          ip: inv.ip || undefined,
          domain: inv.domain || undefined,
          company: inv.company || undefined,
          aliases: inv.aliases,
          date_of_birth: inv.date_of_birth || undefined,
          age_range: inv.age_range || undefined,
          location: inv.location || undefined,
          address: inv.address || undefined,
          nationality: inv.nationality || undefined,
          gender: inv.gender || undefined,
          employer: inv.employer || undefined,
          occupation: inv.occupation || undefined,
          education: inv.education || undefined,
          vehicle: inv.vehicle || undefined,
          physical_description: inv.physical_description || undefined,
          notes: inv.notes || undefined,
        });
        setAliases(inv.aliases || []);
        setSocialMedia(inv.social_media || {});
        setPhotos((inv.photo_ids || []).map((id) => ({
          id, filename: id, url: api.getPhotoUrl(id),
        })));
        setResults(inv.results as InvestigateResponse | null);
        setSavedId(inv.id);
        setTimeline(inv.timeline || []);
      } catch {
        // ignore
      }
    })();

    return () => { cancelled = true; };
  }, [loadInvestigationId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload: InvestigationCreateRequest = { ...form };

    // Merge aliases
    if (aliases.length > 0) payload.aliases = aliases;

    // Merge social media (strip empty values)
    const sm = Object.fromEntries(Object.entries(socialMedia).filter(([, v]) => v.trim()));
    if (Object.keys(sm).length > 0) payload.social_media = sm;

    // Merge photo IDs
    if (photos.length > 0) payload.photo_ids = photos.map((p) => p.id);

    // Use employer field for company if company is empty
    if (!payload.company && payload.employer) {
      payload.company = payload.employer;
    }

    // Case name
    if (caseName.trim()) {
      payload.investigation_name = caseName.trim();
    }

    // Validate at least one field
    const hasValue = [
      payload.name, payload.email, payload.phone, payload.ip, payload.domain,
      payload.company, payload.employer, payload.location,
    ].some((v) => v && v.trim());
    const hasAliases = (payload.aliases?.length ?? 0) > 0;
    const hasSocial = Object.keys(payload.social_media ?? {}).length > 0;

    if (!hasValue && !hasAliases && !hasSocial) return;

    setSubmitting(true);
    try {
      const inv = await api.createInvestigation(payload);
      setResults(inv.results as InvestigateResponse | null);
      setSavedId(inv.id);
      setTimeline(inv.timeline || []);
    } catch (err: any) {
      // fallback: run without saving
      investigate.mutate(payload, {
        onSuccess: (data) => setResults(data),
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleRerun = async () => {
    if (!savedId) return;
    setRerunning(true);
    try {
      const inv = await api.rerunInvestigation(savedId);
      setResults(inv.results as InvestigateResponse | null);
      setTimeline(inv.timeline || []);
    } catch {
      // ignore
    } finally {
      setRerunning(false);
    }
  };

  const handleAddNote = async () => {
    if (!savedId || !noteText.trim()) return;
    setAddingNote(true);
    try {
      const event = await api.addNote(savedId, noteText.trim());
      setTimeline((prev) => [...prev, event]);
      setNoteText('');
      setShowNoteInput(false);
    } catch {
      // ignore
    } finally {
      setAddingNote(false);
    }
  };

  const updateField = (key: string, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value || undefined }));
  };

  const updateSocial = (platform: string, value: string) => {
    setSocialMedia((prev) => ({ ...prev, [platform]: value }));
  };

  const isLoading = submitting || investigate.isPending;

  return (
    <div className="space-y-6">
      {/* Investigation Form */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-navy-800 border border-navy-600 rounded-xl overflow-hidden flex flex-col"
        style={{ maxHeight: 'calc(100vh - 160px)' }}
      >
        <div className="flex items-center gap-3 px-6 pt-6 pb-2">
          <Crosshair className="w-5 h-5 text-accent" />
          <h2 className="text-lg font-semibold text-gray-100">
            {savedId ? 'Investigation' : 'New Investigation'}
          </h2>
          {savedId && (
            <span className="flex items-center gap-1 text-xs text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded">
              <Check className="w-3 h-3" />
              Saved
            </span>
          )}
          <span className="text-xs text-gray-500">Enter any combination of identifiers</span>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col flex-1 min-h-0">
          <div className="flex-1 overflow-y-auto px-6 pb-2 space-y-0">

            {/* ── Case Name ── */}
            <div className="py-3 border-b border-navy-600/50">
              <div className="max-w-md">
                <FieldLabel icon={FileText} label="Case Name" />
                <input
                  type="text"
                  value={caseName}
                  onChange={(e) => setCaseName(e.target.value)}
                  placeholder="e.g. John Doe Case"
                  className={inputClass}
                />
              </div>
            </div>

            {/* ── Section 1: Basic Identity (always visible) ── */}
            <div className="py-3 border-b border-navy-600/50">
              <div className="flex items-center gap-2 mb-3">
                <Fingerprint className="w-4 h-4 text-accent" />
                <span className="text-sm font-semibold text-gray-300">Basic Identity</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div>
                  <FieldLabel icon={User} label="Full Name" />
                  <input
                    type="text"
                    value={form.name || ''}
                    onChange={(e) => updateField('name', e.target.value)}
                    placeholder="John Doe"
                    className={inputClass}
                  />
                </div>
                <div className="md:col-span-2 lg:col-span-2">
                  <FieldLabel icon={Hash} label="Aliases / AKA" />
                  <TagInput
                    tags={aliases}
                    onChange={setAliases}
                    placeholder="Type alias and press Enter"
                  />
                </div>
                <div>
                  <FieldLabel icon={User} label="Date of Birth" />
                  <input
                    type="date"
                    value={form.date_of_birth || ''}
                    onChange={(e) => updateField('date_of_birth', e.target.value)}
                    className={inputClass}
                  />
                </div>
                <div>
                  <FieldLabel icon={User} label="Age Range" />
                  <select
                    value={form.age_range || ''}
                    onChange={(e) => updateField('age_range', e.target.value)}
                    className={selectClass}
                  >
                    {AGE_RANGES.map((r) => (
                      <option key={r} value={r}>
                        {r || '— Select —'}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <FieldLabel icon={User} label="Gender" />
                  <select
                    value={form.gender || ''}
                    onChange={(e) => updateField('gender', e.target.value)}
                    className={selectClass}
                  >
                    {GENDERS.map((g) => (
                      <option key={g} value={g}>
                        {g || '— Select —'}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <FieldLabel icon={Globe} label="Nationality" />
                  <input
                    type="text"
                    value={form.nationality || ''}
                    onChange={(e) => updateField('nationality', e.target.value)}
                    placeholder="e.g. American"
                    className={inputClass}
                  />
                </div>
              </div>
            </div>

            {/* ── Section 2: Contact Information ── */}
            <Section title="Contact Information" icon={<Mail className="w-4 h-4" />} defaultOpen>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <FieldLabel icon={Mail} label="Email" />
                  <input
                    type="text"
                    value={form.email || ''}
                    onChange={(e) => updateField('email', e.target.value)}
                    placeholder="john@example.com"
                    className={inputClass}
                  />
                </div>
                <div>
                  <FieldLabel icon={Phone} label="Phone" />
                  <input
                    type="text"
                    value={form.phone || ''}
                    onChange={(e) => updateField('phone', e.target.value)}
                    placeholder="+1234567890"
                    className={inputClass}
                  />
                </div>
                <div>
                  <FieldLabel icon={MapPin} label="Location" />
                  <input
                    type="text"
                    value={form.location || ''}
                    onChange={(e) => updateField('location', e.target.value)}
                    placeholder="City, State, Country"
                    className={inputClass}
                  />
                </div>
                <div>
                  <FieldLabel icon={MapPin} label="Address" />
                  <textarea
                    value={form.address || ''}
                    onChange={(e) => updateField('address', e.target.value)}
                    placeholder="Full street address"
                    rows={2}
                    className={textareaClass}
                  />
                </div>
              </div>
            </Section>

            {/* ── Section 3: Digital Footprint ── */}
            <Section title="Digital Footprint" icon={<Globe className="w-4 h-4" />}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div>
                  <FieldLabel icon={Wifi} label="IP Address" />
                  <input
                    type="text"
                    value={form.ip || ''}
                    onChange={(e) => updateField('ip', e.target.value)}
                    placeholder="8.8.8.8"
                    className={inputClass}
                  />
                </div>
                <div>
                  <FieldLabel icon={Globe} label="Domain" />
                  <input
                    type="text"
                    value={form.domain || ''}
                    onChange={(e) => updateField('domain', e.target.value)}
                    placeholder="example.com"
                    className={inputClass}
                  />
                </div>
              </div>
              <div className="text-xs text-gray-500 mb-2">Social Media Profiles</div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {socialPlatforms.map(({ key, label, placeholder }) => (
                  <div key={key}>
                    <label className="text-xs text-gray-500 mb-1 block">{label}</label>
                    <input
                      type="text"
                      value={socialMedia[key] || ''}
                      onChange={(e) => updateSocial(key, e.target.value)}
                      placeholder={placeholder}
                      className={inputClass}
                    />
                  </div>
                ))}
              </div>
            </Section>

            {/* ── Section 4: Professional ── */}
            <Section title="Professional" icon={<Briefcase className="w-4 h-4" />}>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <FieldLabel icon={Building2} label="Employer / Company" />
                  <input
                    type="text"
                    value={form.employer || form.company || ''}
                    onChange={(e) => {
                      updateField('employer', e.target.value);
                      updateField('company', e.target.value);
                    }}
                    placeholder="Acme Corp"
                    className={inputClass}
                  />
                </div>
                <div>
                  <FieldLabel icon={Briefcase} label="Occupation / Title" />
                  <input
                    type="text"
                    value={form.occupation || ''}
                    onChange={(e) => updateField('occupation', e.target.value)}
                    placeholder="Software Engineer"
                    className={inputClass}
                  />
                </div>
                <div>
                  <FieldLabel icon={GraduationCap} label="Education" />
                  <input
                    type="text"
                    value={form.education || ''}
                    onChange={(e) => updateField('education', e.target.value)}
                    placeholder="MIT, Harvard, etc."
                    className={inputClass}
                  />
                </div>
              </div>
            </Section>

            {/* ── Section 5: Physical Description ── */}
            <Section title="Physical Description" icon={<User className="w-4 h-4" />}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <FieldLabel icon={User} label="Physical Description" />
                  <textarea
                    value={form.physical_description || ''}
                    onChange={(e) => updateField('physical_description', e.target.value)}
                    placeholder="Height, weight, hair color, eye color, tattoos, scars..."
                    rows={3}
                    className={textareaClass}
                  />
                </div>
                <div>
                  <FieldLabel icon={Car} label="Vehicle" />
                  <input
                    type="text"
                    value={form.vehicle || ''}
                    onChange={(e) => updateField('vehicle', e.target.value)}
                    placeholder="Make, model, color, plate number"
                    className={inputClass}
                  />
                </div>
              </div>
            </Section>

            {/* ── Section 6: Photos ── */}
            <Section
              title="Photos"
              icon={<Camera className="w-4 h-4" />}
              badge={photos.length > 0 ? photos.length : undefined}
            >
              <PhotoUpload
                photos={photos}
                onAdd={(p) => setPhotos((prev) => [...prev, p])}
                onRemove={(id) => setPhotos((prev) => prev.filter((p) => p.id !== id))}
              />
            </Section>

            {/* ── Section 7: Notes ── */}
            <Section title="Notes" icon={<FileText className="w-4 h-4" />}>
              <textarea
                value={form.notes || ''}
                onChange={(e) => updateField('notes', e.target.value)}
                placeholder="Free-form investigator notes..."
                rows={4}
                className={textareaClass}
              />
            </Section>
          </div>

          {/* ── Fixed bottom bar ── */}
          <div className="border-t border-navy-600 px-6 py-4 bg-navy-800 flex items-center gap-3 shrink-0 flex-wrap">
            <button
              type="submit"
              disabled={isLoading}
              className="flex items-center gap-2 px-6 py-2.5 bg-accent/10 text-accent border border-accent/20 rounded-lg text-sm font-semibold hover:bg-accent/20 disabled:opacity-40 disabled:cursor-not-allowed transition-all cursor-pointer"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Crosshair className="w-4 h-4" />
              )}
              {isLoading ? 'Investigating...' : 'Run Investigation'}
            </button>

            {savedId && (
              <>
                <button
                  type="button"
                  onClick={handleRerun}
                  disabled={rerunning}
                  className="flex items-center gap-2 px-4 py-2.5 bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-lg text-sm font-medium hover:bg-blue-500/20 disabled:opacity-40 transition-all cursor-pointer"
                >
                  <RefreshCw className={`w-4 h-4 ${rerunning ? 'animate-spin' : ''}`} />
                  Re-run
                </button>
                <button
                  type="button"
                  onClick={() => setShowNoteInput(!showNoteInput)}
                  className="flex items-center gap-2 px-4 py-2.5 bg-yellow-500/10 text-yellow-400 border border-yellow-500/20 rounded-lg text-sm font-medium hover:bg-yellow-500/20 transition-all cursor-pointer"
                >
                  <MessageSquarePlus className="w-4 h-4" />
                  Add Note
                </button>
              </>
            )}

            {savedId && (
              <span className="text-xs text-gray-600 ml-auto font-mono">
                ID: {savedId.slice(0, 8)}…
              </span>
            )}

            {isLoading && (
              <span className="text-xs text-gray-500 animate-pulse">
                Querying all providers concurrently...
              </span>
            )}
          </div>
        </form>

        {/* Note input */}
        <AnimatePresence>
          {showNoteInput && savedId && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden border-t border-navy-600"
            >
              <div className="px-6 py-3 flex items-center gap-3">
                <input
                  type="text"
                  value={noteText}
                  onChange={(e) => setNoteText(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAddNote()}
                  placeholder="Type a note..."
                  className={`${inputClass} flex-1`}
                  autoFocus
                />
                <button
                  type="button"
                  onClick={handleAddNote}
                  disabled={addingNote || !noteText.trim()}
                  className="px-4 py-2 bg-yellow-500/10 text-yellow-400 border border-yellow-500/20 rounded-lg text-sm font-medium hover:bg-yellow-500/20 disabled:opacity-40 transition-all cursor-pointer"
                >
                  {addingNote ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Save'}
                </button>
                <button
                  type="button"
                  onClick={() => { setShowNoteInput(false); setNoteText(''); }}
                  className="p-2 text-gray-500 hover:text-gray-300 transition-colors cursor-pointer"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {investigate.isError && (
          <div className="mx-6 mb-4 bg-threat/10 border border-threat/20 rounded-lg p-3 text-sm text-threat">
            Error: {(investigate.error as Error).message}
          </div>
        )}
      </motion.div>

      {/* Results */}
      {(isLoading || rerunning) && <LoadingState count={8} />}
      {results && !isLoading && !rerunning && <ResultsMatrix data={results} />}

      {/* Timeline */}
      {timeline.length > 0 && !isLoading && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-navy-800 border border-navy-600 rounded-xl p-6"
        >
          <div className="flex items-center gap-2 mb-4">
            <Clock className="w-4 h-4 text-accent" />
            <h3 className="text-sm font-semibold text-gray-200">Timeline</h3>
            <span className="text-xs text-gray-500">{timeline.length} event{timeline.length !== 1 ? 's' : ''}</span>
          </div>
          <TimelineView events={timeline} />
        </motion.div>
      )}
    </div>
  );
}

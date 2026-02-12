/**
 * API Client — fetch wrapper for the OSINT backend.
 * Uses relative paths so it works behind nginx at /osint/.
 */

import type {
  HealthResponse,
  InvestigateRequest,
  InvestigateResponse,
  InvestigationCreateRequest,
  InvestigationFull,
  InvestigationSummary,
  LookupRequest,
  LookupResponse,
  PhotoUploadResponse,
  ProvidersResponse,
  TimelineEvent,
} from '../types';

const API_BASE = '/osint/api';

class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(`API Error ${status}: ${detail}`);
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      // ignore parse errors
    }
    throw new ApiError(res.status, detail);
  }

  return res.json();
}

export const api = {
  health: () => request<HealthResponse>('/health'),

  providers: () => request<ProvidersResponse>('/providers'),

  lookup: (data: LookupRequest) =>
    request<LookupResponse>('/lookup', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  investigate: (data: InvestigateRequest) =>
    request<InvestigateResponse>('/investigate', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  uploadPhoto: async (file: File): Promise<PhotoUploadResponse> => {
    const url = `${API_BASE}/photos/upload`;
    const formData = new FormData();
    formData.append('file', file);

    const res = await fetch(url, {
      method: 'POST',
      body: formData,
      // Do NOT set Content-Type — browser sets multipart boundary automatically
    });

    if (!res.ok) {
      let detail = res.statusText;
      try {
        const body = await res.json();
        detail = body.detail || detail;
      } catch {
        // ignore
      }
      throw new ApiError(res.status, detail);
    }

    return res.json();
  },

  deletePhoto: async (id: string): Promise<void> => {
    const url = `${API_BASE}/photos/${id}`;
    const res = await fetch(url, { method: 'DELETE' });

    if (!res.ok) {
      let detail = res.statusText;
      try {
        const body = await res.json();
        detail = body.detail || detail;
      } catch {
        // ignore
      }
      throw new ApiError(res.status, detail);
    }
  },

  getPhotoUrl: (id: string): string => `${API_BASE}/photos/${id}`,

  // ── Investigations ─────────────────────────────────────
  createInvestigation: (data: InvestigationCreateRequest) =>
    request<InvestigationFull>('/investigations', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  listInvestigations: (status?: string, query?: string) => {
    const params = new URLSearchParams();
    if (status) params.set('status', status);
    if (query) params.set('q', query);
    const qs = params.toString();
    return request<InvestigationSummary[]>(`/investigations${qs ? `?${qs}` : ''}`);
  },

  getInvestigation: (id: string) =>
    request<InvestigationFull>(`/investigations/${id}`),

  updateInvestigation: (id: string, fields: Record<string, any>) =>
    request<InvestigationFull>(`/investigations/${id}`, {
      method: 'PUT',
      body: JSON.stringify(fields),
    }),

  rerunInvestigation: (id: string) =>
    request<InvestigationFull>(`/investigations/${id}/rerun`, {
      method: 'POST',
    }),

  addNote: (id: string, note: string) =>
    request<TimelineEvent>(`/investigations/${id}/notes`, {
      method: 'POST',
      body: JSON.stringify({ note }),
    }),

  deleteInvestigation: (id: string) =>
    request<{ status: string; id: string }>(`/investigations/${id}`, {
      method: 'DELETE',
    }),
};

export { ApiError };

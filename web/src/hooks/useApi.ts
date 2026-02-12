/**
 * React Query hooks for API calls.
 */

import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '../api/client';
import type { InvestigateRequest, LookupRequest } from '../types';

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: api.health,
    refetchInterval: 30000,
    staleTime: 10000,
  });
}

export function useProviders() {
  return useQuery({
    queryKey: ['providers'],
    queryFn: api.providers,
    staleTime: 60000,
  });
}

export function useLookup() {
  return useMutation({
    mutationFn: (data: LookupRequest) => api.lookup(data),
  });
}

export function useInvestigate() {
  return useMutation({
    mutationFn: (data: InvestigateRequest) => api.investigate(data),
  });
}

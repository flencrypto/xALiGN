'use client';

import { useEffect, useState } from 'react';
import { setupApi, type SetupStatus } from '@/lib/api';

interface UseSetupStatus {
  status: SetupStatus | null;
  loading: boolean;
  isConfigured: (integrationId: string) => boolean;
}

let _cache: SetupStatus | null = null;
let _promise: Promise<SetupStatus> | null = null;

export function useSetupStatus(): UseSetupStatus {
  const [status, setStatus] = useState<SetupStatus | null>(_cache);
  const [loading, setLoading] = useState(_cache === null);

  useEffect(() => {
    if (_cache) {
      setStatus(_cache);
      setLoading(false);
      return;
    }
    if (!_promise) {
      _promise = setupApi.getStatus().catch(() => ({
        integrations: {},
        all_required_configured: false,
        auth_provider: 'none',
        storage_backend: 'local',
      }));
    }
    _promise.then((s) => {
      _cache = s;
      setStatus(s);
      setLoading(false);
    });
  }, []);

  function isConfigured(integrationId: string): boolean {
    if (!status) return true; // optimistic while loading – don't block UI
    return status.integrations[integrationId]?.configured ?? true;
  }

  return { status, loading, isConfigured };
}

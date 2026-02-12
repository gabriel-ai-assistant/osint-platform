import { useState, useCallback } from 'react';
import Header from './Header';
import Sidebar from './Sidebar';
import InvestigationPanel from './InvestigationPanel';
import InvestigationsList from './InvestigationsList';
import LookupPanel from './LookupPanel';
import ProvidersPanel from './ProvidersPanel';
import type { NavPage } from '../types';

export default function Layout() {
  const [page, setPage] = useState<NavPage>('investigation');
  const [loadInvestigationId, setLoadInvestigationId] = useState<string | null>(null);

  const handleOpenInvestigation = useCallback((id: string) => {
    setLoadInvestigationId(id);
    setPage('investigation');
  }, []);

  const handleNewInvestigation = useCallback(() => {
    setLoadInvestigationId(null);
    setPage('investigation');
  }, []);

  const handleNavigate = useCallback((p: NavPage) => {
    if (p !== 'investigation') {
      setLoadInvestigationId(null);
    }
    setPage(p);
  }, []);

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar active={page} onNavigate={handleNavigate} />
        <main className="flex-1 overflow-y-auto p-6 bg-navy-900">
          {page === 'investigation' && (
            <InvestigationPanel
              loadInvestigationId={loadInvestigationId}
              onClearLoad={() => setLoadInvestigationId(null)}
            />
          )}
          {page === 'investigations' && (
            <InvestigationsList
              onOpen={handleOpenInvestigation}
              onNew={handleNewInvestigation}
            />
          )}
          {page === 'lookup' && <LookupPanel />}
          {page === 'providers' && <ProvidersPanel />}
        </main>
      </div>
    </div>
  );
}

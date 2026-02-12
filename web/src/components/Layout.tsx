import { useState } from 'react';
import Header from './Header';
import Sidebar from './Sidebar';
import InvestigationPanel from './InvestigationPanel';
import LookupPanel from './LookupPanel';
import ProvidersPanel from './ProvidersPanel';
import type { NavPage } from '../types';

export default function Layout() {
  const [page, setPage] = useState<NavPage>('investigation');

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar active={page} onNavigate={setPage} />
        <main className="flex-1 overflow-y-auto p-6 bg-navy-900">
          {page === 'investigation' && <InvestigationPanel />}
          {page === 'lookup' && <LookupPanel />}
          {page === 'providers' && <ProvidersPanel />}
        </main>
      </div>
    </div>
  );
}

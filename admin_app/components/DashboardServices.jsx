import React from 'react';
import LoadingSpinner from '../lib/LoadingSpinner.jsx';

const DashboardServices = () => {
  const [status, setStatus] = React.useState(null);
  
  React.useEffect(() => {
    (async () => {
      try {
        const s = await window.api('/api/v1/services/status');
        setStatus(s);
      } catch {
        setStatus(null);
      }
    })();
  }, []);
  
  const pill = (label, ok) => (
    <div className="flex items-center justify-between p-3 rounded-xl border" style={{ backgroundColor: ok ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)', borderColor: ok ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)' }}>
      <div className="flex items-center space-x-3">
        <div className={`w-3 h-3 rounded-full ${ok ? 'bg-medical-success' : 'bg-medical-error'}`}></div>
        <span className="font-secondary">{label}</span>
      </div>
      <span className={`text-sm font-medium ${ok ? 'text-medical-success' : 'text-medical-error'}`}>{ok ? 'Online' : 'Disabled'}</span>
    </div>
  );
  
  if (!status) return <LoadingSpinner />;
  
  return (
    <div className="space-y-2">
      {pill('WhatsApp', !!status.whatsapp?.enabled)}
      {pill('Email', !!status.email?.enabled)}
      {pill('Google Calendar', !!status.calendar?.enabled)}
    </div>
  );
};

export default DashboardServices;


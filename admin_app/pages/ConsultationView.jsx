const ConsultationView = () => {
  const [view, setView] = React.useState('list');
  const [selectedPatient, setSelectedPatient] = React.useState(null);
  const [patients, setPatients] = React.useState(window.samplePatientData || []);
  const [searchQuery, setSearchQuery] = React.useState('');
  const [filterDate, setFilterDate] = React.useState(
    new Date().toISOString().split('T')[0]
  );
  const [isLoading, setIsLoading] = React.useState(false);

  React.useEffect(() => {
    // In production: fetch from API
    // fetchPatients(filterDate).then(data => setPatients(data));
  }, [filterDate]);

  const handleOpenVisitPad = (patient) => {
    setSelectedPatient(patient);
    setView('visitpad');
  };

  const handleOpenTemplateView = () => {
    setSelectedPatient(null);
    setView('template');
  };

  const handleBackToList = () => {
    setView('list');
    setSelectedPatient(null);
  };

  const filteredPatients = React.useMemo(() => {
    return patients.filter(patient =>
      patient.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      patient.id.toString().includes(searchQuery) ||
      patient.phone.includes(searchQuery)
    );
  }, [patients, searchQuery]);

  return (
    <div className="h-full overflow-hidden">
      {view === 'list' ? (
        <PatientListView
          patients={filteredPatients}
          allPatients={patients}
          searchQuery={searchQuery}
          setSearchQuery={setSearchQuery}
          filterDate={filterDate}
          setFilterDate={setFilterDate}
          onOpenVisitPad={handleOpenVisitPad}
          onOpenTemplateView={handleOpenTemplateView}
          isLoading={isLoading}
        />
      ) : (
        <VisitPadView
          patient={selectedPatient}
          onBack={handleBackToList}
          mode={view === 'visitpad' ? "consultation" : "template"}
        />
      )}
    </div>
  );
};

window.ConsultationView = ConsultationView;
window.ConsultationEditor = ConsultationView;


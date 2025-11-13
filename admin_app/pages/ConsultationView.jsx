import React from 'react';
import PatientListView from '../components/PatientListView.jsx';
import VisitPadView from '../components/VisitPadView.jsx';

const ConsultationView = () => {
  const [view, setView] = React.useState('list');
  const [selectedPatient, setSelectedPatient] = React.useState(null);
  const [patients, setPatients] = React.useState([]);
  const [searchQuery, setSearchQuery] = React.useState('');
  const [filterDate, setFilterDate] = React.useState(
    new Date().toISOString().split('T')[0]
  );
  const [isLoading, setIsLoading] = React.useState(false);

  const fetchPatients = React.useCallback(async () => {
    setIsLoading(true);
    try {
        // Fetching appointments for the current day to act as the consultation queue.
        // start_date and end_date are the same for the day filter.
        const url = `/api/v1/appointments?start_date=${filterDate}&end_date=${filterDate}`;
        const appointmentsData = await window.api(url);
        
        // Transform AppointmentResponse into PatientListView format
        const consultationQueue = (appointmentsData || []).map(apt => ({
            id: apt.patient.id,
            name: `${apt.patient.first_name} ${apt.patient.last_name || ''}`.trim(),
            phone: apt.patient.phone_number,
            status: apt.status.value.toUpperCase(),
            time: new Date(apt.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: true }),
            // Mocked/Simplified fields for demo. These should be fetched/calculated properly.
            totalVisits: Math.floor(Math.random() * 20) + 1, 
            recentVisit: apt.start_time ? new Date(apt.start_time).toLocaleDateString() : 'N/A',
            age: 30, // Placeholder
            gender: apt.patient.gender || 'N/A', // Placeholder
            purpose: apt.reason || 'Consultation',
            wait: '0 min',
            medicalHistory: { allergies: ['Dust'], currentMedications: ['None'] }, // Placeholder
            appointment_id: apt.id // Crucial link to appointment
        }));

        setPatients(consultationQueue);
    } catch (error) {
        console.error('Failed to fetch consultation queue:', error);
        setPatients([]);
    } finally {
        setIsLoading(false);
    }
}, [filterDate]);

  React.useEffect(() => {
    fetchPatients();
  }, [fetchPatients]);

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

export default ConsultationView;
const PatientDetails = ({ patient, user }) => {
  const [activeTab, setActiveTab] = React.useState('overview');
  const [patientAppointments, setPatientAppointments] = React.useState([]);
  const [patientPrescriptions, setPatientPrescriptions] = React.useState([]);
  const [patientRemarks, setPatientRemarks] = React.useState([]);
  const [newRemark, setNewRemark] = React.useState('');

  React.useEffect(() => {
    const fetchPatientData = async () => {
      if (!patient) return;

      try {
        const prescriptionData = await window.api(`/api/v1/patients/${patient.id}/prescriptions`);
        setPatientPrescriptions(prescriptionData || []);
      } catch (error) {
        console.error('Error fetching patient prescriptions:', error);
      }

      try {
        const remarksData = await window.api(`/api/v1/patients/${patient.id}/remarks/`);
        setPatientRemarks(remarksData || []);
      } catch (error) {
        console.error('Error fetching patient remarks:', error);
      }

      // TODO: Fetch actual appointments from API
      setPatientAppointments([]);
    };

    fetchPatientData();
  }, [patient]);

  const handleAddRemark = async () => {
    if (!newRemark.trim()) return;
    try {
      const addedRemark = await window.api(`/api/v1/patients/${patient.id}/remarks/`, {
        method: 'POST',
        body: JSON.stringify({ text: newRemark }),
      });
      setPatientRemarks([addedRemark, ...patientRemarks]);
      setNewRemark('');
    } catch (error) {
      console.error('Error adding remark:', error);
    }
  };

  const tabs = [
    { id: 'overview', label: 'Overview', icon: 'fas fa-user' },
    { id: 'appointments', label: 'Appointments', icon: 'fas fa-calendar' },
    { id: 'prescriptions', label: 'Prescriptions', icon: 'fas fa-prescription' },
    { id: 'remarks', label: 'Remarks', icon: 'fas fa-comment-medical' }
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-2 sm:space-x-4 pb-4 border-b border-gray-200">
        <div className="w-16 h-16 bg-medical-accent/10 rounded-full flex items-center justify-center">
          <span className="text-medical-accent text-xl font-bold">
            {patient.first_name?.charAt(0) || patient.name?.charAt(0) || 'P'}
          </span>
        </div>
        <div>
          <h3 className="text-lg sm:text-xl lg:text-2xl font-bold text-medical-dark">{`${patient.first_name || ''} ${patient.last_name || ''}`.trim() || 'Unknown Patient'}</h3>
          <p className="text-medical-gray">Patient ID: {patient.id}</p>
        </div>
      </div>

      <div className="flex space-x-1 bg-gray-100 p-1 rounded-xl">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 flex items-center justify-center space-x-2 py-2 px-4 rounded-lg font-medium transition-all ${activeTab === tab.id
              ? 'bg-white text-medical-accent shadow-sm'
              : 'text-medical-gray hover:text-medical-dark'
              }`}
          >
            <i className={tab.icon}></i>
            <span>{tab.label}</span>
          </button>
        ))}
      </div>

      <div className="min-h-[400px]">
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h4 className="font-semibold text-medical-dark mb-4">Personal Information</h4>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-medical-gray">Phone:</span>
                  <span>{patient.phone_number || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-medical-gray">Email:</span>
                  <span>{patient.email || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-medical-gray">Date of Birth:</span>
                  <span>{patient.date_of_birth || 'N/A'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-medical-gray">Gender:</span>
                  <span>{patient.gender || 'N/A'}</span>
                </div>
              </div>
            </div>
            <div>
              <h4 className="font-semibold text-medical-dark mb-4">Medical Information</h4>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-medical-gray">Blood Type:</span>
                  <span>{patient.blood_type || 'Unknown'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-medical-gray">Allergies:</span>
                  <span>{patient.allergies || 'None known'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-medical-gray">Last Visit:</span>
                  <span>
                    {patient.last_visit_date ?
                      new Date(patient.last_visit_date).toLocaleDateString() :
                      'Never'
                    }
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'appointments' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h4 className="font-semibold text-medical-dark">Appointment History</h4>
              {user?.permissions?.can_manage_appointments && (
                <button className="medical-button px-4 py-2 text-white rounded-lg text-sm relative z-10">
                  <i className="fas fa-plus mr-2"></i>New Appointment
                </button>
              )}
            </div>
            <div className="space-y-3">
              {patientAppointments.length === 0 ? (
                <p className="text-sm text-medical-gray text-center py-4">No appointments found.</p>
              ) : (
                patientAppointments.map(apt => (
                  <div key={apt.id} className="table-row p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-semibold">
                          {new Date(apt.start_time).toLocaleDateString()} - {apt.appointment_type}
                        </div>
                        <div className="text-sm text-medical-gray mt-1">{apt.notes}</div>
                      </div>
                      <span className={`px-2 py-1 rounded-full text-xs ${apt.status === 'completed'
                        ? 'bg-medical-success/10 text-medical-success'
                        : 'bg-medical-accent/10 text-medical-accent'
                        }`}>
                        {apt.status}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {activeTab === 'prescriptions' && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h4 className="font-semibold text-medical-dark">Prescription History</h4>
              {user?.permissions?.can_edit_patient_info && (
                <button className="medical-button px-4 py-2 text-white rounded-lg text-sm relative z-10">
                  <i className="fas fa-plus mr-2"></i>New Prescription
                </button>
              )}
            </div>
            <div className="space-y-3">
              {patientPrescriptions.length === 0 ? (
                <p className="text-sm text-medical-gray text-center py-4">No prescriptions found.</p>
              ) : (
                patientPrescriptions.map(prescription => (
                  <div key={prescription.id} className="table-row p-4 border border-gray-200 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <div className="font-semibold">{prescription.medication_name}</div>
                        <div className="text-sm text-medical-gray">
                          {prescription.dosage} - {prescription.frequency}
                        </div>
                        <div className="text-xs text-medical-gray mt-1">
                          Prescribed: {new Date(prescription.prescribed_date).toLocaleDateString()}
                        </div>
                      </div>
                      <div className="flex flex-wrap items-center gap-2">
                        <button title="View PDF" onClick={() => window.open(`/api/v1/prescriptions/editor/pdf/${prescription.document_id || ''}`, '_blank')} className="px-2 py-1 bg-gray-100 rounded text-sm">PDF</button>
                        <button title="View HTML" onClick={() => window.open(`/api/v1/prescriptions/editor/html/${prescription.document_id || ''}`, '_blank')} className="px-2 py-1 bg-gray-100 rounded text-sm">HTML</button>
                        <button title="Send WhatsApp" onClick={async () => { try { await window.api('/api/v1/prescriptions/share', { method: 'POST', body: JSON.stringify({ patient_id: prescription.patient_id || patient.id, document_id: prescription.document_id, method: 'whatsapp' }) }); window.toast('Sent via WhatsApp'); } catch { window.toast('Send failed'); } }} className="px-2 py-1 bg-green-600 text-white rounded text-sm">WA</button>
                        <button title="Send Email" onClick={async () => { try { await window.api('/api/v1/prescriptions/share', { method: 'POST', body: JSON.stringify({ patient_id: prescription.patient_id || patient.id, document_id: prescription.document_id, method: 'email' }) }); window.toast('Sent via Email'); } catch { window.toast('Send failed'); } }} className="px-2 py-1 bg-blue-600 text-white rounded text-sm">Email</button>
                        <span className={`px-2 py-1 rounded-full text-xs ${prescription.is_active
                          ? 'bg-medical-success/10 text-medical-success'
                          : 'bg-medical-gray/10 text-medical-gray'
                          }`}>
                          {prescription.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {activeTab === 'remarks' && (
          <div className="space-y-4 animate-fade-in">
            <h4 className="font-semibold text-medical-dark">Patient Remarks</h4>
            <div className="space-y-4">
              {user?.permissions?.can_edit_patient_info && (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <textarea
                    value={newRemark}
                    onChange={(e) => setNewRemark(e.target.value)}
                    className="custom-textarea"
                    rows="3"
                    placeholder="Add a new remark..."
                  ></textarea>
                  <div className="flex justify-end mt-2">
                    <button
                      onClick={handleAddRemark}
                      className="medical-button px-4 py-2 text-white rounded-lg text-sm relative z-10"
                    >
                      Add Remark
                    </button>
                  </div>
                </div>
              )}

              <div className="space-y-3">
                {patientRemarks.length > 0 ? (
                  patientRemarks.map(remark => (
                    <div key={remark.id} className="table-row p-4 border border-gray-200 rounded-lg">
                      <p className="text-sm text-medical-dark">{remark.text}</p>
                      <div className="text-xs text-medical-gray mt-2">
                        <span>By {remark.author?.username || 'Unknown'} on </span>
                        <span>{new Date(remark.created_at).toLocaleString()}</span>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-medical-gray text-center py-4">No remarks for this patient yet.</p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};


const PrescriptionEditor = ({ prescription, onClose, refreshPrescriptions }) => {
    const [patientId, setPatientId] = React.useState(prescription?.patient_id || '');
    const [medication, setMedication] = React.useState(prescription?.medication_name || '');
    const [dosage, setDosage] = React.useState(prescription?.dosage || '');
    const [frequency, setFrequency] = React.useState(prescription?.frequency || '');
    const [duration, setDuration] = React.useState(prescription?.duration || '');
    const [patients, setPatients] = React.useState([]);
    const [error, setError] = React.useState('');

    React.useEffect(() => {
        const fetchPatients = async () => {
            try {
                const data = await api('/api/v1/patients');
                setPatients(data || []);
            } catch (err) {
                console.error('Failed to fetch patients', err);
            }
        };
        fetchPatients();
    }, []);

    const handleSubmit = async () => {
        setError('');
        if (!patientId || !medication || !dosage || !frequency || !duration) {
            setError('All fields are required.');
            return;
        }
        const payload = { patient_id: parseInt(patientId), medication_name: medication, dosage, frequency, duration };

        try {
            await api('/api/v1/prescriptions', {
                method: 'POST',
                body: JSON.stringify(payload)
            });
            if (refreshPrescriptions) refreshPrescriptions();
            onClose();
        } catch (err) {
            setError('An error occurred. Please check the console and try again.');
            console.error('Save prescription error:', err);
        }
    };

    return (
        <div className="space-y-6">
            {error && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg">{error}</div>}
            <div>
                <label className="block text-sm font-medium text-medical-gray mb-2">Patient</label>
                <select value={patientId} onChange={(e) => setPatientId(e.target.value)} className="form-input-themed">
                    <option value="">Select a Patient</option>
                    {patients.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <label className="block text-sm font-medium text-medical-gray mb-2">Medication Name</label>
                    <input type="text" value={medication} onChange={(e) => setMedication(e.target.value)} className="form-input-themed" placeholder="e.g., Lisinopril" />
                </div>
                <div>
                    <label className="block text-sm font-medium text-medical-gray mb-2">Dosage</label>
                    <input type="text" value={dosage} onChange={(e) => setDosage(e.target.value)} className="form-input-themed" placeholder="e.g., 10mg" />
                </div>
                <div>
                    <label className="block text-sm font-medium text-medical-gray mb-2">Frequency</label>
                    <input type="text" value={frequency} onChange={(e) => setFrequency(e.target.value)} className="form-input-themed" placeholder="e.g., Once daily" />
                </div>
                <div>
                    <label className="block text-sm font-medium text-medical-gray mb-2">Duration</label>
                    <input type="text" value={duration} onChange={(e) => setDuration(e.target.value)} className="form-input-themed" placeholder="e.g., 30 days" />
                </div>
            </div>
            <div className="flex justify-end space-x-3">
                <button onClick={onClose} className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">Cancel</button>
                <button onClick={handleSubmit} className="medical-button px-4 py-2 text-white rounded-lg relative z-10">
                    Create Prescription
                </button>
            </div>
        </div>
    );
};

window.PrescriptionEditor = PrescriptionEditor;

export default PrescriptionEditor;
const PatientEditor = ({ patient, onClose, refreshPatients }) => {
    const [firstName, setFirstName] = React.useState(patient?.first_name || '');
    const [lastName, setLastName] = React.useState(patient?.last_name || '');
    const [phoneNumber, setPhoneNumber] = React.useState(patient?.phone_number || '');
    const [email, setEmail] = React.useState(patient?.email || '');
    const [dob, setDob] = React.useState(patient?.date_of_birth || '');
    const [error, setError] = React.useState('');

    const handleSubmit = async () => {
        setError('');
        if (!firstName) {
            setError('Patient first name is required.');
            return;
        }
        const payload = {
            first_name: firstName,
            last_name: lastName,
            phone_number: phoneNumber,
            email,
            date_of_birth: dob
        };

        try {
            if (patient) {

            } else {
                await api('/api/v1/patients', {
                    method: 'POST',
                    body: JSON.stringify(payload)
                });
            }
            if (refreshPatients) refreshPatients();
            onClose();
        } catch (err) {
            setError('An error occurred. Please check the console and try again.');
            console.error('Save patient error:', err);
        }
    };

    return (
        <div className="space-y-6">
            {error && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg">{error}</div>}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <label className="block text-sm font-medium text-medical-gray mb-2">First Name</label>
                    <input type="text" value={firstName} onChange={(e) => setFirstName(e.target.value)} className="form-input-themed" placeholder="Enter first name" />
                </div>
                <div>
                    <label className="block text-sm font-medium text-medical-gray mb-2">Last Name</label>
                    <input type="text" value={lastName} onChange={(e) => setLastName(e.target.value)} className="form-input-themed" placeholder="Enter last name" />
                </div>
                <div>
                    <label className="block text-sm font-medium text-medical-gray mb-2">Date of Birth</label>
                    <input type="date" value={dob} onChange={(e) => setDob(e.target.value)} className="form-input-themed" />
                </div>
                <div>
                    <label className="block text-sm font-medium text-medical-gray mb-2">Phone Number</label>
                    <input type="tel" value={phoneNumber} onChange={(e) => setPhoneNumber(e.target.value)} className="form-input-themed" placeholder="Enter phone number" />
                </div>
                <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-medical-gray mb-2">Email</label>
                    <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="form-input-themed" placeholder="Enter email" />
                </div>
            </div>
            <div className="flex justify-end space-x-3">
                <button onClick={onClose} className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">Cancel</button>
                <button onClick={handleSubmit} className="medical-button px-4 py-2 text-white rounded-lg relative z-10">
                    {patient ? 'Update Patient' : 'Create Patient'}
                </button>
            </div>
        </div>
    );
};

window.PatientEditor = PatientEditor;


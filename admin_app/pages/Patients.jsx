import React from 'react';
import LoadingSpinner from '../lib/LoadingSpinner.jsx';
import Modal from '../lib/Modal.jsx';
import PatientDetails from '../components/PatientDetails.jsx';
import PatientEditor from '../components/PatientEditor.jsx'; // Assuming this exists

const Patients = ({ user }) => {
    const [patients, setPatients] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [searchTerm, setSearchTerm] = React.useState('');
    const [selectedPatient, setSelectedPatient] = React.useState(null);
    const [showModal, setShowModal] = React.useState(false);

    React.useEffect(() => {
        const fetchPatients = async () => {
            try {
                const data = await window.api(`/api/v1/patients?search=${searchTerm}`);
                setPatients(Array.isArray(data) ? data : data.patients || []);
            } catch (error) {
                console.error('Error fetching patients:', error);
            } finally {
                setLoading(false);
            }
        };
        fetchPatients();
    }, [searchTerm]);

    const handlePatientClick = (patient) => {
        setSelectedPatient(patient);
        setShowModal(true);
    };

    if (loading) return <LoadingSpinner />;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-lg sm:text-xl lg:text-2xl font-bold text-medical-dark font-primary">Patients</h2>
                <div className="flex space-x-2 sm:space-x-4">
                    <div className="relative">
                        <input
                            type="text"
                            placeholder="Search patients..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="form-input-themed pl-10"
                        />
                        <i className="fas fa-search absolute left-3 top-1/2 transform -translate-y-1/2 text-medical-gray"></i>
                    </div>
                    {user?.permissions?.can_edit_patient_info && window.PatientEditor && (
                        <button onClick={() => {
                            // TODO: Open PatientEditor modal
                        }} className="medical-button px-6 py-3 text-white rounded-xl font-secondary flex flex-wrap items-center gap-2 relative z-10">
                            <i className="fas fa-user-plus"></i>
                            <span>Add Patient</span>
                        </button>
                    )}
                </div>
            </div>

            <div className="medical-card rounded-2xl overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead className="bg-medical-light">
                            <tr>
                                <th className="text-left p-4 font-semibold text-medical-dark">Name</th>
                                <th className="text-left p-4 font-semibold text-medical-dark">Phone</th>
                                <th className="text-left p-4 font-semibold text-medical-dark">Email</th>
                                <th className="text-left p-4 font-semibold text-medical-dark">Last Visit</th>
                                <th className="text-left p-4 font-semibold text-medical-dark">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {patients.map(patient => (
                                <tr key={patient.id} className="table-row border-b border-gray-100">
                                    <td className="p-4">
                                        <div className="flex items-center space-x-3">
                                            <div className="w-10 h-10 bg-medical-accent/10 rounded-full flex items-center justify-center">
                                                <span className="text-medical-accent font-semibold">
                                                    {patient.first_name?.charAt(0) || 'P'}
                                                </span>
                                            </div>
                                            <div>
                                                <div className="font-semibold text-medical-dark">{`${patient.first_name} ${patient.last_name || ''}`}</div>
                                                <div className="text-sm text-medical-gray">ID: {patient.id}</div>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="p-4 text-medical-gray">{patient.phone_number || 'N/A'}</td>
                                    <td className="p-4 text-medical-gray">{patient.email || 'N/A'}</td>
                                    <td className="p-4 text-medical-gray">
                                        {patient.last_visit_date ?
                                            new Date(patient.last_visit_date).toLocaleDateString() :
                                            'Never'
                                        }
                                    </td>
                                    <td className="p-4">
                                        <div className="flex space-x-2">
                                            <button
                                                onClick={() => handlePatientClick(patient)}
                                                className="text-medical-accent hover:text-medical-dark"
                                            >
                                                <i className="fas fa-eye"></i>
                                            </button>
                                            {user?.permissions?.can_edit_patient_info && (
                                                <button className="text-medical-success hover:text-green-700" title="Edit Patient">
                                                    <i className="fas fa-edit"></i>
                                                </button>
                                            )}
                                            {user?.permissions?.can_delete_patient && (
                                                <button className="text-medical-error hover:text-red-700" title="Delete Patient">
                                                    <i className="fas fa-trash"></i>
                                                </button>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>

                {patients.length === 0 && (
                    <div className="text-center py-12">
                        <i className="fas fa-users text-4xl text-medical-gray mb-4"></i>
                        <p className="text-medical-gray">No patients found</p>
                    </div>
                )}
            </div>

            <Modal
                isOpen={showModal}
                onClose={() => setShowModal(false)}
                title="Patient Details"
                width="max-w-6xl"
            >
                {selectedPatient && <PatientDetails patient={selectedPatient} user={user} />}
            </Modal>
        </div>
    );
};

window.Patients = Patients;

export default Patients;
// src/features/patients/components/PatientManagement.jsx
import React, { useState } from 'react';
import PatientDetailView from './PatientDetailView';

function PatientManagement({ patients, fetchPatients }) {
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedPatient, setSelectedPatient] = useState(null);

    const filteredPatients = patients.filter(patient =>
        patient.first_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        patient.last_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        patient.phone_number.includes(searchTerm) ||
        patient.email.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const handleSelectPatient = (patient) => {
        setSelectedPatient(patient);
    };

    const handleBack = () => {
        setSelectedPatient(null);
    };

    if (selectedPatient) {
        return (
            <PatientDetailView 
                patient={selectedPatient}
                onBack={handleBack}
                fetchPatients={fetchPatients}
            />
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-3xl font-bold text-text-dark">Patient Management</h2>
                <div className="text-sm text-text-light">
                    {patients.length} patients registered
                </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm p-6">
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-xl font-semibold text-text-dark">All Patients</h3>
                    <div className="flex items-center space-x-4">
                        <input
                            type="text"
                            placeholder="Search patients..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                        />
                        <span className="text-sm text-text-light">
                            {filteredPatients.length} patients found
                        </span>
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {filteredPatients.length === 0 ? (
                        <div className="col-span-full text-center py-8">
                            <div className="text-gray-400 text-6xl mb-4">👥</div>
                            <p className="text-text-light">No patients found</p>
                        </div>
                    ) : (
                        filteredPatients.map((patient) => (
                            <div
                                key={patient.id}
                                onClick={() => handleSelectPatient(patient)}
                                className="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 cursor-pointer transition-colors border"
                            >
                                <div className="flex items-start justify-between mb-2">
                                    <div>
                                        <h4 className="font-semibold text-text-dark">
                                            {patient.first_name} {patient.last_name}
                                        </h4>
                                        <p className="text-sm text-text-light">
                                            ID: {patient.id}
                                        </p>
                                    </div>
                                    <div className="text-2xl">👤</div>
                                </div>
                                
                                <div className="space-y-1 text-sm">
                                    <p className="text-text-light">
                                        📞 {patient.phone_number}
                                    </p>
                                    <p className="text-text-light">
                                        ✉️ {patient.email}
                                    </p>
                                    {patient.date_of_birth && (
                                        <p className="text-text-light">
                                            🎂 {new Date(patient.date_of_birth).toLocaleDateString()}
                                        </p>
                                    )}
                                </div>

                                <div className="mt-3 pt-3 border-t border-gray-200">
                                    <div className="flex justify-between text-xs text-text-light">
                                        <span>Click to view details</span>
                                        <span>
                                            Registered: {new Date(patient.created_at).toLocaleDateString()}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
}

export default PatientManagement;
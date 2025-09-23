// src/features/patients/components/PatientDetailView.jsx
import React, { useState, useEffect } from 'react';

function PatientDetailView({ patient, onBack, fetchPatients }) {
    const [appointments, setAppointments] = useState([]);
    const [remarks, setRemarks] = useState([]);
    const [newRemark, setNewRemark] = useState('');
    const [isAddingRemark, setIsAddingRemark] = useState(false);

    useEffect(() => {
        fetchPatientAppointments();
        fetchPatientRemarks();
    }, [patient.id]);

    const fetchPatientAppointments = async () => {
        try {
            const response = await fetch(`/api/patients/${patient.id}/appointments`);
            const data = await response.json();
            setAppointments(data);
        } catch (error) {
            console.error('Error fetching patient appointments:', error);
        }
    };

    const fetchPatientRemarks = async () => {
        try {
            const response = await fetch(`/api/patients/${patient.id}/remarks`);
            const data = await response.json();
            setRemarks(data);
        } catch (error) {
            console.error('Error fetching patient remarks:', error);
        }
    };

    const handleAddRemark = async (e) => {
        e.preventDefault();
        if (!newRemark.trim()) return;

        try {
            const response = await fetch(`/api/patients/${patient.id}/remarks`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ remark: newRemark })
            });

            if (response.ok) {
                setNewRemark('');
                setIsAddingRemark(false);
                fetchPatientRemarks();
            }
        } catch (error) {
            console.error('Error adding remark:', error);
        }
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    };

    const formatDateTime = (dateString) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'scheduled':
                return 'bg-blue-100 text-blue-800';
            case 'completed':
                return 'bg-green-100 text-green-800';
            case 'cancelled':
                return 'bg-red-100 text-red-800';
            case 'no-show':
                return 'bg-gray-100 text-gray-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    };

    const calculateAge = (birthDate) => {
        if (!birthDate) return 'N/A';
        const today = new Date();
        const birth = new Date(birthDate);
        const age = today.getFullYear() - birth.getFullYear();
        const monthDiff = today.getMonth() - birth.getMonth();
        if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
            return age - 1;
        }
        return age;
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center space-x-4">
                <button
                    onClick={onBack}
                    className="flex items-center space-x-2 text-primary hover:text-primary-dark transition-colors"
                >
                    <span>←</span>
                    <span>Back to Patients</span>
                </button>
                <div className="h-6 w-px bg-gray-300"></div>
                <h2 className="text-3xl font-bold text-text-dark">
                    {patient.first_name} {patient.last_name}
                </h2>
            </div>

            {/* Patient Info Card */}
            <div className="bg-white rounded-xl shadow-sm p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <div>
                        <h3 className="font-semibold text-text-dark mb-3">Personal Information</h3>
                        <div className="space-y-2 text-sm">
                            <p><strong>Patient ID:</strong> {patient.id}</p>
                            <p><strong>Full Name:</strong> {patient.first_name} {patient.last_name}</p>
                            <p><strong>Date of Birth:</strong> {patient.date_of_birth ? formatDate(patient.date_of_birth) : 'N/A'}</p>
                            <p><strong>Age:</strong> {calculateAge(patient.date_of_birth)} years</p>
                            <p><strong>Gender:</strong> {patient.gender || 'N/A'}</p>
                        </div>
                    </div>

                    <div>
                        <h3 className="font-semibold text-text-dark mb-3">Contact Information</h3>
                        <div className="space-y-2 text-sm">
                            <p><strong>Phone:</strong> {patient.phone_number}</p>
                            <p><strong>Email:</strong> {patient.email}</p>
                            <p><strong>Address:</strong> {patient.address || 'N/A'}</p>
                        </div>
                    </div>

                    <div>
                        <h3 className="font-semibold text-text-dark mb-3">Registration Details</h3>
                        <div className="space-y-2 text-sm">
                            <p><strong>Registered:</strong> {formatDate(patient.created_at)}</p>
                            <p><strong>Last Updated:</strong> {formatDate(patient.updated_at)}</p>
                            <p><strong>Total Appointments:</strong> {appointments.length}</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Appointments */}
            <div className="bg-white rounded-xl shadow-sm p-6">
                <h3 className="text-xl font-semibold text-text-dark mb-4">Appointment History</h3>
                {appointments.length === 0 ? (
                    <p className="text-text-light">No appointments found for this patient.</p>
                ) : (
                    <div className="space-y-3">
                        {appointments.map((appointment) => (
                            <div key={appointment.id} className="border border-gray-200 rounded-lg p-4">
                                <div className="flex justify-between items-start">
                                    <div>
                                        <p className="font-medium text-text-dark">
                                            {formatDateTime(appointment.appointment_time)}
                                        </p>
                                        <p className="text-sm text-text-light">
                                            Location: {appointment.location?.name || 'Unknown'}
                                        </p>
                                        {appointment.notes && (
                                            <p className="text-sm text-text-light mt-1">
                                                Notes: {appointment.notes}
                                            </p>
                                        )}
                                    </div>
                                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(appointment.status)}`}>
                                        {appointment.status}
                                    </span>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Remarks */}
            <div className="bg-white rounded-xl shadow-sm p-6">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-xl font-semibold text-text-dark">Patient Remarks</h3>
                    <button
                        onClick={() => setIsAddingRemark(true)}
                        className="bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg text-sm transition-colors"
                    >
                        + Add Remark
                    </button>
                </div>

                {isAddingRemark && (
                    <form onSubmit={handleAddRemark} className="mb-4 p-4 border border-gray-200 rounded-lg">
                        <textarea
                            value={newRemark}
                            onChange={(e) => setNewRemark(e.target.value)}
                            placeholder="Enter remark..."
                            rows="3"
                            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent resize-none"
                            required
                        />
                        <div className="flex space-x-2 mt-2">
                            <button
                                type="submit"
                                className="bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded text-sm transition-colors"
                            >
                                Save
                            </button>
                            <button
                                type="button"
                                onClick={() => {
                                    setIsAddingRemark(false);
                                    setNewRemark('');
                                }}
                                className="bg-gray-300 hover:bg-gray-400 text-gray-700 px-4 py-2 rounded text-sm transition-colors"
                            >
                                Cancel
                            </button>
                        </div>
                    </form>
                )}

                {remarks.length === 0 ? (
                    <p className="text-text-light">No remarks added for this patient.</p>
                ) : (
                    <div className="space-y-3">
                        {remarks.map((remark) => (
                            <div key={remark.id} className="border border-gray-200 rounded-lg p-4">
                                <p className="text-text-dark mb-2">{remark.remark}</p>
                                <p className="text-xs text-right text-text-light">
                                    -- {remark.author.username} on {formatDate(remark.created_at)}
                                </p>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

export default PatientDetailView;
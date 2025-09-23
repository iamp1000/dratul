// src/features/dashboard/components/AppointmentsForDay.jsx
import React from 'react';

function AppointmentsForDay({ selectedDate, appointments, patients, locations, onEditAppointment, onDeleteAppointment }) {
    const formatDate = (date) => {
        return date.toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    };

    const formatTime = (timeString) => {
        return new Date(timeString).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    const getPatientName = (patientId) => {
        const patient = patients.find(p => p.id === patientId);
        return patient ? `${patient.first_name} ${patient.last_name}` : 'Unknown Patient';
    };

    const getLocationName = (locationId) => {
        const location = locations.find(l => l.id === locationId);
        return location ? location.name : 'Unknown Location';
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

    const sortedAppointments = appointments.sort((a, b) => 
        new Date(a.appointment_time) - new Date(b.appointment_time)
    );

    return (
        <div>
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-semibold text-text-dark">
                    Appointments
                </h3>
                <p className="text-sm text-text-light">
                    {formatDate(selectedDate)}
                </p>
            </div>

            {sortedAppointments.length === 0 ? (
                <div className="text-center py-8">
                    <div className="text-gray-400 text-6xl mb-4">📅</div>
                    <p className="text-text-light">No appointments for this day</p>
                </div>
            ) : (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                    {sortedAppointments.map((appointment) => (
                        <div key={appointment.id} className="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors">
                            <div className="flex justify-between items-start mb-2">
                                <div>
                                    <h4 className="font-semibold text-text-dark">
                                        {getPatientName(appointment.patient_id)}
                                    </h4>
                                    <p className="text-sm text-text-light">
                                        📍 {getLocationName(appointment.location_id)}
                                    </p>
                                </div>
                                <div className="flex items-center space-x-2">
                                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(appointment.status)}`}>
                                        {appointment.status}
                                    </span>
                                    <span className="text-sm font-medium text-primary">
                                        {formatTime(appointment.appointment_time)}
                                    </span>
                                </div>
                            </div>
                            
                            {appointment.notes && (
                                <p className="text-sm text-text-light mb-3 italic">
                                    "{appointment.notes}"
                                </p>
                            )}
                            
                            <div className="flex justify-between items-center">
                                <div className="flex space-x-2">
                                    <button
                                        onClick={() => onEditAppointment(appointment)}
                                        className="text-xs bg-primary text-white px-3 py-1 rounded hover:bg-primary-dark transition-colors"
                                    >
                                        Edit
                                    </button>
                                    <button
                                        onClick={() => onDeleteAppointment(appointment.id)}
                                        className="text-xs bg-red-500 text-white px-3 py-1 rounded hover:bg-red-600 transition-colors"
                                    >
                                        Delete
                                    </button>
                                </div>
                                <p className="text-xs text-text-light">
                                    ID: {appointment.id}
                                </p>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default AppointmentsForDay;
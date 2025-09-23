// src/features/dashboard/components/Dashboard.jsx
import React, { useState } from 'react';
import CalendarView from './CalendarView';
import AppointmentsForDay from './AppointmentsForDay';
import AppointmentModal from './AppointmentModal';
import DashboardStats from './DashboardStats';

function Dashboard({ appointments, setAppointments, patients, locations, fetchAppointments }) {
    const [selectedDate, setSelectedDate] = useState(new Date());
    const [selectedAppointment, setSelectedAppointment] = useState(null);
    const [isAppointmentModalOpen, setIsAppointmentModalOpen] = useState(false);
    const [appointmentFormData, setAppointmentFormData] = useState({
        patient_id: '',
        appointment_time: '',
        location_id: '',
        notes: '',
        status: 'scheduled'
    });

    const resetAppointmentForm = () => {
        setAppointmentFormData({
            patient_id: '',
            appointment_time: '',
            location_id: '',
            notes: '',
            status: 'scheduled'
        });
        setSelectedAppointment(null);
    };

    const handleCreateAppointment = () => {
        resetAppointmentForm();
        setIsAppointmentModalOpen(true);
    };

    const handleEditAppointment = (appointment) => {
        setSelectedAppointment(appointment);
        setAppointmentFormData({
            patient_id: appointment.patient_id,
            appointment_time: appointment.appointment_time.slice(0, 16),
            location_id: appointment.location_id,
            notes: appointment.notes || '',
            status: appointment.status
        });
        setIsAppointmentModalOpen(true);
    };

    const handleAppointmentSubmit = async (e) => {
        e.preventDefault();
        try {
            const url = selectedAppointment 
                ? `/api/appointments/${selectedAppointment.id}` 
                : '/api/appointments';
            const method = selectedAppointment ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(appointmentFormData)
            });
            
            if (response.ok) {
                fetchAppointments();
                setIsAppointmentModalOpen(false);
                resetAppointmentForm();
            }
        } catch (error) {
            console.error('Error saving appointment:', error);
        }
    };

    const handleDeleteAppointment = async (appointmentId) => {
        if (confirm('Are you sure you want to delete this appointment?')) {
            try {
                const response = await fetch(`/api/appointments/${appointmentId}`, {
                    method: 'DELETE'
                });
                if (response.ok) {
                    fetchAppointments();
                }
            } catch (error) {
                console.error('Error deleting appointment:', error);
            }
        }
    };

    const getAppointmentsForDate = (date) => {
        const dateString = date.toISOString().split('T')[0];
        return appointments.filter(apt => 
            apt.appointment_time.startsWith(dateString)
        );
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-3xl font-bold text-text-dark">Dashboard</h2>
                <button
                    onClick={handleCreateAppointment}
                    className="bg-primary hover:bg-primary-dark text-white px-6 py-3 rounded-lg transition-colors font-medium"
                >
                    + New Appointment
                </button>
            </div>

            <DashboardStats 
                appointments={appointments}
                patients={patients}
            />

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="bg-white rounded-xl shadow-sm p-6">
                    <h3 className="text-xl font-semibold text-text-dark mb-4">Calendar</h3>
                    <CalendarView 
                        selectedDate={selectedDate}
                        setSelectedDate={setSelectedDate}
                        appointments={appointments}
                    />
                </div>

                <div className="bg-white rounded-xl shadow-sm p-6">
                    <AppointmentsForDay 
                        selectedDate={selectedDate}
                        appointments={getAppointmentsForDate(selectedDate)}
                        patients={patients}
                        locations={locations}
                        onEditAppointment={handleEditAppointment}
                        onDeleteAppointment={handleDeleteAppointment}
                    />
                </div>
            </div>

            <AppointmentModal 
                isOpen={isAppointmentModalOpen}
                onClose={() => {
                    setIsAppointmentModalOpen(false);
                    resetAppointmentForm();
                }}
                formData={appointmentFormData}
                setFormData={setAppointmentFormData}
                onSubmit={handleAppointmentSubmit}
                patients={patients}
                locations={locations}
                isEditing={!!selectedAppointment}
            />
        </div>
    );
}

export default Dashboard;
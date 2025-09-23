// src/features/dashboard/components/DashboardStats.jsx
import React from 'react';

function DashboardStats({ appointments, patients }) {
    const today = new Date().toISOString().split('T')[0];
    
    const todaysAppointments = appointments.filter(apt => 
        apt.appointment_time.startsWith(today)
    );
    
    const completedAppointments = appointments.filter(apt => 
        apt.status === 'completed'
    );
    
    const scheduledAppointments = appointments.filter(apt => 
        apt.status === 'scheduled'
    );
    
    const cancelledAppointments = appointments.filter(apt => 
        apt.status === 'cancelled'
    );

    const stats = [
        {
            label: "Today's Appointments",
            value: todaysAppointments.length,
            icon: "📅",
            color: "bg-blue-500"
        },
        {
            label: "Total Patients",
            value: patients.length,
            icon: "👥",
            color: "bg-green-500"
        },
        {
            label: "Completed",
            value: completedAppointments.length,
            icon: "✅",
            color: "bg-emerald-500"
        },
        {
            label: "Scheduled",
            value: scheduledAppointments.length,
            icon: "🕐",
            color: "bg-amber-500"
        }
    ];

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {stats.map((stat, index) => (
                <div key={index} className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-text-light mb-1">
                                {stat.label}
                            </p>
                            <p className="text-3xl font-bold text-text-dark">
                                {stat.value}
                            </p>
                        </div>
                        <div className={`w-12 h-12 rounded-lg ${stat.color} flex items-center justify-center text-white text-2xl`}>
                            {stat.icon}
                        </div>
                    </div>
                </div>
            ))}
        </div>
    );
}

export default DashboardStats;
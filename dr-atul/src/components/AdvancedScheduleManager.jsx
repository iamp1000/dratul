// src/features/schedule/components/AdvancedScheduleManager.jsx
import React, { useState, useEffect } from 'react';

function AdvancedScheduleManager() {
    const [schedules, setSchedules] = useState([]);
    const [editingShift, setEditingShift] = useState(null);
    const [selectedDay, setSelectedDay] = useState('monday');

    const daysOfWeek = [
        { key: 'monday', label: 'Monday' },
        { key: 'tuesday', label: 'Tuesday' },
        { key: 'wednesday', label: 'Wednesday' },
        { key: 'thursday', label: 'Thursday' },
        { key: 'friday', label: 'Friday' },
        { key: 'saturday', label: 'Saturday' },
        { key: 'sunday', label: 'Sunday' }
    ];

    useEffect(() => {
        fetchSchedules();
    }, []);

    const fetchSchedules = async () => {
        try {
            const response = await fetch('/api/schedules');
            const data = await response.json();
            setSchedules(data);
        } catch (error) {
            console.error('Error fetching schedules:', error);
        }
    };

    const getScheduleForDay = (day) => {
        return schedules.filter(schedule => schedule.day_of_week === day);
    };

    const handleAddShift = (day) => {
        const newShift = {
            day_of_week: day,
            start_time: '09:00',
            end_time: '17:00',
            is_available: true,
            max_appointments: 8,
            break_start: '12:00',
            break_end: '13:00'
        };
        setEditingShift(newShift);
    };

    const handleEditShift = (shift) => {
        setEditingShift({ ...shift });
    };

    const handleSaveShift = async () => {
        try {
            const url = editingShift.id ? `/api/schedules/${editingShift.id}` : '/api/schedules';
            const method = editingShift.id ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(editingShift)
            });
            
            if (response.ok) {
                fetchSchedules();
                setEditingShift(null);
            }
        } catch (error) {
            console.error('Error saving schedule:', error);
        }
    };

    const handleDeleteShift = async (shiftId) => {
        if (confirm('Are you sure you want to delete this shift?')) {
            try {
                const response = await fetch(`/api/schedules/${shiftId}`, {
                    method: 'DELETE'
                });
                if (response.ok) {
                    fetchSchedules();
                }
            } catch (error) {
                console.error('Error deleting schedule:', error);
            }
        }
    };

    const handleShiftInputChange = (field, value) => {
        setEditingShift(prev => ({
            ...prev,
            [field]: value
        }));
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-3xl font-bold text-text-dark">Schedule Management</h2>
                <div className="text-sm text-text-light">
                    Configure working hours and availability
                </div>
            </div>

            {/* Day Selector */}
            <div className="bg-white rounded-xl shadow-sm p-6">
                <div className="flex space-x-2 mb-6 overflow-x-auto">
                    {daysOfWeek.map(day => (
                        <button
                            key={day.key}
                            onClick={() => setSelectedDay(day.key)}
                            className={`px-4 py-2 rounded-lg font-medium whitespace-nowrap transition-colors ${
                                selectedDay === day.key
                                    ? 'bg-primary text-white'
                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                            }`}
                        >
                            {day.label}
                        </button>
                    ))}
                </div>

                {/* Schedule for Selected Day */}
                <div className="space-y-4">
                    <div className="flex justify-between items-center">
                        <h3 className="text-xl font-semibold text-text-dark capitalize">
                            {selectedDay} Schedule
                        </h3>
                        <button
                            onClick={() => handleAddShift(selectedDay)}
                            className="bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg text-sm transition-colors"
                        >
                            + Add Shift
                        </button>
                    </div>

                    <div className="space-y-3">
                        {getScheduleForDay(selectedDay).length === 0 ? (
                            <div className="text-center py-8 text-gray-500">
                                <div className="text-4xl mb-2">📅</div>
                                <p>No shifts scheduled for {selectedDay}</p>
                            </div>
                        ) : (
                            getScheduleForDay(selectedDay).map((shift) => (
                                <div key={shift.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                                    <div className="flex justify-between items-start">
                                        <div className="flex-1">
                                            <div className="flex items-center space-x-4 mb-2">
                                                <span className="font-medium text-text-dark">
                                                    {shift.start_time} - {shift.end_time}
                                                </span>
                                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                                    shift.is_available
                                                        ? 'bg-green-100 text-green-800'
                                                        : 'bg-red-100 text-red-800'
                                                }`}>
                                                    {shift.is_available ? 'Available' : 'Unavailable'}
                                                </span>
                                            </div>
                                            <div className="text-sm text-text-light space-y-1">
                                                <p>Max Appointments: {shift.max_appointments}</p>
                                                {shift.break_start && shift.break_end && (
                                                    <p>Break: {shift.break_start} - {shift.break_end}</p>
                                                )}
                                            </div>
                                        </div>
                                        <div className="flex space-x-2">
                                            <button
                                                onClick={() => handleEditShift(shift)}
                                                className="text-primary hover:text-primary-dark transition-colors text-sm"
                                            >
                                                Edit
                                            </button>
                                            <button
                                                onClick={() => handleDeleteShift(shift.id)}
                                                className="text-red-600 hover:text-red-800 transition-colors text-sm"
                                            >
                                                Delete
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>

            {/* Edit Shift Modal */}
            {editingShift && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
                    <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
                        <h3 className="text-xl font-bold text-text-dark mb-4">
                            {editingShift.id ? 'Edit Shift' : 'Add New Shift'}
                        </h3>
                        
                        <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-text-dark mb-1">
                                        Start Time
                                    </label>
                                    <input
                                        type="time"
                                        value={editingShift.start_time}
                                        onChange={(e) => handleShiftInputChange('start_time', e.target.value)}
                                        className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-text-dark mb-1">
                                        End Time
                                    </label>
                                    <input
                                        type="time"
                                        value={editingShift.end_time}
                                        onChange={(e) => handleShiftInputChange('end_time', e.target.value)}
                                        className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-text-dark mb-1">
                                    Max Appointments
                                </label>
                                <input
                                    type="number"
                                    value={editingShift.max_appointments}
                                    onChange={(e) => handleShiftInputChange('max_appointments', parseInt(e.target.value))}
                                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                                    min="1"
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-text-dark mb-1">
                                        Break Start
                                    </label>
                                    <input
                                        type="time"
                                        value={editingShift.break_start || ''}
                                        onChange={(e) => handleShiftInputChange('break_start', e.target.value)}
                                        className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-text-dark mb-1">
                                        Break End
                                    </label>
                                    <input
                                        type="time"
                                        value={editingShift.break_end || ''}
                                        onChange={(e) => handleShiftInputChange('break_end', e.target.value)}
                                        className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                                    />
                                </div>
                            </div>

                            <div className="flex items-center">
                                <input
                                    type="checkbox"
                                    checked={editingShift.is_available}
                                    onChange={(e) => handleShiftInputChange('is_available', e.target.checked)}
                                    className="h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
                                />
                                <label className="ml-2 block text-sm text-text-dark">
                                    Available for appointments
                                </label>
                            </div>
                        </div>

                        <div className="flex space-x-3 mt-6">
                            <button
                                onClick={handleSaveShift}
                                className="flex-1 bg-primary hover:bg-primary-dark text-white font-medium py-2 px-4 rounded-lg transition-colors"
                            >
                                Save Shift
                            </button>
                            <button
                                onClick={() => setEditingShift(null)}
                                className="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-700 font-medium py-2 px-4 rounded-lg transition-colors"
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default AdvancedScheduleManager;
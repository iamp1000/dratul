import React from 'react';

const Calendar = ({ appointments, onDateClick, onAppointmentClick, currentDate, setCurrentDate }) => {
    const getDaysInMonth = (date) => {
        return new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
    };

    const getFirstDayOfMonth = (date) => {
        return new Date(date.getFullYear(), date.getMonth(), 1).getDay();
    };

    const getAppointmentsForDate = (date) => {
        if (!appointments) return [];
        return appointments.filter(apt => {
            const aptDate = new Date(apt.start_time);
            return aptDate.toDateString() === date.toDateString();
        });
    };

    const renderCalendarDays = () => {
        const daysInMonth = getDaysInMonth(currentDate);
        const firstDayOfMonth = getFirstDayOfMonth(currentDate);
        const days = [];

        for (let i = 0; i < firstDayOfMonth; i++) {
            days.push(<div key={`empty-${i}`} className="p-2"></div>);
        }

        for (let day = 1; day <= daysInMonth; day++) {
            const date = new Date(currentDate.getFullYear(), currentDate.getMonth(), day);
            const dayAppointments = getAppointmentsForDate(date);
            const isToday = date.toDateString() === new Date().toDateString();

            days.push(
                <div
                    key={day}
                    className={`calendar-cell p-2 border border-gray-200 rounded-lg min-h-[80px] ${isToday ? 'bg-medical-accent/10 border-medical-accent' : ''}`}
                    onClick={() => onDateClick(date)}
                >
                    <div className={`font-semibold mb-1 ${isToday ? 'text-medical-accent' : 'text-medical-dark'}`}>
                        {day}
                    </div>
                    <div className="space-y-1">
                        {dayAppointments.slice(0, 3).map(apt => (
                            <div
                                key={apt.id}
                                className="text-xs p-1 bg-medical-accent/20 text-medical-accent rounded cursor-pointer hover:bg-medical-accent/30"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onAppointmentClick(apt);
                                }}
                            >
                                {new Date(apt.start_time).toLocaleTimeString('en-US', {
                                    hour: '2-digit',
                                    minute: '2-digit'
                                })}
                            </div>
                        ))}
                        {dayAppointments.length > 3 && (
                            <div className="text-xs text-medical-gray">
                                +{dayAppointments.length - 3} more
                            </div>
                        )}
                    </div>
                </div>
            );
        }

        return days;
    };

    const navigateMonth = (direction) => {
        const newDate = new Date(currentDate);
        newDate.setMonth(currentDate.getMonth() + direction);
        setCurrentDate(newDate);
    };

    return (
        <div className="medical-card p-6 rounded-2xl">
            <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold text-medical-dark font-primary">
                    {currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
                </h3>
                <div className="flex space-x-2">
                    <button
                        onClick={() => navigateMonth(-1)}
                        className="p-2 text-medical-accent hover:bg-medical-accent/10 rounded-lg"
                    >
                        <i className="fas fa-chevron-left"></i>
                    </button>
                    <button
                        onClick={() => navigateMonth(1)}
                        className="p-2 text-medical-accent hover:bg-medical-accent/10 rounded-lg"
                    >
                        <i className="fas fa-chevron-right"></i>
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-7 gap-1 sm:gap-2">
                {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                    <div key={day} className="p-2 text-center font-semibold text-medical-gray">
                        {day}
                    </div>
                ))}
                {renderCalendarDays()}
            </div>
        </div>
    );
};

export default Calendar;


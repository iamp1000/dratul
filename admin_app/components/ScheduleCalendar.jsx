const ScheduleCalendar = ({ homeClinicSchedule, hospitalSchedule, onDateClick, currentDate, setCurrentDate, unavailablePeriods }) => {
  const getDaysInMonth = (date) => new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
  const getFirstDayOfMonth = (date) => new Date(date.getFullYear(), date.getMonth(), 1).getDay();

  const isDateBlocked = (date, locationId) => {
    if (!unavailablePeriods || !unavailablePeriods[locationId]) {
      return null;
    }

    const checkDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());

    for (const period of unavailablePeriods[locationId]) {
      const periodStartDate = new Date(period.start_datetime);
      const periodEndDate = new Date(period.end_datetime);
      const startDateOnly = new Date(periodStartDate.getFullYear(), periodStartDate.getMonth(), periodStartDate.getDate());
      const endDateOnly = new Date(periodEndDate.getFullYear(), periodEndDate.getMonth(), periodEndDate.getDate());

      if (checkDate >= startDateOnly && checkDate <= endDateOnly) {
        return period;
      }
    }
    return null;
  };

  const getScheduleForDate = (date, schedule) => {
    if (!schedule) return null;
    const dayOfWeek = (date.getDay() + 6) % 7;
    return schedule[dayOfWeek];
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
      const clinicSchedule = getScheduleForDate(date, homeClinicSchedule);
      const hospitalScheduleData = getScheduleForDate(date, hospitalSchedule);
      const isToday = date.toDateString() === new Date().toDateString();

      const clinicBlock = isDateBlocked(date, 1);
      const hospitalBlock = isDateBlocked(date, 2);

      days.push(
        <div
          key={day}
          className={`calendar-cell p-2 border border-gray-200 rounded-lg min-h-[90px] ${isToday ? 'bg-medical-accent/10 border-medical-accent' : ''}`}
          onClick={() => onDateClick(date, { clinicSchedule, hospitalSchedule: hospitalScheduleData })}
        >
          <div className={`font-semibold mb-1 ${isToday ? 'text-medical-accent' : 'text-medical-dark'}`}>{day}</div>
          <div className="text-xs space-y-1">
            {clinicBlock ? (
              <div className="text-red-600 font-bold p-1 bg-red-100 rounded">
                <strong>C:</strong> BLOCKED
              </div>
            ) : clinicSchedule && clinicSchedule.is_available ? (
              <div className="text-blue-600"><strong>C:</strong> {clinicSchedule.start_time.substring(0, 5)} - {clinicSchedule.end_time.substring(0, 5)}</div>
            ) : (
              <div className="text-gray-400"><strong>C:</strong> Off</div>
            )}

            {hospitalBlock ? (
              <div className="text-red-600 font-bold p-1 bg-red-100 rounded mt-1">
                <strong>H:</strong> BLOCKED
              </div>
            ) : hospitalScheduleData && hospitalScheduleData.is_available ? (
              <div className="text-green-700"><strong>H:</strong> {hospitalScheduleData.start_time.substring(0, 5)} - {hospitalScheduleData.end_time.substring(0, 5)}</div>
            ) : (
              <div className="text-gray-400"><strong>H:</strong> Off</div>
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
          <button onClick={() => navigateMonth(-1)} className="p-2 text-medical-accent hover:bg-medical-accent/10 rounded-lg">
            <i className="fas fa-chevron-left"></i>
          </button>
          <button onClick={() => navigateMonth(1)} className="p-2 text-medical-accent hover:bg-medical-accent/10 rounded-lg">
            <i className="fas fa-chevron-right"></i>
          </button>
        </div>
      </div>
      <div className="grid grid-cols-7 gap-1 sm:gap-2">
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
          <div key={day} className="p-2 text-center font-semibold text-medical-gray">{day}</div>
        ))}
        {renderCalendarDays()}
      </div>
    </div>
  );
};

export default ScheduleCalendar;
const DateAppointments = ({ date, appointments }) => (
  <div className="space-y-4">
    <h4 className="font-semibold text-medical-dark">
      Appointments for {date.toLocaleDateString('en-US', {
        weekday: 'long',
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      })}
    </h4>
    {appointments.length === 0 ? (
      <div className="text-center py-8 text-medical-gray">
        <i className="fas fa-calendar-times text-4xl mb-4"></i>
        <p>No appointments scheduled for this date</p>
      </div>
    ) : (
      <div className="space-y-3">
        {appointments.map(apt => (
          <div key={apt.id} className="table-row p-4 border border-gray-200 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-semibold">{`${apt.patient?.first_name || ''} ${apt.patient?.last_name || ''}`.trim() || 'Unknown Patient'}</div>
                <div className="text-sm text-medical-gray">
                  {new Date(apt.start_time).toLocaleTimeString()} - {apt.appointment_type}
                </div>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="px-2 py-1 bg-medical-accent/10 text-medical-accent rounded-full text-xs">
                  {apt.status}
                </span>
                <button className="text-medical-accent hover:text-medical-dark">
                  <i className="fas fa-eye"></i>
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    )}
  </div>
);


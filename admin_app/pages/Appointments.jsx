const Appointments = ({ openModal, closeModal, user }) => {
  const [appointments, setAppointments] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [selectedAppointment, setSelectedAppointment] = React.useState(null);
  const [selectedDate, setSelectedDate] = React.useState(null);
  const [showModal, setShowModal] = React.useState(false);
  const [currentDate, setCurrentDate] = React.useState(new Date());

  const fetchAppointments = React.useCallback(async () => {
    setLoading(true);
    try {
      const firstDay = new Date(Date.UTC(currentDate.getFullYear(), currentDate.getMonth(), 1));
      const lastDay = new Date(Date.UTC(currentDate.getFullYear(), currentDate.getMonth() + 1, 0));

      const toISODate = (d) => {
        const year = d.getUTCFullYear();
        const month = String(d.getUTCMonth() + 1).padStart(2, '0');
        const day = String(d.getUTCDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
      };

      const startDate = toISODate(firstDay);
      const endDate = toISODate(lastDay);

      const data = await window.api(`/api/v1/appointments?start_date=${startDate}&end_date=${endDate}`);
      setAppointments(Array.isArray(data) ? data : data.appointments || []);
    } catch (error) {
      console.error("Failed to fetch appointments:", error);
    } finally {
      setLoading(false);
    }
  }, [currentDate]);

  React.useEffect(() => {
    fetchAppointments();
  }, [fetchAppointments]);

  const handleDateClick = (date) => {
    setSelectedDate(date);
    setShowModal(true);
  };

  const handleAppointmentClick = (appointment) => {
    setSelectedAppointment(appointment);
    setShowModal(true);
  };

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h2 className="text-lg sm:text-xl lg:text-2xl font-bold text-medical-dark font-primary">Appointments</h2>
        {openModal && window.AppointmentEditor && (
          <button onClick={() => openModal('Create New Appointment', <window.AppointmentEditor onClose={closeModal} user={user} refreshAppointments={fetchAppointments} />)} className="medical-button px-6 py-3 text-white rounded-xl font-secondary flex flex-wrap items-center gap-2 relative z-10">
            <i className="fas fa-plus"></i>
            <span>New Appointment</span>
          </button>
        )}
      </div>

      <Calendar
        appointments={appointments}
        onDateClick={handleDateClick}
        onAppointmentClick={handleAppointmentClick}
        currentDate={currentDate}
        setCurrentDate={setCurrentDate}
      />

      <Modal
        isOpen={showModal}
        onClose={() => {
          setShowModal(false);
          setSelectedAppointment(null);
          setSelectedDate(null);
        }}
        title={selectedAppointment ? "Appointment Details" : "Daily View"}
        width="max-w-4xl"
      >
        {selectedAppointment ? (
          <AppointmentDetails appointment={selectedAppointment} />
        ) : selectedDate ? (
          <DailyViewModalContent
            date={selectedDate}
            appointmentsForDate={appointments.filter(apt =>
              new Date(apt.start_time).toDateString() === selectedDate.toDateString()
            )}
          />
        ) : null}
      </Modal>
    </div>
  );
};

window.Appointments = Appointments;


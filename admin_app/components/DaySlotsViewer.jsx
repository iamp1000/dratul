const DaySlotsViewer = ({ date }) => {
  const [selectedLocationId, setSelectedLocationId] = React.useState(1);
  const [slots, setSlots] = React.useState([]);
  const [loadingSlots, setLoadingSlots] = React.useState(false);
  const [slotError, setSlotError] = React.useState('');

  const [weeklySchedule, setWeeklySchedule] = React.useState(null);
  const [scheduleLoading, setScheduleLoading] = React.useState(true);
  const [scheduleError, setScheduleError] = React.useState('');
  const [displayStatus, setDisplayStatus] = React.useState('loading-schedule');

  React.useEffect(() => {
    const fetchWeeklySchedules = async () => {
      setScheduleLoading(true);
      setScheduleError('');
      try {
        const [clinicScheduleData, hospitalScheduleData] = await Promise.all([
          window.api(`/api/v1/schedules/by-location/1`),
          window.api(`/api/v1/schedules/by-location/2`)
        ]);

        const clinicScheduleMap = (clinicScheduleData || []).reduce((acc, item) => {
          acc[item.day_of_week] = item;
          return acc;
        }, {});
        const hospitalScheduleMap = (hospitalScheduleData || []).reduce((acc, item) => {
          acc[item.day_of_week] = item;
          return acc;
        }, {});

        setWeeklySchedule({
          1: clinicScheduleMap,
          2: hospitalScheduleMap
        });
      } catch (err) {
        console.error("[DaySlotsViewer] Error fetching weekly schedules:", err);
        setScheduleError(`Failed to load doctor's schedule: ${err.message}`);
        setDisplayStatus('error');
      } finally {
        setScheduleLoading(false);
      }
    };

    fetchWeeklySchedules();
  }, []);

  const toISODate = (d) => {
    if (!d) return '';
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  React.useEffect(() => {
    const checkAvailabilityAndFetchSlots = async () => {
      if (!date || scheduleLoading || !weeklySchedule) {
        if (scheduleError) setDisplayStatus('error');
        else if (scheduleLoading) setDisplayStatus('loading-schedule');
        return;
      }

      setLoadingSlots(true);
      setSlotError('');
      setSlots([]);
      setDisplayStatus('loading-slots');
      const formattedDate = toISODate(date);
      const dayOfWeek = (date.getDay() + 6) % 7;

      const locationSchedule = weeklySchedule[selectedLocationId];
      const daySchedule = locationSchedule ? locationSchedule[dayOfWeek] : null;

      if (daySchedule && daySchedule.is_available === false) {
        setSlotError('Doctor is unavailable on this day.');
        setDisplayStatus('unavailable');
        setLoadingSlots(false);
        return;
      }

      try {
        const fetchedSlots = await window.api(`/api/v1/slots/${selectedLocationId}/${formattedDate}`);
        const validSlots = Array.isArray(fetchedSlots) ? fetchedSlots : [];
        setSlots(validSlots);

        if (validSlots.length === 0) {
          if (!slotError) setSlotError('No slots generated or found for this day and location.');
          setDisplayStatus('no-slots');
        } else {
          setDisplayStatus('ready');
        }
      } catch (err) {
        console.error(`Error fetching slots for ${formattedDate}:`, err);
        setSlotError(`Failed to load slots: ${err.message}`);
        setSlots([]);
        setDisplayStatus('error');
      } finally {
        setLoadingSlots(false);
      }
    };

    checkAvailabilityAndFetchSlots();
  }, [date, selectedLocationId, weeklySchedule, scheduleLoading, scheduleError]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'available': return 'bg-green-100 text-green-700 border-green-200';
      case 'booked': return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'unavailable': return 'bg-gray-100 text-gray-500 border-gray-200';
      default: return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-xl mb-4">
        <button
          onClick={() => setSelectedLocationId(1)}
          className={`flex-1 py-2 px-4 rounded-lg font-medium transition-all text-sm ${selectedLocationId === 1 ? 'bg-white text-medical-accent shadow-sm' : 'text-medical-gray hover:text-medical-dark'}`}
        >
          <i className="fas fa-clinic-medical mr-1"></i> Home Clinic
        </button>
        <button
          onClick={() => setSelectedLocationId(2)}
          className={`flex-1 py-2 px-4 rounded-lg font-medium transition-all text-sm ${selectedLocationId === 2 ? 'bg-white text-medical-accent shadow-sm' : 'text-medical-gray hover:text-medical-dark'}`}
        >
          <i className="fas fa-hospital mr-1"></i> Hospital
        </button>
      </div>

      {displayStatus === 'loading-schedule' || displayStatus === 'loading-slots' ? (
        <LoadingSpinner />
      ) : displayStatus === 'error' || displayStatus === 'unavailable' ? (
        <div className="text-center py-6 text-red-600 bg-red-50 p-4 rounded-lg border border-red-200">
          <i className={`fas ${displayStatus === 'unavailable' ? 'fa-calendar-times' : 'fa-exclamation-triangle'} text-2xl mb-2`}></i>
          <p className="text-sm">{slotError || scheduleError || 'An error occurred.'}</p>
        </div>
      ) : displayStatus === 'no-slots' || slots.length === 0 ? (
        <div className="text-center py-6 text-medical-gray bg-gray-50 p-4 rounded-lg border border-gray-200">
          <i className="fas fa-clock text-2xl mb-2"></i>
          <p className="text-sm">No available appointment times found.</p>
        </div>
      ) : (
        <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-2">
          {slots.map(slot => (
            <div key={slot.id} className={`p-2 border rounded-lg text-center ${getStatusColor(slot.status)}`}>
              <div className="font-semibold text-xs sm:text-sm">
                {new Date(slot.start_time).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })}
              </div>
              <div className="text-xs capitalize mt-1 opacity-80">
                {slot.status}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};


const SingleDayScheduleEditor = ({ date, scheduleForDay, onClose, refreshSchedules }) => {
  const [homeClinic, setHomeClinic] = React.useState(scheduleForDay?.clinicSchedule || { start_time: '18:00', end_time: '20:00', is_available: false });
  const [hospital, setHospital] = React.useState(scheduleForDay?.hospitalSchedule || { start_time: '11:00', end_time: '13:30', is_available: false });
  const [error, setError] = React.useState('');
  const [pickerOpen, setPickerOpen] = React.useState(null);

  const handleSave = async () => {
    setError('');
    const dayOfWeek = (date.getDay() + 6) % 7;

    const schedulesToUpdate = [
      { locationId: 1, data: homeClinic },
      { locationId: 2, data: hospital },
    ];

    try {
      const apiCalls = schedulesToUpdate.map(s => {
        const payload = {
          location_id: s.locationId,
          day_of_week: dayOfWeek,
          start_time: s.data.start_time,
          end_time: s.data.end_time,
          is_available: s.data.is_available,
        };
        return window.api(`/api/v1/schedules/${s.locationId}/${dayOfWeek}`, {
          method: 'PUT',
          body: JSON.stringify(payload)
        });
      });
      await Promise.all(apiCalls);
      refreshSchedules();
      onClose();
    } catch (err) {
      const errorData = await err.json?.();
      setError(errorData?.detail || 'An unexpected error occurred.');
      console.error('Day schedule save error:', err);
    }
  };

  return (
    <div className="space-y-6">
      {error && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg">{error}</div>}
      <div>
        <h4 className="font-semibold text-medical-dark mb-2">Home Clinic</h4>
        <div className="grid grid-cols-3 gap-4 items-center">
          <div>
            <label className="block text-xs font-medium text-medical-gray mb-1">Start Time</label>
            <div className="relative">
              <div className="absolute inset-y-0 end-0 top-0 flex items-center pe-3.5 pointer-events-none">
                <svg className="w-4 h-4 text-gray-500 dark:text-gray-400" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 24 24">
                  <path fillRule="evenodd" d="M2 12C2 6.477 6.477 2 12 2s10 4.477 10 10-4.477 10-10 10S2 17.523 2 12Zm11-4a1 1 0 1 0-2 0v4a1 1 0 0 0 .293.707l3 3a1 1 0 0 0 1.414-1.414L13 11.586V8Z" clipRule="evenodd"/>
                </svg>
              </div>
              <div onClick={() => !homeClinic.is_available ? null : setPickerOpen({ locId: 1 })} className={`form-input-themed custom-datetime ${!homeClinic.is_available ? 'bg-gray-100 cursor-not-allowed' : 'cursor-pointer'}`}>{homeClinic.start_time.substring(0, 5) || 'Start time'}</div>
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-medical-gray mb-1">End Time</label>
            <div className="relative">
              <div className="absolute inset-y-0 end-0 top-0 flex items-center pe-3.5 pointer-events-none">
                <svg className="w-4 h-4 text-gray-500 dark:text-gray-400" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 24 24">
                  <path fillRule="evenodd" d="M2 12C2 6.477 6.477 2 12 2s10 4.477 10 10-4.477 10-10 10S2 17.523 2 12Zm11-4a1 1 0 1 0-2 0v4a1 1 0 0 0 .293.707l3 3a1 1 0 0 0 1.414-1.414L13 11.586V8Z" clipRule="evenodd"/>
                </svg>
              </div>
              <div onClick={() => !homeClinic.is_available ? null : setPickerOpen({ locId: 1 })} className={`form-input-themed custom-datetime ${!homeClinic.is_available ? 'bg-gray-100 cursor-not-allowed' : 'cursor-pointer'}`}>{homeClinic.end_time.substring(0, 5) || 'End time'}</div>
            </div>
          </div>
          <label className="flex flex-wrap items-center gap-2 cursor-pointer mt-5">
            <input type="checkbox" checked={homeClinic.is_available} onChange={(e) => setHomeClinic(p => ({ ...p, is_available: e.target.checked }))} className="w-4 h-4 text-medical-accent rounded" />
            <span>Available</span>
          </label>
        </div>
      </div>
      <div>
        <h4 className="font-semibold text-medical-dark mb-2">Hospital</h4>
        <div className="grid grid-cols-3 gap-4 items-center">
          <div>
            <label className="block text-xs font-medium text-medical-gray mb-1">Start Time</label>
            <div className="relative">
              <div className="absolute inset-y-0 end-0 top-0 flex items-center pe-3.5 pointer-events-none">
                <svg className="w-4 h-4 text-gray-500 dark:text-gray-400" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 24 24">
                  <path fillRule="evenodd" d="M2 12C2 6.477 6.477 2 12 2s10 4.477 10 10-4.477 10-10 10S2 17.523 2 12Zm11-4a1 1 0 1 0-2 0v4a1 1 0 0 0 .293.707l3 3a1 1 0 0 0 1.414-1.414L13 11.586V8Z" clipRule="evenodd"/>
                </svg>
              </div>
              <div onClick={() => !hospital.is_available ? null : setPickerOpen({ locId: 2 })} className={`form-input-themed custom-datetime ${!hospital.is_available ? 'bg-gray-100 cursor-not-allowed' : 'cursor-pointer'}`}>{hospital.start_time.substring(0, 5) || 'Start time'}</div>
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-medical-gray mb-1">End Time</label>
            <div className="relative">
              <div className="absolute inset-y-0 end-0 top-0 flex items-center pe-3.5 pointer-events-none">
                <svg className="w-4 h-4 text-gray-500 dark:text-gray-400" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 24 24">
                  <path fillRule="evenodd" d="M2 12C2 6.477 6.477 2 12 2s10 4.477 10 10-4.477 10-10 10S2 17.523 2 12Zm11-4a1 1 0 1 0-2 0v4a1 1 0 0 0 .293.707l3 3a1 1 0 0 0 1.414-1.414L13 11.586V8Z" clipRule="evenodd"/>
                </svg>
              </div>
              <div onClick={() => !hospital.is_available ? null : setPickerOpen({ locId: 2 })} className={`form-input-themed custom-datetime ${!hospital.is_available ? 'bg-gray-100 cursor-not-allowed' : 'cursor-pointer'}`}>{hospital.end_time.substring(0, 5) || 'End time'}</div>
            </div>
          </div>
          <label className="flex flex-wrap items-center gap-2 cursor-pointer mt-5">
            <input type="checkbox" checked={hospital.is_available} onChange={(e) => setHospital(p => ({ ...p, is_available: e.target.checked }))} className="w-4 h-4 text-medical-accent rounded" />
            <span>Available</span>
          </label>
        </div>
      </div>
      <div className="flex justify-end space-x-3 pt-4 border-t">
        <button onClick={onClose} className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">Cancel</button>
        <button onClick={handleSave} className="medical-button px-4 py-2 text-white rounded-lg relative z-10">Save Changes</button>
      </div>

      {pickerOpen && (
        <TimeRangePicker
          isOpen={true}
          onClose={() => setPickerOpen(null)}
          onConfirm={({ startTime, endTime }) => {
            if(pickerOpen.locId === 1) {
              setHomeClinic(p => ({ ...p, start_time: startTime, end_time: endTime }));
            } else {
              setHospital(p => ({ ...p, start_time: startTime, end_time: endTime }));
            }
            setPickerOpen(null);
          }}
          initialStartTime={pickerOpen.locId === 1 ? homeClinic.start_time : hospital.start_time}
          initialEndTime={pickerOpen.locId === 1 ? homeClinic.end_time : hospital.end_time}
        />
      )}
    </div>
  );
};


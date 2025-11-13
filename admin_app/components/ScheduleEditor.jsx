const ScheduleEditor = ({ schedules, locations, onSaveSuccess, onClose }) => {
  const [localSchedules, setLocalSchedules] = React.useState({});
  const [saveError, setSaveError] = React.useState('');
  const [isSaving, setIsSaving] = React.useState(false);
  const [pickerOpen, setPickerOpen] = React.useState(null);
  const [activeLocationId, setActiveLocationId] = React.useState(locations[0]?.id || 1);

  React.useEffect(() => {
    if (schedules && Object.keys(schedules).length > 0) {
      const newLocalSchedules = JSON.parse(JSON.stringify(schedules));
      if (!newLocalSchedules[1]) newLocalSchedules[1] = {};
      if (!newLocalSchedules[2]) newLocalSchedules[2] = {};
      setLocalSchedules(newLocalSchedules);
    } else {
      setLocalSchedules({ 1: {}, 2: {} });
    }
  }, [schedules]);

  const handleTimeChange = (locationId, dayIndex, field, value) => {
    setSaveError('');
    setLocalSchedules(prev => {
      const newState = JSON.parse(JSON.stringify(prev));
      if (!newState[locationId]) {
        newState[locationId] = {};
      }
      const currentDayData = newState[locationId][dayIndex] || {
        day_of_week: dayIndex,
        start_time: '09:00:00',
        end_time: '17:00:00',
        is_available: false,
        appointment_duration: 30,
        max_appointments: null
      };
      currentDayData[field] = value;
      newState[locationId][dayIndex] = currentDayData;
      return newState;
    });
  };

  const handleNumericChange = (locationId, dayIndex, field, value) => {
    setSaveError('');
    const numValue = value === '' ? null : parseInt(value, 10);
    const finalValue = (numValue !== null && !isNaN(numValue) && numValue >= 0) ? numValue : null;
    setLocalSchedules(prev => {
      const newState = JSON.parse(JSON.stringify(prev));
      if (!newState[locationId]) newState[locationId] = {};
      const currentDayData = newState[locationId][dayIndex] || {
        day_of_week: dayIndex,
        start_time: '09:00:00',
        end_time: '17:00:00',
        is_available: false,
        appointment_duration: 30,
        max_appointments: null
      };
      currentDayData[field] = finalValue;
      newState[locationId][dayIndex] = currentDayData;
      return newState;
    });
  };

  const handleAvailabilityChange = (locationId, dayIndex, isAvailable) => {
    setSaveError('');
    setLocalSchedules(prev => {
      let defaults = {
        start_time: '09:00:00',
        end_time: '17:00:00',
        appointment_duration: 30,
        max_appointments: null
      };

      if (prev[locationId]) {
        const otherAvailableDays = Object.values(prev[locationId]).filter(day => day.is_available && day.day_of_week !== dayIndex);
        if (otherAvailableDays.length > 0) {
          defaults.start_time = otherAvailableDays[0].start_time;
          defaults.end_time = otherAvailableDays[0].end_time;
          defaults.appointment_duration = otherAvailableDays[0].appointment_duration;
          defaults.max_appointments = otherAvailableDays[0].max_appointments;
        }
      }

      const newSchedules = JSON.parse(JSON.stringify(prev));
      const currentLocationSchedule = newSchedules[locationId];

      if (!currentLocationSchedule[dayIndex]) {
        currentLocationSchedule[dayIndex] = {
          day_of_week: dayIndex,
          ...defaults,
          is_available: isAvailable
        };
      } else {
        currentLocationSchedule[dayIndex].is_available = isAvailable;
      }

      if (isAvailable) {
        currentLocationSchedule[dayIndex].start_time = defaults.start_time;
        currentLocationSchedule[dayIndex].end_time = defaults.end_time;
        currentLocationSchedule[dayIndex].appointment_duration = defaults.appointment_duration;
        currentLocationSchedule[dayIndex].max_appointments = defaults.max_appointments;
      }

      return newSchedules;
    });
  };

  const activeSchedule = localSchedules[activeLocationId] || {};

  const handleSaveClick = async () => {
    setIsSaving(true);
    setSaveError('');
    try {
      const locationIdToSave = activeLocationId;
      const schedulePayload = Object.values(localSchedules[locationIdToSave] || {}).map(daySchedule => ({
        ...daySchedule,
        location_id: parseInt(locationIdToSave),
        start_time: typeof daySchedule.start_time === 'string' && daySchedule.start_time.length === 5 ? `${daySchedule.start_time}:00` : daySchedule.start_time,
        end_time: typeof daySchedule.end_time === 'string' && daySchedule.end_time.length === 5 ? `${daySchedule.end_time}:00` : daySchedule.end_time
      }));
      await window.api(`/api/v1/schedules/by-location/${locationIdToSave}`, {
        method: 'POST',
        body: JSON.stringify(schedulePayload)
      });

      setIsSaving(false);
      if (onSaveSuccess) onSaveSuccess();
      onClose();
    } catch (error) {
      console.error("Error saving schedules:", error);
      let errorMessage = 'An unexpected error occurred while saving.';
      try {
        if (error instanceof Error && error.message.includes('HTTP status code')) {
          errorMessage = error.message;
        } else if (typeof error.json === 'function') {
          const errorData = await error.json();
          if (errorData && errorData.detail) {
            errorMessage = errorData.detail;
          }
        } else if (error.message) {
          errorMessage = error.message;
        }
      } catch (parseError) {
        console.error("Could not parse error details:", parseError);
      }
      setSaveError(errorMessage);
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      {saveError && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-4">
          <p className="font-bold">Save Failed:</p>
          <p className="text-sm">{saveError}</p>
        </div>
      )}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-xl">
        {locations.map(loc => (
          <button
            key={loc.id}
            onClick={() => setActiveLocationId(loc.id)}
            className={`flex-1 py-2 px-4 rounded-lg font-medium transition-all ${activeLocationId === loc.id ? 'bg-white text-medical-accent shadow-sm' : 'text-medical-gray hover:text-medical-dark'}`}
          >
            {loc.name}
          </button>
        ))}
      </div>

      {[...Array(7).keys()].map(dayIndex => {
        const dayName = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][dayIndex];
        const dayData = activeSchedule[dayIndex] || {};

        return (
          <div key={dayIndex} className="grid grid-cols-6 gap-4 items-center p-3 border-b">
            <h4 className="font-semibold text-medical-dark">{dayName}</h4>
            <div>
              <label className="block text-xs font-medium text-medical-gray mb-1">Start Time</label>
              <div className="relative">
                <div className="absolute inset-y-0 end-0 top-0 flex items-center pe-3.5 pointer-events-none">
                  <svg className="w-4 h-4 text-gray-500 dark:text-gray-400" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 24 24">
                    <path fillRule="evenodd" d="M2 12C2 6.477 6.477 2 12 2s10 4.477 10 10-4.477 10-10 10S2 17.523 2 12Zm11-4a1 1 0 1 0-2 0v4a1 1 0 0 0 .293.707l3 3a1 1 0 0 0 1.414-1.414L13 11.586V8Z" clipRule="evenodd"/>
                  </svg>
                </div>
                <div
                  onClick={() => !dayData?.is_available ? null : setPickerOpen({ dayIndex, locId: activeLocationId })}
                  className={`form-input-themed custom-datetime ${!dayData?.is_available ? 'bg-gray-100 cursor-not-allowed' : 'cursor-pointer'}`}
                >
                  {dayData?.start_time?.substring(0, 5) || 'Start time'}
                </div>
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
                <div
                  onClick={() => !dayData?.is_available ? null : setPickerOpen({ dayIndex, locId: activeLocationId })}
                  className={`form-input-themed custom-datetime ${!dayData?.is_available ? 'bg-gray-100 cursor-not-allowed' : 'cursor-pointer'}`}
                >
                  {dayData?.end_time?.substring(0, 5) || 'End time'}
                </div>
              </div>
            </div>
            <div className="flex items-center justify-center">
              <label className="flex flex-wrap items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={!!dayData?.is_available}
                  onChange={(e) => handleAvailabilityChange(activeLocationId, dayIndex, e.target.checked)}
                  className="w-4 h-4 text-medical-accent rounded"
                />
                <span>Available</span>
              </label>
            </div>
            <div>
              <label className="block text-xs font-medium text-medical-gray mb-1">Duration (min)</label>
              <input
                type="number"
                value={dayData?.appointment_duration ?? ''}
                onChange={(e) => handleNumericChange(activeLocationId, dayIndex, 'appointment_duration', e.target.value)}
                className="form-input-themed w-20"
                min="5"
                max="60"
                step="5"
                placeholder="e.g., 30"
                disabled={!dayData?.is_available}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-medical-gray mb-1">Max Appts</label>
              <input
                type="number"
                value={dayData?.max_appointments ?? ''}
                onChange={(e) => handleNumericChange(activeLocationId, dayIndex, 'max_appointments', e.target.value)}
                className="form-input-themed w-20"
                min="0"
                placeholder="None"
                disabled={!dayData?.is_available}
              />
            </div>
          </div>
        )
      })}

      <div className="flex justify-end space-x-3">
        <button onClick={onClose} className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300" disabled={isSaving}>
          Cancel
        </button>
        <button onClick={handleSaveClick} className="medical-button px-4 py-2 text-white rounded-lg relative z-10" disabled={isSaving}>
          {isSaving ? 'Saving...' : 'Save Schedule'}
        </button>
      </div>

      {pickerOpen && pickerOpen.locId === activeLocationId && (
        <TimeRangePicker
          isOpen={true}
          onClose={() => setPickerOpen(null)}
          onConfirm={({ startTime, endTime }) => {
            handleTimeChange(activeLocationId, pickerOpen.dayIndex, 'start_time', startTime);
            handleTimeChange(activeLocationId, pickerOpen.dayIndex, 'end_time', endTime);
            setPickerOpen(null);
          }}
          initialStartTime={activeSchedule[pickerOpen.dayIndex]?.start_time}
          initialEndTime={activeSchedule[pickerOpen.dayIndex]?.end_time}
        />
      )}
    </div>
  );
};

export default ScheduleEditor;
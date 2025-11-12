const DayEditorModal = ({ date, scheduleForDay, onClose, refreshSchedules, existingClinicBlock, existingHospitalBlock }) => {
  const [activeTab, setActiveTab] = React.useState('block');

  return (
    <div className="space-y-4">
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-xl">
        <button
          onClick={() => setActiveTab('block')}
          className={`flex-1 py-2 px-4 rounded-lg font-medium transition-all ${activeTab === 'block' ? 'bg-white text-red-600 shadow-sm' : 'text-medical-gray hover:text-medical-dark'}`}
        >
          <i className="fas fa-ban mr-2"></i>Block Day
        </button>
        <button
          onClick={() => setActiveTab('edit')}
          className={`flex-1 py-2 px-4 rounded-lg font-medium transition-all ${activeTab === 'edit' ? 'bg-white text-medical-accent shadow-sm' : 'text-medical-gray hover:text-medical-dark'}`}
        >
          <i className="fas fa-clock mr-2"></i>Edit Schedule
        </button>
      </div>
      <div>
        {activeTab === 'block' && (
          <DailyUnavailabilityEditor
            date={date}
            onClose={onClose}
            existingClinicBlock={existingClinicBlock}
            existingHospitalBlock={existingHospitalBlock}
          />
        )}
        {activeTab === 'edit' && (
          <SingleDayScheduleEditor
            date={date}
            scheduleForDay={scheduleForDay}
            onClose={onClose}
            refreshSchedules={refreshSchedules}
          />
        )}
      </div>
    </div>
  );
};


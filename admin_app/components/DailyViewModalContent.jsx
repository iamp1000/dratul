import React from 'react';
import DateAppointments from './DateAppointments.jsx';
import DaySlotsViewer from './DaySlotsViewer.jsx';

const DailyViewModalContent = ({ date, appointmentsForDate }) => {
  const [activeTab, setActiveTab] = React.useState('appointments');

  return (
    <div className="space-y-4">
      <h4 className="font-semibold text-medical-dark mb-0">
        {date.toLocaleDateString('en-US', {
          weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
        })}
      </h4>
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-xl">
        <button
          onClick={() => setActiveTab('appointments')}
          className={`flex-1 py-2 px-4 rounded-lg font-medium transition-all text-sm ${activeTab === 'appointments' ? 'bg-white text-medical-accent shadow-sm' : 'text-medical-gray hover:text-medical-dark'}`}
        >
          <i className="fas fa-calendar-check mr-1"></i> Appointments ({appointmentsForDate.length})
        </button>
        <button
          onClick={() => setActiveTab('slots')}
          className={`flex-1 py-2 px-4 rounded-lg font-medium transition-all text-sm ${activeTab === 'slots' ? 'bg-white text-medical-accent shadow-sm' : 'text-medical-gray hover:text-medical-dark'}`}
        >
          <i className="fas fa-clock mr-1"></i> All Slots
        </button>
      </div>

      <div className="mt-4">
        {activeTab === 'appointments' && (
          <DateAppointments date={date} appointments={appointmentsForDate} />
        )}
        {activeTab === 'slots' && (
          <DaySlotsViewer date={date} />
        )}
      </div>
    </div>
  );
};

export default DailyViewModalContent;

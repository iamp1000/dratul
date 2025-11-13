import React from 'react';

const AppointmentDetails = ({ appointment }) => (
  <div className="space-y-6">
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div>
        <h4 className="font-semibold text-medical-dark mb-3">Appointment Information</h4>
        <div className="space-y-2 text-sm">
          <div><span className="font-medium">Date:</span> {new Date(appointment.start_time).toLocaleDateString()}</div>
          <div><span className="font-medium">Time:</span> {new Date(appointment.start_time).toLocaleTimeString()}</div>
          <div><span className="font-medium">Status:</span>
            <span className="ml-2 px-2 py-1 bg-medical-accent/10 text-medical-accent rounded-full text-xs">
              {appointment.status}
            </span>
          </div>
          <div><span className="font-medium">Type:</span> {appointment.appointment_type}</div>
        </div>
      </div>
      <div>
        <h4 className="font-semibold text-medical-dark mb-3">Patient Information</h4>
        <div className="space-y-2 text-sm">
          <div><span className="font-medium">Name:</span> {`${appointment.patient?.first_name || ''} ${appointment.patient?.last_name || ''}`.trim() || 'N/A'}</div>
          <div><span className="font-medium">Phone:</span> {appointment.patient?.phone_number || 'N/A'}</div>
          <div><span className="font-medium">Email:</span> {appointment.patient?.email || 'N/A'}</div>
        </div>
      </div>
    </div>

    <div>
      <h4 className="font-semibold text-medical-dark mb-3">Notes</h4>
      <div className="bg-gray-50 p-3 rounded-lg text-sm">
        {appointment.notes || appointment.reason || 'No notes available'}
      </div>
    </div>

    <div className="flex space-x-3">
      <button className="medical-button px-4 py-2 text-white rounded-lg text-sm relative z-10">
        <i className="fas fa-edit mr-2"></i>Edit
      </button>
      <button className="px-4 py-2 bg-medical-error text-white rounded-lg text-sm hover:bg-medical-error/90">
        <i className="fas fa-times mr-2"></i>Cancel
      </button>
      <button className="px-4 py-2 bg-medical-success text-white rounded-lg text-sm hover:bg-medical-success/90">
        <i className="fas fa-check mr-2"></i>Complete
      </button>
    </div>
  </div>
);

export default AppointmentDetails;
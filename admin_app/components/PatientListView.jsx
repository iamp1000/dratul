import React from 'react';

const PatientListView = ({
  patients,
  allPatients,
  searchQuery,
  setSearchQuery,
  filterDate,
  setFilterDate,
  onOpenVisitPad,
  onOpenTemplateView,
  isLoading
}) => {
  const stats = React.useMemo(() => ({
    pending: allPatients.filter(p => p.status === 'BOOKED').length,
    ongoing: allPatients.filter(p => p.status === 'ON-GOING').length,
    completed: allPatients.filter(p => p.status === 'REVIEWED').length
  }), [allPatients]);

  return (
    <div className="h-full flex flex-col bg-white rounded-xl shadow-lg overflow-hidden animate-fade-in">
      <div className="bg-gradient-to-r from-medical-blue via-[#1565C0] to-medical-accent p-6 text-white">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div className="flex-1">
            <h2 className="text-2xl font-bold font-primary flex items-center gap-3">
              <i className="fas fa-calendar-day"></i>
              Today's Consultations
            </h2>
            <p className="text-blue-100 text-sm mt-1">
              {new Date(filterDate).toLocaleDateString('en-IN', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
              })}
            </p>
          </div>

          <div className="flex items-center gap-3 flex-wrap">
            <div className="bg-white/20 backdrop-blur-md px-4 py-3 rounded-xl border border-white/30 hover:bg-white/30 transition-all">
              <div className="text-xs text-blue-100 font-medium">Pending</div>
              <div className="text-2xl font-bold">{stats.pending}</div>
            </div>
            <div className="bg-white/20 backdrop-blur-md px-4 py-3 rounded-xl border border-white/30 hover:bg-white/30 transition-all">
              <div className="text-xs text-blue-100 font-medium">On-Going</div>
              <div className="text-2xl font-bold">{stats.ongoing}</div>
            </div>
            <div className="bg-white/20 backdrop-blur-md px-4 py-3 rounded-xl border border-white/30 hover:bg-white/30 transition-all">
              <div className="text-xs text-blue-100 font-medium">Completed</div>
              <div className="text-2xl font-bold">{stats.completed}</div>
            </div>
          </div>
        </div>

        <div className="mt-4 flex flex-col md:flex-row gap-3">
          <div className="flex-1 relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search by patient name, ID, or phone number..."
              className="w-full px-4 py-3 pl-12 rounded-lg bg-white/20 backdrop-blur-sm text-white placeholder-blue-200 border border-white/30 focus:outline-none focus:ring-2 focus:ring-white/50 focus:bg-white/30 transition-all"
            />
            <i className="fas fa-search absolute left-4 top-1/2 transform -translate-y-1/2 text-blue-200"></i>
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-4 top-1/2 transform -translate-y-1/2 text-blue-200 hover:text-white"
              >
                <i className="fas fa-times"></i>
              </button>
            )}
          </div>
          <div className="relative">
            <div className="absolute inset-y-0 end-0 top-0 flex items-center pe-3.5 pointer-events-none">
              <svg className="w-4 h-4 text-blue-200" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 20 20">
                <path d="M20 4a2 2 0 0 0-2-2h-2V1a1 1 0 0 0-2 0v1h-3V1a1 1 0 0 0-2 0v1H6V1a1 1 0 0 0-2 0v1H2a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V4Zm-2 13H4V8h14v9Z"/>
              </svg>
            </div>
            <input
              type="date"
              value={filterDate}
              onChange={(e) => setFilterDate(e.target.value)}
              className="px-4 py-3 pe-10 rounded-lg bg-white/20 backdrop-blur-sm text-white border border-white/30 focus:outline-none focus:ring-2 focus:ring-white/50"
            />
          </div>
          <button className="px-6 py-3 bg-white text-medical-blue rounded-lg font-semibold hover:bg-blue-50 hover:shadow-lg transition-all flex items-center gap-2">
            <i className="fas fa-plus"></i>
            New Patient
          </button>
          <button 
            id="consultation-template-btn" 
            onClick={onOpenTemplateView}
            className="px-6 py-3 bg-white text-medical-blue rounded-lg font-semibold hover:bg-blue-50 hover:shadow-lg transition-all flex items-center gap-2">
            <i className="fas fa-file-medical-alt"></i>
            Templates
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <i className="fas fa-spinner fa-spin text-4xl text-medical-accent mb-4"></i>
              <p className="text-gray-600">Loading patients...</p>
            </div>
          </div>
        ) : patients.length === 0 ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <i className="fas fa-users text-6xl text-gray-300 mb-4"></i>
              <h3 className="text-xl font-semibold text-gray-700 mb-2">No Patients Found</h3>
              <p className="text-gray-500">
                {searchQuery ? 'Try adjusting your search criteria' : 'No appointments for this date'}
              </p>
            </div>
          </div>
        ) : (
          <table className="w-full">
            <thead className="sticky top-0 bg-gradient-to-r from-gray-50 to-blue-50 z-10 border-b-2 border-medical-accent/20">
              <tr className="text-left text-sm text-gray-700">
                <th className="px-6 py-4 font-semibold">ID</th>
                <th className="px-6 py-4 font-semibold">Patient Name</th>
                <th className="px-6 py-4 font-semibold">Phone</th>
                <th className="px-6 py-4 font-semibold">Recent Visit</th>
                <th className="px-6 py-4 font-semibold">#Visits</th>
                <th className="px-6 py-4 font-semibold">Time</th>
                <th className="px-6 py-4 font-semibold">Wait</th>
                <th className="px-6 py-4 font-semibold">Status</th>
                <th className="px-6 py-4 font-semibold">Purpose</th>
                <th className="px-6 py-4 font-semibold">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {patients.map((patient, index) => (
                <tr
                  key={patient.id}
                  className="hover:bg-gradient-to-r hover:from-blue-50/50 hover:to-transparent transition-all duration-200 animate-fade-in"
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{patient.id}</td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gradient-to-br from-medical-blue to-medical-accent rounded-full flex items-center justify-center text-white font-semibold text-sm shadow-md">
                        {patient.name.charAt(0)}
                      </div>
                      <div>
                        <div className="font-semibold text-gray-900">{patient.name}</div>
                        <div className="text-xs text-gray-500 flex items-center gap-2">
                          <span>{patient.age}Y, {patient.gender}</span>
                          {patient.medicalHistory?.allergies?.length > 0 && (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                              <i className="fas fa-exclamation-triangle mr-1"></i>
                              Allergies
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    <div className="flex items-center gap-2">
                      <i className="fas fa-phone-alt text-gray-400 text-xs"></i>
                      {patient.phone}
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">{patient.recentVisit}</td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-medical-accent/10 text-medical-accent font-semibold text-sm">
                      {patient.totalVisits}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600 font-medium">{patient.time}</td>
                  <td className="px-6 py-4">
                    <span className="text-sm font-semibold text-orange-600 flex items-center gap-1">
                      <i className="far fa-clock text-xs"></i>
                      {patient.wait}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold inline-flex items-center gap-1 ${patient.status === 'ON-GOING'
                      ? 'bg-green-100 text-green-700 border border-green-200' :
                      patient.status === 'BOOKED'
                        ? 'bg-blue-100 text-blue-700 border border-blue-200' :
                        'bg-gray-100 text-gray-700 border border-gray-200'
                      }`}>
                      <span className={`w-2 h-2 rounded-full ${patient.status === 'ON-GOING' ? 'bg-green-500 animate-pulse' :
                        patient.status === 'BOOKED' ? 'bg-blue-500' :
                          'bg-gray-500'
                        }`}></span>
                      {patient.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">{patient.purpose}</td>
                  <td className="px-6 py-4">
                    <button
                      onClick={() => onOpenVisitPad(patient)}
                      className="px-4 py-2 bg-gradient-to-r from-medical-blue to-medical-accent text-white rounded-lg font-medium hover:shadow-lg hover:scale-105 transition-all duration-200 text-sm flex items-center gap-2"
                    >
                      <i className="fas fa-notes-medical"></i>
                      Visit Pad
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      <div className="px-6 py-3 bg-gray-50 border-t border-gray-200">
        <p className="text-sm text-gray-600">
          Showing <span className="font-semibold">{patients.length}</span> of <span className="font-semibold">{allPatients.length}</span> patients
        </p>
      </div>
    </div>
  );
};

export default PatientListView;
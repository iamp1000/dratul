import React from 'react';

const Sidebar = ({ currentView, setCurrentView, user, isMobileMenuOpen, setIsMobileMenuOpen }) => {
  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: 'fas fa-home' },
    { id: 'appointments', label: 'Appointments', icon: 'fas fa-calendar-alt' },
    { id: 'schedule', label: 'Doctor Schedule', icon: 'fas fa-clock' },
    { id: 'patients', label: 'Patients', icon: 'fas fa-users' },
    { id: 'consultation', label: 'Consultation', icon: 'fas fa-notes-medical', permission: 'can_edit_patient_info' },
    { id: 'templates', label: 'Templates', icon: 'fas fa-file-medical-alt', permission: 'can_edit_patient_info' },
    { id: 'users', label: 'Users', icon: 'fas fa-user-cog', permission: 'can_manage_users' },
    { id: 'logs', label: 'Audit Logs', icon: 'fas fa-clipboard-list', permission: 'can_access_logs' }
  ];

  const checkPermission = (item) => {
    if (!item.permission) return true;
    return Boolean(user?.permissions && user.permissions[item.permission]);
  };



  const handleLogout = () => {
    sessionStorage.clear();
    window.location.href = '/admin_login.html';
  };

  return (
    <>
      {isMobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-40 md:hidden"
          onClick={() => setIsMobileMenuOpen(false)}
        />
      )}
      <aside
        className={`w-64 sidebar-nowrap sidebar-gradient text-white flex flex-col h-full overflow-y-auto fixed md:relative z-40 transform transition-transform duration-300 ${
          isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        <div className="p-6 border-b border-white/20">
          <div className="flex items-center mb-4">
            <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center mr-3">
              <i className="fas fa-stethoscope text-white text-xl"></i>
            </div>
            <div>
              <div className="text-xl font-bold">Medical Portal</div>
              <div className="text-blue-200 text-sm">Dr. Dhingra's Clinic</div>
            </div>
          </div>
          <div className="bg-white/10 p-3 rounded-xl">
            <div className="flex items-center">
              <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center mr-2">
                <i className="fas fa-user text-white text-sm"></i>
              </div>
              <div>
                <div className="font-semibold text-sm">{user?.username || 'User'}</div>
                <div className="text-blue-200 text-xs capitalize">{user?.role}</div>
              </div>
            </div>
          </div>
        </div>
        <nav className="flex-1 p-4 space-y-2">
          {menuItems.filter(checkPermission).map((item) => (
            <button
              key={item.id}
              onClick={() => {
                setCurrentView(item.id);
                setIsMobileMenuOpen(false);
              }}
              className={`nav-item w-full text-left px-3 py-3 rounded-xl flex items-center space-x-3 ${
                currentView === item.id ? 'active' : ''
              }`}
            >
              <i className={item.icon}></i>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
        <div className="p-4 border-t border-white/20 mt-auto">
          <button
            onClick={handleLogout}
            className="w-full text-left px-3 py-3 rounded-xl flex items-center space-x-3 text-red-200 hover:bg-red-500/10"
          >
            <i className="fas fa-sign-out-alt"></i>
            <span>Logout</span>
          </button>
        </div>
      </aside>
    </>
  );
};


export default Sidebar;
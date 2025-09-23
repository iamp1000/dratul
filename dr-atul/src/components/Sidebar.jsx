// src/layouts/Sidebar/Sidebar.jsx
import React from 'react';
import NavLink from './NavLink';

function Sidebar({ activeTab, setActiveTab }) {
    const menuItems = [
        { id: 'dashboard', label: 'Dashboard', icon: '📊' },
        { id: 'users', label: 'User Management', icon: '👥' },
        { id: 'patients', label: 'Patient Management', icon: '🏥' },
        { id: 'schedule', label: 'Schedule Manager', icon: '📅' },
        { id: 'logs', label: 'Activity Logs', icon: '📋' }
    ];

    return (
        <div className="bg-primary w-64 shadow-lg">
            <div className="p-6">
                <div className="flex items-center space-x-3 mb-8">
                    <div className="w-10 h-10 bg-accent rounded-lg flex items-center justify-center">
                        <span className="text-2xl">🏥</span>
                    </div>
                    <div>
                        <h1 className="text-xl font-bold text-white">Clinic OS</h1>
                        <p className="text-sm text-gray-300">Admin Panel</p>
                    </div>
                </div>
                
                <nav className="space-y-2">
                    {menuItems.map((item) => (
                        <NavLink
                            key={item.id}
                            id={item.id}
                            label={item.label}
                            icon={item.icon}
                            isActive={activeTab === item.id}
                            onClick={() => setActiveTab(item.id)}
                        />
                    ))}
                </nav>
            </div>
            
            <div className="absolute bottom-0 left-0 right-0 p-6 bg-primary-dark">
                <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-accent rounded-full flex items-center justify-center">
                        <span className="text-sm font-semibold text-primary">A</span>
                    </div>
                    <div className="flex-1">
                        <p className="text-white text-sm font-medium">Admin User</p>
                        <p className="text-gray-300 text-xs">admin@clinic.com</p>
                    </div>
                    <button className="text-gray-300 hover:text-white transition-colors">
                        <span className="text-lg">⚙️</span>
                    </button>
                </div>
            </div>
        </div>
    );
}

export default Sidebar;
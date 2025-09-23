// src/layouts/AdminLayout/AdminLayout.jsx
import React, { useState, useEffect } from 'react';
import Sidebar from '../Sidebar/Sidebar';
import Dashboard from '../../features/dashboard/components/Dashboard';
import UserManagement from '../../features/users/components/UserManagement';
import PatientManagement from '../../features/patients/components/PatientManagement';
import AdvancedScheduleManager from '../../features/schedule/components/AdvancedScheduleManager';
import ActivityLogView from '../../features/activity/components/ActivityLogView';

function AdminLayout() {
    const [activeTab, setActiveTab] = useState('dashboard');
    const [users, setUsers] = useState([]);
    const [patients, setPatients] = useState([]);
    const [appointments, setAppointments] = useState([]);
    const [locations, setLocations] = useState([]);
    const [logs, setLogs] = useState([]);
    const [isLoading, setIsLoading] = useState(false);

    // Fetch initial data
    useEffect(() => {
        fetchUsers();
        fetchPatients();
        fetchAppointments();
        fetchLocations();
        fetchLogs();
    }, []);

    const fetchUsers = async () => {
        setIsLoading(true);
        try {
            const response = await fetch('/api/users');
            const data = await response.json();
            setUsers(data);
        } catch (error) {
            console.error('Error fetching users:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const fetchPatients = async () => {
        try {
            const response = await fetch('/api/patients');
            const data = await response.json();
            setPatients(data);
        } catch (error) {
            console.error('Error fetching patients:', error);
        }
    };

    const fetchAppointments = async () => {
        try {
            const response = await fetch('/api/appointments');
            const data = await response.json();
            setAppointments(data);
        } catch (error) {
            console.error('Error fetching appointments:', error);
        }
    };

    const fetchLocations = async () => {
        try {
            const response = await fetch('/api/locations');
            const data = await response.json();
            setLocations(data);
        } catch (error) {
            console.error('Error fetching locations:', error);
        }
    };

    const fetchLogs = async () => {
        try {
            const response = await fetch('/api/logs');
            const data = await response.json();
            setLogs(data);
        } catch (error) {
            console.error('Error fetching logs:', error);
        }
    };

    const renderActiveComponent = () => {
        const commonProps = {
            users,
            setUsers,
            patients,
            setPatients,
            appointments,
            setAppointments,
            locations,
            logs,
            setLogs,
            isLoading,
            fetchUsers,
            fetchPatients,
            fetchAppointments,
            fetchLogs
        };

        switch (activeTab) {
            case 'dashboard':
                return <Dashboard {...commonProps} />;
            case 'users':
                return <UserManagement {...commonProps} />;
            case 'patients':
                return <PatientManagement {...commonProps} />;
            case 'schedule':
                return <AdvancedScheduleManager {...commonProps} />;
            case 'logs':
                return <ActivityLogView {...commonProps} />;
            default:
                return <Dashboard {...commonProps} />;
        }
    };

    return (
        <div className="flex h-screen bg-secondary">
            <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
            <div className="flex-1 flex flex-col overflow-hidden">
                <main className="flex-1 overflow-x-hidden overflow-y-auto bg-light p-6">
                    {renderActiveComponent()}
                </main>
            </div>
        </div>
    );
}

export default AdminLayout;
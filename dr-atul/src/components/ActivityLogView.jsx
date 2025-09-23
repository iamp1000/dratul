// src/features/activity/components/ActivityLogView.jsx
import React, { useState, useEffect } from 'react';

function ActivityLogView({ logs, fetchLogs }) {
    const [filteredLogs, setFilteredLogs] = useState([]);
    const [filters, setFilters] = useState({
        action: '',
        username: '',
        dateFrom: '',
        dateTo: ''
    });

    const actionTypes = [
        'CREATE', 'UPDATE', 'DELETE', 'LOGIN', 'LOGOUT', 'VIEW'
    ];

    useEffect(() => {
        applyFilters();
    }, [logs, filters]);

    const applyFilters = () => {
        let filtered = [...logs];

        if (filters.action) {
            filtered = filtered.filter(log => log.action === filters.action);
        }

        if (filters.username) {
            filtered = filtered.filter(log => 
                log.username.toLowerCase().includes(filters.username.toLowerCase())
            );
        }

        if (filters.dateFrom) {
            const fromDate = new Date(filters.dateFrom);
            filtered = filtered.filter(log => new Date(log.timestamp) >= fromDate);
        }

        if (filters.dateTo) {
            const toDate = new Date(filters.dateTo);
            toDate.setHours(23, 59, 59, 999); // End of day
            filtered = filtered.filter(log => new Date(log.timestamp) <= toDate);
        }

        // Sort by timestamp (newest first)
        filtered.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

        setFilteredLogs(filtered);
    };

    const handleFilterChange = (field, value) => {
        setFilters(prev => ({
            ...prev,
            [field]: value
        }));
    };

    const clearFilters = () => {
        setFilters({
            action: '',
            username: '',
            dateFrom: '',
            dateTo: ''
        });
    };

    const formatTimestamp = (timestamp) => {
        return new Date(timestamp).toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    };

    const getActionColor = (action) => {
        switch (action) {
            case 'CREATE':
                return 'bg-green-100 text-green-800';
            case 'UPDATE':
                return 'bg-blue-100 text-blue-800';
            case 'DELETE':
                return 'bg-red-100 text-red-800';
            case 'LOGIN':
                return 'bg-purple-100 text-purple-800';
            case 'LOGOUT':
                return 'bg-gray-100 text-gray-800';
            case 'VIEW':
                return 'bg-yellow-100 text-yellow-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    };

    const getActionIcon = (action) => {
        switch (action) {
            case 'CREATE':
                return '➕';
            case 'UPDATE':
                return '✏️';
            case 'DELETE':
                return '🗑️';
            case 'LOGIN':
                return '🔐';
            case 'LOGOUT':
                return '🚪';
            case 'VIEW':
                return '👁️';
            default:
                return '📝';
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-3xl font-bold text-text-dark">Activity Logs</h2>
                <div className="text-sm text-text-light">
                    {filteredLogs.length} of {logs.length} logs shown
                </div>
            </div>

            {/* Filters */}
            <div className="bg-white rounded-xl shadow-sm p-6">
                <h3 className="text-lg font-semibold text-text-dark mb-4">Filters</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div>
                        <label className="block text-sm font-medium text-text-dark mb-1">
                            Action Type
                        </label>
                        <select
                            value={filters.action}
                            onChange={(e) => handleFilterChange('action', e.target.value)}
                            className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                        >
                            <option value="">All Actions</option>
                            {actionTypes.map(action => (
                                <option key={action} value={action}>{action}</option>
                            ))}
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-text-dark mb-1">
                            Username
                        </label>
                        <input
                            type="text"
                            value={filters.username}
                            onChange={(e) => handleFilterChange('username', e.target.value)}
                            placeholder="Search username..."
                            className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-text-dark mb-1">
                            Date From
                        </label>
                        <input
                            type="date"
                            value={filters.dateFrom}
                            onChange={(e) => handleFilterChange('dateFrom', e.target.value)}
                            className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-text-dark mb-1">
                            Date To
                        </label>
                        <input
                            type="date"
                            value={filters.dateTo}
                            onChange={(e) => handleFilterChange('dateTo', e.target.value)}
                            className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                        />
                    </div>
                </div>

                <div className="flex justify-between items-center mt-4">
                    <button
                        onClick={clearFilters}
                        className="text-primary hover:text-primary-dark transition-colors text-sm"
                    >
                        Clear All Filters
                    </button>
                    <button
                        onClick={fetchLogs}
                        className="bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg text-sm transition-colors"
                    >
                        Refresh Logs
                    </button>
                </div>
            </div>

            {/* Logs Table */}
            <div className="bg-white rounded-xl shadow-sm p-6">
                <div className="overflow-x-auto">
                    {filteredLogs.length === 0 ? (
                        <div className="text-center py-8">
                            <div className="text-gray-400 text-6xl mb-4">📋</div>
                            <p className="text-text-light">No activity logs found with current filters</p>
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {filteredLogs.map((log) => (
                                <div key={log.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                                    <div className="flex items-start justify-between">
                                        <div className="flex items-start space-x-3 flex-1">
                                            <div className="text-2xl">{getActionIcon(log.action)}</div>
                                            <div className="flex-1">
                                                <div className="flex items-center space-x-3 mb-1">
                                                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getActionColor(log.action)}`}>
                                                        {log.action}
                                                    </span>
                                                    <span className="font-medium text-text-dark">
                                                        {log.username}
                                                    </span>
                                                    <span className="text-sm text-text-light">
                                                        {formatTimestamp(log.timestamp)}
                                                    </span>
                                                </div>
                                                <p className="text-sm text-text-dark mb-1">{log.description}</p>
                                                {log.details && (
                                                    <div className="text-xs text-text-light bg-gray-100 rounded p-2 mt-2">
                                                        <pre className="whitespace-pre-wrap font-mono">
                                                            {typeof log.details === 'string' 
                                                                ? log.details 
                                                                : JSON.stringify(log.details, null, 2)
                                                            }
                                                        </pre>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                        <div className="text-xs text-text-light">
                                            ID: {log.id}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {filteredLogs.length > 0 && (
                    <div className="mt-6 flex justify-center">
                        <p className="text-sm text-text-light">
                            Showing {filteredLogs.length} activity logs
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}

export default ActivityLogView;
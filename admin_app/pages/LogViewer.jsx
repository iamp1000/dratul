const LogViewer = ({ user }) => {
    const [logs, setLogs] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [filters, setFilters] = React.useState({
        userId: '',
        category: '',
        startDate: '',
        endDate: '',
    });
    const [users, setUsers] = React.useState([]);
    const [isFixing, setIsFixing] = React.useState(false);
    const [fixReport, setFixReport] = React.useState(null);

    React.useEffect(() => {
        const fetchUsers = async () => {
            try {
                const data = await api('/api/v1/users');
                setUsers(Array.isArray(data) ? data : []);
            } catch (error) {
                console.error('Error fetching users:', error);
            }
        };
        fetchUsers();
    }, []);

    const fetchLogs = React.useCallback(async () => {
        setLoading(true);
        const params = new URLSearchParams();
        if (filters.userId) params.append('user_id', filters.userId);
        if (filters.category) params.append('category', filters.category);
        if (filters.startDate) params.append('start_date', filters.startDate);
        if (filters.endDate) params.append('end_date', filters.endDate);

        try {

            const data = await api(`/api/v1/logs/comprehensive?${params.toString()}`);
            setLogs(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error('Error fetching logs:', error);
            setLogs([]);
        } finally {
            setLoading(false);
        }
    }, [filters]);

    React.useEffect(() => {

        const handler = setTimeout(() => fetchLogs(), 500);
        return () => clearTimeout(handler);
    }, [fetchLogs]);

    const handleFilterChange = (e) => {
        const { name, value } = e.target;
        setFilters(prev => ({ ...prev, [name]: value }));
    };

    const handleFixAnomalies = async () => {
        setIsFixing(true);
        setFixReport(null);
        try {
            const report = await api('/api/v1/health/fix-anomalies', {
                method: 'POST',
            });
            setFixReport(report);

            fetchLogs();
        } catch (err) {
            console.error('Error fixing anomalies:', err);

            setFixReport({ errors: [err.message || 'An unknown error occurred'] });
        } finally {
            setIsFixing(false);
        }
    };

    const logCategories = ['GENERAL', 'AUTHENTICATION', 'PATIENT', 'APPOINTMENT', 'USER'];

    const getSeverityClass = (severity, logType) => {

        if (logType === 'health_alert') {

            return 'bg-yellow-100 text-yellow-800 border border-yellow-300';
        }
        switch (severity) {
            case 'CRITICAL': return 'bg-red-600 text-white';
            case 'ERROR': return 'bg-red-200 text-red-800';
            case 'WARN': return 'bg-yellow-200 text-yellow-800';
            default: return 'bg-blue-200 text-blue-800';
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-lg sm:text-xl lg:text-2xl font-bold text-medical-dark font-primary">Audit Logs & System Health</h2>
                {user?.permissions?.can_run_anomaly_fix && (
                    <button
                        onClick={handleFixAnomalies}
                        disabled={isFixing}
                        className="medical-button px-4 py-2 text-white rounded-xl font-secondary flex items-center gap-2 relative z-10 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isFixing ? (
                            <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div><span>Fixing...</span></>
                        ) : (
                            <><i className="fas fa-magic"></i><span>Run Anomaly Fix</span></>
                        )}
                    </button>
                )}
            </div>

            { }
            {fixReport && (
                <div className={`p-4 rounded-lg border ${fixReport.errors && fixReport.errors.length > 0 ? 'bg-red-50 border-red-200 text-red-700' : 'bg-green-50 border-green-200 text-green-700'}`}>
                    <h4 className="font-bold mb-1">{fixReport.errors && fixReport.errors.length > 0 ? 'Fix Failed' : 'Fix Report Complete'}</h4>
                    {fixReport.errors && fixReport.errors.length > 0 ? (
                        <ul className="list-disc list-inside text-sm">
                            {fixReport.errors.map((err, i) => <li key={i}>{err}</li>)}
                        </ul>
                    ) : (
                        <p className="text-sm">Successfully fixed {fixReport.fixed_slots?.length || 0} slot status(es) and {fixReport.fixed_counters?.length || 0} slot counter(s).</p>
                    )}
                </div>
            )}

            <div className="p-4 bg-gray-50 rounded-xl border border-gray-200 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <div>
                    <label className="text-sm font-medium text-medical-gray">User</label>
                    <select name="userId" value={filters.userId} onChange={handleFilterChange} className="mt-1 form-input-themed">
                        <option value="">All Users</option>
                        {users.map(user => <option key={user.id} value={user.id}>{user.username}</option>)}                            </select>
                </div>
                <div>
                    <label className="text-sm font-medium text-medical-gray">Category</label>
                    <select name="category" value={filters.category} onChange={handleFilterChange} className="mt-1 form-input-themed">
                        <option value="">All Categories</option>
                        {logCategories.map(cat => <option key={cat} value={cat}>{cat}</option>)}                            </select>
                </div>
                <div>
                    <label className="text-sm font-medium text-medical-gray">Start Date</label>
                    <input type="date" name="startDate" value={filters.startDate} onChange={handleFilterChange} className="custom-datetime mt-1 form-input-themed" />
                </div>
                <div>
                    <label className="text-sm font-medium text-medical-gray">End Date</label>
                    <input type="date" name="endDate" value={filters.endDate} onChange={handleFilterChange} className="custom-datetime mt-1 form-input-themed" />
                </div>
            </div>

            <div className="medical-card rounded-2xl overflow-hidden">
                <div className="overflow-x-auto">
                    {loading ? <LoadingSpinner /> : (
                        <div className="overflow-x-auto -mx-4 sm:mx-0"><table className="w-full">
                            <thead className="bg-medical-light">
                                <tr>
                                    <th className="text-left p-4 font-semibold text-medical-dark">Timestamp</th>
                                    <th className="text-left p-4 font-semibold text-medical-dark">User</th>
                                    <th className="text-left p-4 font-semibold text-medical-dark">Category</th>
                                    <th className="text-left p-4 font-semibold text-medical-dark">Severity</th>
                                    <th className="text-left p-4 font-semibold text-medical-dark">Action</th>
                                    <th className="text-left p-4 font-semibold text-medical-dark">Details</th>
                                </tr>
                            </thead>
                            <tbody>
                                {logs.map((entry, index) => {

                                    const isHealthAlert = entry.log_type === 'health_alert';
                                    const key = isHealthAlert ? `health-${index}` : `log-${entry.id}`;
                                    const rowClass = `table-row border-b border-gray-100 ${isHealthAlert ? 'bg-yellow-50 hover:bg-yellow-100' : ''}`;
                                    const severityClass = getSeverityClass(entry.severity, entry.log_type);

                                    return (
                                        <tr key={key} className={rowClass}>
                                            <td className="p-4 text-medical-gray text-sm whitespace-nowrap">
                                                {new Date(entry.timestamp).toLocaleString()}
                                                {isHealthAlert && <i className="fas fa-exclamation-triangle text-yellow-600 ml-2" title="Health Alert"></i>}
                                            </td>
                                            <td className="p-4 text-medical-gray">{entry.username || 'System'}</td>
                                            <td className="p-4">
                                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${isHealthAlert ? 'bg-yellow-200 text-yellow-800' : 'bg-gray-200 text-gray-800'}`}>
                                                    {entry.category}
                                                </span>
                                            </td>
                                            <td className="p-4">
                                                <span className={`px-2 py-1 rounded-full text-xs font-medium ${severityClass}`}>
                                                    {entry.severity}
                                                </span>
                                            </td>
                                            <td className="p-4 text-medical-gray">{entry.action}</td>
                                            <td className="p-4 text-medical-gray text-sm">
                                                {isHealthAlert && `[Slot ID: ${entry.resource_id}] `}{entry.details || 'N/A'}
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table></div>
                    )}
                </div>
                {!loading && logs.length === 0 && (
                    <div className="text-center py-12">
                        <i className="fas fa-clipboard-list text-4xl text-medical-gray mb-4"></i>
                        <p className="text-medical-gray">No logs found for the selected filters.</p>
                    </div>
                )}
            </div>
        </div >
    );
};

window.LogViewer = LogViewer;
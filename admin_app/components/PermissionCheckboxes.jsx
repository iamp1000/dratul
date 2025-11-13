const PermissionCheckboxes = ({ permissions, setPermissions, isSuperAdmin, isEditingOwnAccount }) => {
    // Map permissions keys to user-friendly labels and descriptions
    const permissionConfig = [
        { key: 'can_manage_users', label: 'Manage Users/Roles', description: 'Can create, edit, or delete user accounts (excluding SuperAdmin).' },
        { key: 'can_edit_schedule', label: 'Edit Doctor Schedule', description: 'Can modify working hours and create emergency blocks.' },
        { key: 'can_manage_appointments', label: 'Manage Appointments', description: 'Can schedule, cancel, and modify appointments/slots.' },
        { key: 'can_edit_patient_info', label: 'Edit Patient Records', description: 'Can create new patients and modify existing patient details/EMR data.' },
        { key: 'can_delete_patient', label: 'Delete Patient Records', description: 'Can permanently remove patient records from the database.' },
        { key: 'can_access_logs', label: 'Access Audit Logs', description: 'Can view the comprehensive system activity and security logs.' },
        { key: 'can_run_anomaly_fix', label: 'Run System Fixes', description: 'Can run consistency checks and fix data anomalies.' },
    ];

    const handleToggle = (key) => {
        setPermissions(prev => ({
            ...prev,
            [key]: !prev[key]
        }));
    };

    const isDisabled = (key) => {
        // Block editing own permissions to prevent self-lockout
        return isEditingOwnAccount && key !== 'can_manage_appointments';
    };

    return (
        <div className="medical-card p-4 rounded-xl border-t border-gray-200 mt-4">
            <h3 className="text-lg font-semibold text-medical-dark mb-3 border-b pb-2">User Permissions</h3>
            <div className="space-y-3">
                {permissionConfig.map(p => (
                    <div key={p.key} className={`flex items-center space-x-3 p-2 rounded-lg ${permissions[p.key] ? 'bg-medical-light' : 'bg-gray-50'} border`}>
                        <input
                            type="checkbox"
                            checked={!!permissions[p.key]}
                            onChange={() => handleToggle(p.key)}
                            className="w-4 h-4 text-medical-accent rounded focus:ring-medical-accent"
                            disabled={isDisabled(p.key) || isSuperAdmin}
                        />
                        <div>
                            <span className="font-medium text-medical-dark block">{p.label}</span>
                            <span className="text-xs text-medical-gray">{p.description}</span>
                        </div>
                    </div>
                ))}
                {isSuperAdmin && (
                    <div className="text-sm text-red-600 bg-red-50 p-2 rounded-lg border border-red-200">
                        Warning: Permissions for the SuperAdmin account are read-only and enforced by the backend.
                    </div>
                )}
            </div>
        </div>
    );
};

window.PermissionCheckboxes = PermissionCheckboxes;

export default PermissionCheckboxes;
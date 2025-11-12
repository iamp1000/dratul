const UserEditor = ({ user, onClose, refreshUsers, loggedInUser }) => {
    const [username, setUsername] = React.useState(user?.username || '');
    const [email, setEmail] = React.useState(user?.email || '');
    const [role, setRole] = React.useState(user?.role || 'staff');
    const [phoneNumber, setPhoneNumber] = React.useState(user?.phone_number || '');
    const [password, setPassword] = React.useState('');
    const [isActive, setIsActive] = React.useState(user ? user.is_active : true);
    const [error, setError] = React.useState('');

    // NEW: State for current permissions (used for PUT payload)
    const [permissions, setPermissions] = React.useState(user?.permissions || {});

    // Utility to check if this is the SuperAdmin (ID 1 is guaranteed owner in backend logic)
    const isSuperAdmin = user?.id === 1 && user?.role === 'admin';
    const isEditingOwnAccount = user && loggedInUser && user.id === loggedInUser.id;

    const handleSubmit = async () => {
        setError('');

        // Prevent editing of SuperAdmin permissions/role in the UI
        if (isSuperAdmin && role !== user.role) {
            setError('Cannot change the role of the SuperAdmin account.');
            return;
        }
        if (isSuperAdmin && JSON.stringify(permissions) !== JSON.stringify(user.permissions)) {
            setError('Cannot modify the permissions of the SuperAdmin account.');
            return;
        }

        // Prevent Admin from stripping their own admin/logs/user management permissions
        if (isEditingOwnAccount && !isSuperAdmin && user && user.role === 'admin') {
            // If they remove can_manage_users or can_access_logs, prevent save.
            if (!permissions.can_manage_users || !permissions.can_access_logs) {
                setError('Cannot remove critical administrative permissions from your own account.');
                return;
            }
        }

        const payload = {
            username, email, role, phone_number: phoneNumber, is_active: isActive
        };

        // Only include permissions if updating an existing user (they are needed for update payload)
        if (user) {
            // Explicitly stringify and parse to ensure the object is correctly formatted for the backend JSON field
            payload.permissions = JSON.parse(JSON.stringify(permissions));
        }


        if (!user || password) {
            if (password.length < 8) {
                setError('Password must be at least 8 characters long.');
                return;
            }
            payload.password = password;
        }

        try {
            if (user) {
                await api(`/api/v1/users/${user.id}`, {
                    method: 'PUT',
                    body: JSON.stringify(payload)
                });
            } else {
                await api('/api/v1/users', {
                    method: 'POST',
                    body: JSON.stringify(payload)
                });
            }
            refreshUsers();
            onClose();
        } catch (err) {
            setError('An error occurred. Please try again.');
            console.error('Save user error:', err);
        }
    };

    return (
        <div className="space-y-6">
            {error && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg">{error}</div>}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <label className="block text-sm font-medium text-medical-gray mb-2">Username</label>
                    <input
                        type="text"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        className="form-input-themed"
                        placeholder="Enter username"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-medical-gray mb-2">Email</label>
                    <input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="form-input-themed"
                        placeholder="Enter email"
                    />
                </div>
                <div>
                    <label className="block text-sm font-medium text-medical-gray mb-2">Role</label>
                    <select
                        value={role}
                        onChange={(e) => setRole(e.target.value)}
                        className="form-input-themed"
                        disabled={isSuperAdmin} // SuperAdmin role is locked on the frontend
                    >
                        <option value="staff">Staff</option>
                        <option value="doctor">Doctor</option>
                        <option value="viewer">Viewer</option>
                        <option value="admin">Admin</option>
                    </select>
                </div>
                <div>
                    <label className="block text-sm font-medium text-medical-gray mb-2">Phone Number</label>
                    <input
                        type="tel"
                        value={phoneNumber}
                        onChange={(e) => setPhoneNumber(e.target.value)}
                        className="form-input-themed"
                        placeholder="Enter phone number"
                    />
                </div>
            </div>

            {!user && (
                <div>
                    <label className="block text-sm font-medium text-medical-gray mb-2">Password</label>
                    <input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="form-input-themed"
                        placeholder="Enter new password"
                    />
                </div>
            )}

            <div className="flex flex-wrap items-center gap-2 sm:space-x-4">
                <label className="flex flex-wrap items-center gap-2">
                    <input
                        type="checkbox"
                        checked={isActive}
                        onChange={(e) => setIsActive(e.target.checked)}
                        className="w-4 h-4 text-medical-accent rounded focus:ring-medical-accent"
                    />
                    <span>Active User</span>
                </label>
                <label className="flex flex-wrap items-center gap-2">
                    <input
                        type="checkbox"
                        defaultChecked={user?.mfa_enabled}
                        className="custom-checkbox w-4 h-4 text-medical-accent rounded focus:ring-medical-accent"
                    />
                    <span>Enable MFA</span>
                </label>
            </div>

            {user?.role === 'admin' && (
                <PermissionCheckboxes
                    permissions={permissions}
                    setPermissions={setPermissions}
                    isSuperAdmin={isSuperAdmin}
                    isEditingOwnAccount={isEditingOwnAccount}
                />
            )}

            <div className="flex justify-end space-x-3">
                <button onClick={onClose} className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">
                    Cancel
                </button>
                <button onClick={handleSubmit} className="medical-button px-4 py-2 text-white rounded-lg relative z-10">
                    {user ? 'Update User' : 'Create User'}
                </button>
            </div>
        </div>
    );
};

window.UserEditor = UserEditor;
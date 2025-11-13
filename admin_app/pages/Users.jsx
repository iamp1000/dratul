import React from 'react';
import LoadingSpinner from '../lib/LoadingSpinner.jsx';
import Modal from '../lib/Modal.jsx';
import UserEditor from '../components/UserEditor.jsx';

const Users = ({ user: loggedInUser }) => {
    const [users, setUsers] = React.useState([]);

    const handleResetPassword = (user) => {
        if (confirm(`Are you sure you want to open the password reset modal for user ${user.username}?`)) {
            // Pass the user to UserEditor to open the modal
            handleEditUser(user);
        }
    };

    const handleDeleteUser = async (userId, username) => {
        if (confirm(`WARNING: Are you sure you want to delete the user ${username} (ID: ${userId})? This action cannot be undone.`)) {
            try {
                // The backend crud.py already contains SuperAdmin protection logic (ID 1 cannot be deleted)
                await api(`/api/v1/users/${userId}`, {
                    method: 'DELETE'
                });
                toast(`User ${username} deleted successfully.`);
                fetchUsers(); // Refresh the list
            } catch (err) {
                console.error('Delete user error:', err);
                toast(`Deletion failed: ${err.message || 'An unexpected error occurred.'}`);
            }
        }
    };

    const [loading, setLoading] = React.useState(true);
    const [showModal, setShowModal] = React.useState(false);
    const [editingUser, setEditingUser] = React.useState(null);

    const fetchUsers = async () => {
        setLoading(true);
        try {
            const data = await api('/api/v1/users');
            setUsers(Array.isArray(data) ? data : data.users || []);
        } catch (error) {
            console.error('Error fetching users:', error);
        } finally {
            setLoading(false);
        }
    };

    React.useEffect(() => {
        fetchUsers();
    }, []);

    const handleEditUser = (user) => {
        setEditingUser(user);
        setShowModal(true);
    };

    const handleAddUser = () => {
        setEditingUser(null);
        setShowModal(true);
    };

    const handleCloseModal = () => {
        setShowModal(false);
        setEditingUser(null);
    };

    if (loading) return <LoadingSpinner />;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h2 className="text-lg sm:text-xl lg:text-2xl font-bold text-medical-dark font-primary">User Management</h2>
                {loggedInUser?.permissions?.can_manage_users && (
                    <button onClick={handleAddUser} className="medical-button px-6 py-3 text-white rounded-xl font-secondary flex flex-wrap items-center gap-2 relative z-10">
                        <i className="fas fa-user-plus"></i>
                        <span>Add User</span>
                    </button>
                )}
            </div>

            <div className="medical-card rounded-2xl overflow-hidden">
                <div className="overflow-x-auto">
                    <div className="overflow-x-auto -mx-4 sm:mx-0"><table className="w-full">
                        <thead className="bg-medical-light">
                            <tr>
                                <th className="text-left p-4 font-semibold text-medical-dark">User</th>
                                <th className="text-left p-4 font-semibold text-medical-dark">Role</th>
                                <th className="text-left p-4 font-semibold text-medical-dark">Email</th>
                                <th className="text-left p-4 font-semibold text-medical-dark">Status</th>
                                <th className="text-left p-4 font-semibold text-medical-dark">Last Login</th>
                                <th className="text-left p-4 font-semibold text-medical-dark">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {users.map(user => (
                                <tr key={user.id} className="table-row border-b border-gray-100">
                                    <td className="p-4">
                                        <div className="flex items-center space-x-3">
                                            <div className="w-10 h-10 bg-medical-accent/10 rounded-full flex items-center justify-center">
                                                <span className="text-medical-accent font-semibold">
                                                    {user.username?.charAt(0).toUpperCase() || 'U'}
                                                </span>
                                            </div>
                                            <div>
                                                <div className="font-semibold text-medical-dark">{user.username}</div>
                                                <div className="text-sm text-medical-gray">ID: {user.id}</div>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="p-4">
                                        <span className={`px-3 py-1 rounded-full text-xs font-medium capitalize ${user.role === 'admin' ? 'bg-medical-error/10 text-medical-error' :
                                            user.role === 'doctor' ? 'bg-medical-success/10 text-medical-success' :
                                                'bg-medical-accent/10 text-medical-accent'
                                            }`}>
                                            {user.role}
                                        </span>
                                    </td>
                                    <td className="p-4 text-medical-gray">{user.email}</td>
                                    <td className="p-4">
                                        <span className={`px-2 py-1 rounded-full text-xs ${user.is_active
                                            ? 'bg-medical-success/10 text-medical-success'
                                            : 'bg-medical-error/10 text-medical-error'
                                            }`}>
                                            {user.is_active ? 'Active' : 'Inactive'}
                                        </span>
                                    </td>
                                    <td className="p-4 text-medical-gray">
                                        {user.last_login ?
                                            new Date(user.last_login).toLocaleDateString() :
                                            'Never'
                                        }
                                    </td>
                                    <td className="p-4">
                                        {loggedInUser?.permissions?.can_manage_users ? (
                                            <div className="flex space-x-2">
                                                <button
                                                    onClick={() => handleEditUser(user)}
                                                    className="text-medical-accent hover:text-medical-dark"
                                                    title="Edit User"
                                                >
                                                    <i className="fas fa-edit"></i>
                                                </button>
                                                {/* The key button opens the editor for password update */}
                                                <button
                                                    onClick={() => handleResetPassword(user)}
                                                    className="text-medical-success hover:text-green-700"
                                                    title="Reset Password/Edit User"
                                                >
                                                    <i className="fas fa-key"></i>
                                                </button>
                                                <button
                                                    onClick={() => handleDeleteUser(user.id, user.username)}
                                                    className="text-medical-error hover:text-red-700"
                                                    title="Delete User"
                                                >
                                                    <i className="fas fa-trash"></i>
                                                </button>
                                            </div>
                                        ) : (
                                            <span className="text-medical-gray text-sm">View Only</span>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table></div>
                </div>
            </div>

            <Modal
                isOpen={showModal}
                onClose={handleCloseModal}
                title={editingUser ? 'Edit User' : 'Add New User'}
            >
                {/* Pass the currently logged-in user's ID to check for self-editing */}
                <UserEditor
                    user={editingUser}
                    onClose={handleCloseModal}
                    refreshUsers={fetchUsers}
                    loggedInUser={loggedInUser}
                />
            </Modal>
        </div>
    );
};

window.Users = Users;

export default Users;
// src/features/users/components/UserManagement.jsx
import React, { useState } from 'react';
import UserModal from './UserModal';
import UserTable from './UserTable';

function UserManagement({ users, setUsers, fetchUsers, isLoading }) {
    const [searchTerm, setSearchTerm] = useState('');
    const [selectedUser, setSelectedUser] = useState(null);
    const [isUserModalOpen, setIsUserModalOpen] = useState(false);
    const [userFormData, setUserFormData] = useState({
        username: '',
        first_name: '',
        last_name: '',
        email: '',
        phone_number: '',
        role: 'admin',
        is_active: true,
        password: ''
    });

    const resetUserForm = () => {
        setUserFormData({
            username: '',
            first_name: '',
            last_name: '',
            email: '',
            phone_number: '',
            role: 'admin',
            is_active: true,
            password: ''
        });
        setSelectedUser(null);
    };

    const handleCreateUser = () => {
        resetUserForm();
        setIsUserModalOpen(true);
    };

    const handleEditUser = (user) => {
        setSelectedUser(user);
        setUserFormData({
            username: user.username,
            first_name: user.first_name,
            last_name: user.last_name,
            email: user.email,
            phone_number: user.phone_number || '',
            role: user.role,
            is_active: user.is_active,
            password: '' // Don't pre-fill password
        });
        setIsUserModalOpen(true);
    };

    const handleUserSubmit = async (e) => {
        e.preventDefault();
        try {
            const url = selectedUser ? `/api/users/${selectedUser.id}` : '/api/users';
            const method = selectedUser ? 'PUT' : 'POST';
            
            const submitData = { ...userFormData };
            if (selectedUser && !submitData.password) {
                delete submitData.password; // Don't send empty password for updates
            }
            
            const response = await fetch(url, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(submitData)
            });
            
            if (response.ok) {
                fetchUsers();
                setIsUserModalOpen(false);
                resetUserForm();
            } else {
                const error = await response.json();
                alert(`Error: ${error.detail || 'Failed to save user'}`);
            }
        } catch (error) {
            console.error('Error saving user:', error);
            alert('Error saving user');
        }
    };

    const handleDeleteUser = async (userId) => {
        if (confirm('Are you sure you want to delete this user?')) {
            try {
                const response = await fetch(`/api/users/${userId}`, {
                    method: 'DELETE'
                });
                if (response.ok) {
                    fetchUsers();
                } else {
                    alert('Error deleting user');
                }
            } catch (error) {
                console.error('Error deleting user:', error);
                alert('Error deleting user');
            }
        }
    };

    const handleToggleActive = async (userId, currentStatus) => {
        try {
            const response = await fetch(`/api/users/${userId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_active: !currentStatus })
            });
            if (response.ok) {
                fetchUsers();
            }
        } catch (error) {
            console.error('Error updating user status:', error);
        }
    };

    const filteredUsers = users.filter(user =>
        user.username.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.first_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.last_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        user.email.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h2 className="text-3xl font-bold text-text-dark">User Management</h2>
                <button
                    onClick={handleCreateUser}
                    className="bg-primary hover:bg-primary-dark text-white px-6 py-3 rounded-lg transition-colors font-medium"
                >
                    + New User
                </button>
            </div>

            <div className="bg-white rounded-xl shadow-sm p-6">
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-xl font-semibold text-text-dark">All Users</h3>
                    <div className="flex items-center space-x-4">
                        <input
                            type="text"
                            placeholder="Search users..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
                        />
                        <span className="text-sm text-text-light">
                            {filteredUsers.length} users found
                        </span>
                    </div>
                </div>

                <UserTable 
                    users={filteredUsers}
                    onEditUser={handleEditUser}
                    onDeleteUser={handleDeleteUser}
                    onToggleActive={handleToggleActive}
                    isLoading={isLoading}
                />
            </div>

            <UserModal 
                isOpen={isUserModalOpen}
                onClose={() => {
                    setIsUserModalOpen(false);
                    resetUserForm();
                }}
                formData={userFormData}
                setFormData={setUserFormData}
                onSubmit={handleUserSubmit}
                isEditing={!!selectedUser}
            />
        </div>
    );
}

export default UserManagement;
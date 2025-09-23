// src/App.jsx
import React from 'react';
import AdminLayout from './layouts/AdminLayout/AdminLayout';
import { AuthProvider } from './hooks/useAuth';

function App() {
    return (
        <AuthProvider>
            <AdminLayout />
        </AuthProvider>
    );
}

export default App;
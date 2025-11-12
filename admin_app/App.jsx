import React, { useState, useEffect } from "react";
import LoginPage from "./pages/LoginPage.jsx";
import Sidebar from "./components/Sidebar.jsx";
import Dashboard from "./pages/Dashboard.jsx";

const App = () => {
    const [user, setUser] = useState(() => {
        const savedUser = sessionStorage.getItem("user");
        return savedUser ? JSON.parse(savedUser) : null;
    });

    // Called by LoginPage after successful login
    const handleLoginSuccess = (userData) => {
        sessionStorage.setItem("user", JSON.stringify(userData));
        setUser(userData);
    };

    // Log out helper (you can wire this later)
    const handleLogout = () => {
        sessionStorage.clear();
        setUser(null);
    };

    if (!user) {
        // Show login page if not logged in
        return <LoginPage onLoginSuccess={handleLoginSuccess} />;
    }

    const username = user?.username || "Admin";

    return (
        <div className="min-h-screen bg-gradient-to-br from-medical-light-gray via-medical-light to-medical-light-gray">
            <div className="flex flex-col md:flex-row h-screen overflow-hidden">
                <Sidebar
                    currentView="dashboard"
                    setCurrentView={() => { }}
                    user={user}
                    isMobileMenuOpen={false}
                    setIsMobileMenuOpen={() => { }}
                    onLogout={handleLogout}
                />
                <main className="flex-1 overflow-auto relative ml-0 md:ml-0">
                    <div className="md:hidden flex items-center justify-between p-4 bg-white/80 backdrop-blur-sm sticky top-0 z-30 shadow-sm">
                        <div className="font-semibold text-medical-dark">{username}</div>
                    </div>
                    <div className="p-8">
                        <div className="max-w-7xl mx-auto floating-elements relative">
                            <h1 className="text-2xl font-bold text-medical-dark mb-4">
                                Welcome, {username}
                            </h1>
                            <p>This is your admin dashboard. Use the sidebar to navigate.</p>
                            <Dashboard user={user} />
                        </div>
                    </div>
                </main>
            </div>
        </div>
    );
};

export default App;

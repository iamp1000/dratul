import React, { useState, useEffect } from "react";
import LoginPage from "./pages/LoginPage.jsx";
import Sidebar from "./components/Sidebar.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Appointments from "./pages/Appointments.jsx";
import DoctorSchedule from "./pages/DoctorSchedule.jsx";
import Patients from "./pages/Patients.jsx";
import ConsultationView from "./pages/ConsultationView.jsx";
import TemplateEditorView from "./pages/TemplateEditorView.jsx";
import Users from "./pages/Users.jsx";
import LogViewer from "./pages/LogViewer.jsx";
import Modal from "./lib/Modal.jsx";

const App = () => {
    const [user, setUser] = useState(() => {
        const savedUser = sessionStorage.getItem("user");
        return savedUser ? JSON.parse(savedUser) : null;
    });

    const [currentView, setCurrentView] = useState("dashboard");
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [modalTitle, setModalTitle] = useState('');
    const [modalContent, setModalContent] = useState(null);

    const openModal = (title, content) => {
        setModalTitle(title);
        setModalContent(content);
        setIsModalOpen(true);
    };

    const closeModal = () => {
        setIsModalOpen(false);
        setModalTitle('');
        setModalContent(null);
    };

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

    const renderCurrentView = () => {
        switch (currentView) {
            case 'dashboard':
                return <Dashboard openModal={openModal} closeModal={closeModal} user={user} />;
            case 'appointments':
                return <Appointments openModal={openModal} closeModal={closeModal} user={user} />;
            case 'schedule':
                return <DoctorSchedule openModal={openModal} closeModal={closeModal} user={user} />;
            case 'patients':
                return <Patients user={user} />;
            case 'consultation':
                return <ConsultationView />;
            case 'templates':
                return <TemplateEditorView />;
            case 'users':
                return <Users user={user} />;
            case 'logs':
                return <LogViewer user={user} />;
            default:
                return (
                    <div className="p-4 text-center">
                        <h2 className="text-xl font-bold text-medical-dark">Coming Soon</h2>
                        <p className="text-medical-gray">The {currentView} view is not yet implemented.</p>
                        <button onClick={() => setCurrentView('dashboard')} className="mt-4 text-medical-accent hover:underline">Back to Dashboard</button>
                    </div>
                );
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-medical-light-gray via-medical-light to-medical-light-gray">
            <div className="flex flex-col md:flex-row h-screen">
                <Sidebar
                    currentView={currentView}
                    setCurrentView={setCurrentView}
                    user={user}
                    isMobileMenuOpen={isMobileMenuOpen}
                    setIsMobileMenuOpen={setIsMobileMenuOpen}
                    onLogout={handleLogout}
                />
                <main className="flex-1 overflow-auto relative ml-0 md:ml-0">
                    <div className="md:hidden flex items-center justify-between p-4 bg-white/80 backdrop-blur-sm sticky top-0 z-30 shadow-sm">
                        <button onClick={() => setIsMobileMenuOpen(true)} className="text-medical-dark mr-4">
                             <i className="fas fa-bars text-xl"></i>
                        </button>
                        <div className="font-semibold text-medical-dark">{username}</div>
                    </div>
                    <div className="p-8">
                        <div className="max-w-7xl mx-auto floating-elements relative">
                             {currentView === 'dashboard' && (
                                <h1 className="text-2xl font-bold text-medical-dark mb-4">
                                    Welcome, {username}
                                </h1>
                             )}
                            {renderCurrentView()}
                        </div>
                    </div>
                    <Modal
                        isOpen={isModalOpen}
                        onClose={closeModal}
                        title={modalTitle}
                    >
                        {modalContent}
                    </Modal>
                </main>

                {/* Floating Action Button for New Appointment */}
                <button 
                    onClick={() => {
                        if (window.AppointmentEditor) {
                            openModal('Create New Appointment', <AppointmentEditor onClose={closeModal} user={user} refreshAppointments={() => setCurrentView('appointments')} />) 
                        } else {
                            alert('Appointment editor component not yet loaded or imported.');
                        }
                    }}
                    title="Schedule New Appointment"
                    className="fixed bottom-8 right-8 z-50 p-4 bg-medical-accent text-white rounded-full shadow-2xl hover:bg-medical-blue transition-all transform hover:scale-110"
                >
                    <i className="fas fa-calendar-plus text-xl"></i>
                </button>

            </div>
        </div>
    );
};

export default App;

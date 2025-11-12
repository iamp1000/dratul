import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import App from './App.jsx';
import LoginPage from './pages/LoginPage.jsx';
import './styles.css';

const Root = () => {
  const isLoggedIn = !!sessionStorage.getItem('accessToken');
  return (
    <BrowserRouter>
      <Routes>
        <Route path='/' element={isLoggedIn ? <App /> : <Navigate to='/login' />} />
        <Route path='/login' element={<LoginPage />} />
      </Routes>
    </BrowserRouter>
  );
};

console.log("Main.jsx initialized");
ReactDOM.createRoot(document.getElementById('root')).render(<Root />);

// Original App function (legacy code retained below for reference if needed)
/*
// const LegacyApp = () => {
  // const [isMobileMenuOpen, setIsMobileMenuOpen] = React.useState(false);
  // const [user, setUser] = React.useState(() => {
    const userData = sessionStorage.getItem('user');
    return userData ? JSON.parse(userData) : null;
  });
  // const [currentView, setCurrentView] = React.useState('dashboard');
  // const [isModalOpen, setIsModalOpen] = React.useState(false);
  const [modalTitle, setModalTitle] = React.useState('');
  const [modalContent, setModalContent] = React.useState(null);

  // const openModal = (title, content) => {
    setModalTitle(title);
    setModalContent(content);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setModalTitle('');
    setModalContent(null);
  };

  React.useEffect(() => {
    const token = sessionStorage.getItem('accessToken');
    if (!token || !user) {
      window.location.href = './admin_login.html';
    }
  }, [user]);

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  const renderCurrentView = () => {
    switch (currentView) {
      case 'dashboard':
        return window.Dashboard ? <window.Dashboard openModal={openModal} closeModal={closeModal} /> : <div>Loading Dashboard...</div>;
      case 'appointments':
        return window.Appointments ? <window.Appointments openModal={openModal} closeModal={closeModal} user={user} /> : <div>Loading Appointments...</div>;
      case 'schedule':
        return window.DoctorSchedule ? <window.DoctorSchedule openModal={openModal} closeModal={closeModal} user={user} /> : <div>Loading Schedule...</div>;
      case 'patients':
        return window.Patients ? <window.Patients user={user} /> : <div>Loading Patients...</div>;
      case 'consultation':
        return window.ConsultationEditor ? <window.ConsultationEditor /> : <div>Loading Consultation...</div>;
      case 'templates':
        return window.TemplateEditorView ? <window.TemplateEditorView /> : <div>Loading Templates...</div>;
      case 'users':
        return user.role === 'admin' ? (window.Users ? <window.Users user={user} /> : <div>Loading Users...</div>) : window.Dashboard ? <window.Dashboard /> : <div>Loading Dashboard...</div>;
      case 'logs':
        return user.role === 'admin' ? (window.LogViewer ? <window.LogViewer user={user} /> : <div>Loading Logs...</div>) : window.Dashboard ? <window.Dashboard /> : <div>Loading Dashboard...</div>;
      default:
        return window.Dashboard ? <window.Dashboard /> : <div>Loading Dashboard...</div>;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-medical-light-gray via-medical-light to-medical-light-gray">
      <div className="flex flex-col md:flex-row h-screen overflow-hidden">
        <Sidebar
          currentView={currentView}
          setCurrentView={setCurrentView}
          user={user}
          isMobileMenuOpen={isMobileMenuOpen}
          setIsMobileMenuOpen={setIsMobileMenuOpen}
        />
        <main className="flex-1 overflow-auto relative ml-0 md:ml-0">
          <div className="md:hidden flex items-center justify-between p-4 bg-white/80 backdrop-blur-sm sticky top-0 z-30 shadow-sm">
            <button onClick={() => setIsMobileMenuOpen(true)} className="text-medical-dark">
              <i className="fas fa-bars text-xl"></i>
            </button>
            <div className="font-semibold text-medical-dark">{user?.username}</div>
          </div>
          <div className="p-8">
            <div className="max-w-7xl mx-auto floating-elements relative">
              {renderCurrentView()}
              <Modal
                isOpen={isModalOpen}
                onClose={closeModal}
                title={modalTitle}
              >
                {modalContent}
              </Modal>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(<><App />{window.QuickActions && <window.QuickActions />}</>);
*/


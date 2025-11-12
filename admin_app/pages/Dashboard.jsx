const Dashboard = ({ openModal, closeModal }) => {
  const [stats, setStats] = React.useState(null);
  const [recentPresc, setRecentPresc] = React.useState([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await window.api('/api/v1/dashboard/stats');
        setStats(data);
      } catch (error) {
        console.error('Error fetching stats:', error);
      } finally {
        setLoading(false);
      }
    };
    const fetchRecent = async () => {
      try {
        const data = await window.api('/api/v1/prescriptions/recent?limit=5');
        setRecentPresc(Array.isArray(data) ? data : []);
      } catch { }
    };
    fetchStats();
    fetchRecent();
  }, []);

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h2 className="text-lg sm:text-xl lg:text-2xl font-bold text-medical-dark font-primary">Dashboard Overview</h2>
        <div className="text-medical-gray font-secondary">
          <i className="fas fa-calendar-day mr-2"></i>
          {new Date().toLocaleDateString('en-US', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric'
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          icon="fas fa-users"
          title="Total Patients"
          value={stats?.total_patients || 0}
          subtitle="All Time"
          color="medical-success"
        />
        <StatCard
          icon="fas fa-calendar-check"
          title="Today's Appointments"
          value={stats?.appointments_today || 0}
          subtitle="Today"
          color="medical-accent"
        />
        <StatCard
          icon="fas fa-clock"
          title="Pending Appointments"
          value={stats?.pending_appointments || 0}
          subtitle="Waiting"
          color="medical-warning"
        />
        <StatCard
          icon="fas fa-chart-line"
          title="This Week"
          value={stats?.appointments_week || 0}
          subtitle="7 Days"
          color="medical-blue"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="medical-card p-6 rounded-2xl">
          <h3 className="text-lg font-bold text-medical-dark mb-4 font-primary">Quick Actions</h3>
          <div className="space-y-3">
            <button onClick={() => openModal('Create New Appointment', window.AppointmentEditor ? <window.AppointmentEditor onClose={closeModal} user={JSON.parse(sessionStorage.getItem('user'))} /> : <div>Appointment Editor loading...</div>)} className="medical-button w-full p-3 text-white rounded-xl font-secondary flex items-center justify-center space-x-2 relative z-10">
              <i className="fas fa-plus"></i>
              <span>New Appointment</span>
            </button>
            <button onClick={() => openModal('Add New Patient', window.PatientEditor ? <window.PatientEditor onClose={closeModal} /> : <div>Patient Editor loading...</div>)} className="medical-button w-full p-3 text-white rounded-xl font-secondary flex items-center justify-center space-x-2 relative z-10">
              <i className="fas fa-user-plus"></i>
              <span>Add Patient</span>
            </button>
          </div>
        </div>

        <div className="medical-card p-6 rounded-2xl">
          <h3 className="text-lg font-bold text-medical-dark mb-4 font-primary">System Status</h3>
          <div className="space-y-3">
            <DashboardServices />
          </div>
        </div>
      </div>

      <div className="medical-card p-6 rounded-2xl mt-6">
        <h3 className="text-lg font-bold text-medical-dark mb-4 font-primary">Recent Prescriptions</h3>
        {recentPresc.length === 0 ? (
          <div className="text-medical-gray text-sm">No recent prescriptions.</div>
        ) : (
          <div className="space-y-2">
            {recentPresc.map(p => (
              <div key={p.id} className="flex items-center justify-between p-3 border border-gray-200 rounded-lg">
                <div>
                  <div className="font-medium text-medical-dark">{p.medication_name}</div>
                  <div className="text-sm text-medical-gray">Patient ID: {p.patient_id} • {new Date(p.prescribed_date).toLocaleDateString()}</div>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <button onClick={() => window.open(`/api/v1/prescriptions/editor/pdf/${p.document_id || ''}`, '_blank')} className="px-2 py-1 bg-gray-100 rounded text-sm">PDF</button>
                  <button onClick={() => window.open(`/api/v1/prescriptions/editor/html/${p.document_id || ''}`, '_blank')} className="px-2 py-1 bg-gray-100 rounded text-sm">HTML</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

window.Dashboard = Dashboard;

export default Dashboard;
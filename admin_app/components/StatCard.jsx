const StatCard = ({ icon, title, value, subtitle, color = "medical-accent" }) => (
  <div className="stat-card p-6 rounded-2xl medical-card animate-slide-up">
    <div className="flex items-center justify-between mb-4">
      <div className={`w-12 h-12 bg-${color}/10 rounded-xl flex items-center justify-center`}>
        <i className={`${icon} text-${color} text-xl`}></i>
      </div>
      <div className={`px-3 py-1 bg-${color}/10 text-${color} text-sm font-medium rounded-full`}>
        {subtitle}
      </div>
    </div>
    <div className="text-xl sm:text-2xl lg:text-3xl font-bold text-medical-dark mb-1">{value}</div>
    <div className="text-medical-gray font-secondary">{title}</div>
  </div>
);



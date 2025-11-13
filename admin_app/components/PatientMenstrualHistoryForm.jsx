const PatientMenstrualHistoryForm = ({ patientId }) => {
  const [history, setHistory] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState('');

  React.useEffect(() => {
    if (!patientId) return;
    const fetchHistory = async () => {
      setLoading(true);
      setError('');
      try {
        const data = await window.api(`/api/v1/patients/${patientId}/menstrual-history`);
        setHistory(data);
      } catch (err) {
        setError(`Failed to load history: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, [patientId]);

  const handleSave = async () => {
    setError('');
    setLoading(true);
    try {
      const dataToSave = { ...history };
      delete dataToSave.id;
      delete dataToSave.patient_id;
      if (dataToSave.age_at_menarche === '') dataToSave.age_at_menarche = null;

      const savedData = await window.api(`/api/v1/patients/${patientId}/menstrual-history`, {
        method: 'POST',
        body: JSON.stringify(dataToSave),
      });
      setHistory(savedData);
      window.toast('Menstrual history saved.');
    } catch (err) {
      setError(`Failed to save history: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setHistory(prev => ({ ...prev, [name]: value }));
  };

  if (loading) return <div className="p-4"><LoadingSpinner /></div>;
  if (error) return <div className="p-4 text-red-500">{error}</div>;
  if (!history) return null;

  return (
    <div className="medical-card p-6 rounded-2xl">
      <h3 className="text-lg font-semibold text-medical-dark mb-4 border-b pb-2">Menstrual Info</h3>
      <div className="space-y-4 text-sm">
        <div className="grid grid-cols-3 items-center gap-4">
          <label className="custom-label col-span-1">Age at Menarche</label>
          <input type="number" name="age_at_menarche" value={history.age_at_menarche || ''} onChange={handleChange} className="form-input-themed col-span-2" placeholder="Enter age" />
        </div>
        <div className="grid grid-cols-3 items-center gap-4">
          <label className="custom-label col-span-1">LMP</label>
          <div className="relative col-span-2">
            <div className="absolute inset-y-0 end-0 top-0 flex items-center pe-3.5 pointer-events-none">
              <svg className="w-4 h-4 text-gray-500 dark:text-gray-400" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 20 20">
                <path d="M20 4a2 2 0 0 0-2-2h-2V1a1 1 0 0 0-2 0v1h-3V1a1 1 0 0 0-2 0v1H6V1a1 1 0 0 0-2 0v1H2a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V4Zm-2 13H4V8h14v9Z"/>
              </svg>
            </div>
            <input type="date" name="lmp" value={history.lmp || ''} onChange={handleChange} className="form-input-themed custom-datetime menstrual-lmp-picker" placeholder="Select date" />
          </div>
        </div>
        <div className="grid grid-cols-3 items-center gap-4">
          <label className="custom-label col-span-1">Regularity of Cycle</label>
          <select name="regularity" value={history.regularity || ''} onChange={handleChange} className="custom-select col-span-2">
            <option value="">Select...</option>
            <option value="Regular">Regular</option>
            <option value="Irregular">Irregular</option>
          </select>
        </div>
        <div className="grid grid-cols-3 items-center gap-4">
          <label className="custom-label col-span-1">Duration for Bleeding</label>
          <input type="text" name="duration_of_bleeding" value={history.duration_of_bleeding || ''} onChange={handleChange} className="form-input-themed col-span-2" placeholder="e.g., 4-5 days" />
        </div>
        <div className="grid grid-cols-3 items-center gap-4">
          <label className="custom-label col-span-1">Period of Menstrual Cycle</label>
          <input type="text" name="period_of_cycle" value={history.period_of_cycle || ''} onChange={handleChange} className="form-input-themed col-span-2" placeholder="e.g., 28 days" />
        </div>
        <div className="grid grid-cols-3 items-start gap-4">
          <label className="custom-label col-span-1 mt-3">Details of Issues</label>
          <textarea name="details_of_issues" value={history.details_of_issues || ''} onChange={handleChange} className="custom-textarea col-span-2" rows="3" placeholder="Enter details..."></textarea>
        </div>
      </div>
      <div className="flex justify-end mt-4">
        <button onClick={handleSave} className="medical-button px-4 py-2 text-white rounded-lg text-sm relative z-10">
          Save History
        </button>
      </div>
    </div>
  );
};

export default PatientMenstrualHistoryForm;
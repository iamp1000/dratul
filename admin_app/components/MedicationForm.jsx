const MedicationForm = ({ medicationsData, setMedicationsData }) => {
  const handleAddMedication = () => {
    setMedicationsData(prev => [
      ...prev,
      { type: 'TAB', medicine_name: '', dosage: '', when: '', frequency: 'daily', duration: '', notes: '' }
    ]);
  };

  const handleRemoveMedication = (indexToRemove) => {
    setMedicationsData(prev => prev.filter((_, index) => index !== indexToRemove));
  };

  const handleMedicationChange = (index, field, value) => {
    setMedicationsData(prev =>
      prev.map((med, i) =>
        i === index ? { ...med, [field]: value } : med
      )
    );
  };

  return (
    <div className="medical-card p-6 rounded-2xl">
      <div className="flex items-center justify-between mb-4 border-b pb-2">
        <h3 className="text-lg font-semibold text-medical-dark">Medications (Rx)</h3>
        <div>
          <button onClick={() => setMedicationsData([])} className="text-sm text-red-600 hover:underline mr-4">Clear All</button>
          <button onClick={handleAddMedication} className="medical-button px-3 py-1 text-white rounded-lg text-sm">
            <i className="fas fa-plus mr-1"></i> Add Medicine
          </button>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-medical-gray">
              <th className="p-2 w-12">#</th>
              <th className="p-2 w-20">Type</th>
              <th className="p-2 min-w-[200px]">Medicine</th>
              <th className="p-2 w-28">Dosage</th>
              <th className="p-2 w-28">When</th>
              <th className="p-2 w-24">Freq.</th>
              <th className="p-2 w-28">Duration</th>
              <th className="p-2 min-w-[150px]">Notes</th>
              <th className="p-2 w-10"></th>
            </tr>
          </thead>
          <tbody>
            {medicationsData.map((med, index) => (
              <tr key={index} className="border-b last:border-b-0">
                <td className="p-2 text-center text-medical-gray">{index + 1}</td>
                <td className="p-1">
                  <select value={med.type} onChange={(e) => handleMedicationChange(index, 'type', e.target.value)} className="form-input-themed p-1 text-xs">
                    <option value="TAB">TAB</option>
                    <option value="CAP">CAP</option>
                    <option value="SYP">SYP</option>
                    <option value="INJ">INJ</option>
                    <option value="CRM">CRM</option>
                    <option value="OTH">OTH</option>
                  </select>
                </td>
                <td className="p-1"><input type="text" placeholder="Medicine Name" value={med.medicine_name} onChange={(e) => handleMedicationChange(index, 'medicine_name', e.target.value)} className="form-input-themed p-1" /></td>
                <td className="p-1"><input type="text" placeholder="e.g., 1-0-1" value={med.dosage} onChange={(e) => handleMedicationChange(index, 'dosage', e.target.value)} className="form-input-themed p-1" /></td>
                <td className="p-1">
                  <select value={med.when} onChange={(e) => handleMedicationChange(index, 'when', e.target.value)} className="form-input-themed p-1 text-xs">
                    <option value="">Select</option>
                    <option value="Before Food">Before Food</option>
                    <option value="After Food">After Food</option>
                    <option value="With Food">With Food</option>
                    <option value="Bed Time">Bed Time</option>
                  </select>
                </td>
                <td className="p-1"><input type="text" placeholder="daily" value={med.frequency} onChange={(e) => handleMedicationChange(index, 'frequency', e.target.value)} className="form-input-themed p-1" /></td>
                <td className="p-1"><input type="text" placeholder="e.g., 20 days" value={med.duration} onChange={(e) => handleMedicationChange(index, 'duration', e.target.value)} className="form-input-themed p-1" /></td>
                <td className="p-1"><input type="text" placeholder="Notes" value={med.notes} onChange={(e) => handleMedicationChange(index, 'notes', e.target.value)} className="form-input-themed p-1" /></td>
                <td className="p-1 text-center">
                  <button onClick={() => handleRemoveMedication(index)} className="text-red-500 hover:text-red-700">
                    <i className="fas fa-trash-alt"></i>
                  </button>
                </td>
              </tr>
            ))}
            {medicationsData.length === 0 && (
              <tr><td colSpan="9" className="text-center p-4 text-medical-gray">No medications added.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default MedicationForm;
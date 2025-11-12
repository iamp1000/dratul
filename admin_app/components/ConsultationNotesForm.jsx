const ConsultationNotesForm = ({ notesData, setNotesData }) => {
  const quickNotesRef = React.useRef(null);
  const examNotesRef = React.useRef(null);
  const quillInstances = React.useRef({});
  const [diagnosisInput, setDiagnosisInput] = React.useState('');

  React.useEffect(() => {
    const Quill = window.Quill;
    if (!Quill) return;

    const initQuill = (ref, key) => {
      if (ref.current && !quillInstances.current[key]) {
        if (ref.current.querySelector('.ql-editor')) return;

        const quill = new Quill(ref.current, {
          theme: 'snow',
          modules: {
            toolbar: [
              ['bold', 'italic', 'underline'],
              [{ 'list': 'ordered' }, { 'list': 'bullet' }]
            ]
          },
          placeholder: `Enter ${key === 'quickNotes' ? 'quick notes' : 'systemic examination'}...`
        });
        quill.on('text-change', () => {
          setNotesData(prev => ({ ...prev, [key]: JSON.stringify(quill.getContents().ops) }));
        });
        quillInstances.current[key] = quill;
      }
    };

    initQuill(quickNotesRef, 'quick_notes');
    initQuill(examNotesRef, 'systemic_examination');

    return () => {
      Object.values(quillInstances.current).forEach(q => q && q.off('text-change'));
    };
  }, []);

  const handleTextAreaChange = (e) => {
    const { name, value } = e.target;
    setNotesData(prev => ({ ...prev, [name]: value }));
  };

  const handleAddDiagnosis = () => {
    const newDiagnosis = diagnosisInput.trim();
    if (newDiagnosis && !notesData.diagnoses?.some(d => d.diagnosis_name === newDiagnosis)) {
      setNotesData(prev => ({
        ...prev,
        diagnoses: [...(prev.diagnoses || []), { diagnosis_name: newDiagnosis }]
      }));
      setDiagnosisInput('');
    }
  };

  const handleDiagnosisKeyDown = (e) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      handleAddDiagnosis();
    }
  };

  const handleRemoveDiagnosis = (indexToRemove) => {
    setNotesData(prev => ({
      ...prev,
      diagnoses: prev.diagnoses.filter((_, index) => index !== indexToRemove)
    }));
  };

  React.useEffect(() => {
    if (quillInstances.current.quick_notes && notesData.quick_notes) {
      try {
        quillInstances.current.quick_notes.setContents(JSON.parse(notesData.quick_notes));
      } catch { }
    }
    if (quillInstances.current.systemic_examination && notesData.systemic_examination) {
      try {
        quillInstances.current.systemic_examination.setContents(JSON.parse(notesData.systemic_examination));
      } catch { }
    }
  }, [notesData.quick_notes, notesData.systemic_examination]);

  return (
    <div className="medical-card p-6 rounded-2xl space-y-4">
      <div>
        <label className="custom-label">Quick Notes</label>
        <div ref={quickNotesRef} style={{ height: '100px' }}></div>
      </div>
      <div>
        <label className="custom-label">Complaints</label>
        <textarea
          name="complaints"
          value={notesData.complaints || ''}
          onChange={handleTextAreaChange}
          className="custom-textarea"
          rows="3"
          placeholder="Enter patient complaints..."
        ></textarea>
      </div>
      <div>
        <label className="custom-label">Diagnosis</label>
        <div className="flex flex-wrap items-center gap-2 mb-2 p-2 border border-gray-200 rounded-lg min-h-[40px]">
          {(notesData.diagnoses || []).map((diag, index) => (
            <span key={index} className="inline-flex items-center bg-medical-accent/10 text-medical-accent text-sm font-medium px-2.5 py-0.5 rounded-full">
              {diag.diagnosis_name}
              <button
                type="button"
                onClick={() => handleRemoveDiagnosis(index)}
                className="ml-1.5 text-medical-accent hover:text-red-500"
              >
                <i className="fas fa-times-circle text-xs"></i>
              </button>
            </span>
          ))}
          <input
            type="text"
            value={diagnosisInput}
            onChange={(e) => setDiagnosisInput(e.target.value)}
            onKeyDown={handleDiagnosisKeyDown}
            onBlur={handleAddDiagnosis}
            className="flex-grow p-1 border-none focus:ring-0 text-sm"
            placeholder="Add diagnosis (press Enter)..."
          />
        </div>
      </div>
    </div>
  );
};


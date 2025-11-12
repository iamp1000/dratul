const PhysicalExaminationForm = ({ notesData, setNotesData }) => {
  const systemicRef = React.useRef(null);
  const breastRef = React.useRef(null);
  const speculumRef = React.useRef(null);
  const quillInstances = React.useRef({});

  const initQuill = (ref, key, placeholder) => {
    const Quill = window.Quill;
    if (!Quill || !ref.current || quillInstances.current[key]) {
      if (ref.current && ref.current.querySelector('.ql-editor')) {
        setQuillContent(key, notesData[key]);
      }
      return;
    }

    const quill = new Quill(ref.current, {
      theme: 'snow',
      modules: { toolbar: [['bold', 'italic'], [{ 'list': 'ordered' }, { 'list': 'bullet' }]] },
      placeholder: placeholder
    });

    quill.on('text-change', () => {
      setNotesData(prev => ({ ...prev, [key]: JSON.stringify(quill.getContents().ops) }));
    });
    quillInstances.current[key] = quill;
    setQuillContent(key, notesData[key]);
  };

  const setQuillContent = (key, content) => {
    const quill = quillInstances.current[key];
    if (quill && content) {
      try {
        const currentContent = JSON.stringify(quill.getContents().ops);
        if (currentContent !== content) {
          quill.setContents(JSON.parse(content));
        }
      } catch (e) { console.error('Failed to set Quill content for', key, e); }
    } else if (quill && !content) {
      quill.setContents([]);
    }
  };

  React.useEffect(() => {
    initQuill(systemicRef, 'systemic_examination', 'Enter systemic examination notes...');
    initQuill(breastRef, 'breast_examination_notes', 'Enter breast examination notes...');
    initQuill(speculumRef, 'per_speculum_notes', 'Enter per speculum notes...');
  }, []);

  React.useEffect(() => {
    setQuillContent('systemic_examination', notesData.systemic_examination);
    setQuillContent('breast_examination_notes', notesData.breast_examination_notes);
    setQuillContent('per_speculum_notes', notesData.per_speculum_notes);
  }, [notesData.systemic_examination, notesData.breast_examination_notes, notesData.per_speculum_notes]);

  return (
    <div className="medical-card p-6 rounded-2xl space-y-4">
      <h3 className="text-lg font-semibold text-medical-dark mb-4 border-b pb-2">Physical Examination</h3>
      <div>
        <label className="custom-label">Systemic Examination</label>
        <div ref={systemicRef} style={{ height: '100px' }}></div>
      </div>
      <div>
        <label className="custom-label">Breast Examination</label>
        <div ref={breastRef} style={{ height: '100px' }}></div>
      </div>
      <div>
        <label className="custom-label">Per Speculum</label>
        <div ref={speculumRef} style={{ height: '100px' }}></div>
      </div>
    </div>
  );
};


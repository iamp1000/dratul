const InvestigationFollowUpForm = ({ formData, setFormData }) => {
  const usgFindingsRef = React.useRef(null);
  const labTestsRef = React.useRef(null);
  const quillInstances = React.useRef({});
  const [nextVisitType, setNextVisitType] = React.useState('duration');
  const [nextVisitValue, setNextVisitValue] = React.useState('');
  const [nextVisitUnit, setNextVisitUnit] = React.useState('Days');

  React.useEffect(() => {
    const Quill = window.Quill;
    if (!Quill) return;
    const initQuill = (ref, key, placeholder) => {
      if (ref.current && !quillInstances.current[key]) {
        if (ref.current.querySelector('.ql-editor')) return;
        const quill = new Quill(ref.current, {
          theme: 'snow',
          modules: { toolbar: [['bold', 'italic'], [{ 'list': 'ordered' }, { 'list': 'bullet' }]] },
          placeholder: placeholder
        });
        quill.on('text-change', () => {
          setFormData(prev => ({ ...prev, [key]: JSON.stringify(quill.getContents().ops) }));
        });
        quillInstances.current[key] = quill;
      }
    };
    initQuill(usgFindingsRef, 'usg_findings', 'Enter USG findings...');
    initQuill(labTestsRef, 'lab_tests_imaging', 'Enter lab tests and imaging details...');
    return () => {
      Object.values(quillInstances.current).forEach(q => q && q.off('text-change'));
    };
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));

    if (name === 'nextVisitValue' || name === 'nextVisitUnit') {
      let instruction = '';
      const currentVal = name === 'nextVisitValue' ? value : nextVisitValue;
      const currentUnit = name === 'nextVisitUnit' ? value : nextVisitUnit;
      if (currentVal && currentUnit) {
        instruction = `${currentVal} ${currentUnit}`;
      }
      setFormData(prev => ({ ...prev, next_visit_instructions: instruction }));
    }
  };

  React.useEffect(() => {
    if (formData.next_visit_instructions) {
      const parts = formData.next_visit_instructions.split(' ');
      if (parts.length === 2 && !isNaN(parts[0])) {
        setNextVisitValue(parts[0]);
        setNextVisitUnit(parts[1]);
        setNextVisitType('duration');
      }
    } else if (formData.next_visit_date) {
      setNextVisitType('date');
    } else {
      setNextVisitType('duration');
      setNextVisitValue('');
      setNextVisitUnit('Days');
    }
  }, [formData.next_visit_instructions, formData.next_visit_date]);

  React.useEffect(() => {
    const setQuillContent = (key, content) => {
      if (quillInstances.current[key] && content) {
        try {
          const currentContent = JSON.stringify(quillInstances.current[key].getContents().ops);
          if (currentContent !== content) {
            quillInstances.current[key].setContents(JSON.parse(content));
          }
        } catch { }
      } else if (quillInstances.current[key] && !content) {
        quillInstances.current[key].setContents([]);
      }
    }
    setQuillContent('usg_findings', formData.usg_findings);
    setQuillContent('lab_tests_imaging', formData.lab_tests_imaging);
  }, [formData.usg_findings, formData.lab_tests_imaging]);

  return (
    <div className="medical-card p-6 rounded-2xl space-y-4">
      <div>
        <label className="custom-label">Tests Requested</label>
        <textarea
          name="tests_requested"
          value={formData.tests_requested || ''}
          onChange={handleInputChange}
          className="custom-textarea"
          rows="2"
          placeholder="List any tests requested..."
        ></textarea>
      </div>

      <div>
        <label className="custom-label">Next Visit</label>
        <div className="flex items-center space-x-2">
          <input
            type="radio"
            name="nextVisitType"
            value="duration"
            checked={nextVisitType === 'duration'}
            onChange={() => { setNextVisitType('duration'); handleInputChange({ target: { name: 'next_visit_date', value: null } }); }}
            className="mr-1"
          />
          <input
            type="number"
            name="nextVisitValue"
            value={nextVisitValue}
            onChange={(e) => { setNextVisitValue(e.target.value); handleInputChange(e); }}
            className="form-input-themed w-20"
            placeholder="No of"
            disabled={nextVisitType !== 'duration'}
          />
          <select
            name="nextVisitUnit"
            value={nextVisitUnit}
            onChange={(e) => { setNextVisitUnit(e.target.value); handleInputChange(e); }}
            className="custom-select w-28"
            disabled={nextVisitType !== 'duration'}
          >
            <option>Days</option>
            <option>Weeks</option>
            <option>Months</option>
          </select>
          <span className="text-medical-gray">Or</span>
          <input
            type="radio"
            name="nextVisitType"
            value="date"
            checked={nextVisitType === 'date'}
            onChange={() => { setNextVisitType('date'); handleInputChange({ target: { name: 'next_visit_instructions', value: null } }); setNextVisitValue(''); setNextVisitUnit('Days'); }}
            className="ml-2 mr-1"
          />
          <input
            type="date"
            id="next-visit-date-picker"
            name="next_visit_date"
            value={formData.next_visit_date || ''}
            className="form-input-themed custom-datetime flex-grow"
            placeholder="Select date"
            disabled={nextVisitType !== 'date'}
          />
        </div>
      </div>

      <div>
        <label className="custom-label">Referred To</label>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-2 border p-3 rounded-lg bg-gray-50">
          <input type="text" name="referral_doctor_name" value={formData.referral_doctor_name || ''} onChange={handleInputChange} className="form-input-themed" placeholder="Doctor Name" />
          <input type="text" name="referral_speciality" value={formData.referral_speciality || ''} onChange={handleInputChange} className="form-input-themed" placeholder="Speciality" />
          <input type="tel" name="referral_phone" value={formData.referral_phone || ''} onChange={handleInputChange} className="form-input-themed" placeholder="Phone No" />
          <input type="email" name="referral_email" value={formData.referral_email || ''} onChange={handleInputChange} className="form-input-themed" placeholder="Email" />
        </div>
      </div>

      <div>
        <label className="custom-label">USG Findings</label>
        <div ref={usgFindingsRef} style={{ height: '100px' }}></div>
      </div>

      <div>
        <label className="custom-label">Lab Tests and Imaging</label>
        <div ref={labTestsRef} style={{ height: '100px' }}></div>
      </div>
    </div>
  );
};

export default InvestigationFollowUpForm;
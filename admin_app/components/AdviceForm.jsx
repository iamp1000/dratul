const AdviceForm = ({ adviceData, setAdviceData }) => {
  const adviceEditorRef = React.useRef(null);
  const quillInstance = React.useRef(null);

  React.useEffect(() => {
    const Quill = window.Quill;
    if (Quill && adviceEditorRef.current && !quillInstance.current) {
      if (adviceEditorRef.current.querySelector('.ql-editor')) return;

      const quill = new Quill(adviceEditorRef.current, {
        theme: 'snow',
        modules: {
          toolbar: [
            ['bold', 'italic', 'underline'],
            [{ 'list': 'ordered' }, { 'list': 'bullet' }]
          ]
        },
        placeholder: 'Enter advice for the patient...'
      });
      quill.on('text-change', () => {
        setAdviceData(prev => ({ ...prev, advice: JSON.stringify(quill.getContents().ops) }));
      });
      quillInstance.current = quill;
    }

    return () => {
      quillInstance.current?.off('text-change');
    };
  }, []);

  React.useEffect(() => {
    if (quillInstance.current && adviceData.advice) {
      try {
        const currentContent = JSON.stringify(quillInstance.current.getContents().ops);
        if (currentContent !== adviceData.advice) {
          quillInstance.current.setContents(JSON.parse(adviceData.advice));
        }
      } catch { }
    } else if (quillInstance.current && !adviceData.advice) {
      quillInstance.current.setContents([]);
    }
  }, [adviceData.advice]);

  return (
    <div className="medical-card p-6 rounded-2xl">
      <h3 className="text-lg font-semibold text-medical-dark mb-4 border-b pb-2">Advice</h3>
      <div ref={adviceEditorRef} style={{ height: '150px' }}></div>
    </div>
  );
};


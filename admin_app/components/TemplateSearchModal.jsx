const TemplateSearchModal = ({ onClose, onSelectTemplate }) => {
  const [searchTerm, setSearchTerm] = React.useState('');

  const filteredTemplates = (window.examinationTemplates || []).filter(t =>
    t.templateName.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 modal-overlay">
      <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full max-h-[90vh] overflow-hidden animate-bounce-gentle flex flex-col">
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-bold text-medical-dark">Select Examination Template</h2>
          <button onClick={onClose} className="text-medical-gray hover:text-medical-dark">
            <i className="fas fa-times text-lg"></i>
          </button>
        </div>
        <div className="p-4">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search templates..."
            className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-medical-accent focus:border-transparent"
            autoFocus
          />
        </div>
        <div className="flex-grow overflow-y-auto scroll-custom p-4 space-y-2">
          {filteredTemplates.map(template => (
            <button
              key={template.templateName}
              onClick={() => onSelectTemplate(template)}
              className="w-full text-left p-4 bg-gray-50 hover:bg-medical-light border border-gray-200 hover:border-medical-accent rounded-lg transition-all"
            >
              <span className="font-semibold text-medical-dark">{template.templateName}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TemplateSearchModal;
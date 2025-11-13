const InvestigationSelectModal = ({ isOpen, onClose, onConfirm }) => {
  const [activeTab, setActiveTab] = React.useState('common');
  const [commonTests, setCommonTests] = React.useState([]);
  const [additionalTests, setAdditionalTests] = React.useState([]);
  const [searchTerm, setSearchTerm] = React.useState('');
  const [selectedTests, setSelectedTests] = React.useState([]);

  React.useEffect(() => {
    if (isOpen) {
      fetch("./static/investigations_dictionary.json")
        .then(res => res.json())
        .then(data => setCommonTests(data))
        .catch(err => console.error("Failed to load common tests:", err));

      fetch("./static/additional_tests_db.json")
        .then(res => res.json())
        .then(data => setAdditionalTests(data))
        .catch(err => console.error("Failed to load additional tests:", err));
    }
  }, [isOpen]);

  const filteredAdditionalTests = React.useMemo(() => {
    if (!searchTerm) return additionalTests;
    const lowerSearch = searchTerm.toLowerCase();
    return additionalTests.filter(test => 
      test.toLowerCase().includes(lowerSearch)
    );
  }, [searchTerm, additionalTests]);

  const handleToggleTest = (testName) => {
    setSelectedTests(prev => {
      if (prev.includes(testName)) {
        return prev.filter(t => t !== testName);
      } else {
        return [...prev, testName];
      }
    });
  };

  const handleConfirm = () => {
    onConfirm(selectedTests);
    setSelectedTests([]);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center modal-overlay" onClick={onClose}>
      <div 
        className="medical-card rounded-2xl shadow-2xl w-full max-w-3xl max-h-[80vh] overflow-hidden flex flex-col animate-bounce-gentle"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-4 border-b border-gray-200 flex-shrink-0">
          <h2 className="text-xl font-bold text-medical-dark font-primary">Investigations</h2>
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-medical-gray">Auto Calculate</span>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" value="" className="sr-only peer" defaultChecked />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-medical-accent"></div>
              </label>
            </div>
            <button onClick={onClose} className="text-medical-gray hover:text-medical-dark">
              <i className="fas fa-times text-xl"></i>
            </button>
          </div>
        </div>

        <div className="p-4 border-b border-gray-200 flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
              <button 
                onClick={() => setActiveTab('common')}
                className={`px-6 py-2 rounded-md font-medium text-sm ${activeTab === 'common' ? 'bg-white shadow text-medical-accent' : 'text-medical-gray'}`}
              >
                Common Tests
              </button>
              <button 
                onClick={() => setActiveTab('additional')}
                className={`px-6 py-2 rounded-md font-medium text-sm ${activeTab === 'additional' ? 'bg-white shadow text-medical-accent' : 'text-medical-gray'}`}
              >
                Additional Tests
              </button>
            </div>
            <button className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm text-medical-dark font-medium hover:bg-gray-100 flex items-center">
              <i className="fas fa-calendar-alt mr-2 text-medical-accent"></i> Date
            </button>
          </div>
          {activeTab === 'additional' && (
            <div className="relative mt-4">
              <input 
                type="text" 
                placeholder="Search test name..." 
                className="form-input-themed pl-10 py-2 w-full"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)} 
              />
              <i className="fas fa-search absolute left-3 top-1/2 transform -translate-y-1/2 text-medical-gray"></i>
            </div>
          )}
        </div>

        <div className="p-4 overflow-y-auto scroll-custom flex-grow bg-gray-50">
          {activeTab === 'common' && (
            <div className="space-y-2">
              {commonTests.map((group, i) => (
                <details key={i} className="bg-white border border-gray-200 rounded-lg">
                  <summary className="font-semibold text-medical-dark cursor-pointer p-3 flex justify-between items-center">
                    {group.category}
                    <i className="fas fa-chevron-down transform transition-transform group-open:rotate-180"></i>
                  </summary>
                  <div className="p-3 border-t border-gray-100 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                    {group.tests.map((test, idx) => (
                      <label key={idx} className="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-100 cursor-pointer">
                        <input 
                          type="checkbox" 
                          className="w-4 h-4 text-medical-accent rounded focus:ring-medical-accent"
                          checked={selectedTests.includes(test.name)}
                          onChange={() => handleToggleTest(test.name)}
                        />
                        <span className="text-sm text-medical-dark">{test.name}</span>
                      </label>
                    ))}
                  </div>
                </details>
              ))}
            </div>
          )}
          {activeTab === 'additional' && (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {filteredAdditionalTests.map((testName, idx) => (
                <label key={idx} className="flex items-center space-x-2 p-2 rounded-lg bg-white border border-gray-200 hover:bg-gray-100 cursor-pointer">
                  <input 
                    type="checkbox" 
                    className="w-4 h-4 text-medical-accent rounded focus:ring-medical-accent"
                    checked={selectedTests.includes(testName)}
                    onChange={() => handleToggleTest(testName)}
                  />
                  <span className="text-sm text-medical-dark">{testName}</span>
                </label>
              ))}
              {filteredAdditionalTests.length === 0 && (
                <p className="text-medical-gray col-span-full text-center p-4">No tests found for "{searchTerm}"</p>
              )}
            </div>
          )}
        </div>

        <div className="p-4 border-t border-gray-200 flex-shrink-0 flex justify-between items-center bg-white">
          <span className="text-sm font-medium text-medical-accent">
            {selectedTests.length} test{selectedTests.length !== 1 ? 's' : ''} selected
          </span>
          <button 
            onClick={handleConfirm}
            className="medical-button px-6 py-2 text-white rounded-lg font-secondary flex items-center gap-2 relative z-10"
            disabled={selectedTests.length === 0}
          >
            <i className="fas fa-plus"></i>
            <span>Add Selected Tests</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default InvestigationSelectModal;
const InvestigationResultsModal = ({ isOpen, onClose, onSave, initialResultsData }) => {
  const [activeTab, setActiveTab] = React.useState('common');
  const [commonTests, setCommonTests] = React.useState([]);
  const [additionalTests, setAdditionalTests] = React.useState([]);
  const [searchTerm, setSearchTerm] = React.useState('');
  const [resultsData, setResultsData] = React.useState(initialResultsData || {});
  const [isLoading, setIsLoading] = React.useState(true);

  React.useEffect(() => {
    if (isOpen) {
      setIsLoading(true);
      Promise.all([
        fetch("./static/investigations_dictionary.json").then(res => res.json()),
        fetch("./static/additional_tests_db.json").then(res => res.json())
      ]).then(([common, additional]) => {
        setCommonTests(common);
        setAdditionalTests(additional);
        setIsLoading(false);
      }).catch(err => {
        console.error("Failed to load test lists:", err);
        setIsLoading(false);
      });
    } else {
      setSearchTerm('');
      setActiveTab('common');
    }
  }, [isOpen]);

  const handleSave = () => {
    onSave(resultsData);
  };

  const filteredAdditionalTests = React.useMemo(() => {
    if (!searchTerm) return additionalTests;
    const lowerSearch = searchTerm.toLowerCase();
    return additionalTests.filter(test => 
      test.toLowerCase().includes(lowerSearch)
    );
  }, [searchTerm, additionalTests]);

  const renderCommonTests = () => (
    <InvestigationResultsContent 
      resultsData={resultsData} 
      setResultsData={setResultsData} 
      testDictionary={commonTests}
      isLoading={isLoading}
      searchTerm={searchTerm}
    />
  );

  const renderAdditionalTests = () => {
    if (isLoading) return <LoadingSpinner />;
    
    const adHocTestsInResults = Object.values(resultsData).flatMap(category => Object.keys(category))
      .filter(testName => 
        !commonTests.some(g => g.tests.some(t => t.name === testName)) && 
        !additionalTests.includes(testName)
      );

    const adHocTestGroup = {
      category: "OTHER TESTS",
      tests: [...new Set(adHocTestsInResults)].map((name, i) => ({ id: `adhoc-${i}`, name, unit: '', normal_range: '' }))
    };

    const additionalTestGroups = [
      {
        category: "ALL ADDITIONAL TESTS",
        tests: filteredAdditionalTests.map((name, i) => ({ id: i, name, unit: 'N/A', normal_range: 'N/A' }))
      }
    ];

    return (
      <InvestigationResultsContent 
        resultsData={resultsData} 
        setResultsData={setResultsData} 
        testDictionary={adHocTestGroup.tests.length > 0 ? additionalTestGroups.concat(adHocTestGroup) : additionalTestGroups}
        isLoading={isLoading}
        searchTerm={searchTerm}
      />
    );
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center modal-overlay" onClick={onClose}>
      <div 
        className="medical-card rounded-2xl shadow-2xl w-full max-w-4xl max-h-[80vh] overflow-hidden flex flex-col animate-bounce-gentle"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between p-4 border-b border-gray-200 flex-shrink-0">
          <h2 className="text-xl font-bold text-medical-dark font-primary flex items-center">
            <i className="fas fa-microscope text-medical-accent mr-3"></i>
            Investigation Results
          </h2>
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
          <div className="flex flex-col sm:flex-row items-center justify-between">
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
            <div className="flex items-center space-x-2 mt-3 sm:mt-0">
              <div className="relative">
                <input 
                  type="text" 
                  placeholder="Search test name..." 
                  className="form-input-themed pl-10 py-2 w-full sm:w-64"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)} 
                />
                <i className="fas fa-search absolute left-3 top-1/2 transform -translate-y-1/2 text-medical-gray"></i>
              </div>
              <button className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm text-medical-dark font-medium hover:bg-gray-100 flex items-center">
                <i className="fas fa-calendar-alt mr-2 text-medical-accent"></i> Date
              </button>
            </div>
          </div>
        </div>

        <div className="p-4 overflow-y-auto scroll-custom flex-grow bg-gray-50">
          {activeTab === 'common' ? renderCommonTests() : renderAdditionalTests()}
        </div>

        <div className="p-4 border-t border-gray-200 flex-shrink-0 flex justify-end items-center bg-white">
          <button 
            onClick={handleSave}
            className="medical-button px-6 py-2 text-white rounded-lg font-secondary flex items-center gap-2 relative z-10"
          >
            <i className="fas fa-save"></i>
            <span>Save Results</span>
          </button>
        </div>
      </div>
    </div>
  );
};


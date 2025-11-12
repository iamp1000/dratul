const InvestigationResultsContent = ({ resultsData, setResultsData, testDictionary, isLoading, searchTerm }) => {
  const handleChange = (category, testName, value) => {
    setResultsData(prev => ({
      ...prev,
      [category]: {
        ...(prev[category] || {}),
        [testName]: value
      }
    }));
  };

  const getResultStatus = (value, normalRange) => {
    try {
      const val = parseFloat(value);
      if (isNaN(val)) return 'text-medical-dark'; 
      const [low, high] = normalRange.split('-').map(Number);
      if (!isNaN(low) && !isNaN(high)) {
        if (val < low || val > high) return 'text-red-500 font-bold';
      }
    } catch {}
    return 'text-medical-dark'; 
  };

  return (
    <div className="w-full space-y-3">
      {isLoading && <LoadingSpinner />}
      {!isLoading && testDictionary
        .map(group => ({
          ...group,
          tests: group.tests.filter(test => 
            !searchTerm || test.name.toLowerCase().includes(searchTerm.toLowerCase())
          )
        }))
        .filter(group => group.tests.length > 0)
        .map((group, i) => (
        <details key={i} className="mb-2 bg-white border border-gray-200 rounded-lg open:shadow-md transition-shadow">
          <summary className="font-semibold text-medical-dark cursor-pointer p-4 text-base flex justify-between items-center">
            {group.category}
            <i className="fas fa-chevron-down transform transition-transform group-open:rotate-180"></i>
          </summary>
          <div className="pt-0 p-4 border-t border-gray-100 grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-x-4 gap-y-4 text-sm text-medical-dark">
            <span className="md:col-span-2 font-semibold text-medical-gray text-xs uppercase">Test/Investigations</span>
            <span className="font-semibold text-medical-gray text-xs uppercase">Result</span>
            <span className="font-semibold text-medical-gray text-xs uppercase">Units (Normal Range)</span>
            {group.tests.map((t, idx) => (
              <React.Fragment key={idx}>
                <span className="md:col-span-2 font-medium self-center text-medical-dark">{t.name}</span>
                <input
                  type="text"
                  className={`form-input-themed py-2 px-2 text-sm ${getResultStatus(resultsData[group.category]?.[t.name], t.normal_range)}`}
                  placeholder="Value..."
                  value={resultsData[group.category]?.[t.name] || ""}
                  onChange={(e) =>
                    handleChange(group.category, t.name, e.target.value)
                  }
                  disabled={t.calculated}
                />
                <span className="text-medical-gray text-xs self-center">
                  {t.unit} {t.normal_range && `(${t.normal_range})`}
                </span>
              </React.Fragment>
            ))}
          </div>
        </details>
        ))}
      {!isLoading && testDictionary.length === 0 && (
        <p className="text-medical-gray text-center p-4">No test results to display.</p>
      )}
    </div>
  );
};


import React from 'react';

const VisitPadView = ({ patient, onBack, mode = "consultation" }) => {

    const [activeTab, setActiveTab] = React.useState('vitals');
    const [isInvestigationModalOpen, setIsInvestigationModalOpen] = React.useState(false);
    const [isResultsModalOpen, setIsResultsModalOpen] = React.useState(false);
    const [isSaving, setIsSaving] = React.useState(false);
    const [lastSaved, setLastSaved] = React.useState(null);
    const [specialtyConfig, setSpecialtyConfig] = React.useState(null);
    const [templateName, setTemplateName] = React.useState('');
    
    React.useEffect(() => {
        if (mode !== 'consultation' || !patient || !patient.id) return;

        const fetchHistory = async () => {
            try {
                // 1. Fetch Patient History
                const historyData = await api(`/api/v1/patients/${patient.id}/history`);
                
                // 2. Update formData state
                setFormData(prev => ({
                    ...prev,
                    history: {
                        id: historyData.id, // Store ID for PUT request
                        detailed_history: historyData.detailed_history || '',
                        allergies: historyData.allergies || '',
                        currentMedications: historyData.current_medications || '' // Note: schema alias is currentMedications, but the response key might be current_medications
                    }
                }));

                // 3. Load Quill Content
                if (historyEditorRef.current) {
                    const Quill = window.Quill;
                    if (Quill && historyData.detailed_history) {
                        // Always prefer setting content via innerHTML for Quill, as it handles both plain text and HTML
                        historyEditorRef.current.root.innerHTML = historyData.detailed_history;
                    } else if (Quill) {
                        // Clear editor for new entry
                        historyEditorRef.current.setText('');
                    }
                }
            } catch (error) {
                console.error('Failed to load patient history:', error);
                // Keep empty state if load fails
            }
        };

        fetchHistory();

    }, [patient, mode]); // Re-run when patient changes or mode changes
    // --- END: Load Patient History on Mount/Patient Change ---

    React.useEffect(() => {
        const fetchConfig = async () => {
            try {
                const res = await fetch('./endocrinology.json');
                if (!res.ok) throw new Error('Failed to load specialty config');
                const data = await res.json();
                setSpecialtyConfig(data);
            } catch (err) {
                console.error("Error loading specialty config:", err.message);
            }
        };
        fetchConfig();
    }, []);

    // --- NEW: State for dynamic vitals ---
    const [visibleVitals, setVisibleVitals] = React.useState({});
    const [showVitalsDropdown, setShowVitalsDropdown] = React.useState(false);
    const vitalButtonRef = React.useRef(null);
    const vitalDropdownRef = React.useRef(null);

    React.useEffect(() => {
        const handleClickOutside = (event) => {
            if (
                vitalButtonRef.current && !vitalButtonRef.current.contains(event.target) &&
                vitalDropdownRef.current && !vitalDropdownRef.current.contains(event.target)
            ) {
                setShowVitalsDropdown(false);
            }
        };

        if (showVitalsDropdown) {
            document.addEventListener('mousedown', handleClickOutside);
        } else {
            document.removeEventListener('mousedown', handleClickOutside);
        }

        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [showVitalsDropdown]);

    // Master configuration for all vitals
    const vitalsConfig = {
        // Core Vitals (Always Show)
        bp: { label: 'Blood Pressure (mmHg)', icon: 'fas fa-tachometer-alt text-red-500' },
        pulse: { label: 'Pulse (bpm)', icon: 'fas fa-heart text-pink-500' },
        height: { label: 'Height (cm)', icon: 'fas fa-arrows-alt-v text-blue-500' },
        weight: { label: 'Weight (kg)', icon: 'fas fa-weight text-purple-500' },
        temp: { label: 'Temperature (°F)', icon: 'fas fa-thermometer-half text-orange-500' },
        spo2: { label: 'SPO2 (%)', icon: 'fas fa-lungs text-cyan-500' },
        resp_rate: { label: 'Resp. Rate (/min)', icon: 'fas fa-wind text-teal-500' },
        bmi: { label: 'BMI', icon: 'fas fa-calculator text-indigo-500' },
        // Optional Vitals (Add on demand)
        waist: { label: 'Waist (cm)', icon: 'fas fa-ruler-horizontal text-gray-500', group: 'measurements' },
        hip: { label: 'Hip (cm)', icon: 'fas fa-ruler-combined text-gray-500', group: 'measurements' },
        waist_hip_ratio: { label: 'Waist/Hip Ratio', icon: 'fas fa-calculator text-indigo-500', group: 'measurements', readOnly: true, placeholder: 'Auto-calculated' },
        lmp: { label: 'LMP', icon: 'fas fa-calendar-alt text-pink-500', group: 'obgyn', type: 'date' },
        edd: { label: 'EDD', icon: 'fas fa-baby text-blue-500', group: 'obgyn', type: 'date' },
        gestational_age: { label: 'Gestational Age', icon: 'fas fa-hourglass-half text-purple-500', group: 'obgyn', type: 'gestational' },
    };

    const toggleVital = (key) => {
        setVisibleVitals(prev => ({
            ...prev,
            [key]: !prev[key]
        }));
        setShowVitalsDropdown(false); // Close dropdown after selection
    };

    const getAvailableVitals = () => {
        return Object.keys(vitalsConfig).filter(key =>
            vitalsConfig[key].group && !visibleVitals[key]
        );
    };





    // --- END: State for dynamic vitals ---
    const [formData, setFormData] = React.useState({
        vitals: {
            bp_systolic: '',
            bp_diastolic: '',
            pulse: '',
            height: '',
            weight: '',
            temp: '',
            spo2: '',
            bmi: '',
            respiratoryRate: ''
        },
        complaints: [],
        diagnosis: [],
        history: {
            detailed_history: '', // Used for Past Surgeries, Major Injuries, Infectious Diseases
            chronic_illnesses: '', // For Chronic illnesses
            family_history_narrative: '', // For Family History
            lifestyle_habits: 'none', // Smoking, alcohol, diet
            social_factors: '', // Living situation, stressors
            allergies: (mode === 'consultation' && patient.medicalHistory?.allergies?.join(', ')) || '',
            currentMedications: (mode === 'consultation' && patient.medicalHistory?.currentMedications?.join(', ')) || ''
        },
        examination_fields: [], // Changed to array for dynamic sections
        investigationResults: {},
        investigations: [],
        prescriptions: [],
        advice: '',
        followUp: '',
        nextVisitDate: '',
            referral_doctor_name: '',
            referral_speciality: '',
            referral_phone: '',
            referral_email: ''
    });
    const examinationEditorRefs = React.useRef({});
    const adviceEditorRef = React.useRef(null);
    const historyEditorRef = React.useRef(null);
    React.useEffect(() => {
        if (typeof Quill !== 'undefined') {
            const toolbarOptions = [
                ['bold', 'italic', 'underline'],
                [{ 'list': 'ordered' }, { 'list': 'bullet' }],
                [{ 'header': [1, 2, 3, false] }],
                ['clean']
            ];

            // Initialize static editors (Advice and History)
            if (!adviceEditorRef.current) {
                adviceEditorRef.current = new Quill('#advice-editor', {
                    theme: 'snow',
                    placeholder: 'Enter advice, diet recommendations, lifestyle modifications...',
                    modules: { toolbar: toolbarOptions }
                });
                // Add listener to update formData
                adviceEditorRef.current.on('text-change', () => {
                    setFormData(prev => ({ ...prev, advice: adviceEditorRef.current.root.innerHTML }));
                });
            }
            if (!historyEditorRef.current) {
                historyEditorRef.current = new Quill('#history-editor', {
                    theme: 'snow',
                    placeholder: 'Enter detailed medical history...',
                    modules: { toolbar: toolbarOptions }
                });
                // Add listener to update formData
                historyEditorRef.current.on('text-change', () => {
                    setFormData(prev => ({ ...prev, history: { ...prev.history, detailed_history: historyEditorRef.current.root.innerHTML } }));
                });
            }

            // Initialize DYNAMIC examination editors based on specialty config
            if (specialtyConfig && specialtyConfig.custom_examination_fields) {
                // Clear any old refs
                examinationEditorRefs.current = {};

                specialtyConfig.custom_examination_fields.forEach(fieldName => {
                    // Create a safe ID from the field name
                    const safeId = fieldName.replace(/[^a-zA-Z0-9]/g, '-');
                    const editorId = `#exam-field-${safeId}`;
                    const element = document.querySelector(editorId);

                    // Check if element exists AND is not already initialized
                    if (element && !element.classList.contains('ql-container')) {
                        const quill = new Quill(element, {
                            theme: 'snow',
                            placeholder: `Enter ${fieldName} findings...`,
                            modules: { toolbar: toolbarOptions }
                        });

                        quill.on('text-change', () => {
                            setFormData(prev => ({
                                ...prev,
                                examination_fields: {
                                    ...prev.examination_fields,
                                    [fieldName]: quill.root.innerHTML
                                }
                            }));
                        });

                        // Store the instance in our refs object
                        examinationEditorRefs.current[fieldName] = quill;
                    }
                });
            }
        }
    }, [specialtyConfig]); // Re-run this effect when specialtyConfig loads
    React.useEffect(() => {
        const autoSaveInterval = setInterval(() => {
            handleAutoSave();
        }, 30000);

        return () => clearInterval(autoSaveInterval);
    }, [formData]);

    // ============================================================================
    // HANDLERS
    // ============================================================================

    const handleVitalsChange = (field, value) => {
        setFormData(prev => {
            const newData = { ...prev.vitals, [field]: value };

            // --- CONSOLIDATED CALCULATIONS ---

            // 1. Auto-calculate BMI
            const height = (field === 'height') ? parseFloat(value) : parseFloat(newData.height);
            const weight = (field === 'weight') ? parseFloat(value) : parseFloat(newData.weight);
            if (height > 0 && weight > 0) {
                const heightInMeters = height / 100;
                newData.bmi = (weight / (heightInMeters * heightInMeters)).toFixed(1);
            } else {
                newData.bmi = '';
            }

            // 2. Auto-calculate Waist/Hip Ratio
            const waistCm = (field === 'waist') ? parseFloat(value) : parseFloat(newData.waist);
            const hipCm = (field === 'hip') ? parseFloat(value) : parseFloat(newData.hip);
            if (waistCm > 0 && hipCm > 0) {
                newData.waist_hip_ratio = (waistCm / hipCm).toFixed(2);
            } else {
                newData.waist_hip_ratio = '';
            }

            return { ...prev, vitals: newData };
        });
    };

    const addComplaint = () => {
        setFormData(prev => ({
            ...prev,
            complaints: [...prev.complaints, {
                complaint: '',
                duration: '',
                severity: 'moderate'
            }]
        }));
    };

    const updateComplaint = (index, field, value) => {
        setFormData(prev => ({
            ...prev,
            complaints: prev.complaints.map((item, i) =>
                i === index ? { ...item, [field]: value } : item
            )
        }));
    };

    const removeComplaint = (index) => {
        setFormData(prev => ({
            ...prev,
            complaints: prev.complaints.filter((_, i) => i !== index)
        }));
    };

    const addDiagnosis = () => {
        setFormData(prev => ({
            ...prev,
            diagnosis: [...prev.diagnosis, {
                code: '',
                description: '',
                type: 'provisional',
                notes: ''
            }]
        }));
    };

    const updateDiagnosis = (index, field, value) => {
        setFormData(prev => ({
            ...prev,
            diagnosis: prev.diagnosis.map((item, i) =>
                i === index ? { ...item, [field]: value } : item
            )
        }));
    };

    const removeDiagnosis = (index) => {
        setFormData(prev => ({
            ...prev,
            diagnosis: prev.diagnosis.filter((_, i) => i !== index)
        }));
    };

    const addInvestigation = (testName = '') => {
        setFormData(prev => ({
            ...prev,
            investigations: [...prev.investigations, {
                testName: testName,
                category: '',
                urgency: 'routine',
                notes: ''
            }]
        }));
    };

    const updateInvestigation = (index, field, value) => {
        setFormData(prev => ({
            ...prev,
            investigations: prev.investigations.map((item, i) =>
                i === index ? { ...item, [field]: value } : item
            )
        }));
    };

    const removeInvestigation = (index) => {
        setFormData(prev => ({
            ...prev,
            investigations: prev.investigations.filter((_, i) => i !== index)
        }));
    };

    const addPrescription = () => {
        setFormData(prev => ({
            ...prev,
            prescriptions: [...prev.prescriptions, {
                medicine: '',
                type: 'branded', // branded or generic
                dosage: '',
                frequency: '',
                duration: '',
                instructions: '',
                route: 'oral'
            }]
        }));
    };

    const updatePrescription = (index, field, value) => {
        setFormData(prev => ({
            ...prev,
            prescriptions: prev.prescriptions.map((item, i) =>
                i === index ? { ...item, [field]: value } : item
            )
        }));
    };

    const removePrescription = (index) => {
        setFormData(prev => ({
            ...prev,
            prescriptions: prev.prescriptions.filter((_, i) => i !== index)
        }));
    };

    const handleAutoSave = () => {
        // In production: Save to backend
        console.log('Auto-saving...', formData);
        setLastSaved(new Date());
    };

    const handleSaveAndPrint = async () => {
        setIsSaving(true);

        // --- NEW: Step 1: Save Medical History (POST/PUT) ---
        if (mode === 'consultation' && patient.id) {
            try {
                const historyPayload = {
                    id: formData.history.id,
                    allergies: formData.history.allergies,
                    currentMedications: formData.history.currentMedications,
                    detailed_history: historyEditorRef.current?.root.innerHTML || ''
                };
                
                const savedHistory = await api(`/api/v1/patients/${patient.id}/history`, {
                    method: 'POST', // POST handles create or update via crud.create_or_update_patient_history
                    body: JSON.stringify(historyPayload),
                });
                
                console.log('Medical History Saved/Updated:', savedHistory);
                // Update state with confirmed ID
                setFormData(prev => ({ ...prev, history: { ...prev.history, id: savedHistory.id } }));

            } catch (error) {
                alert('Error saving Medical History. Aborting consultation save.');
                console.error('Error saving Medical History:', error);
                setIsSaving(false);
                return; // ABORT
            }
        }
        // --- END NEW: Step 1: Save Medical History ---

        // --- Step 2: Collect and Structure Consultation Data ---
        const consultationPayload = {
            patient_id: patient.id,
            appointment_id: patient.appointment_id, // Passed from ConsultationView queue
            consultation_date: new Date().toISOString(),
            
            // Main Text Fields
            advice: adviceEditorRef.current?.root.innerHTML || '',
            quick_notes: formData.history.detailed_history, // Using detailed history as quick notes
            
            // Vitals (Mapping directly)
            vitals: { 
                ...formData.vitals,
                temperature: formData.vitals.temp // Frontend uses 'temp', backend uses 'temperature'
            },
            
            // Diagnoses (Mapping list of {code, description} to list of {diagnosis_name})
            diagnoses: formData.diagnosis.map(d => ({
                diagnosis_name: d.description || d.code || 'Unspecified Diagnosis'
            })),
            
            // Medications (Mapping list of prescriptions to list of ConsultationMedicationCreate)
            medications: formData.prescriptions.map(p => ({
                type: p.type, // branded/generic
                medicine_name: p.medicine,
                dosage: p.dosage,
                when: p.when,
                frequency: p.frequency,
                duration: p.duration,
                notes: p.instructions,
                route: p.route
            })),
            
            // Follow-up/Referral Fields
            next_visit_date: formData.nextVisitDate || null,
            next_visit_instructions: formData.nextVisitInstructions || null,
            referral_doctor_name: formData.referral_doctor_name,
            referral_speciality: formData.referral_speciality,
            referral_phone: formData.referral_phone,
            referral_email: formData.referral_email
        };

        try {
            console.log('Final Consultation Payload:', consultationPayload);
            
            // --- Step 3: API Call to Save Consultation ---
            const savedConsultation = await window.api('/api/v1/consultations/', {
                method: 'POST',
                body: JSON.stringify(consultationPayload),
            });

            console.log('Consultation Saved:', savedConsultation);

            alert('Consultation saved successfully! Ready to print.');
            setLastSaved(new Date());
        } catch (error) {
            console.error('Error saving consultation:', error);
            alert(`Error saving data. Details: ${error.message || 'An unexpected error occurred.'}`);
        } finally {
            setIsSaving(false);
        }
    };

    const handleSaveTemplate = async () => { // <-- Make async
        if (!templateName) {
            alert('Please enter a name for the template.');
            return;
        }
    
        // Gather all template data
        const templateData = {
            templateName: templateName,
            vitals: formData.vitals,
            complaints: formData.complaints,
            diagnosis: formData.diagnosis,
            history: formData.history,
            examination_fields: formData.examination_fields,
            investigations: formData.investigations,
            prescriptions: formData.prescriptions,
            advice: adviceEditorRef.current?.root.innerHTML || '',
        };
    
        // --- NEW: API call to save the template ---
        try {
           await api('/api/v1/templates', { 
               method: 'POST', 
               body: JSON.stringify(templateData) 
           });
           toast('Template saved successfully!');
           onBack(); // Go back to list
        } catch (err) {
           alert('Failed to save template: ' + err.message);
           console.error('Save template error:', err);
        }
        // --- END NEW ---
    };

    const handleEndConsultation = () => {
        if (confirm('Are you sure you want to end this consultation?')) {
            handleSaveAndPrint();
            // Navigate back to list after a short delay
            setTimeout(() => onBack(), 1500);
        }
    };

    // ============================================================================
    // RENDER
    // ============================================================================

    return (
        <div className="h-full flex flex-col bg-white rounded-xl shadow-lg overflow-hidden">
            {/* Header */}
            <div className="bg-gradient-to-r from-medical-blue via-[#1565C0] to-medical-accent p-4 text-white shadow-lg">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <button
                            onClick={onBack}
                            className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                            title={mode === 'template' ? 'Back to Templates' : 'Back to patient list'}
                        >
                            <i className="fas fa-arrow-left text-xl"></i>
                        </button>
                        {mode === 'consultation' && patient && (
                            <div className="flex items-center gap-3">
                                <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center text-2xl font-bold border-2 border-white/30">
                                    {patient.name.charAt(0)}
                                </div>
                                <div>
                                    <h2 className="text-xl font-bold flex items-center gap-2">
                                        {patient.name}
                                        {patient.medicalHistory?.allergies?.length > 0 && (
                                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold bg-red-500 text-white">
                                                <i className="fas fa-exclamation-triangle mr-1"></i>
                                                Allergies
                                            </span>
                                        )}
                                    </h2>
                                    <p className="text-sm text-blue-100">
                                        ID: {patient.id} | {patient.age}Y/{patient.gender} | {patient.phone}
                                    </p>
                                </div>
                            </div>
                        )}
                        {mode === 'template' && (
                            <div className="flex items-center gap-3">
                                <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center text-2xl font-bold border-2 border-white/30">
                                    <i className="fas fa-file-medical-alt"></i>
                                </div>
                                <div>
                                    <h2 className="text-xl font-bold">Template Editor</h2>
                                    <p className="text-sm text-blue-100">Creating a new consultation template</p>
                                </div>
                            </div>
                        )}
                    </div>
                    <div className="flex gap-2 items-center">
                        {mode === 'consultation' && lastSaved && (
                            <span className="text-xs text-blue-100 mr-2">
                                <i className="fas fa-check-circle mr-1"></i>
                                Last saved: {lastSaved.toLocaleTimeString()}
                            </span>
                        )}
                        {mode === 'consultation' && (
                            <>
                                <button
                                    onClick={handleSaveAndPrint}
                                    disabled={isSaving}
                                    className="px-4 py-2 bg-white text-medical-blue hover:bg-blue-50 rounded-lg flex items-center gap-2 transition-all font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {isSaving ? (
                                        <><i className="fas fa-spinner fa-spin"></i> Saving...</>
                                    ) : (
                                        <><i className="fas fa-save"></i> Save & Print</>
                                    )}
                                </button>
                                <button
                                    onClick={handleEndConsultation}
                                    className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg flex items-center gap-2 transition-colors font-semibold"
                                >
                                    <i className="fas fa-check-double"></i>
                                    End Consultation
                                </button>
                            </>
                        )}
                        {mode === 'template' && (
                            <button
                                type="button"
                                onClick={handleSaveTemplate}
                                className="px-4 py-2 bg-white text-medical-blue hover:bg-blue-50 rounded-lg flex items-center gap-2 transition-all font-semibold"
                            >
                                <i className="fas fa-save"></i>
                                Save Template
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {/* Main Content Area */}
            <div className="flex-1 overflow-y-auto p-6 bg-gradient-to-br from-gray-50 to-blue-50/30">
                <div className="max-w-7xl mx-auto space-y-6">

                    {/* --- NEW: Template Name Input (Template Mode Only) --- */}
                    {mode === 'template' && (
                        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                            <h3 className="text-lg font-bold text-medical-dark mb-4 pb-3 border-b-2 border-gray-100">
                                Template Details
                            </h3>
                            <div>
                                <label className="block text-sm font-semibold text-gray-700 mb-2">Template Name</label>
                                <input
                                    type="text"
                                    placeholder="e.g., Diabetes Follow-up, First Gynae Visit"
                                    className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-medical-accent focus:border-transparent"
                                    value={templateName}
                                    onChange={(e) => setTemplateName(e.target.value)}
                                />
                            </div>
                        </div>
                    )}

                    {/* --- NEW: Patient Info Section (Hidden in template mode) --- */}
                    {mode === 'consultation' && patient && (
                        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
                            <h3 className="text-lg font-bold text-medical-dark mb-4 flex items-center gap-2 pb-3 border-b-2 border-gray-100">
                                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center">
                                    <i className="fas fa-user-circle text-white"></i>
                                </div>
                                <span>Personal Information</span>
                            </h3>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-x-6 gap-y-4 text-sm">
                                <div>
                                    <label className="block text-xs font-semibold text-gray-500 mb-1">Full Name</label>
                                    <p className="text-gray-900 font-medium">{`${patient.first_name || ''} ${patient.last_name || ''}`}</p>
                                </div>
                                <div>
                                    <label className="block text-xs font-semibold text-gray-500 mb-1">Patient ID</label>
                                    <p className="text-gray-900 font-medium">#{patient.id}</p>
                                </div>
                                <div>
                                    <label className="block text-xs font-semibold text-gray-500 mb-1">Phone Number</label>
                                    <p className="text-gray-900 font-medium">{patient.phone_number || 'N/A'}</p>
                                </div>
                                <div>
                                    <label className="block text-xs font-semibold text-gray-500 mb-1">Email</label>
                                    <p className="text-gray-900 font-medium">{patient.email || 'N/A'}</p>
                                </div>
                                <div>
                                    <label className="block text-xs font-semibold text-gray-500 mb-1">Date of Birth</label>
                                    <p className="text-gray-900 font-medium">{patient.date_of_birth ? new Date(patient.date_of_birth).toLocaleDateString() : 'N/A'}</p>
                                </div>
                                <div>
                                    <label className="block text-xs font-semibold text-gray-500 mb-1">Gender</label>
                                    <p className="text-gray-900 font-medium">{patient.gender || 'N/A'}</p>
                                </div>
                                <div>
                                    <label className="block text-xs font-semibold text-gray-500 mb-1">City</label>
                                    <p className="text-gray-900 font-medium">{patient.city || 'N/A'}</p>
                                </div>
                            </div>
                        </div>
                    )}
                    {/* --- END: Patient Info Section --- */}

                    {/* Vitals Section */}
                    <div className="bg-white p-6 rounded-xl border border-blue-100 shadow-sm hover:shadow-md transition-shadow">
                        <div className="flex items-center justify-between pb-3 border-b-2 border-blue-100">
                            <h3 className="text-lg font-bold text-medical-dark flex items-center gap-2">
                                <div className="w-10 h-10 bg-gradient-to-br from-red-500 to-pink-500 rounded-lg flex items-center justify-center">
                                    <i className="fas fa-heartbeat text-white"></i>
                                </div>
                                <span>Vitals</span>
                            </h3>

                            {/* --- NEW: Dynamic Vitals Button --- */}
                            <div className="relative">
                                <button
                                    ref={vitalButtonRef}
                                    onClick={() => setShowVitalsDropdown(!showVitalsDropdown)}
                                    className="px-4 py-2 bg-medical-light text-medical-blue rounded-lg font-semibold hover:bg-blue-100 transition-all text-sm flex items-center gap-2"
                                >
                                    <i className="fas fa-plus"></i>
                                    Add Vital
                                </button>
                                {showVitalsDropdown && (
                                    <div ref={vitalDropdownRef} className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-xl z-20 border border-gray-200">
                                        {getAvailableVitals().length > 0 ? (
                                            getAvailableVitals().map(key => (
                                                <button
                                                    key={key}
                                                    onClick={() => toggleVital(key)}
                                                    className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
                                                >
                                                    <i className={`${vitalsConfig[key].icon} w-4`}></i>
                                                    <span>{vitalsConfig[key].label}</span>
                                                </button>
                                            ))
                                        ) : (
                                            <span className="block px-4 py-2 text-sm text-gray-400">All vitals added</span>
                                        )}
                                    </div>
                                )}
                            </div>
                            {/* --- END: Dynamic Vitals Button --- */}
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-4">
                            {Object.entries(vitalsConfig).map(([key, config]) => {
                                const isVisible = !config.group || visibleVitals[key];
                                if (!isVisible) return null;

                                // Handle special BP input
                                if (key === 'bp') {
                                    return (
                                        <div key={key} className="md:col-span-1">
                                            <label className="block text-sm font-semibold text-gray-700 mb-2">
                                                <i className={config.icon + " mr-1"}></i>{config.label}
                                            </label>
                                            <div className="flex gap-2">
                                                <input type="number" placeholder="Sys" className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-red-400 focus:border-transparent transition-all" value={formData.vitals.bp_systolic || ''} onChange={(e) => handleVitalsChange('bp_systolic', e.target.value)} />
                                                <span className="text-gray-400 self-center">/</span>
                                                <input type="number" placeholder="Dia" className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-red-400 focus:border-transparent transition-all" value={formData.vitals.bp_diastolic || ''} onChange={(e) => handleVitalsChange('bp_diastolic', e.target.value)} />
                                            </div>
                                        </div>
                                    );
                                }

                                // Handle special Gestational Age input
                                if (key === 'gestational_age') {
                                    return (
                                        <div key={key} className="md:col-span-2 lg:col-span-1">
                                            <label className="block text-sm font-semibold text-gray-700 mb-2"><i className={config.icon + " mr-1"}></i>{config.label}</label>
                                            <div className="flex gap-2">
                                                <input type="number" placeholder="Weeks" className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-400 focus:border-transparent transition-all" value={formData.vitals.gestational_age_weeks || ''} onChange={(e) => handleVitalsChange('gestational_age_weeks', e.target.value)} />
                                                <input type="number" placeholder="Days" className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-purple-400 focus:border-transparent transition-all" value={formData.vitals.gestational_age_days || ''} onChange={(e) => handleVitalsChange('gestational_age_days', e.target.value)} />
                                            </div>
                                        </div>
                                    );
                                }

                                // Default input rendering
                                return (
                                    <div key={key} className={key === 'bmi' || key === 'waist_hip_ratio' ? 'lg:col-span-1' : ''}>
                                        <label className="block text-sm font-semibold text-gray-700 mb-2">
                                            <i className={config.icon + " mr-1"}></i>{config.label}
                                        </label>
                                        <input
                                            type={config.type === 'date' ? 'date' : 'number'}
                                            step={key === 'temp' || key === 'height' || key === 'weight' || key === 'waist' || key === 'hip' ? "0.1" : key === 'bmi' || key === 'waist_hip_ratio' ? "0.01" : "1"}
                                            placeholder={config.readOnly ? config.placeholder : `e.g., ${key === 'pulse' ? '72' : key === 'height' ? '170' : '98'}`}
                                            className={`w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-${config.icon.split(' ')[2].split('-')[0]}-400 focus:border-transparent transition-all ${config.readOnly ? 'bg-gray-50 font-semibold' : ''}`}
                                            value={formData.vitals[key] || ''}
                                            onChange={config.readOnly ? undefined : (e) => handleVitalsChange(key, e.target.value)}
                                            readOnly={config.readOnly}
                                        />
                                    </div>
                                );
                            })}
                        </div>
                    </div>

                    {/* Medical History Section */}
                    <div className="bg-white p-6 rounded-xl border border-amber-100 shadow-sm hover:shadow-md transition-shadow">
                        <h3 className="text-lg font-bold text-medical-dark mb-4 flex items-center gap-2 pb-3 border-b-2 border-amber-100">
                            <div className="w-10 h-10 bg-gradient-to-br from-amber-500 to-orange-500 rounded-lg flex items-center justify-center">
                                <i className="fas fa-history text-white"></i>
                            </div>
                            <span>Medical History</span>
                        </h3>
                        <div className="space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                                        <i className="fas fa-allergies text-red-500 mr-1"></i>
                                        Known Allergies
                                    </label>
                                    <input
                                        type="text"
                                        placeholder="e.g., Penicillin, Peanuts"
                                        className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-red-400 focus:border-transparent"
                                        value={formData.history.allergies}
                                        onChange={(e) => setFormData(prev => ({
                                            ...prev,
                                            history: { ...prev.history, allergies: e.target.value }
                                        }))}
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                                        <i className="fas fa-pills text-green-500 mr-1"></i>
                                        Current Medications
                                    </label>
                                    <input
                                        type="text"
                                        placeholder="e.g., Metformin, Aspirin"
                                        className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-green-400 focus:border-transparent"
                                        value={formData.history.currentMedications}
                                        onChange={(e) => setFormData(prev => ({
                                            ...prev,
                                            history: { ...prev.history, currentMedications: e.target.value }
                                        }))}
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-semibold text-gray-700 mb-2">
                                    <i className="fas fa-file-medical text-amber-500 mr-1"></i>
                                    Past Medical History (Surgeries, Major Injuries, Hospitalizations)
                                </label>
                                <div id="history-editor" className="border-2 border-gray-200 rounded-lg" style={{ minHeight: '100px' }}></div>
                            </div>

                            <div>
                                <label className="block text-sm font-semibold text-gray-700 mb-2">
                                    <i className="fas fa-notes-medical text-purple-500 mr-1"></i>
                                    Chronic Illnesses
                                </label>
                                <textarea
                                placeholder="e.g., Diabetes Type 2, Hypertension, Asthma..."
                                className="custom-textarea"
                                rows="2"
                                value={formData.history.chronic_illnesses}
                                onChange={(e) => setFormData(prev => ({
                                ...prev,
                                history: { ...prev.history, chronic_illnesses: e.target.value }
                                }))}
                                ></textarea>
                            </div>

                            <div>
                                <label className="block text-sm font-semibold text-gray-700 mb-2">
                                    <i className="fas fa-users text-blue-500 mr-1"></i>
                                    Family History
                                </label>
                                <textarea
                                    placeholder="e.g., Father had heart disease at 55, Mother is diabetic..."
                                    className="custom-textarea"
                                    rows="2"
                                    value={formData.history.family_history_narrative}
                                    onChange={(e) => setFormData(prev => ({
                                        ...prev,
                                        history: { ...prev.history, family_history_narrative: e.target.value }
                                    }))}
                                ></textarea>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div>
                                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                                        <i className="fas fa-smoking text-gray-700 mr-1"></i>
                                        Smoking Status
                                    </label>
                                    <select
                                        className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-gray-400 focus:border-transparent"
                                        value={formData.history.smoking_status}
                                        onChange={(e) => setFormData(prev => ({
                                            ...prev,
                                            history: { ...prev.history, smoking_status: e.target.value }
                                        }))}
                                    >
                                        <option value="none">Never Smoked</option>
                                        <option value="past">Ex-Smoker</option>
                                        <option value="current">Current Smoker</option>
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                                        <i className="fas fa-wine-glass-alt text-red-500 mr-1"></i>
                                        Alcohol Use
                                    </label>
                                    <select
                                        className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-red-400 focus:border-transparent"
                                        value={formData.history.alcohol_status}
                                        onChange={(e) => setFormData(prev => ({
                                            ...prev,
                                            history: { ...prev.history, alcohol_status: e.target.value }
                                        }))}
                                    >
                                        <option value="none">None</option>
                                        <option value="social">Social</option>
                                        <option value="daily">Daily</option>
                                        <option value="heavy">Heavy</option>
                                    </select>
                                </div>
                            </div>
                            
                            <div>
                                <label className="block text-sm font-semibold text-gray-700 mb-2">
                                    <i className="fas fa-home text-teal-500 mr-1"></i>
                                    Social / Environmental Factors
                                </label>
                                <textarea
                                    placeholder="e.g., Living situation, Occupation, Recent stressors..."
                                    className="custom-textarea"
                                    rows="3"
                                    value={formData.history.social_factors}
                                    onChange={(e) => setFormData(prev => ({
                                        ...prev,
                                        history: { ...prev.history, social_factors: e.target.value }
                                    }))}
                                ></textarea>
                            </div>
                        </div>
                    </div>

                    {/* Chief Complaints Section */}
                    <div className="bg-white p-6 rounded-xl border border-purple-100 shadow-sm hover:shadow-md transition-shadow">
                        <div className="flex items-center justify-between mb-4 pb-3 border-b-2 border-purple-100">
                            <h3 className="text-lg font-bold text-medical-dark flex items-center gap-2">
                                <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-lg flex items-center justify-center">
                                    <i className="fas fa-notes-medical text-white"></i>
                                </div>
                                <span>Chief Complaints</span>
                            </h3>
                            <button
                                onClick={addComplaint}
                                className="px-4 py-2 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:shadow-lg transition-all text-sm flex items-center gap-2 font-semibold"
                            >
                                <i className="fas fa-plus"></i>
                                Add Complaint
                            </button>
                        </div>
                        {formData.complaints.length === 0 ? (
                            <div className="text-center py-12 bg-purple-50 rounded-lg border-2 border-dashed border-purple-200">
                                <i className="fas fa-clipboard-list text-5xl text-purple-300 mb-3"></i>
                                <p className="text-gray-600 font-medium">No complaints added yet</p>
                                <p className="text-sm text-gray-500 mt-1">Click "Add Complaint" to record patient's chief complaints</p>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {formData.complaints.map((complaint, index) => (
                                    <div key={index} className="p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg border border-purple-200 hover:shadow-md transition-shadow">
                                        <div className="flex items-start gap-3">
                                            <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-3">
                                                <input
                                                    type="text"
                                                    placeholder="Complaint description"
                                                    className="px-3 py-2 border-2 border-purple-200 rounded-lg focus:ring-2 focus:ring-purple-400 focus:border-transparent"
                                                    value={complaint.complaint}
                                                    onChange={(e) => updateComplaint(index, 'complaint', e.target.value)}
                                                />
                                                <input
                                                    type="text"
                                                    placeholder="Duration (e.g., 2 days)"
                                                    className="px-3 py-2 border-2 border-purple-200 rounded-lg focus:ring-2 focus:ring-purple-400 focus:border-transparent"
                                                    value={complaint.duration}
                                                    onChange={(e) => updateComplaint(index, 'duration', e.target.value)}
                                                />
                                                <select
                                                    className="px-3 py-2 border-2 border-purple-200 rounded-lg focus:ring-2 focus:ring-purple-400 focus:border-transparent"
                                                    value={complaint.severity}
                                                    onChange={(e) => updateComplaint(index, 'severity', e.target.value)}
                                                >
                                                    <option value="mild">Mild</option>
                                                    <option value="moderate">Moderate</option>
                                                    <option value="severe">Severe</option>
                                                </select>
                                            </div>
                                            <button
                                                onClick={() => removeComplaint(index)}
                                                className="p-2 text-red-500 hover:bg-red-100 rounded-lg transition-colors"
                                                title="Remove complaint"
                                            >
                                                <i className="fas fa-trash"></i>
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Diagnosis Section */}
                    <div className="bg-white p-6 rounded-xl border border-indigo-100 shadow-sm hover:shadow-md transition-shadow">
                        <div className="flex items-center justify-between mb-4 pb-3 border-b-2 border-indigo-100">
                            <h3 className="text-lg font-bold text-medical-dark flex items-center gap-2">
                                <div className="w-10 h-10 bg-gradient-to-br from-indigo-500 to-blue-500 rounded-lg flex items-center justify-center">
                                    <i className="fas fa-stethoscope text-white"></i>
                                </div>
                                <span>Diagnosis</span>
                            </h3>
                            <button
                                onClick={addDiagnosis}
                                className="px-4 py-2 bg-gradient-to-r from-indigo-500 to-blue-500 text-white rounded-lg hover:shadow-lg transition-all text-sm flex items-center gap-2 font-semibold"
                            >
                                <i className="fas fa-plus"></i>
                                Add Diagnosis
                            </button>
                        </div>

                        <div className="space-y-4">
                            <div className="flex flex-wrap items-center gap-2 p-2 border-2 border-indigo-200 rounded-lg min-h-[48px]">
                                {formData.diagnosis.map((diag, index) => (
                                    <div key={index} className="inline-flex items-center bg-indigo-100 text-indigo-700 text-sm font-medium px-3 py-1 rounded-full">
                                        {diag.description || diag.code || 'New Diagnosis'}
                                        <button
                                            type="button"
                                            onClick={() => removeDiagnosis(index)}
                                            className="ml-2 text-indigo-700 hover:text-red-600"
                                        >
                                            <i className="fas fa-times-circle text-xs"></i>
                                        </button>
                                    </div>
                                ))}
                                <button
                                    onClick={addDiagnosis}
                                    className="text-indigo-700 hover:text-indigo-900 text-sm font-medium p-1 rounded-lg border border-indigo-200 hover:bg-indigo-50 transition-colors"
                                >
                                    <i className="fas fa-plus mr-1 text-xs"></i> Add New
                                </button>
                            </div>
                        
                            {formData.diagnosis.length === 0 ? (
                                <div className="text-center py-4 text-indigo-500 bg-indigo-50 rounded-lg border border-dashed border-indigo-200">
                                    No active diagnoses. Add one above.
                                </div>
                            ) : (
                                <div className="space-y-3 p-4 border border-indigo-200 rounded-lg bg-indigo-50/50">
                                    <h4 className="font-bold text-medical-dark">Edit Active Diagnoses:</h4>
                                    {formData.diagnosis.map((diag, index) => (
                                        <div key={index} className="p-4 bg-white rounded-lg shadow-sm border border-indigo-100">
                                            <div className="flex items-start gap-3">
                                                <div className="flex-1 space-y-3">
                                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                                                        <input
                                                            type="text"
                                                            placeholder="ICD Code (e.g., J00)"
                                                            className="px-3 py-2 border-2 border-indigo-200 rounded-lg focus:ring-2 focus:ring-indigo-400 focus:border-transparent"
                                                            value={diag.code}
                                                            onChange={(e) => updateDiagnosis(index, 'code', e.target.value)}
                                                        />
                                                        <input
                                                            type="text"
                                                            placeholder="Diagnosis description"
                                                            className="px-3 py-2 border-2 border-indigo-200 rounded-lg focus:ring-2 focus:ring-indigo-400 focus:border-transparent md:col-span-2"
                                                            value={diag.description}
                                                            onChange={(e) => updateDiagnosis(index, 'description', e.target.value)}
                                                        />
                                                    </div>
                                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                                                        <select
                                                            className="px-3 py-2 border-2 border-indigo-200 rounded-lg focus:ring-2 focus:ring-indigo-400 focus:border-transparent"
                                                            value={diag.type}
                                                            onChange={(e) => updateDiagnosis(index, 'type', e.target.value)}
                                                        >
                                                            <option value="provisional">Provisional Diagnosis</option>
                                                            <option value="final">Final Diagnosis</option>
                                                            <option value="differential">Differential Diagnosis</option>
                                                        </select>
                                                        <input
                                                            type="text"
                                                            placeholder="Additional notes"
                                                            className="px-3 py-2 border-2 border-indigo-200 rounded-lg focus:ring-2 focus:ring-indigo-400 focus:border-transparent"
                                                            value={diag.notes}
                                                            onChange={(e) => updateDiagnosis(index, 'notes', e.target.value)}
                                                        />
                                                    </div>
                                                </div>
                                                <button
                                                    onClick={() => removeDiagnosis(index)}
                                                    className="p-2 text-red-500 hover:bg-red-100 rounded-lg transition-colors"
                                                    title="Remove diagnosis"
                                                >
                                                    <i className="fas fa-trash"></i>
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Investigation Results Section */}
                    <div className="bg-white p-6 rounded-xl border border-cyan-100 shadow-sm hover:shadow-md transition-shadow">
                        <div className="flex items-center justify-between mb-4 pb-3 border-b-2 border-cyan-100">
                            <h3 className="text-lg font-bold text-medical-dark flex items-center gap-2">
                                <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-teal-500 rounded-lg flex items-center justify-center">
                                    <i className="fas fa-microscope text-white"></i>
                                </div>
                                <span>Investigation Results</span>
                            </h3>
                            <div className="flex space-x-2">
                                <button
                                    onClick={() => setIsResultsModalOpen(true)}
                                    className="px-4 py-2 bg-white border border-medical-accent text-medical-accent rounded-lg hover:bg-medical-accent/10 transition-all text-sm flex items-center gap-2 font-semibold"
                                >
                                    <i className="fas fa-microscope"></i>
                                    Enter Lab Results
                                </button>
                            </div>
                        </div>
                        {/* This inline card is now removed and replaced by a modal */}
                    </div>

                    {/* Investigations (To Order) Section */}
                    <div className="bg-white p-6 rounded-xl border border-cyan-100 shadow-sm hover:shadow-md transition-shadow">
                        <div className="flex items-center justify-between mb-4 pb-3 border-b-2 border-cyan-100">
                            <h3 className="text-lg font-bold text-medical-dark flex items-center gap-2">
                                <div className="w-10 h-10 bg-gradient-to-br from-cyan-500 to-teal-500 rounded-lg flex items-center justify-center">
                                    <i className="fas fa-flask text-white"></i>
                                </div>
                                <span>Investigations / Lab Tests</span>
                            </h3>
                            <div className="flex space-x-2">
                                <button
                                    onClick={() => setIsInvestigationModalOpen(true)}
                                    className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-teal-500 text-white rounded-lg hover:shadow-lg transition-all text-sm flex items-center gap-2 font-semibold"
                                >
                                    <i className="fas fa-plus"></i>
                                    Add Investigation
                                </button>
                            </div>
                        </div>
                        {formData.investigations.length === 0 ? (
                            <div className="text-center py-12 bg-cyan-50 rounded-lg border-2 border-dashed border-cyan-200">
                                <i className="fas fa-vials text-5xl text-cyan-300 mb-3"></i>
                                <p className="text-gray-600 font-medium">No investigations ordered yet</p>
                                <p className="text-sm text-gray-500 mt-1">Click "Add Investigation" to order lab tests or imaging</p>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {formData.investigations.map((inv, index) => (
                                    <div key={index} className="p-4 bg-white rounded-xl shadow-md border border-cyan-200">
                                        <div className="flex items-start gap-4">
                                            <div className="flex-1 grid grid-cols-1 md:grid-cols-3 gap-4">
                                                {/* Test Name */}
                                                <div>
                                                    <label className="block text-xs font-semibold text-gray-500 mb-1">Test Name</label>
                                                    <input
                                                        type="text"
                                                        placeholder="e.g., CBC, Thyroid Profile"
                                                        className="w-full px-3 py-2 border-2 border-cyan-200 rounded-lg focus:ring-2 focus:ring-cyan-400 font-medium"
                                                        value={inv.testName}
                                                        onChange={(e) => updateInvestigation(index, 'testName', e.target.value)}
                                                    />
                                                </div>
                                                {/* Category */}
                                                <div>
                                                    <label className="block text-xs font-semibold text-gray-500 mb-1">Category</label>
                                                    <select
                                                        className="w-full px-3 py-2 border-2 border-cyan-200 rounded-lg focus:ring-2 focus:ring-cyan-400"
                                                        value={inv.category}
                                                        onChange={(e) => updateInvestigation(index, 'category', e.target.value)}
                                                    >
                                                        <option value="">Category</option>
                                                        <option value="blood">Blood Test</option>
                                                        <option value="urine">Urine Test</option>
                                                        <option value="imaging_xray">X-Ray</option>
                                                        <option value="imaging_usg">Ultrasound</option>
                                                        <option value="imaging_mri">MRI</option>
                                                        <option value="imaging_ct">CT Scan</option>
                                                        <option value="cardiology_ecg">ECG</option>
                                                        <option value="other">Other</option>
                                                    </select>
                                                </div>
                                                {/* Urgency */}
                                                <div>
                                                    <label className="block text-xs font-semibold text-gray-500 mb-1">Urgency</label>
                                                    <select
                                                        className="w-full px-3 py-2 border-2 border-cyan-200 rounded-lg focus:ring-2 focus:ring-cyan-400"
                                                        value={inv.urgency}
                                                        onChange={(e) => updateInvestigation(index, 'urgency', e.target.value)}
                                                    >
                                                        <option value="routine">Routine</option>
                                                        <option value="urgent">Urgent</option>
                                                        <option value="stat">STAT</option>
                                                    </select>
                                                </div>
                                                {/* Notes */}
                                                <div className="md:col-span-3">
                                                    <label className="block text-xs font-semibold text-gray-500 mb-1">Notes / Instructions</label>
                                                    <input
                                                        type="text"
                                                        placeholder="e.g., Fasting required, Contrast study"
                                                        className="w-full px-3 py-2 border-2 border-cyan-200 rounded-lg focus:ring-2 focus:ring-cyan-400"
                                                        value={inv.notes}
                                                        onChange={(e) => updateInvestigation(index, 'notes', e.target.value)}
                                                    />
                                                </div>
                                            </div>
                                            {/* Remove Button */}
                                            <div>
                                                <button
                                                    onClick={() => removeInvestigation(index)}
                                                    className="p-2 text-red-500 hover:bg-red-100 rounded-lg transition-colors"
                                                    title="Remove investigation"
                                                >
                                                    <i className="fas fa-trash"></i>
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Prescription Section */}
                    <div className="bg-white p-6 rounded-xl border border-green-100 shadow-sm hover:shadow-md transition-shadow">
                        <div className="flex items-center justify-between mb-4 pb-3 border-b-2 border-green-100">
                            <h3 className="text-lg font-bold text-medical-dark flex items-center gap-2">
                                <div className="w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-500 rounded-lg flex items-center justify-center">
                                    <i className="fas fa-prescription text-white"></i>
                                </div>
                                <span>Prescription</span>
                            </h3>
                            <button
                                onClick={addPrescription}
                                className="px-4 py-2 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-lg hover:shadow-lg transition-all text-sm flex items-center gap-2 font-semibold"
                            >
                                <i className="fas fa-plus"></i>
                                Add Medicine
                            </button>
                        </div>
                        {formData.prescriptions.length === 0 ? (
                            <div className="text-center py-12 bg-green-50 rounded-lg border-2 border-dashed border-green-200">
                                <i className="fas fa-pills text-5xl text-green-300 mb-3"></i>
                                <p className="text-gray-600 font-medium">No medicines prescribed yet</p>
                                <p className="text-sm text-gray-500 mt-1">Click "Add Medicine" to prescribe medications</p>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {formData.prescriptions.map((prescription, index) => (
                                    <div key={index} className="p-4 bg-white rounded-xl shadow-md border border-green-200">
                                        <div className="flex items-center justify-between mb-3 border-b pb-2">
                                            <h4 className="font-bold text-lg text-green-700">
                                                {index + 1}. {prescription.medicine || 'New Medication'}
                                            </h4>
                                            <button
                                                onClick={() => removePrescription(index)}
                                                className="p-2 text-red-500 hover:bg-red-100 rounded-lg transition-colors"
                                                title="Remove prescription"
                                            >
                                                <i className="fas fa-trash"></i>
                                            </button>
                                        </div>
                                        
                                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                                            {/* Row 1: Name and Type */}
                                            <div className="lg:col-span-2">
                                                <label className="block text-xs font-semibold text-gray-500 mb-1">Medicine Name</label>
                                                <input
                                                    type="text"
                                                    placeholder="e.g., Amoxicillin"
                                                    className="w-full px-3 py-2 border-2 border-green-200 rounded-lg focus:ring-2 focus:ring-green-400 font-medium"
                                                    value={prescription.medicine}
                                                    onChange={(e) => updatePrescription(index, 'medicine', e.target.value)}
                                                />
                                            </div>
                                            <div>
                                                <label className="block text-xs font-semibold text-gray-500 mb-1">Form/Type</label>
                                                <select
                                                    className="w-full px-3 py-2 border-2 border-green-200 rounded-lg focus:ring-2 focus:ring-green-400"
                                                    value={prescription.type}
                                                    onChange={(e) => updatePrescription(index, 'type', e.target.value)}
                                                >
                                                    <option value="branded">Branded</option>
                                                    <option value="generic">Generic</option>
                                                </select>
                                            </div>
                                            <div>
                                                 <label className="block text-xs font-semibold text-gray-500 mb-1">Dosage</label>
                                                <input
                                                    type="text"
                                                    placeholder="e.g., 500mg"
                                                    className="w-full px-3 py-2 border-2 border-green-200 rounded-lg focus:ring-2 focus:ring-green-400"
                                                    value={prescription.dosage}
                                                    onChange={(e) => updatePrescription(index, 'dosage', e.target.value)}
                                                />
                                            </div>

                                            {/* Row 2: Frequency, Route, Duration */}
                                            <div>
                                                <label className="block text-xs font-semibold text-gray-500 mb-1">Frequency</label>
                                                <select
                                                    className="w-full px-3 py-2 border-2 border-green-200 rounded-lg focus:ring-2 focus:ring-green-400"
                                                    value={prescription.frequency}
                                                    onChange={(e) => updatePrescription(index, 'frequency', e.target.value)}
                                                >
                                                    <option value="">Select Freq</option>
                                                    <option value="od">Once Daily (OD)</option>
                                                    <option value="bd">Twice Daily (BD)</option>
                                                    <option value="tds">Three Times Daily (TDS)</option>
                                                    <option value="qid">Four Times Daily (QID)</option>
                                                    <option value="sos">SOS</option>
                                                    <option value="stat">STAT</option>
                                                </select>
                                            </div>
                                            <div>
                                                <label className="block text-xs font-semibold text-gray-500 mb-1">Route</label>
                                                <select
                                                    className="w-full px-3 py-2 border-2 border-green-200 rounded-lg focus:ring-2 focus:ring-green-400"
                                                    value={prescription.route}
                                                    onChange={(e) => updatePrescription(index, 'route', e.target.value)}
                                                >
                                                    <option value="oral">Oral</option>
                                                    <option value="topical">Topical</option>
                                                    <option value="iv">IV</option>
                                                    <option value="im">IM</option>
                                                    <option value="sc">SC</option>
                                                </select>
                                            </div>
                                            <div>
                                                <label className="block text-xs font-semibold text-gray-500 mb-1">Duration</label>
                                                <input
                                                    type="text"
                                                    placeholder="e.g., 7 days"
                                                    className="w-full px-3 py-2 border-2 border-green-200 rounded-lg focus:ring-2 focus:ring-green-400"
                                                    value={prescription.duration}
                                                    onChange={(e) => updatePrescription(index, 'duration', e.target.value)}
                                                />
                                            </div>
                                            <div className="sm:col-span-2 lg:col-span-1">
                                                <label className="block text-xs font-semibold text-gray-500 mb-1">When</label>
                                                <select
                                                    className="w-full px-3 py-2 border-2 border-green-200 rounded-lg focus:ring-2 focus:ring-green-400"
                                                    value={prescription.when}
                                                    onChange={(e) => updatePrescription(index, 'when', e.target.value)}
                                                >
                                                    <option value="">Select When</option>
                                                    <option value="Before Food">Before Food</option>
                                                    <option value="After Food">After Food</option>
                                                    <option value="With Food">With Food</option>
                                                    <option value="Bed Time">Bed Time</option>
                                                </select>
                                            </div>

                                            {/* Row 3: Instructions */}
                                            <div className="lg:col-span-4">
                                                <label className="block text-xs font-semibold text-gray-500 mb-1">Instructions</label>
                                                <textarea
                                                    placeholder="Special instructions (e.g., Take after meals, Avoid alcohol)"
                                                    className="custom-textarea"
                                                    rows="2"
                                                    value={prescription.instructions}
                                                    onChange={(e) => updatePrescription(index, 'instructions', e.target.value)}
                                                ></textarea>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Advice & Follow-up Section */}
                    <div className="bg-white p-6 rounded-xl border border-blue-100 shadow-sm hover:shadow-md transition-shadow">
                        <h3 className="text-lg font-bold text-medical-dark mb-4 flex items-center gap-2 pb-3 border-b-2 border-blue-100">
                            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center">
                                <i className="fas fa-clipboard-list text-white"></i>
                            </div>
                            <span>Advice & Follow-up Instructions</span>
                        </h3>
                        <div className="space-y-4">
                            <div id="advice-editor" className="border-2 border-gray-200 rounded-lg" style={{ minHeight: '200px' }}></div>
                            {/* --- START: Structured Follow-up/Next Visit --- */}
                            <div>
                                <label className="block text-sm font-semibold text-gray-700 mb-2">
                                    <i className="fas fa-calendar-check text-blue-500 mr-1"></i>
                                    Next Visit / Follow-up
                                </label>
                                <div className="flex items-center space-x-2">
                                    <select
                                        className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-400 focus:border-transparent"
                                        value={formData.nextVisitType || 'duration'}
                                        onChange={(e) => setFormData(prev => ({ ...prev, nextVisitType: e.target.value }))}
                                    >
                                        <option value="duration">Duration (e.g., 3 weeks)</option>
                                        <option value="date">Specific Date</option>
                                    </select>
                                </div>
                                {formData.nextVisitType === 'duration' || !formData.nextVisitType ? (
                                    <div className="flex items-center space-x-2 mt-2">
                                        <input
                                            type="number"
                                            placeholder="No. of"
                                            className="w-20 px-3 py-2 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-400 focus:border-transparent"
                                            value={formData.nextVisitValue || ''}
                                            onChange={(e) => setFormData(prev => ({ ...prev, nextVisitValue: e.target.value, nextVisitInstructions: `${e.target.value} ${formData.nextVisitUnit || 'Days'}` }))}
                                        />
                                        <select
                                            className="w-28 px-3 py-2 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-400 focus:border-transparent"
                                            value={formData.nextVisitUnit || 'Days'}
                                            onChange={(e) => setFormData(prev => ({ ...prev, nextVisitUnit: e.target.value, nextVisitInstructions: `${formData.nextVisitValue || ''} ${e.target.value}` }))}
                                        >
                                            <option>Days</option>
                                            <option>Weeks</option>
                                            <option>Months</option>
                                        </select>
                                        <span className="text-sm text-gray-600">({formData.nextVisitInstructions || 'e.g., 3 Weeks'})</span>
                                    </div>
                                ) : (
                                    <div class="relative mt-2">
                                        <div class="absolute inset-y-0 end-0 top-0 flex items-center pe-3.5 pointer-events-none">
                                            <svg class="w-4 h-4 text-gray-500 dark:text-gray-400" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 20 20">
                                                <path d="M20 4a2 2 0 0 0-2-2h-2V1a1 1 0 0 0-2 0v1h-3V1a1 1 0 0 0-2 0v1H6V1a1 1 0 0 0-2 0v1H2a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V4Zm-2 13H4V8h14v9Z"/>
                                            </svg>
                                        </div>
                                        <input
                                            type="date"
                                            className="form-input-themed custom-datetime"
                                            value={formData.nextVisitDate}
                                            onChange={(e) => setFormData(prev => ({ ...prev, nextVisitDate: e.target.value }))}
                                            min={new Date().toISOString().split('T')[0]}
                                        />
                                    </div>
                                )}
                                <input type="hidden" value={formData.nextVisitInstructions || ''} name="next_visit_instructions" />
                                <input type="hidden" value={formData.nextVisitDate || ''} name="next_visit_date" />
                            </div>
                            {/* --- END: Structured Follow-up/Next Visit --- */}

                            {/* --- START: Referral Section --- */}
                            <div>
                                <label className="block text-sm font-semibold text-gray-700 mb-2">
                                    <i className="fas fa-user-md text-gray-600 mr-1"></i>
                                    Referred To (Optional)
                                </label>
                                <div className="grid grid-cols-1 md:grid-cols-4 gap-2 border p-3 rounded-lg bg-gray-50">
                                    <input 
                                        type="text" 
                                        name="referral_doctor_name" 
                                        value={formData.referral_doctor_name || ''} 
                                        onChange={(e) => setFormData(prev => ({ ...prev, referral_doctor_name: e.target.value }))}
                                        className="form-input-themed" 
                                        placeholder="Doctor Name" 
                                    />
                                    <input 
                                        type="text" 
                                        name="referral_speciality" 
                                        value={formData.referral_speciality || ''} 
                                        onChange={(e) => setFormData(prev => ({ ...prev, referral_speciality: e.target.value }))}
                                        className="form-input-themed" 
                                        placeholder="Speciality" 
                                    />
                                    <input 
                                        type="tel" 
                                        name="referral_phone" 
                                        value={formData.referral_phone || ''} 
                                        onChange={(e) => setFormData(prev => ({ ...prev, referral_phone: e.target.value }))}
                                        className="form-input-themed" 
                                        placeholder="Phone No" 
                                    />
                                    <input 
                                        type="email" 
                                        name="referral_email" 
                                        value={formData.referral_email || ''} 
                                        onChange={(e) => setFormData(prev => ({ ...prev, referral_email: e.target.value }))}
                                        className="form-input-themed" 
                                        placeholder="Email" 
                                    />
                                </div>
                            </div>
                            {/* --- END: Referral Section --- */}
                        </div>
                    </div>

                    {isInvestigationModalOpen && (
                        <InvestigationSelectModal
                            isOpen={isInvestigationModalOpen}
                            onClose={() => setIsInvestigationModalOpen(false)}
                            onConfirm={(testsToAdd) => {
                                testsToAdd.forEach(testName => addInvestigation(testName));
                                setIsInvestigationModalOpen(false);
                            }}
                        />
                    )}
                    
                    {isResultsModalOpen && (
                        <InvestigationResultsModal
                            isOpen={isResultsModalOpen}
                            onClose={() => setIsResultsModalOpen(false)}
                            initialResultsData={formData.investigationResults}
                            onSave={(newResults) => {
                                setFormData(prev => ({ ...prev, investigationResults: newResults }));
                                setIsResultsModalOpen(false);
                                toast('Lab results saved.');
                            }}
                        />
                    )}

                    {/* Previous Prescriptions Section */}
                    {mode === 'consultation' && patient.previousVisits && patient.previousVisits.length > 0 && (
                        <div className="bg-white p-6 rounded-xl border border-violet-100 shadow-sm hover:shadow-md transition-shadow">
                            <h3 className="text-lg font-bold text-medical-dark mb-4 flex items-center gap-2 pb-3 border-b-2 border-violet-100">
                                <div className="w-10 h-10 bg-gradient-to-br from-violet-500 to-purple-500 rounded-lg flex items-center justify-center">
                                    <i className="fas fa-history text-white"></i>
                                </div>
                                <span>Previous Prescriptions</span>
                            </h3>
                            <div className="space-y-3">
                                {patient.previousVisits.map((visit, index) => (
                                    <div key={index} className="p-4 bg-gradient-to-r from-violet-50 to-purple-50 rounded-lg border border-violet-200">
                                        <div className="flex justify-between items-start mb-3">
                                            <div>
                                                <h4 className="font-semibold text-gray-900">
                                                    Visit Date: {new Date(visit.date).toLocaleDateString('en-IN', {
                                                        year: 'numeric',
                                                        month: 'long',
                                                        day: 'numeric'
                                                    })}
                                                </h4>
                                                <p className="text-sm text-gray-600 mt-1">
                                                    <strong>Complaints:</strong> {visit.complaints.join(', ')}
                                                </p>
                                                <p className="text-sm text-gray-600">
                                                    <strong>Diagnosis:</strong> {visit.diagnosis.join(', ')}
                                                </p>
                                            </div>
                                        </div>
                                        <div className="mt-3 pt-3 border-t border-violet-200">
                                            <p className="text-sm font-semibold text-gray-700 mb-2">Medications:</p>
                                            <div className="space-y-2">
                                                {visit.prescriptions.map((rx, rxIndex) => (
                                                    <div key={rxIndex} className="flex items-center gap-2 text-sm bg-white p-2 rounded-lg">
                                                        <i className="fas fa-pills text-violet-500"></i>
                                                        <span className="font-medium">{rx.medicine}</span>
                                                        <span className="text-gray-500">-</span>
                                                        <span>{rx.dosage}, {rx.frequency}, {rx.duration}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                </div>
            </div>
        </div>
    );
};

window.VisitPadView = VisitPadView;

export default VisitPadView;
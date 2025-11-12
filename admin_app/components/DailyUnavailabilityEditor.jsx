const DailyUnavailabilityEditor = ({ date, onClose, existingClinicBlock, existingHospitalBlock }) => {
    const toISODateString = (d) => {
        if (!d) return '';
        const dateObj = new Date(d);
        return `${dateObj.getFullYear()}-${String(dateObj.getMonth() + 1).padStart(2, '0')}-${String(dateObj.getDate()).padStart(2, '0')}`;
    };

    const getInitialStartDate = () => {
        const d1 = existingClinicBlock ? new Date(existingClinicBlock.start_datetime) : null;
        const d2 = existingHospitalBlock ? new Date(existingHospitalBlock.start_datetime) : null;
        if (d1 && d2) return toISODateString(d1 < d2 ? d1 : d2);
        return toISODateString(d1 || d2 || date);
    };

    const getInitialEndDate = () => {
        const d1 = existingClinicBlock ? new Date(existingClinicBlock.end_datetime) : null;
        const d2 = existingHospitalBlock ? new Date(existingHospitalBlock.end_datetime) : null;
        if (d1 && d2) return toISODateString(d1 > d2 ? d1 : d2);
        return toISODateString(d1 || d2 || date);
    };

    const [startDate, setStartDate] = React.useState(getInitialStartDate());
    const [endDate, setEndDate] = React.useState(getInitialEndDate());
    const [reason, setReason] = React.useState(existingClinicBlock?.reason || existingHospitalBlock?.reason || '');
    const [selectedLocations, setSelectedLocations] = React.useState({
        1: !!existingClinicBlock,
        2: !!existingHospitalBlock
    });

    React.useEffect(() => {
        if (!existingClinicBlock && !existingHospitalBlock) {
            setSelectedLocations({ 1: true, 2: true });
        }
    }, [existingClinicBlock, existingHospitalBlock]);

    const [error, setError] = React.useState('');
    const [isSubmitting, setIsSubmitting] = React.useState(false);

    const clinicBlockId = existingClinicBlock?.id || null;
    const hospitalBlockId = existingHospitalBlock?.id || null;

    const handleLocationChange = (locationId) => {
        setSelectedLocations(prev => ({ ...prev, [locationId]: !prev[locationId] }));
    };

    const handleSubmit = async () => {
        setError('');
        setIsSubmitting(true);

        if (!startDate || !endDate) {
            setError('Start date and end date are required.');
            setIsSubmitting(false);
            return;
        }

        const startDateTime = new Date(startDate);
        startDateTime.setHours(0, 0, 0, 0);
        const endDateTime = new Date(endDate);
        endDateTime.setHours(23, 59, 59, 999);

        const apiCalls = [];

        const clinicIsChecked = selectedLocations[1];
        if (clinicIsChecked) {
            const payload = {
                location_id: 1,
                start_datetime: startDateTime.toISOString(),
                end_datetime: endDateTime.toISOString(),
                reason: reason,
            };
            if (clinicBlockId) {
                apiCalls.push(window.api(`/api/v1/unavailable-periods/${clinicBlockId}`, {
                    method: 'PUT',
                    body: JSON.stringify(payload)
                }));
            } else {
                apiCalls.push(window.api('/api/v1/unavailable-periods/', {
                    method: 'POST',
                    body: JSON.stringify(payload)
                }));
            }
        } else if (clinicBlockId) {
            apiCalls.push(window.api(`/api/v1/unavailable-periods/${clinicBlockId}`, { method: 'DELETE' }));
        }

        const hospitalIsChecked = selectedLocations[2];
        if (hospitalIsChecked) {
            const payload = {
                location_id: 2,
                start_datetime: startDateTime.toISOString(),
                end_datetime: endDateTime.toISOString(),
                reason: reason,
            };
            if (hospitalBlockId) {
                apiCalls.push(window.api(`/api/v1/unavailable-periods/${hospitalBlockId}`, {
                    method: 'PUT',
                    body: JSON.stringify(payload)
                }));
            } else {
                apiCalls.push(window.api('/api/v1/unavailable-periods/', {
                    method: 'POST',
                    body: JSON.stringify(payload)
                }));
            }
        } else if (hospitalBlockId) {
            apiCalls.push(window.api(`/api/v1/unavailable-periods/${hospitalBlockId}`, { method: 'DELETE' }));
        }

        if (apiCalls.length === 0 && !clinicBlockId && !hospitalBlockId) {
            setError('At least one location must be selected to create a new block.');
            setIsSubmitting(false);
            return;
        }

        try {
            await Promise.all(apiCalls);
            setIsSubmitting(false);
            onClose();
        } catch (err) {
            setError(err.message || 'An error occurred. Please try again.');
            console.error('Save unavailable period error:', err);
            setIsSubmitting(false);
        }
    };

    const handleDeleteAll = async () => {
        setError('');
        setIsSubmitting(true);
        const apiCalls = [];
        if (clinicBlockId) {
            apiCalls.push(window.api(`/api/v1/unavailable-periods/${clinicBlockId}`, { method: 'DELETE' }));
        }
        if (hospitalBlockId) {
            apiCalls.push(window.api(`/api/v1/unavailable-periods/${hospitalBlockId}`, { method: 'DELETE' }));
        }

        if (apiCalls.length === 0) {
            setError('Nothing to delete.');
            setIsSubmitting(false);
            return;
        }

        try {
            await Promise.all(apiCalls);
            setIsSubmitting(false);
            onClose();
        } catch (err) {
            setError(err.message || 'An error occurred while deleting.');
            setIsSubmitting(false);
        }
    };

    return (
        <div className="space-y-6">
            {error && <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg">{error}</div>}
            <div>
                <label className="block text-sm font-medium text-medical-gray mb-2">Block Off Dates</label>
                <p className="text-sm text-medical-gray">Select a date range to mark as unavailable for online bookings.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <label className="block text-sm font-medium text-medical-gray mb-2">Start Date</label>
                    <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="form-input-themed" />
                </div>
                <div>
                    <label className="block text-sm font-medium text-medical-gray mb-2">End Date</label>
                    <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="form-input-themed" />
                </div>
            </div>
            <div>
                <label className="block text-sm font-medium text-medical-gray mb-2">Select Locations</label>
                <div className="flex space-x-6 mt-2">
                    <label className="flex flex-wrap items-center gap-2 cursor-pointer">
                        <input
                            type="checkbox"
                            checked={selectedLocations[1]}
                            onChange={() => handleLocationChange(1)}
                            className="w-4 h-4 text-medical-accent rounded"
                        />
                        <span>Home Clinic</span>
                    </label>
                    <label className="flex flex-wrap items-center gap-2 cursor-pointer">
                        <input
                            type="checkbox"
                            checked={selectedLocations[2]}
                            onChange={() => handleLocationChange(2)}
                            className="w-4 h-4 text-medical-accent rounded"
                        />
                        <span>Hospital</span>
                    </label>
                </div>
            </div>
            <div>
                <label className="block text-sm font-medium text-medical-gray mb-2">Reason (Optional)</label>
                <input type="text" value={reason} onChange={(e) => setReason(e.target.value)} className="form-input-themed" placeholder="e.g., Holiday, Personal Leave" />
            </div>
            <div className="flex justify-between items-center">
                <div>
                    {(clinicBlockId || hospitalBlockId) && (
                        <button
                            onClick={handleDeleteAll}
                            className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200"
                            disabled={isSubmitting}
                        >
                            <i className="fas fa-trash-alt mr-2"></i>
                            Remove Block
                        </button>
                    )}
                </div>
                <div className="flex space-x-3">
                    <button onClick={onClose} className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300" disabled={isSubmitting}>Cancel</button>
                    <button onClick={handleSubmit} className="medical-button px-4 py-2 text-white rounded-lg relative z-10" disabled={isSubmitting}>
                        {isSubmitting ? 'Saving...' : (clinicBlockId || hospitalBlockId ? 'Update Block' : 'Save Block')}
                    </button>
                </div>
            </div>
        </div>
    );
};


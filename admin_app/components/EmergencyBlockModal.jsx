const EmergencyBlockModal = ({ onClose }) => {
            const [blockDate, setBlockDate] = React.useState(new Date().toISOString().split('T')[0]);
            const [reason, setReason] = React.useState('');
            const [error, setError] = React.useState('');
            const [pickerOpen, setPickerOpen] = React.useState(null); // { locId: 1|2 }
            const dayScheduleRef = React.useRef(null);

            // Flatpickr hook removed
            const [successMessage, setSuccessMessage] = React.useState('');

            // Flatpickr hook removed

            const handleSubmit = async () => {
                setError('');
                setSuccessMessage('');
                if (!blockDate || !reason) {
                    setError('Both date and reason are required.');
                    return;
                }

                const payload = {
                    block_date: blockDate,
                    reason: reason,
                };

                try {
                    const result = await api('/api/v1/unavailable-periods/emergency-block', {
                        method: 'POST',
                        body: JSON.stringify(payload),
                    });
                    setSuccessMessage(`Successfully cancelled ${result.length} appointment(s) and blocked the day.`);

                    setTimeout(() => onClose(), 3000);
                } catch (err) {

                    setError(err.message || 'An unexpected error occurred.');
                    console.error('Emergency block error:', err.message);
                }
            };

            return (
                <div className="space-y-6" ref={dayScheduleRef}>
                    { }
                    {error && (
                        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg mb-4">
                            <p className="font-bold">Error:</p>
                            <p>{error}</p>
                        </div>
                    )}
                    {successMessage && <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded-lg">{successMessage}</div>}
                    <div>
                        <label className="block text-sm font-medium text-medical-gray mb-2">Emergency Block</label>
                        <p className="text-sm text-medical-gray">This action will cancel all appointments for the selected day and notify patients via WhatsApp.</p>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-medical-gray mb-2">Date to Block</label>
                        <div class="relative">
                        <div className="absolute inset-y-0 end-0 top-0 flex items-center pe-3.5 pointer-events-none">
                            <svg className="w-4 h-4 text-gray-500 dark:text-gray-400" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M20 4a2 2 0 0 0-2-2h-2V1a1 1 0 0 0-2 0v1h-3V1a1 1 0 0 0-2 0v1H6V1a1 1 0 0 0-2 0v1H2a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V4Zm-2 13H4V8h14v9Z"/>
                            </svg>
                        </div>
                        <input type="date" id="emergency-block-date-picker" value={blockDate} onChange={(e) => setBlockDate(e.target.value)} className="form-input-themed custom-datetime" />
                    </div>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-medical-gray mb-2">Reason for Emergency</label>
                        <input type="text" value={reason} onChange={(e) => setReason(e.target.value)} className="form-input-themed" placeholder="e.g., Unforeseen personal matter" />
                    </div>
                    <div className="flex justify-end space-x-3">
                        <button onClick={onClose} className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">Cancel</button>
                        <button onClick={handleSubmit} className="bg-red-600 hover:bg-red-700 px-4 py-2 text-white rounded-lg relative z-10">
                            Confirm Emergency Block
                        </button>
                    </div>
                </div>
            );
        };

window.EmergencyBlockModal = EmergencyBlockModal;


export default EmergencyBlockModal;
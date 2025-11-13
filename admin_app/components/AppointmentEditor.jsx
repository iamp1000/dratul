import React from 'react';
import LoadingSpinner from '../lib/LoadingSpinner.jsx';
import DatePicker from './DatePicker.jsx';
import TimeRangePicker from './TimeRangePicker.jsx';

const AppointmentEditor = ({ appointment, onClose, refreshAppointments, user }) => {
    console.log('[AppointmentEditor] Rendering/Re-rendering...');
    const [patientId, setPatientId] = React.useState(appointment?.patient_id || '');
    const [locationId, setLocationId] = React.useState(appointment?.location_id || 1);
    const [appointmentDate, setAppointmentDate] = React.useState(appointment ? new Date(appointment.start_time).toISOString().split('T')[0] : new Date().toISOString().split('T')[0]);
    const [appointmentTime, setAppointmentTime] = React.useState(appointment ? new Date(appointment.start_time).toTimeString().substring(0, 5) : '');
    const [reason, setReason] = React.useState(appointment?.reason || '');
    const [patients, setPatients] = React.useState([]);
    const [errors, setErrors] = React.useState([]);

    const [isNewPatient, setIsNewPatient] = React.useState(false);
    const [firstName, setFirstName] = React.useState('');
    const [lastName, setLastName] = React.useState('');
    const [dob, setDob] = React.useState('');
    const [city, setCity] = React.useState('');
    const [phoneNumber, setPhoneNumber] = React.useState('');
    const [email, setEmail] = React.useState('');

    const [patientSearch, setPatientSearch] = React.useState('');
    const [filteredPatients, setFilteredPatients] = React.useState([]);
    const [availableSlots, setAvailableSlots] = React.useState([]);
    const [loadingSlots, setLoadingSlots] = React.useState(false);
    const [slotError, setSlotError] = React.useState('');
    const [isWalkIn, setIsWalkIn] = React.useState(false);
    const [showTimePicker, setShowTimePicker] = React.useState(false);

    React.useEffect(() => {
        const fetchPatients = async () => {
            try {
                const data = await api('/api/v1/patients');
                setPatients(data || []);
            } catch (err) {
                console.error('Failed to fetch patients', err);
            }
        };
        fetchPatients();
    }, []);

    React.useEffect(() => {
        const fetchSlots = async () => {

            if (!appointmentDate || !locationId) {
                setAvailableSlots([]);
                setSlotError('Please select a date and location.');
                return;
            }

            setLoadingSlots(true);
            setSlotError('');
            setAvailableSlots([]);

            setAppointmentTime('');

            const toISODate = (d) => {
                if (!d) return '';

                return d;
            };
            const formattedDate = toISODate(appointmentDate);

            try {
                console.log(`[AppointmentEditor] Fetching slots for Loc ${locationId} on ${formattedDate}`);
                const fetchedSlots = await api(`/api/v1/slots/${locationId}/${formattedDate}`);

                const availableOnly = Array.isArray(fetchedSlots) ? fetchedSlots.filter(slot => slot.status === 'available') : [];

                console.log(`[AppointmentEditor] Received slots:`, fetchedSlots);
                console.log(`[AppointmentEditor] Filtered available slots:`, availableOnly);

                setAvailableSlots(availableOnly);
                if (availableOnly.length === 0) {
                    setSlotError('No available slots found for this day and location.');
                }

            } catch (err) {
                console.error(`[AppointmentEditor] Error fetching slots for ${formattedDate}:`, err);
                setSlotError(`Failed to load slots: ${err.message}`);
                setAvailableSlots([]);
            } finally {
                setLoadingSlots(false);
            }
        };

        fetchSlots();
    }, [appointmentDate, locationId]);

    const handlePatientSearch = (e) => {
        const searchTerm = e.target.value;
        setPatientSearch(searchTerm);
        if (searchTerm) {
            const lowerSearch = searchTerm.toLowerCase();
            setFilteredPatients(
                patients.filter(p =>
                    `${p.first_name || ''} ${p.last_name || ''}`.toLowerCase().includes(lowerSearch) ||
                    p.phone_number?.includes(lowerSearch)
                )
            );
        } else {
            setFilteredPatients(patients);
        }
    };

    const selectPatient = (patient) => {
        setPatientId(patient.id);
        setPatientSearch(`${patient.first_name || ''} ${patient.last_name || ''}`.trim());
        setFilteredPatients([]);
    };

    const handleSubmit = async () => {

        setErrors([]);
        const validationErrors = [];
        if (!isNewPatient) {
            if (!patientId) validationErrors.push('An existing patient must be selected.');
        } else {
            if (!firstName) validationErrors.push('First Name is a required field.');
            if (!dob) validationErrors.push('Date of Birth is a required field.');
        }
        if (!isWalkIn) {
            if (!appointmentDate) validationErrors.push('Appointment Date is required.');
            if (!appointmentTime) validationErrors.push('Appointment Time is required.');
        }

        if (validationErrors.length > 0) {
            setErrors(validationErrors);
            return;
        }
        setErrors([]);

        let formattedStartTime = null;
        let formattedEndTime = null;
        if (!isWalkIn) {
            const selectedSlot = availableSlots.find(s => s.start_time === appointmentTime);
            if (!selectedSlot) {
                setErrors(['Invalid time slot selected. Please select again.']);
                return;
            }
            formattedStartTime = selectedSlot.start_time;
            formattedEndTime = selectedSlot.end_time;
        }

        let payload = {
            location_id: locationId,
            start_time: formattedStartTime,
            end_time: formattedEndTime,
            reason,
            patient_id: null,
            new_patient: null
        };

        if (isNewPatient) {
            payload.new_patient = {
                first_name: firstName,
                last_name: lastName,
                date_of_birth: dob,
                city: city,
                phone_number: phoneNumber,
                email: email
            };

        } else {
            payload.patient_id = parseInt(patientId);

            if (isNaN(payload.patient_id)) {

                setErrors(['Invalid Patient ID selected. Please select a valid patient.']);
                return;
            }

        }

        if (isWalkIn) {
            payload.is_walk_in = true;
        }

        try {
            await api('/api/v1/appointments', {
                method: 'POST',
                body: JSON.stringify(payload)
            });
            if (refreshAppointments) refreshAppointments();
            onClose();
        } catch (err) {

            setErrors([err.message || 'An unexpected error occurred.']);
            console.error('Save appointment error:', err.message);
        }
    };

    return (
        <div className="space-y-6">
            {errors.length > 0 && (
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg">
                    <p className="font-bold mb-2">Please fix the following issues:</p>
                    <ul className="list-disc list-inside text-sm">
                        {errors.map((err, index) => <li key={index}>{err}</li>)}
                    </ul>
                </div>
            )}

            { }
            <div className="flex items-center justify-center bg-gray-100 p-1 rounded-lg">
                <button
                    onClick={() => setIsNewPatient(false)}
                    className={`flex-1 py-2 px-4 rounded-md font-medium transition-all ${!isNewPatient ? 'bg-white shadow text-medical-accent' : 'text-medical-gray'}`}
                >
                    Existing Patient
                </button>
                <button
                    onClick={() => setIsNewPatient(true)}
                    className={`flex-1 py-2 px-4 rounded-md font-medium transition-all ${isNewPatient ? 'bg-white shadow text-medical-accent' : 'text-medical-gray'}`}
                >
                    New Patient
                </button>
            </div>

            {isNewPatient ? (
                <div className="space-y-4 animate-fade-in">
                    <h3 className="text-lg font-semibold text-medical-dark">New Patient Details</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div>
                            <label className="block text-sm font-medium text-medical-gray mb-2">First Name <span className="text-red-500">*</span></label>
                            <input type="text" value={firstName} onChange={(e) => setFirstName(e.target.value)} className="form-input-themed" placeholder="Enter first name" />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-medical-gray mb-2">Last Name</label>
                            <input type="text" value={lastName} onChange={(e) => setLastName(e.target.value)} className="form-input-themed" placeholder="Enter last name" />
                        </div>
                        <div>
                            <DatePicker 
                                label="Date of Birth"
                                value={dob} 
                                onChange={(e) => setDob(e.target.value)}
                                required={true}
                                // No minDate/maxDate for DOB
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-medical-gray mb-2">City</label>
                            <input type="text" value={city} onChange={(e) => setCity(e.target.value)} className="form-input-themed" placeholder="Enter city" />
                        </div>
                        { }
                        <div>
                            <label className="block text-sm font-medium text-medical-gray mb-2">Phone Number</label>
                            <input type="tel" value={phoneNumber} onChange={(e) => setPhoneNumber(e.target.value)} className="form-input-themed" placeholder="Enter phone number" />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-medical-gray mb-2">Email</label>
                            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="form-input-themed" placeholder="Enter email" />
                        </div>
                        { }
                    </div>
                </div>
            ) : (
                <div className="animate-fade-in">
                    <label className="block text-sm font-medium text-medical-gray mb-2">Patient</label>
                    <div className="relative">
                        <input
                            type="text"
                            value={patientSearch}
                            onChange={handlePatientSearch}
                            onFocus={() => {
                                const lowerSearch = patientSearch.toLowerCase();
                                setFilteredPatients(patients.filter(p =>
                                    `${p.first_name || ''} ${p.last_name || ''}`.toLowerCase().includes(lowerSearch) ||
                                    p.phone_number?.includes(lowerSearch)
                                ));
                            }}
                            onBlur={() => setTimeout(() => setFilteredPatients([]), 200)}
                            className="form-input-themed"
                            placeholder="Search for an existing patient..."
                        />
                        {filteredPatients.length > 0 && (
                            <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                                {filteredPatients.map(p => (
                                    <div
                                        key={p.id}
                                        onClick={() => selectPatient(p)}
                                        className="p-3 hover:bg-medical-light cursor-pointer border-b last:border-b-0"
                                    >
                                        <div className="font-semibold">{`${p.first_name || ''} ${p.last_name || ''}`.trim()}</div>
                                        <div className="text-sm text-medical-gray">{p.phone_number || 'No phone'}</div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            )}

            { }
            <div className="flex items-center space-x-2 my-4">
                <input
                    type="checkbox"
                    id="walk-in-toggle"
                    checked={isWalkIn}
                    onChange={(e) => setIsWalkIn(e.target.checked)}
                    className="w-4 h-4 text-medical-accent rounded focus:ring-medical-accent"
                />
                <label htmlFor="walk-in-toggle" className="text-sm font-medium text-medical-gray cursor-pointer">
                    Register as Walk-in Patient (No specific time slot)
                </label>
            </div>
            { }

            <div className="border-t border-gray-200 pt-4 space-y-4">
                <h3 className="text-lg font-semibold text-medical-dark">Appointment Details</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6"> { }
                    { }
                    <div>
                        <label className="custom-label required">Location</label>
                        <select
                            value={locationId}
                            onChange={(e) => { const newLocId = parseInt(e.target.value, 10); console.log('[AppointmentEditor] Location changed:', newLocId); setLocationId(newLocId); }}
                            className="custom-select"
                        >
                            <option value={1}>Home Clinic</option>
                            <option value={2}>Hospital</option>
                        </select>
                    </div>
                    { }
                    <DatePicker
                        label="Date"
                        value={appointmentDate}
                        onChange={(e) => { const newDate = e.target.value; console.log('[AppointmentEditor] Date changed:', newDate); setAppointmentDate(newDate); }}
                        minDate={new Date().toISOString().split('T')[0]}
                        required={true}
                        disabled={isWalkIn}
                    />
                    <div className={`md:col-span-3 ${isWalkIn ? 'opacity-50' : ''}`}> { }
                        <label className={`custom-label ${!isWalkIn ? 'required' : ''}`}>Time</label> { }
                        { }
                        {loadingSlots ? (
                            <LoadingSpinner />
                        ) : slotError ? (
                            <p className="text-medical-error text-sm p-3 bg-red-50 rounded-lg">{slotError}</p>
                        ) : (
                            <div className="flex flex-col space-y-2">
                                <div
                                    onClick={() => !isWalkIn ? setShowTimePicker(true) : null}
                                    className={`w-full px-3 py-2 border-2 rounded-lg text-sm text-center font-medium transition-all cursor-pointer 
                                        ${appointmentTime ? 'border-medical-accent bg-blue-50 text-medical-dark' : 'border-gray-300 text-medical-gray hover:border-medical-accent'} 
                                        ${isWalkIn ? 'bg-gray-100 cursor-not-allowed' : ''}`
                                    }
                                >
                                    {appointmentTime ? new Date(appointmentTime).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true }) : (slotError || 'Select Time Slot')}
                                </div>
                                {availableSlots.length > 0 && (
                                    <p className='text-xs text-medical-gray'>* {availableSlots.length} available slots not shown. Click above to pick a time.</p>
                                )}
                            </div>
                        )}

                        {showTimePicker && (
                            <TimeRangePicker
                                isOpen={showTimePicker}
                                onClose={() => setShowTimePicker(false)}
                                onConfirm={({ startTime, endTime }) => {
                                    setAppointmentTime(startTime); 
                                    setShowTimePicker(false);
                                }}
                                initialStartTime={appointmentTime}
                                initialEndTime={appointmentTime}
                            />
                        )}
                        { }
                    </div>
                </div>
                <div>
                    <label className="block text-sm font-medium text-medical-gray mb-2">Reason for Visit</label>
                    <textarea value={reason} onChange={(e) => setReason(e.target.value)} className="custom-textarea" rows="3" placeholder="Enter reason for appointment"></textarea>
                </div>
            </div>

            <div className="flex justify-end space-x-3">
                <button onClick={onClose} className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">Cancel</button>
                <button onClick={handleSubmit} className="medical-button px-4 py-2 text-white rounded-lg relative z-10">
                    Create Appointment
                </button>
            </div>
        </div>
    );
};

window.AppointmentEditor = AppointmentEditor;
export default AppointmentEditor;
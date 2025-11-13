import React from 'react';

const DatePicker = ({ label, value, onChange, minDate, required = false, disabled = false, placeholder = "Select Date" }) => (
    <div>
        {label && (
            <label className="custom-label">
                {label} {required && <span className="text-red-500">*</span>}
            </label>
        )}
        <div className="relative">
            <div className="absolute inset-y-0 end-0 top-0 flex items-center pe-3.5 pointer-events-none">
                <svg className="w-4 h-4 text-gray-500 dark:text-gray-400" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M20 4a2 2 0 0 0-2-2h-2V1a1 1 0 0 0-2 0v1h-3V1a1 1 0 0 0-2 0v1H6V1a1 1 0 0 0-2 0v1H2a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V4Zm-2 13H4V8h14v9Z"/>
                </svg>
            </div>
            <input
                type="text"
                data-input-type="date"
                value={value || ''}
                onChange={onChange}
                min={minDate}
                data-flatpickr-min-date={minDate}
                required={required}
                disabled={disabled}
                placeholder={placeholder}
                className={`form-input-themed custom-datetime ${disabled ? 'bg-gray-100 cursor-not-allowed' : ''}`}
            />
        </div>
    </div>
);

export default DatePicker;
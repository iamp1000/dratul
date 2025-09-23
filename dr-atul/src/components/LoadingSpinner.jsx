// src/components/ui/LoadingSpinner/LoadingSpinner.jsx
import React from 'react';

function LoadingSpinner({ size = 'medium', color = 'primary' }) {
    const sizeClasses = {
        small: 'w-4 h-4',
        medium: 'w-8 h-8',
        large: 'w-12 h-12'
    };

    const colorClasses = {
        primary: 'border-primary',
        white: 'border-white',
        gray: 'border-gray-500'
    };

    return (
        <div className="flex justify-center items-center">
            <div
                className={`
                    ${sizeClasses[size]} 
                    ${colorClasses[color]} 
                    border-2 border-opacity-20 border-solid rounded-full 
                    border-t-opacity-100 animate-spin
                `}
            ></div>
        </div>
    );
}

export default LoadingSpinner;
// src/components/ui/Modal/Modal.jsx
import React, { useEffect } from 'react';

function Modal({ isOpen, onClose, children }) {
    useEffect(() => {
        const handleEscape = (event) => {
            if (event.keyCode === 27) {
                onClose();
            }
        };

        if (isOpen) {
            document.addEventListener('keydown', handleEscape);
            document.body.style.overflow = 'hidden';
        }

        return () => {
            document.removeEventListener('keydown', handleEscape);
            document.body.style.overflow = 'unset';
        };
    }, [isOpen, onClose]);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Backdrop */}
            <div
                className="fixed inset-0 bg-black bg-opacity-50 backdrop-blur-sm"
                onClick={onClose}
            ></div>
            
            {/* Modal Content */}
            <div className="relative z-10 max-h-screen overflow-y-auto">
                <div className="p-4">
                    {children}
                </div>
            </div>
        </div>
    );
}

export default Modal;
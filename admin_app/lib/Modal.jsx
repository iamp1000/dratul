import React from 'react';

const Modal = ({ isOpen, onClose, title, children, width = "max-w-2xl" }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 modal-overlay">
      <div className={`bg-white rounded-2xl shadow-2xl ${width} max-h-[90vh] overflow-hidden animate-bounce-gentle flex flex-col`}>
        <div className="flex items-center justify-between p-6 border-b border-gray-200 flex-shrink-0">
          <h2 className="text-xl font-bold text-medical-dark font-primary">{title}</h2>
          <button onClick={onClose} className="text-medical-gray hover:text-medical-dark">
            <i className="fas fa-times text-xl"></i>
          </button>
        </div>
        <div className="p-6 overflow-y-auto scroll-custom flex-grow">{children}</div>
      </div>
    </div>
  );
};

export default Modal;
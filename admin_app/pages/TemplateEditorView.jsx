import React from 'react';

const TemplateEditorView = () => {
    return (
        <div className="space-y-6 animate-fade-in">
            <h2 className="text-2xl font-bold text-medical-dark font-primary">Consultation Templates</h2>

            <div className="medical-card p-6 rounded-2xl">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-xl font-bold text-medical-dark">Create New Template</h3>
                </div>
                <p className="text-medical-gray mb-4">
                    Use the form below to create a new template. Fill in any fields you want to be pre-loaded when you select this template during a consultation.
                </p>

                <div className="space-y-4">
                    <div>
                        <label className="custom-label required">Template Name</label>
                        <input
                            type="text"
                            placeholder="e.g., Diabetes Follow-up, First Visit Gynae"
                            className="form-input-themed"
                        />
                    </div>

                    <button className="medical-button px-6 py-3 text-white rounded-xl font-secondary flex items-center gap-2 relative z-10">
                        <i className="fas fa-save"></i>
                        <span>Save New Template</span>
                    </button>
                </div>
            </div>

            <div className="medical-card p-6 rounded-2xl">
                <h3 className="text-xl font-bold text-medical-dark mb-4">Existing Templates</h3>
                <p className="text-medical-gray">
                    (This area will show a list of your saved templates.)
                </p>
            </div>
        </div>
    );
};

window.TemplateEditorView = TemplateEditorView;

export default TemplateEditorView;
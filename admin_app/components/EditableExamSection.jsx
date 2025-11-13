const EditableExamSection = ({ sectionData, onFieldChange, onRemove }) => {
  const { templateName, fields } = sectionData;

  const handleChange = (e) => {
    const { name, value } = e.target;
    onFieldChange(name, value);
  };

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-xl overflow-hidden">
      <div className="flex items-center justify-between p-3 bg-gray-100 border-b border-gray-200">
        <h4 className="font-bold text-medical-dark">{templateName}</h4>
        <button
          onClick={onRemove}
          className="text-red-500 hover:text-red-700 p-1 rounded-full hover:bg-red-100"
          title="Remove this section"
        >
          <i className="fas fa-trash-alt"></i>
        </button>
      </div>

      <div className="p-4 space-y-6">
        <fieldset className="p-4 border border-gray-200 rounded-lg bg-white">
          <legend className="px-2 font-semibold text-gray-800">Thyroid Examination</legend>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <FormInput label="Palpation" name="thyroid_palpation" value={fields.thyroid_palpation} onChange={handleChange} placeholder="e.g., Diffuse, Nodular" />
            <FormInput label="Consistency" name="thyroid_consistency" value={fields.thyroid_consistency} onChange={handleChange} placeholder="e.g., Firm, Soft" />
            <FormInput label="Lymph Nodes" name="thyroid_lymph_nodes" value={fields.thyroid_lymph_nodes} onChange={handleChange} placeholder="e.g., Palpable" />
          </div>
          <div className="mt-4">
            <FormTextArea label="Thyroid Notes" name="thyroid_notes" value={fields.thyroid_notes} onChange={handleChange} placeholder="Additional observations..." rows={2} />
          </div>
        </fieldset>

        <fieldset className="p-4 border border-gray-200 rounded-lg bg-white">
          <legend className="px-2 font-semibold text-gray-800">Foot Examination</legend>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Right Foot</label>
              <div className="space-y-3">
                <FormInput label="Visual" name="foot_right_visual" value={fields.foot_right_visual} onChange={handleChange} placeholder="e.g., Color, Ulcers" />
                <FormInput label="Pulses (DP/PT)" name="foot_right_pulses" value={fields.foot_right_pulses} onChange={handleChange} placeholder="e.g., 2+/2+" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">Left Foot</label>
              <div className="space-y-3">
                <FormInput label="Visual" name="foot_left_visual" value={fields.foot_left_visual} onChange={handleChange} placeholder="e.g., Color, Ulcers" />
                <FormInput label="Pulses (DP/PT)" name="foot_left_pulses" value={fields.foot_left_pulses} onChange={handleChange} placeholder="e.g., 2+/2+" />
              </div>
            </div>
          </div>
          <div className="mt-4">
            <FormTextArea label="Foot Exam Notes" name="foot_exam_notes" value={fields.foot_exam_notes} onChange={handleChange} placeholder="Overall notes, footwear assessment..." rows={2} />
          </div>
        </fieldset>

        <fieldset className="p-4 border border-gray-200 rounded-lg bg-white">
          <legend className="px-2 font-semibold text-gray-800">Peripheral Neuropathy Assessment</legend>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormInput label="Monofilament Test (10g)" name="neuropathy_monofilament" value={fields.neuropathy_monofilament} onChange={handleChange} placeholder="e.g., R 8/10, L 9/10" />
            <FormInput label="Vibration (Tuning Fork)" name="neuropathy_vibration" value={fields.neuropathy_vibration} onChange={handleChange} placeholder="e.g., Diminished at ankles" />
          </div>
          <div className="mt-4">
            <FormTextArea label="Neuropathy Notes" name="neuropathy_notes" value={fields.neuropathy_notes} onChange={handleChange} placeholder="Additional findings, reflexes..." rows={2} />
          </div>
        </fieldset>

        <fieldset className="p-4 border border-gray-200 rounded-lg bg-white">
          <legend className="px-2 font-semibold text-gray-800">Fundus Exam</legend>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <FormInput label="Right Eye" name="fundus_right_eye" value={fields.fundus_right_eye} onChange={handleChange} placeholder="e.g., NPDR, PDR" />
            <FormInput label="Left Eye" name="fundus_left_eye" value={fields.fundus_left_eye} onChange={handleChange} placeholder="e.g., No retinopathy" />
          </div>
          <div className="mt-4">
            <FormTextArea label="Fundus Exam Notes" name="fundus_exam_notes" value={fields.fundus_exam_notes} onChange={handleChange} placeholder="e.g., Referred to ophthalmologist" rows={2} />
          </div>
        </fieldset>
      </div>
    </div>
  );
};

export default EditableExamSection;
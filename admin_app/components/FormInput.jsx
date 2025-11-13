const FormInput = ({ label, name, value, onChange, placeholder = "" }) => (
  <div>
    <label className="block text-sm font-semibold text-gray-700 mb-2">{label}</label>
    <input
      type="text"
      name={name}
      value={value || ''}
      onChange={onChange}
      placeholder={placeholder}
      className="w-full px-3 py-2 border-2 border-gray-200 rounded-lg focus:ring-2 focus:ring-teal-400 focus:border-transparent transition-all"
    />
  </div>
);

export default FormInput;
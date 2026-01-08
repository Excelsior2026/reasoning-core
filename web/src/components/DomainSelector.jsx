export function DomainSelector({ value, onChange }) {
  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-gray-700">
        Domain Type
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
      >
        <option value="generic">Generic</option>
        <option value="medical">Medical</option>
        <option value="business">Business</option>
        <option value="meeting">Meeting/Agenda</option>
      </select>
      <p className="text-xs text-gray-500">
        Select the domain type for specialized extraction
      </p>
    </div>
  )
}

import { ChevronDown } from 'lucide-react';
import { Language } from '../types';

interface LanguageSelectorProps {
  label: string;
  languages: Language[];
  selectedLanguage: string;
  onSelect: (code: string) => void;
  disabled?: boolean;
}

export const LanguageSelector = ({
  label,
  languages,
  selectedLanguage,
  onSelect,
  disabled,
}: LanguageSelectorProps) => {
  const selectedLang = languages.find((lang) => lang.code === selectedLanguage);

  return (
    <div className="flex flex-col space-y-2">
      <label className="text-sm font-medium text-gray-700">{label}</label>
      <div className="relative">
        <select
          value={selectedLanguage}
          onChange={(e) => onSelect(e.target.value)}
          disabled={disabled}
          className="w-full px-4 py-3 bg-white border-2 border-gray-300 rounded-lg appearance-none cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 hover:border-gray-400"
        >
          {languages.map((lang) => (
            <option key={lang.code} value={lang.code}>
              {lang.name}
            </option>
          ))}
        </select>
        <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-500 pointer-events-none" />
      </div>
    </div>
  );
};

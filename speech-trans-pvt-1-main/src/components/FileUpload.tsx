import { useRef, useState } from 'react';
import { Upload, X, FileAudio } from 'lucide-react';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  selectedFile: File | null;
  onClear: () => void;
  disabled?: boolean;
}

export const FileUpload = ({ onFileSelect, selectedFile, onClear, disabled }: FileUploadProps) => {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) {
      setIsDragging(true);
    }
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    if (disabled) return;

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      onFileSelect(files[0]);
    }
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      onFileSelect(files[0]);
    }
  };

  const handleClick = () => {
    if (!disabled) {
      fileInputRef.current?.click();
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <div className="w-full">
      {!selectedFile ? (
        <div
          onClick={handleClick}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`
            relative border-2 border-dashed rounded-xl p-12 text-center cursor-pointer
            transition-all duration-200 ease-in-out
            ${isDragging
              ? 'border-blue-500 bg-blue-50 scale-[1.02]'
              : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
            }
            ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
          `}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".wav,.mp3,.m4a,.flac,audio/wav,audio/mpeg,audio/mp4,audio/x-m4a,audio/flac"
            onChange={handleFileInput}
            className="hidden"
            disabled={disabled}
          />

          <div className="flex flex-col items-center space-y-4">
            <div className={`
              p-4 rounded-full transition-colors duration-200
              ${isDragging ? 'bg-blue-100' : 'bg-gray-100'}
            `}>
              <Upload className={`
                w-8 h-8 transition-colors duration-200
                ${isDragging ? 'text-blue-600' : 'text-gray-500'}
              `} />
            </div>

            <div>
              <p className="text-lg font-medium text-gray-700 mb-1">
                Drop audio file here or click to browse
              </p>
              <p className="text-sm text-gray-500">
                Supported formats: WAV, MP3, M4A, FLAC (max 50MB)
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="border-2 border-blue-200 bg-blue-50 rounded-xl p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4 flex-1 min-w-0">
              <div className="p-3 bg-blue-100 rounded-lg flex-shrink-0">
                <FileAudio className="w-6 h-6 text-blue-600" />
              </div>

              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-900 truncate">
                  {selectedFile.name}
                </p>
                <p className="text-sm text-gray-600">
                  {formatFileSize(selectedFile.size)}
                </p>
              </div>
            </div>

            <button
              onClick={onClear}
              disabled={disabled}
              className="ml-4 p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0"
              aria-label="Remove file"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

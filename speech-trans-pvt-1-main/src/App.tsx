import { useState } from 'react';
import { Globe, Loader2 } from 'lucide-react';
import { FileUpload } from './components/FileUpload';
import { AudioRecorder } from './components/AudioRecorder';
import { LanguageSelector } from './components/LanguageSelector';
import { AudioPlayer } from './components/AudioPlayer';
import { ToastContainer } from './components/Toast';
import { translateAudio, validateAudioFile } from './services/api';
import { LANGUAGES } from './constants/languages';
import { ToastMessage, TranslationResult } from './types';

function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [sourceLanguage, setSourceLanguage] = useState('auto');
  const [targetLanguage, setTargetLanguage] = useState('es');
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<TranslationResult | null>(null);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const addToast = (type: 'success' | 'error' | 'info', message: string) => {
    const id = Date.now().toString();
    setToasts((prev) => [...prev, { id, type, message }]);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  };

  const handleFileSelect = (file: File) => {
    const validation = validateAudioFile(file);
    if (!validation.valid) {
      addToast('error', validation.error || 'Invalid file');
      return;
    }
    setSelectedFile(file);
    addToast('success', 'Audio file loaded successfully');
  };

  const handleClearFile = () => {
    setSelectedFile(null);
    setResult(null);
  };

  const handleRecordingComplete = (file: File) => {
    setSelectedFile(file);
    addToast('success', 'Recording saved successfully');
  };

  const handleTranslate = async () => {
    if (!selectedFile) return;

    setIsProcessing(true);
    setProgress(0);
    setResult(null);

    try {
      const { blob, processingTime } = await translateAudio(
        selectedFile,
        (prog) => setProgress(Math.round(prog))
      );

      const audioUrl = URL.createObjectURL(blob);
      const fileName = `translated-${selectedFile.name}`;

      setResult({ audioBlob: blob, audioUrl, processingTime, fileName });
      addToast('success', 'Translation completed successfully!');
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : 'Translation failed';
      addToast('error', errorMessage);
      console.error('Translation error:', error);
    } finally {
      setIsProcessing(false);
      setProgress(0);
    }
  };

  const handleReset = () => {
    setSelectedFile(null);
    setResult(null);
    setProgress(0);
  };

  const canTranslate = selectedFile && !isProcessing;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100">
      <ToastContainer toasts={toasts} onClose={removeToast} />

      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <header className="text-center mb-12">
          <div className="flex items-center justify-center mb-4">
            <div className="p-3 bg-blue-600 rounded-2xl shadow-lg">
              <Globe className="w-8 h-8 text-white" />
            </div>
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Speech Translation Studio
          </h1>
          <p className="text-lg text-gray-600">
            Transform your voice across languages with AI-powered translation
          </p>
        </header>

        {!result ? (
          <div className="bg-white rounded-2xl shadow-xl p-8 space-y-8">
            <div>
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Upload Audio
              </h2>
              <FileUpload
                onFileSelect={handleFileSelect}
                selectedFile={selectedFile}
                onClear={handleClearFile}
                disabled={isProcessing}
              />
            </div>

            {!selectedFile && (
              <div className="flex items-center space-x-4">
                <div className="flex-1 h-px bg-gray-200" />
                <span className="text-sm text-gray-500 font-medium">OR</span>
                <div className="flex-1 h-px bg-gray-200" />
              </div>
            )}

            {!selectedFile && (
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-4">
                  Record Audio
                </h2>
                <AudioRecorder
                  onRecordingComplete={handleRecordingComplete}
                  disabled={isProcessing}
                />
              </div>
            )}

            {selectedFile && (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <LanguageSelector
                    label="Source Language"
                    languages={LANGUAGES}
                    selectedLanguage={sourceLanguage}
                    onSelect={setSourceLanguage}
                    disabled={isProcessing}
                  />
                  <LanguageSelector
                    label="Target Language"
                    languages={LANGUAGES.filter((lang) => lang.code !== 'auto')}
                    selectedLanguage={targetLanguage}
                    onSelect={setTargetLanguage}
                    disabled={isProcessing}
                  />
                </div>

                <div className="pt-4">
                  <button
                    onClick={handleTranslate}
                    disabled={!canTranslate}
                    className="w-full py-4 bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-xl font-semibold text-lg hover:from-blue-700 hover:to-blue-800 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-[1.02] disabled:transform-none flex items-center justify-center space-x-3"
                  >
                    {isProcessing ? (
                      <>
                        <Loader2 className="w-6 h-6 animate-spin" />
                        <span>Processing... {progress}%</span>
                      </>
                    ) : (
                      <>
                        <Globe className="w-6 h-6" />
                        <span>Translate Audio</span>
                      </>
                    )}
                  </button>

                  {isProcessing && (
                    <div className="mt-4">
                      <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-blue-600 to-blue-500 h-2 transition-all duration-300 ease-out"
                          style={{ width: `${progress}%` }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        ) : (
          <AudioPlayer
            audioUrl={result.audioUrl}
            fileName={result.fileName}
            processingTime={result.processingTime}
            onReset={handleReset}
          />
        )}

        <footer className="mt-12 text-center text-sm text-gray-500">
          <p>Powered by advanced AI speech translation technology</p>
        </footer>
      </div>
    </div>
  );
}

export default App;

export interface Language {
  code: string;
  name: string;
}

export interface AudioFile {
  file: File;
  url: string;
  duration?: number;
}

export interface TranslationResult {
  audioBlob: Blob;
  audioUrl: string;
  processingTime: number;
  fileName: string;
}

export interface ProcessingState {
  isProcessing: boolean;
  progress: number;
  error: string | null;
}

export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'info';
  message: string;
}

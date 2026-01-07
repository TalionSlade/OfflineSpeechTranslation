const API_BASE_URL = 'http://localhost:8000';

export const translateAudio = async (
  audioFile: File,
  onProgress?: (progress: number) => void
): Promise<{ blob: Blob; processingTime: number }> => {
  const startTime = Date.now();
  const formData = new FormData();
  formData.append('file', audioFile);

  try {
    const xhr = new XMLHttpRequest();

    return new Promise((resolve, reject) => {
      xhr.upload.addEventListener('progress', (event) => {
        if (event.lengthComputable && onProgress) {
          const uploadProgress = (event.loaded / event.total) * 50;
          onProgress(uploadProgress);
        }
      });

      xhr.addEventListener('progress', (event) => {
        if (event.lengthComputable && onProgress) {
          const downloadProgress = 50 + (event.loaded / event.total) * 50;
          onProgress(downloadProgress);
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          const processingTime = Date.now() - startTime;
          const blob = xhr.response;
          resolve({ blob, processingTime });
        } else {
          reject(new Error(`Server error: ${xhr.status}`));
        }
      });

      xhr.addEventListener('error', () => {
        reject(new Error('Network error occurred'));
      });

      xhr.addEventListener('timeout', () => {
        reject(new Error('Request timeout'));
      });

      xhr.open('POST', `${API_BASE_URL}/v1/process`);
      xhr.responseType = 'blob';
      xhr.timeout = 120000;
      xhr.send(formData);
    });
  } catch (error) {
    throw new Error(
      error instanceof Error ? error.message : 'Failed to process audio'
    );
  }
};

export const validateAudioFile = (file: File): { valid: boolean; error?: string } => {
  const maxSize = 50 * 1024 * 1024;
  const allowedFormats = ['audio/wav', 'audio/mpeg', 'audio/mp4', 'audio/x-m4a', 'audio/flac'];
  const allowedExtensions = ['.wav', '.mp3', '.m4a', '.flac'];

  if (file.size > maxSize) {
    return { valid: false, error: 'File size exceeds 50MB limit' };
  }

  const hasValidType = allowedFormats.includes(file.type);
  const hasValidExtension = allowedExtensions.some(ext =>
    file.name.toLowerCase().endsWith(ext)
  );

  if (!hasValidType && !hasValidExtension) {
    return { valid: false, error: 'Unsupported file format. Please use WAV, MP3, M4A, or FLAC' };
  }

  return { valid: true };
};

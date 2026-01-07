import { useState, useRef, useEffect } from 'react';
import { Mic, Square, Circle } from 'lucide-react';

interface AudioRecorderProps {
  onRecordingComplete: (file: File) => void;
  disabled?: boolean;
}

export const AudioRecorder = ({ onRecordingComplete, disabled }: AudioRecorderProps) => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const audioFile = new File([audioBlob], `recording-${timestamp}.wav`, {
          type: 'audio/wav',
        });
        onRecordingComplete(audioFile);

        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);

      timerRef.current = window.setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    } catch (error) {
      console.error('Error accessing microphone:', error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsPaused(false);

      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  };

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="flex items-center justify-center">
      {!isRecording ? (
        <button
          onClick={startRecording}
          disabled={disabled}
          className="flex items-center space-x-3 px-6 py-3 bg-white border-2 border-gray-300 text-gray-700 rounded-xl hover:border-blue-500 hover:bg-blue-50 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed group"
        >
          <Mic className="w-5 h-5 group-hover:text-blue-600 transition-colors" />
          <span className="font-medium">Record Audio</span>
        </button>
      ) : (
        <div className="flex items-center space-x-4 px-6 py-4 bg-red-50 border-2 border-red-200 rounded-xl">
          <div className="flex items-center space-x-3">
            <div className="relative">
              <Circle className="w-5 h-5 text-red-600 fill-current animate-pulse" />
            </div>
            <span className="font-mono text-lg font-medium text-gray-900">
              {formatTime(recordingTime)}
            </span>
          </div>

          <button
            onClick={stopRecording}
            className="flex items-center space-x-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            <Square className="w-4 h-4 fill-current" />
            <span className="font-medium">Stop</span>
          </button>
        </div>
      )}
    </div>
  );
};

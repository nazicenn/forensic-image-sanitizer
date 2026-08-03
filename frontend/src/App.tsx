import React, { useState } from 'react';
import { Upload, CheckCircle, XCircle, Loader2, Sun, Moon, FileImage, Download } from 'lucide-react';
import { useDropzone } from 'react-dropzone';
import toast, { Toaster } from 'react-hot-toast';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface JobStatus {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  original_filename: string;
  processed_filename?: string;
  error_message?: string;
}

function App() {
  const [darkMode, setDarkMode] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [job, setJob] = useState<JobStatus | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [cleanLevel, setCleanLevel] = useState('medium');

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'image/*': ['.jpg', '.jpeg', '.png', '.webp', '.tiff']
    },
    maxSize: 50 * 1024 * 1024,
    onDrop: (acceptedFiles) => {
      const file = acceptedFiles[0];
      if (file) {
        setFile(file);
        toast.success(`📎 ${file.name} added`);
      }
    },
    onDropRejected: (rejections) => {
      const error = rejections[0]?.errors[0];
      if (error?.code === 'file-too-large') {
        toast.error('File too large! Maximum 50MB');
      } else {
        toast.error('Invalid file type. Please upload an image.');
      }
    }
  });

  const handleUpload = async () => {
    if (!file) {
      toast.error('Please select an image first');
      return;
    }

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('clean_level', cleanLevel);

    try {
      const response = await axios.post(`${API_URL}/api/v1/upload/`, formData, {
        headers: {
  'Content-Type': 'multipart/form-data',
'X-API-Key': import.meta.env.VITE_API_KEY || 'test-key',},
      });

      const data = response.data;
      setJob({
        id: data.job_id,
        status: 'pending',
        progress: 0,
        original_filename: data.original_filename,
      });

      toast.success('✅ Upload successful! Processing started.');
      pollJobStatus(data.job_id);
    } catch (error) {
      toast.error('Upload failed. Please try again.');
      setUploading(false);
    }
  };

  const pollJobStatus = async (jobId: string) => {
    const interval = setInterval(async () => {
      try {
        const response = await axios.get(`${API_URL}/api/v1/status/${jobId}`);
        const data = response.data;
        
        setJob((prev) => ({
          ...prev!,
          status: data.status,
          progress: data.progress || 0,
          processed_filename: data.processed_filename,
          error_message: data.error_message,
        }));

        if (data.status === 'completed' || data.status === 'failed') {
          clearInterval(interval);
          setUploading(false);
          if (data.status === 'completed') {
            toast.success('🎉 Image processed successfully!');
          } else {
            toast.error('❌ Processing failed: ' + (data.error_message || 'Unknown error'));
          }
        }
      } catch (error) {
        console.error('Polling error:', error);
      }
    }, 2000);
  };

  const handleDownload = () => {
    if (job?.processed_filename) {
      window.open(`${API_URL}/api/v1/download/${job.id}`, '_blank');
    }
  };

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    document.documentElement.classList.toggle('dark');
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-500';
      case 'failed': return 'text-red-500';
      case 'processing': return 'text-blue-500';
      default: return 'text-yellow-500';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="w-6 h-6 text-green-500" />;
      case 'failed': return <XCircle className="w-6 h-6 text-red-500" />;
      case 'processing': return <Loader2 className="w-6 h-6 text-blue-500 animate-spin" />;
      default: return <Loader2 className="w-6 h-6 text-yellow-500 animate-pulse" />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
      <Toaster position="top-right" />

      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <div className="flex items-center gap-3">
            <FileImage className="w-8 h-8 text-blue-500" />
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">
              Forensic Image Sanitizer
            </h1>
            <span className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 px-2 py-1 rounded-full">
              AI Forensics
            </span>
          </div>
          <button
            onClick={toggleDarkMode}
            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-6">
          {/* Upload Section */}
          <div className="card">
            <h2 className="text-lg font-semibold mb-4">Upload Image</h2>
            
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200 ${
                isDragActive
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                  : 'border-gray-300 dark:border-gray-600 hover:border-blue-400 dark:hover:border-blue-500'
              }`}
            >
              <input {...getInputProps()} />
              <FileImage className="w-12 h-12 mx-auto text-gray-400 dark:text-gray-500 mb-4" />
              {file ? (
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">{file.name}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              ) : (
                <div>
                  <p className="text-gray-600 dark:text-gray-300">
                    {isDragActive ? 'Drop your image here' : 'Drag & drop an image here, or click to select'}
                  </p>
                  <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                    Supports JPG, PNG, WEBP, TIFF (Max 50MB)
                  </p>
                </div>
              )}
            </div>

            <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Clean Level
                </label>
                <select
                  value={cleanLevel}
                  onChange={(e) => setCleanLevel(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                >
                  <option value="light">Light</option>
                  <option value="medium">Medium</option>
                  <option value="aggressive">Aggressive</option>
                  <option value="forensic">Forensic</option>
                </select>
              </div>
              <div className="flex items-end">
                <button
                  onClick={handleUpload}
                  disabled={!file || uploading}
                  className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {uploading ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Upload className="w-4 h-4" />
                  )}
                  {uploading ? 'Uploading...' : 'Upload & Process'}
                </button>
              </div>
            </div>
          </div>

          {/* Status Section */}
          {job && (
            <div className="card">
              <h2 className="text-lg font-semibold mb-4">Processing Status</h2>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {getStatusIcon(job.status)}
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white capitalize">
                        {job.status}
                      </p>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {job.original_filename}
                      </p>
                    </div>
                  </div>
                  <span className={`font-semibold ${getStatusColor(job.status)}`}>
                    {job.progress}%
                  </span>
                </div>

                {/* Progress Bar */}
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-blue-500 rounded-full h-2 transition-all duration-500"
                    style={{ width: `${job.progress}%` }}
                  />
                </div>

                {job.error_message && (
                  <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-3">
                    <p className="text-sm text-red-600 dark:text-red-400">
                      ❌ {job.error_message}
                    </p>
                  </div>
                )}

                {job.status === 'completed' && job.processed_filename && (
                  <button
                    onClick={handleDownload}
                    className="w-full px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors duration-200 flex items-center justify-center gap-2"
                  >
                    <Download className="w-4 h-4" />
                    Download Processed Image
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Features Section */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="card text-center">
              <div className="text-3xl mb-2">🛡️</div>
              <h3 className="font-semibold text-gray-900 dark:text-white">Metadata Clean</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">Remove EXIF, IPTC, XMP, GPS</p>
            </div>
            <div className="card text-center">
              <div className="text-3xl mb-2">🔍</div>
              <h3 className="font-semibold text-gray-900 dark:text-white">AI Trace Removal</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">GAN, Diffusion, Fingerprints</p>
            </div>
            <div className="card text-center">
              <div className="text-3xl mb-2">📊</div>
              <h3 className="font-semibold text-gray-900 dark:text-white">Quality Preserved</h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">SSIM ≥ 0.95, PSNR ≥ 35dB</p>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-12 py-6 text-center text-sm text-gray-500 dark:text-gray-400 border-t border-gray-200 dark:border-gray-700">
        <p>Forensic Image Sanitizer v0.1.0 — AI Image Forensics Tool</p>
      </footer>
    </div>
  );
}

export default App;
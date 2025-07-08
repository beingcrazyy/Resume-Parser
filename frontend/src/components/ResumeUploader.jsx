import React, { useState } from 'react';
import axios from 'axios';
import { TransitionGroup, CSSTransition } from 'react-transition-group';
import Toast from './Toast';
import DragDropZone from './DragDropZone';
import './DragDropAnimation.css';

const ResumeUploader = () => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [toast, setToast] = useState(null);
  const [uploadProgress, setUploadProgress] = useState({});
  const [uploadStatus, setUploadStatus] = useState(null);
  const [uploadedData, setUploadedData] = useState(null);
  const [jobDescription, setJobDescription] = useState("");
  const [jobDescriptionFile, setJobDescriptionFile] = useState(null);

  const handleFilesDrop = (acceptedFiles) => {
    setFiles(acceptedFiles);
    setToast(null);
    setUploadProgress({});
    setUploadedData(null);
  };

  const handleJobDescriptionChange = (e) => {
    setJobDescription(e.target.value);
    setJobDescriptionFile(null);
  };
  const handleJobDescriptionFileChange = (e) => {
    setJobDescriptionFile(e.target.files[0]);
    setJobDescription("");
  };

  const uploadJobDescription = async () => {
    if (!jobDescription && !jobDescriptionFile) return;
    const formData = new FormData();
    if (jobDescriptionFile) {
      formData.append("file", jobDescriptionFile);
    } else {
      formData.append("description", jobDescription);
    }
    await axios.post("http://localhost:8000/upload_job_description", formData, {
      headers: { "Content-Type": "multipart/form-data" }
    });
  };

  const uploadFiles = async () => {
    if (files.length === 0) return;
    setUploading(true);
    setUploadStatus(null);
    try {
      await uploadJobDescription();
    } catch (e) {
      setToast({ type: 'error', message: 'Failed to upload job description' });
      setUploading(false);
      return;
    }
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });
    try {
      const response = await axios.post('http://localhost:8000/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(prev => ({ ...prev, total: percentCompleted }));
        }
      });
      setToast({
        type: 'success',
        message: 'Files uploaded successfully!'
      });
      setUploadedData(response.data);
    } catch (error) {
      setToast({
        type: 'error',
        message: error.response?.data?.error || 'Error uploading files'
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="mb-6">
        <label className="block text-lg font-semibold mb-2">Job Description</label>
        <textarea
          className="w-full p-2 border rounded mb-2"
          rows={4}
          placeholder="Paste job description here or upload a file"
          value={jobDescription}
          onChange={handleJobDescriptionChange}
          disabled={uploading}
        />
        <input
          type="file"
          accept=".pdf,.docx,.txt"
          onChange={handleJobDescriptionFileChange}
          disabled={uploading}
        />
      </div>
      <DragDropZone
        onFilesDrop={handleFilesDrop}
        accept={{
          'application/pdf': ['.pdf'],
          'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
        }}
      />
      {files.length > 0 && (
        <div className="mt-6">
          <h3 className="text-lg font-semibold mb-3">Selected Files:</h3>
          <TransitionGroup component="ul" className="space-y-2">
            {files.map(file => (
              <CSSTransition
                key={file.name}
                timeout={300}
                classNames="file-item"
              >
                <li className="flex items-center justify-between p-3 bg-gray-50 rounded shadow-sm hover:shadow-md transition-shadow duration-200">
                  <div className="flex items-center space-x-3">
                    <span className="text-xl">{file.name.toLowerCase().endsWith('.pdf') ? '📄' : '📝'}</span>
                    <span className="truncate">{file.name}</span>
                  </div>
                  <span className="text-sm text-gray-500 flex items-center">
                    <span className="px-2 py-1 bg-gray-200 rounded-full">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </span>
                  </span>
                </li>
              </CSSTransition>
            ))}
          </TransitionGroup>
          <button
            onClick={uploadFiles}
            disabled={uploading}
            className={`mt-4 px-6 py-2 rounded-lg text-white ${
              uploading
                ? 'bg-blue-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {uploading ? 'Uploading...' : 'Upload Files'}
          </button>
          {uploadProgress.total && uploading && (
            <div className="mt-4">
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div
                  className="bg-blue-600 h-2.5 rounded-full transition-all"
                  style={{ width: `${uploadProgress.total}%` }}
                ></div>
              </div>
              <p className="text-sm text-gray-600 mt-1">
                {uploadProgress.total}% uploaded
              </p>
            </div>
          )}
          {uploadedData && (
            <div className="mt-6 bg-white rounded-lg shadow p-6">
              <h3 className="text-xl font-semibold mb-4">Parsed Resume Data</h3>
              {uploadedData.files.map((file, index) => (
                <div key={index} className="mb-6 last:mb-0">
                  <h4 className="text-lg font-medium mb-2">{file.filename}</h4>
                  <div className="bg-gray-50 rounded p-4">
                    <pre className="whitespace-pre-wrap text-sm text-gray-700 overflow-auto">
                      {JSON.stringify(file.parsed_resume, null, 2)}
                    </pre>
                  </div>
                </div>
              ))}
            </div>
          )}
          {toast && (
            <Toast
              type={toast.type}
              message={toast.message}
              onClose={() => setToast(null)}
            />
          )}
        </div>
      )}
    </div>
  );
};

export default ResumeUploader;
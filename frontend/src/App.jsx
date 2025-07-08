import React from 'react';
import ResumeUploader from './components/ResumeUploader';

function App() {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto px-4">
        <h1 className="text-3xl font-bold text-center text-gray-800 mb-8">
          Resume Parser
        </h1>
        <ResumeUploader />
      </div>
    </div>
  );
}

export default App;
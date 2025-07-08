import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import './DragDropAnimation.css';

const DragDropZone = ({ onFilesDrop, accept }) => {
  const [isDraggingOver, setIsDraggingOver] = useState(false);

  const onDrop = useCallback(
    (acceptedFiles) => {
      setIsDraggingOver(false);
      onFilesDrop(acceptedFiles);
    },
    [onFilesDrop]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept,
    multiple: true,
    onDragEnter: () => setIsDraggingOver(true),
    onDragLeave: () => setIsDraggingOver(false)
  });

  const getZoneStyle = () => {
    if (isDraggingOver) {
      return 'border-blue-500 bg-blue-50';
    }
    if (isDragActive) {
      return 'border-green-500 bg-green-50';
    }
    return 'border-gray-300 hover:border-gray-400 hover:bg-gray-50';
  };

  return (
    <div
      {...getRootProps()}
      className={`
        border-2 border-dashed rounded-lg p-8
        transition-all duration-200 ease-in-out
        cursor-pointer text-center
        ${getZoneStyle()}
        ${isDraggingOver ? 'drag-over' : ''}
        ${isDragActive ? 'drag-active' : ''}
      `}
    >
      <input {...getInputProps()} />
      <div className="space-y-2">
        <div className="text-4xl text-gray-400 drag-icon">
          {isDraggingOver ? '📄' : '📁'}
        </div>
        <div className="text-gray-600">
          {isDraggingOver ? (
            <p className="text-blue-600 font-medium">Drop files here!</p>
          ) : isDragActive ? (
            <p className="text-green-600">Drop the files here ...</p>
          ) : (
            <>
              <p className="font-medium">Drag & drop resume files here</p>
              <p className="text-sm text-gray-500 mt-1">or click to browse</p>
            </>
          )}
        </div>
        <div className="text-xs text-gray-500 mt-2">
          Supported formats: PDF, DOCX
        </div>
      </div>
    </div>
  );
};

export default DragDropZone;
import React, { useState } from 'react';
import Papa from 'papaparse';

interface BulkImportModalProps {
  institutionId: string;
  onClose: () => void;
  onSuccess: (data: any) => void;
}

interface CSVRow {
  name: string;
  email: string;
  tutor_email: string;
}

export const BulkImportModal: React.FC<BulkImportModalProps> = ({
  institutionId,
  onClose,
  onSuccess
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<CSVRow[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    if (!selectedFile.name.endsWith('.csv')) {
      setError('Please select a CSV file');
      return;
    }

    setFile(selectedFile);
    setError(null);

    // Parse CSV for preview
    Papa.parse(selectedFile, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => {
        if (results.errors.length > 0) {
          setError(`CSV parsing error: ${results.errors[0].message}`);
          return;
        }

        // Validate required columns
        const requiredColumns = ['name', 'email', 'tutor_email'];
        const headers = results.meta.fields || [];

        for (const requiredCol of requiredColumns) {
          if (!headers.includes(requiredCol)) {
            setError(`Missing required column: ${requiredCol}`);
            return;
          }
        }

        // Show first 5 rows for preview
        const previewData = results.data.slice(0, 5) as CSVRow[];
        setPreview(previewData);
      },
      error: (err) => {
        setError(`Failed to parse CSV file: ${err.message}`);
      }
    });
  };

  const handleImport = async () => {
    if (!file) return;

    setIsProcessing(true);
    setError(null);

    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      complete: async (results) => {
        try {
          if (results.errors.length > 0) {
            throw new Error(`CSV error: ${results.errors[0].message}`);
          }

          // Validate data before sending
          const csvData = results.data as CSVRow[];
          const validRows = csvData.filter(row =>
            row.name && row.email && row.tutor_email
          );

          if (validRows.length === 0) {
            throw new Error('No valid rows found in CSV');
          }

          const response = await fetch('/learners/bulk-import', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              institution_id: institutionId,
              learners: validRows
            })
          });

          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Bulk import failed');
          }

          const data = await response.json();
          onSuccess(data);
        } catch (err: any) {
          setError(err.message);
          setIsProcessing(false);
        }
      }
    });
  };

  const downloadSampleCSV = () => {
    const sampleData = [
      { name: 'John Doe', email: 'john.doe@student.edu', tutor_email: 'tutor@university.edu' },
      { name: 'Jane Smith', email: 'jane.smith@student.edu', tutor_email: 'tutor@university.edu' }
    ];

    const csv = Papa.unparse(sampleData);
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'sample_learners.csv';
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content bulk-import-modal">
        <div className="modal-header">
          <h2>Bulk Import Learners</h2>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="instructions">
          <p>Upload a CSV file with the following columns:</p>
          <ul>
            <li><strong>name</strong> - Learner's full name</li>
            <li><strong>email</strong> - Email address</li>
            <li><strong>tutor_email</strong> - Assigned tutor's email</li>
          </ul>
          <button
            type="button"
            className="btn btn-link"
            onClick={downloadSampleCSV}
          >
            Download Sample CSV
          </button>
        </div>

        <div className="file-upload">
          <input
            type="file"
            accept=".csv"
            onChange={handleFileSelect}
            id="csv-file"
          />
          <label htmlFor="csv-file" className="file-upload-label">
            Choose CSV File
          </label>
        </div>

        {preview.length > 0 && (
          <div className="preview">
            <h3>Preview (first 5 rows)</h3>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Tutor Email</th>
                  </tr>
                </thead>
                <tbody>
                  {preview.map((row, i) => (
                    <tr key={i}>
                      <td>{row.name}</td>
                      <td>{row.email}</td>
                      <td>{row.tutor_email}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {preview.length < 5 && (
              <p className="preview-note">
                Showing {preview.length} rows. Upload to see all data.
              </p>
            )}
          </div>
        )}

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <div className="modal-actions">
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onClose}
          >
            Cancel
          </button>
          <button
            className="btn btn-primary"
            onClick={handleImport}
            disabled={!file || isProcessing || preview.length === 0}
          >
            {isProcessing ? 'Importing...' : `Import ${preview.length} Learners`}
          </button>
        </div>
      </div>
    </div>
  );
};

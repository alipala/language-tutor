'use client';

import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  Download, FileText, Database, History, Package, 
  CheckCircle, AlertCircle, Loader2, X, Info
} from 'lucide-react';
import { getApiUrl } from '@/lib/api-utils';

interface ExportModalProps {
  isOpen: boolean;
  onClose: () => void;
  userName: string;
  userStats?: {
    learningPlans: number;
    conversations: number;
    assessments: number;
  };
}

interface ExportOption {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  formats: string[];
  endpoint: string;
  color: string;
}

interface ExportProgress {
  isExporting: boolean;
  currentExport: string | null;
  progress: number;
  status: 'idle' | 'preparing' | 'generating' | 'downloading' | 'complete' | 'error';
  error: string | null;
}

export default function ExportModal({ isOpen, onClose, userName }: ExportModalProps) {
  const [exportProgress, setExportProgress] = useState<ExportProgress>({
    isExporting: false,
    currentExport: null,
    progress: 0,
    status: 'idle',
    error: null
  });

  const exportOptions: ExportOption[] = [
    {
      id: 'assessments',
      title: 'Assessment & Learning Plans',
      description: 'Export your speaking assessments, skill scores, and personalized learning plans',
      icon: <FileText className="h-6 w-6" />,
      formats: ['PDF', 'JSON', 'CSV'],
      endpoint: '/api/export/learning-plans',
      color: 'bg-gradient-to-r from-blue-500 to-teal-600'
    },
    {
      id: 'conversations',
      title: 'Conversation History & Analysis',
      description: 'Export your practice sessions, summaries, and enhanced AI analysis',
      icon: <History className="h-6 w-6" />,
      formats: ['PDF', 'JSON', 'CSV'],
      endpoint: '/api/export/conversations',
      color: 'bg-gradient-to-r from-green-500 to-emerald-600'
    }
  ];

  const handleExport = async (option: ExportOption, format: string) => {
    setExportProgress({
      isExporting: true,
      currentExport: `${option.title} (${format})`,
      progress: 0,
      status: 'preparing',
      error: null
    });

    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('Authentication required');
      }

      // Update progress
      setExportProgress(prev => ({ ...prev, progress: 25, status: 'generating' }));

      const apiUrl = getApiUrl();
      const response = await fetch(`${apiUrl}${option.endpoint}?format=${format.toLowerCase()}`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Export failed: ${response.status}`);
      }

      // Update progress
      setExportProgress(prev => ({ ...prev, progress: 75, status: 'downloading' }));

      // Get filename from Content-Disposition header or create default
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = `${option.id}_${userName.replace(/\s+/g, '_')}.${format.toLowerCase()}`;
      
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, '');
        }
      }

      // Create blob and download
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      // Complete
      setExportProgress(prev => ({ ...prev, progress: 100, status: 'complete' }));
      
      // Reset after 2 seconds
      setTimeout(() => {
        setExportProgress({
          isExporting: false,
          currentExport: null,
          progress: 0,
          status: 'idle',
          error: null
        });
      }, 2000);

    } catch (error: any) {
      console.error('Export error:', error);
      setExportProgress(prev => ({
        ...prev,
        status: 'error',
        error: error.message || 'Export failed'
      }));
    }
  };

  const resetExport = () => {
    setExportProgress({
      isExporting: false,
      currentExport: null,
      progress: 0,
      status: 'idle',
      error: null
    });
  };

  const getStatusIcon = () => {
    switch (exportProgress.status) {
      case 'preparing':
      case 'generating':
      case 'downloading':
        return <Loader2 className="h-4 w-4 animate-spin" />;
      case 'complete':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return null;
    }
  };

  const getStatusText = () => {
    switch (exportProgress.status) {
      case 'preparing':
        return 'Preparing export...';
      case 'generating':
        return 'Generating document...';
      case 'downloading':
        return 'Starting download...';
      case 'complete':
        return 'Export completed!';
      case 'error':
        return `Error: ${exportProgress.error}`;
      default:
        return '';
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center text-2xl font-bold text-gray-800">
            <Download className="h-6 w-6 mr-2 text-blue-600" />
            Export Learning Journey
          </DialogTitle>
        </DialogHeader>

        {/* Export Progress */}
        {exportProgress.isExporting && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center">
                {getStatusIcon()}
                <span className="ml-2 font-medium text-blue-800">
                  {exportProgress.currentExport}
                </span>
              </div>
              {exportProgress.status === 'error' && (
                <Button
                  onClick={resetExport}
                  variant="outline"
                  size="sm"
                  className="text-red-600 border-red-300"
                >
                  <X className="h-3 w-3 mr-1" />
                  Dismiss
                </Button>
              )}
            </div>
            <div className="mb-2">
              <Progress value={exportProgress.progress} className="h-2" />
            </div>
            <p className="text-sm text-blue-700">{getStatusText()}</p>
          </div>
        )}

        {/* Info Banner */}
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
          <div className="flex items-start">
            <Info className="h-5 w-5 text-amber-600 mt-0.5 mr-2 flex-shrink-0" />
            <div className="text-sm text-amber-800">
              <p className="font-medium mb-1">Export Your Learning Data</p>
              <p>
                Download your language learning progress in various formats. PDF reports provide 
                a comprehensive overview, while CSV files are perfect for data analysis.
              </p>
            </div>
          </div>
        </div>

        {/* Export Options */}
        <div className="space-y-6">
          {exportOptions.map((option) => (
            <div key={option.id} className="border border-gray-200 rounded-xl overflow-hidden">
              {/* Header */}
              <div className={`${option.color} text-white p-4`}>
                <div className="flex items-center">
                  {option.icon}
                  <div className="ml-3">
                    <h3 className="text-lg font-semibold">{option.title}</h3>
                    <p className="text-white/90 text-sm">{option.description}</p>
                  </div>
                </div>
              </div>

              {/* Format Options */}
              <div className="p-4 bg-white">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {option.formats.map((format) => (
                    <Button
                      key={format}
                      onClick={() => handleExport(option, format)}
                      disabled={exportProgress.isExporting}
                      variant="outline"
                      className="flex flex-col items-center p-4 h-auto hover:bg-gray-50 transition-colors"
                    >
                      <div className="mb-2">
                        {format === 'PDF' && <FileText className="h-6 w-6 text-red-500" />}
                        {format === 'JSON' && <Database className="h-6 w-6 text-blue-500" />}
                        {format === 'CSV' && <FileText className="h-6 w-6 text-green-500" />}
                        {format === 'ZIP' && <Package className="h-6 w-6 text-purple-500" />}
                      </div>
                      <span className="font-medium">{format}</span>
                      <span className="text-xs text-gray-500 mt-1">
                        {format === 'PDF' && 'Formatted Report'}
                        {format === 'JSON' && 'Raw Data'}
                        {format === 'CSV' && 'Spreadsheet'}
                        {format === 'ZIP' && 'All Formats'}
                      </span>
                    </Button>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="flex justify-end pt-4 border-t border-gray-200">
          <Button
            onClick={onClose}
            variant="outline"
            disabled={exportProgress.isExporting}
          >
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}

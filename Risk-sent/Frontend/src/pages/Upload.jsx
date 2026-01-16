import React, { useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { ShieldAlert, Upload as UploadIcon, FileText, X, CheckCircle, ArrowLeft, File } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';

export default function Upload() {
  const [files, setFiles] = useState([]);
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const { toast } = useToast();

  const handleDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFiles = Array.from(e.dataTransfer.files);
    addFiles(droppedFiles);
  }, []);

  const handleFileInput = (e) => {
    const selectedFiles = Array.from(e.target.files);
    addFiles(selectedFiles);
  };

  const addFiles = (newFiles) => {
    const validFiles = newFiles.filter(file => {
      const validTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
      if (!validTypes.includes(file.type)) {
        toast({
          title: 'Invalid file type',
          description: `${file.name} is not a supported document type.`,
          variant: 'destructive'
        });
        return false;
      }
      return true;
    });

    setFiles(prev => [...prev, ...validFiles.map(file => ({
      file,
      id: Math.random().toString(36).substr(2, 9),
      status: 'pending'
    }))]);
  };

  const removeFile = (id) => {
    setFiles(prev => prev.filter(f => f.id !== id));
  };

  const handleUpload = async () => {
    if (files.length === 0) return;
  
    setUploading(true);
  
    for (const fileItem of files) {
      try {
        // mark uploading
        setFiles(prev =>
          prev.map(f =>
            f.id === fileItem.id ? { ...f, status: 'uploading' } : f
          )
        );
  
        const formData = new FormData();
        formData.append("file", fileItem.file); // 🔑 key = "file"
  
        const response = await fetch("http://127.0.0.1:8000/api/v1/uploads", {
          method: "POST",
          body: formData,
          credentials : "include"
        });
  
        if (!response.ok) {
          throw new Error("Upload failed");
        }
  
        // mark complete
        setFiles(prev =>
          prev.map(f =>
            f.id === fileItem.id ? { ...f, status: 'complete' } : f
          )
        );
      } catch (err) {
        console.error(err);
  
        setFiles(prev =>
          prev.map(f =>
            f.id === fileItem.id ? { ...f, status: 'error' } : f
          )
        );
      }
    }
  
    setUploading(false);
  
    toast({
      title: "Upload complete",
      description: `${files.length} document(s) uploaded successfully.`,
    });
  };
  

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card/80 backdrop-blur-xl sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link to="/dashboard" className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors">
              <ArrowLeft size={20} />
              <span>Back to Dashboard</span>
            </Link>
          </div>
          <div className="flex items-center gap-3">
            <div className="bg-primary p-2 rounded-lg">
              <ShieldAlert className="text-primary-foreground" size={20} />
            </div>
            <span className="font-display font-bold text-foreground text-lg">
              RiskSense <span className="text-gradient">Pro</span>
            </span>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-12 max-w-4xl">
        <div className="text-center mb-12">
          <h1 className="font-display text-4xl font-bold text-foreground mb-4">
            Upload Documents
          </h1>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            Upload financial documents for AI-powered risk analysis. Supported formats: PDF, Word, and text files.
          </p>
        </div>

        {/* Drop Zone */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`
            relative border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-300
            ${isDragging 
              ? 'border-primary bg-primary/5 scale-[1.02]' 
              : 'border-border hover:border-primary/50 hover:bg-card/50'
            }
          `}
        >
          <input
            type="file"
            multiple
            accept=".pdf,.doc,.docx,.txt"
            onChange={handleFileInput}
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          />
          
          <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-primary/10 flex items-center justify-center">
            <UploadIcon className={`text-primary transition-transform ${isDragging ? 'scale-110' : ''}`} size={32} />
          </div>
          
          <h3 className="font-display text-xl font-semibold text-foreground mb-2">
            {isDragging ? 'Drop files here' : 'Drag & drop documents'}
          </h3>
          <p className="text-muted-foreground mb-4">
            or click to browse your files
          </p>
          <p className="text-xs text-muted-foreground">
            PDF, DOC, DOCX, TXT up to 50MB each
          </p>
        </div>

        {/* File List */}
        {files.length > 0 && (
          <div className="mt-8 space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-display font-semibold text-foreground">
                Selected Files ({files.length})
              </h3>
              <Button 
                onClick={handleUpload} 
                disabled={uploading || files.every(f => f.status === 'complete')}
                className="bg-primary hover:bg-primary/90"
              >
                {uploading ? 'Uploading...' : 'Upload All'}
              </Button>
            </div>
            
            <div className="space-y-3">
              {files.map((fileItem) => (
                <div 
                  key={fileItem.id}
                  className="flex items-center gap-4 p-4 rounded-xl bg-card border border-border"
                >
                  <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center flex-shrink-0">
                    {fileItem.status === 'complete' ? (
                      <CheckCircle className="text-green-500" size={20} />
                    ) : (
                      <File className="text-primary" size={20} />
                    )}
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-foreground truncate">
                      {fileItem.file.name}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      {(fileItem.file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    {fileItem.status === 'uploading' && (
                      <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                    )}
                    {fileItem.status === 'complete' && (
                      <span className="text-sm text-green-500 font-medium">Complete</span>
                    )}
                    {fileItem.status === 'pending' && (
                      <button 
                        onClick={() => removeFile(fileItem.id)}
                        className="p-1 text-muted-foreground hover:text-destructive transition-colors"
                      >
                        <X size={18} />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recent Uploads */}
        <div className="mt-16">
          <h3 className="font-display text-xl font-semibold text-foreground mb-6">
            Recent Documents
          </h3>
          <div className="grid gap-4">
            <div className="flex items-center gap-4 p-4 rounded-xl bg-card border border-border hover:border-primary/50 transition-colors cursor-pointer">
              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                <FileText className="text-primary" size={20} />
              </div>
              <div className="flex-1">
                <p className="font-medium text-foreground">2024 10-K Report</p>
                <p className="text-sm text-muted-foreground">Uploaded 2 days ago</p>
              </div>
              <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded-full">
                Analyzed
              </span>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

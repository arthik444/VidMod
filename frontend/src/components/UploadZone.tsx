import React, { useState, useRef } from 'react';
import { Upload as UploadIcon, FileVideo, X, CheckCircle2, Loader2, Play } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface UploadZoneProps {
    onUploadComplete: (file: File, metadata: VideoMetadata) => void;
}

export interface VideoMetadata {
    name: string;
    size: string;
    duration: string;
    resolution: string;
}

const UploadZone: React.FC<UploadZoneProps> = ({ onUploadComplete }) => {
    const [isDragging, setIsDragging] = useState(false);
    const [file, setFile] = useState<File | null>(null);
    const [status, setStatus] = useState<'idle' | 'uploading' | 'processing' | 'ready'>('idle');
    const [progress, setProgress] = useState(0);
    const [metadata, setMetadata] = useState<VideoMetadata | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        const droppedFile = e.dataTransfer.files[0];
        if (droppedFile && droppedFile.type.startsWith('video/')) {
            handleFileSelection(droppedFile);
        }
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const selectedFile = e.target.files?.[0];
        if (selectedFile) {
            handleFileSelection(selectedFile);
        }
    };

    const handleFileSelection = (selectedFile: File) => {
        setFile(selectedFile);
        setStatus('uploading');
        setProgress(0);

        // Simulate upload and processing
        simulateProgress();

        // Extract metadata (mocked for now, but could use a hidden video element)
        setMetadata({
            name: selectedFile.name,
            size: (selectedFile.size / (1024 * 1024)).toFixed(2) + ' MB',
            duration: '00:15', // Mocked max 20s
            resolution: '1920x1080'
        });
    };

    const simulateProgress = () => {
        let currentProgress = 0;
        const interval = setInterval(() => {
            currentProgress += Math.random() * 15;
            if (currentProgress >= 100) {
                currentProgress = 100;
                clearInterval(interval);

                if (status === 'uploading') {
                    setStatus('processing');
                    setTimeout(() => simulateProcessing(), 500);
                }
            }
            setProgress(Math.min(currentProgress, 100));
        }, 300);
    };

    const simulateProcessing = () => {
        setProgress(0);
        let currentProgress = 0;
        const interval = setInterval(() => {
            currentProgress += Math.random() * 10;
            if (currentProgress >= 100) {
                currentProgress = 100;
                clearInterval(interval);
                setStatus('ready');
            }
            setProgress(Math.min(currentProgress, 100));
        }, 400);
    };

    const reset = () => {
        setFile(null);
        setStatus('idle');
        setProgress(0);
        setMetadata(null);
    };

    return (
        <div className="h-full flex flex-col items-center justify-center p-8 bg-background">
            <div className="w-full max-w-2xl">
                <div className="mb-8 text-center">
                    <h1 className="text-2xl font-bold mb-2 tracking-tight">Upload Video for Analysis</h1>
                    <p className="text-muted-foreground text-sm">Zenith Sensor automatically detects compliance violations in your content.</p>
                </div>

                <div
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    className={cn(
                        "relative rounded-2xl border-2 border-dashed transition-all duration-300 flex flex-col items-center justify-center p-12 min-h-[400px] bg-card/30",
                        isDragging ? "border-accent bg-accent/5 scale-[1.02]" : "border-border hover:border-muted/50",
                        status !== 'idle' && "border-solid border-border pointer-events-none"
                    )}
                >
                    {status === 'idle' && (
                        <>
                            <div className="w-20 h-20 rounded-full bg-muted/20 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                                <UploadIcon className="w-8 h-8 text-muted-foreground" />
                            </div>
                            <div className="text-center space-y-4">
                                <div className="space-y-1">
                                    <p className="text-lg font-medium text-foreground">Drag and drop video files to upload</p>
                                    <p className="text-sm text-muted-foreground">Your videos will be private until you publish them.</p>
                                </div>
                                <button
                                    onClick={() => fileInputRef.current?.click()}
                                    className="px-6 py-2.5 bg-accent text-white rounded-lg font-bold shadow-lg shadow-accent/20 hover:opacity-90 transition-all active:scale-95"
                                >
                                    Select File
                                </button>
                                <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest mt-8">MAX 20 SECONDS • MP4, MOV</p>
                            </div>
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept="video/*"
                                className="hidden"
                                onChange={handleFileChange}
                            />
                        </>
                    )}

                    {status !== 'idle' && (
                        <div className="w-full space-y-8 animate-in fade-in duration-500">
                            <div className="flex items-center gap-6 p-6 rounded-xl bg-background/50 border border-border">
                                <div className="w-16 h-16 rounded-lg bg-accent/10 flex items-center justify-center flex-shrink-0">
                                    <FileVideo className="w-8 h-8 text-accent" />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center justify-between mb-1">
                                        <h3 className="font-bold truncate pr-4 text-lg">{metadata?.name}</h3>
                                        <button onClick={reset} className="p-1 hover:bg-muted/30 rounded-full transition-colors pointer-events-auto">
                                            <X className="w-5 h-5 text-muted-foreground" />
                                        </button>
                                    </div>
                                    <div className="flex gap-4 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                                        <span>{metadata?.size}</span>
                                        <span>{metadata?.duration}</span>
                                        <span>{metadata?.resolution}</span>
                                    </div>
                                </div>
                            </div>

                            <div className="space-y-6">
                                <div className="space-y-2">
                                    <div className="flex justify-between items-end text-sm">
                                        <span className="font-bold flex items-center gap-2">
                                            {status === 'uploading' ? (
                                                <>
                                                    <Loader2 className="w-4 h-4 animate-spin text-accent" />
                                                    Uploading...
                                                </>
                                            ) : status === 'processing' ? (
                                                <>
                                                    <Loader2 className="w-4 h-4 animate-spin text-accent" />
                                                    Extracting frames & audio...
                                                </>
                                            ) : (
                                                <>
                                                    <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                                                    Ready for analysis
                                                </>
                                            )}
                                        </span>
                                        <span className="text-muted-foreground font-mono">{Math.floor(progress)}%</span>
                                    </div>
                                    <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
                                        <div
                                            className={cn(
                                                "h-full transition-all duration-300 ease-out",
                                                status === 'ready' ? "bg-emerald-500" : "bg-accent shadow-[0_0_10px_rgba(59,130,246,0.5)]"
                                            )}
                                            style={{ width: `${progress}%` }}
                                        />
                                    </div>
                                </div>

                                {status === 'ready' && (
                                    <div className="flex flex-col gap-4 animate-in slide-in-from-bottom-4 duration-500">
                                        <button
                                            onClick={() => file && metadata && onUploadComplete(file, metadata)}
                                            className="w-full py-4 bg-accent text-white rounded-xl font-bold flex items-center justify-center gap-2 shadow-xl shadow-accent/40 hover:scale-[1.01] active:scale-[0.99] transition-all"
                                        >
                                            <Play className="w-5 h-5 fill-current" />
                                            Run Compliance Analysis
                                        </button>
                                        <p className="text-[10px] text-center text-muted-foreground font-medium uppercase tracking-[0.2em]">
                                            All files are encrypted and processed locally
                                        </p>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default UploadZone;

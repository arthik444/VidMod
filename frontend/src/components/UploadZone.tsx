import React, { useState, useRef } from 'react';
import { Upload as UploadIcon, X, CheckCircle2, Loader2, Play, Layout, Shield, Globe, Check, ChevronDown } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { Platform, Region, Rating } from '../services/policyEngine';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface UploadZoneProps {
    platform: string;
    region: string;
    rating: string;
    onPlatformChange: (platform: string) => void;
    onRegionChange: (region: string) => void;
    onRatingChange: (rating: string) => void;
    onUploadComplete: (metadata: VideoMetadata) => void;
    onFileSelected: (metadata: VideoMetadata) => void;
    onBrowseLibrary?: () => void;
}

export interface VideoMetadata {
    name: string;
    size: string;
    duration: string;
    resolution: string;
    url: string;
    file: File;
    jobId?: string;
}

const platforms = Object.values(Platform);
const regions = Object.values(Region);
const ratings = Object.values(Rating);

const UploadZone: React.FC<UploadZoneProps> = ({
    platform,
    region,
    rating,
    onPlatformChange,
    onRegionChange,
    onRatingChange,
    onUploadComplete,
    onFileSelected,
    onBrowseLibrary
}) => {
    const [isDragging, setIsDragging] = useState(false);
    const [videoUrl, setVideoUrl] = useState<string | null>(null);
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

    const handleFileSelection = async (selectedFile: File) => {
        const url = URL.createObjectURL(selectedFile);
        setVideoUrl(url);
        setStatus('uploading');
        setProgress(0);

        try {
            const metadataPromise = new Promise<VideoMetadata>((resolve) => {
                const video = document.createElement('video');
                video.preload = 'metadata';
                video.onloadedmetadata = () => {
                    resolve({
                        name: selectedFile.name,
                        size: (selectedFile.size / (1024 * 1024)).toFixed(2) + ' MB',
                        duration: `${Math.floor(video.duration)}s`,
                        resolution: `${video.videoWidth}x${video.videoHeight}`,
                        url: url,
                        file: selectedFile
                    });
                };
                video.src = url;
            });

            const jobIdPromise = uploadToBackend(selectedFile);
            const [baseMetadata, jobId] = await Promise.all([metadataPromise, jobIdPromise]);

            if (jobId) {
                const finalMetadata = { ...baseMetadata, jobId };
                setMetadata(finalMetadata);
                onFileSelected(finalMetadata);
                setStatus('ready');
                setProgress(100);
            } else {
                setStatus('idle');
            }

        } catch (error) {
            console.error('File selection failed:', error);
            setStatus('idle');
        }
    };

    const uploadToBackend = async (file: File) => {
        setProgress(10);
        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('http://localhost:8000/api/upload', {
                method: 'POST',
                body: formData,
            });

            setProgress(50);
            if (!response.ok) throw new Error(`Upload failed: ${response.statusText}`);

            const data = await response.json();
            return data.job_id;
        } catch (error) {
            console.error('Upload failed:', error);
            return null;
        }
    };


    const reset = () => {
        if (videoUrl) URL.revokeObjectURL(videoUrl);
        setVideoUrl(null);
        setStatus('idle');
        setProgress(0);
        setMetadata(null);
    };

    return (
        <div className="h-full flex flex-col items-center justify-center p-8 bg-background">
            <div className="w-full max-w-3xl">
                <div className="mb-8 text-center animate-in fade-in slide-in-from-top-4 duration-700">
                    <h1 className="text-4xl font-black mb-3 tracking-tighter bg-gradient-to-r from-foreground to-foreground/50 bg-clip-text text-transparent">Compliance Engine</h1>
                    <p className="text-muted-foreground font-medium">Verify your content against global broadcasting standards.</p>
                </div>

                <div
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    className={cn(
                        "relative rounded-[2.5rem] border-2 border-dashed transition-all duration-700 flex flex-col items-center justify-center p-8 min-h-[500px] overflow-hidden bg-card/10 backdrop-blur-xl shadow-2xl ",
                        isDragging ? "border-accent bg-accent/5 scale-[1.01] shadow-[0_0_80px_rgba(59,130,246,0.15)]" : "border-white/5 hover:border-accent/30 hover:bg-card/20",
                        status !== 'idle' && "border-solid border-white/5 p-4"
                    )}
                >
                    {/* Ambient Glows */}
                    <div className="absolute -top-24 -left-24 w-64 h-64 bg-accent/10 rounded-full blur-[100px] pointer-events-none" />
                    <div className="absolute -bottom-24 -right-24 w-64 h-64 bg-accent/10 rounded-full blur-[100px] pointer-events-none" />

                    {status === 'idle' && (
                        <>
                            <div
                                className="w-24 h-24 rounded-3xl bg-gradient-to-br from-accent to-accent/80 flex items-center justify-center mb-8 shadow-[0_20px_40px_rgba(59,130,246,0.4)] relative group cursor-pointer"
                                onClick={() => fileInputRef.current?.click()}
                            >
                                <UploadIcon className="w-10 h-10 text-white animate-bounce-slow" />
                                <div className="absolute inset-0 rounded-3xl bg-white opacity-0 group-hover:opacity-20 transition-opacity" />
                            </div>
                            <div className="text-center space-y-8 z-10">
                                <div className="space-y-3">
                                    <p className="text-2xl font-black text-foreground tracking-tight">Ready to Analyze?</p>
                                    <p className="text-muted-foreground max-w-sm mx-auto font-medium leading-relaxed">Drop your video here or click below to start the high-fidelity compliance detection.</p>
                                </div>
                                <div className="flex flex-col gap-4 items-center">
                                    <button
                                        onClick={() => fileInputRef.current?.click()}
                                        className="px-10 py-4 bg-foreground text-background rounded-2xl font-black text-lg shadow-2xl hover:opacity-90 hover:translate-y-[-4px] transition-all active:scale-95 flex items-center gap-3"
                                    >
                                        Select Video File
                                    </button>
                                    {onBrowseLibrary && (
                                        <button
                                            onClick={onBrowseLibrary}
                                            className="px-10 py-4 bg-white/5 border border-white/10 text-foreground rounded-2xl font-bold hover:bg-white/10 hover:translate-y-[-4px] transition-all active:scale-95"
                                        >
                                            📚 Browse Demo Library
                                        </button>
                                    )}
                                </div>
                                <div className="flex gap-6 justify-center items-center mt-12">
                                    <div className="flex flex-col items-center gap-1">
                                        <span className="text-[10px] font-black text-muted-foreground uppercase tracking-widest opacity-60">Durations</span>
                                        <span className="text-xs font-bold px-3 py-1 rounded-full bg-white/5 border border-white/5">Up to 120s</span>
                                    </div>
                                    <div className="w-[1px] h-6 bg-white/10" />
                                    <div className="flex flex-col items-center gap-1">
                                        <span className="text-[10px] font-black text-muted-foreground uppercase tracking-widest opacity-60">Format</span>
                                        <span className="text-xs font-bold px-3 py-1 rounded-full bg-white/5 border border-white/5">MP4 / MOV</span>
                                    </div>
                                </div>
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
                        <div className="w-full h-full flex flex-col z-10 p-4">
                            {/* Header Section */}
                            <div className="flex items-center gap-6 p-6 rounded-3xl bg-white/5 border border-white/10 backdrop-blur-2xl shadow-inner mb-8 transition-all hover:bg-white/[0.08]">
                                <div className="w-32 h-20 rounded-2xl bg-black flex items-center justify-center flex-shrink-0 shadow-2xl overflow-hidden relative border border-white/10 group/preview">
                                    {videoUrl && (
                                        <video
                                            src={videoUrl}
                                            className="w-full h-full object-cover transition-transform duration-700 group-hover/preview:scale-110"
                                            autoPlay
                                            muted
                                            loop
                                            playsInline
                                        />
                                    )}
                                    <div className="absolute inset-0 bg-accent/5 pointer-events-none" />
                                </div>
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-center justify-between mb-3">
                                        <h3 className="font-black truncate pr-4 text-2xl tracking-tighter">{metadata?.name}</h3>
                                        <button onClick={reset} className="p-2.5 hover:bg-red-500/20 hover:text-red-400 rounded-2xl transition-all border border-transparent hover:border-red-500/30">
                                            <X className="w-5 h-5" />
                                        </button>
                                    </div>
                                    <div className="flex gap-3 text-[10px] font-black text-muted-foreground uppercase tracking-[0.2em]">
                                        <span className="bg-white/5 px-2.5 py-1 rounded-lg border border-white/5">{metadata?.size}</span>
                                        <span className="bg-white/5 px-2.5 py-1 rounded-lg border border-white/5">{metadata?.duration}</span>
                                        <span className="bg-white/5 px-2.5 py-1 rounded-lg border border-white/5">{metadata?.resolution}</span>
                                    </div>
                                </div>
                            </div>

                            {/* Main Configuration Section */}
                            <div className="flex-1 flex flex-col">
                                {status === 'uploading' || status === 'processing' ? (
                                    <div className="flex-1 flex flex-col justify-center gap-8 py-12">
                                        <div className="space-y-4">
                                            <div className="flex justify-between items-end">
                                                <div className="flex items-center gap-3">
                                                    <div className="p-2 rounded-xl bg-accent/10 border border-accent/20">
                                                        <Loader2 className="w-5 h-5 animate-spin text-accent" />
                                                    </div>
                                                    <span className="text-sm font-black uppercase tracking-[0.2em] animate-pulse">
                                                        {status === 'uploading' ? 'Initializing Secure Stream...' : 'Calibrating AI Engine...'}
                                                    </span>
                                                </div>
                                                <span className="text-2xl font-black font-mono text-accent">{Math.floor(progress)}%</span>
                                            </div>
                                            <div className="h-2.5 w-full bg-white/5 rounded-full overflow-hidden border border-white/5">
                                                <div
                                                    className="h-full bg-gradient-to-r from-accent via-accent/80 to-accent transition-all duration-300 ease-out shadow-[0_0_20px_rgba(59,130,246,0.4)] relative"
                                                    style={{ width: `${progress}%` }}
                                                >
                                                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="flex-1 flex flex-col gap-8 animate-in fade-in slide-in-from-bottom-8 duration-1000">
                                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                            {/* Platform Selector */}
                                            <div className="space-y-3">
                                                <label className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-muted-foreground ml-1">
                                                    <Layout className="w-3 h-3" />
                                                    Target Platform
                                                </label>
                                                <div className="relative group/sel">
                                                    <div className="w-full flex items-center justify-between px-4 py-3.5 rounded-2xl bg-white/5 border border-white/10 hover:border-accent/50 hover:bg-white/10 cursor-pointer transition-all">
                                                        <span className="font-bold text-sm tracking-tight">{platform}</span>
                                                        <ChevronDown className="w-4 h-4 text-muted-foreground" />
                                                    </div>
                                                    <div className="absolute bottom-full left-0 w-full mb-2 p-1.5 bg-background/90 border border-white/10 rounded-2xl shadow-2xl backdrop-blur-3xl opacity-0 group-hover/sel:opacity-100 translate-y-2 group-hover/sel:translate-y-0 pointer-events-none group-hover/sel:pointer-events-auto transition-all z-50">
                                                        {platforms.map(p => (
                                                            <button
                                                                key={p}
                                                                onClick={() => onPlatformChange(p)}
                                                                className="w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-bold hover:bg-accent/10 hover:text-accent transition-all"
                                                            >
                                                                {p}
                                                                {platform === p && <Check className="w-3 h-3" />}
                                                            </button>
                                                        ))}
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Rating Selector */}
                                            <div className="space-y-3">
                                                <label className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-muted-foreground ml-1">
                                                    <Shield className="w-3 h-3" />
                                                    Content Rating
                                                </label>
                                                <div className="relative group/sel">
                                                    <div className="w-full flex items-center justify-between px-4 py-3.5 rounded-2xl bg-white/5 border border-white/10 hover:border-accent/50 hover:bg-white/10 cursor-pointer transition-all">
                                                        <span className="font-bold text-sm tracking-tight">{rating}</span>
                                                        <ChevronDown className="w-4 h-4 text-muted-foreground" />
                                                    </div>
                                                    <div className="absolute bottom-full left-0 w-full mb-2 p-1.5 bg-background/90 border border-white/10 rounded-2xl shadow-2xl backdrop-blur-3xl opacity-0 group-hover/sel:opacity-100 translate-y-2 group-hover/sel:translate-y-0 pointer-events-none group-hover/sel:pointer-events-auto transition-all z-50">
                                                        {ratings.map(r => (
                                                            <button
                                                                key={r}
                                                                onClick={() => onRatingChange(r)}
                                                                className="w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-bold hover:bg-accent/10 hover:text-accent transition-all"
                                                            >
                                                                {r}
                                                                {rating === r && <Check className="w-3 h-3" />}
                                                            </button>
                                                        ))}
                                                    </div>
                                                </div>
                                            </div>

                                            {/* Region Selector */}
                                            <div className="space-y-3">
                                                <label className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-muted-foreground ml-1">
                                                    <Globe className="w-3 h-3" />
                                                    Global Region
                                                </label>
                                                <div className="relative group/sel">
                                                    <div className="w-full flex items-center justify-between px-4 py-3.5 rounded-2xl bg-white/5 border border-white/10 hover:border-accent/50 hover:bg-white/10 cursor-pointer transition-all">
                                                        <span className="font-bold text-sm tracking-tight">{region}</span>
                                                        <ChevronDown className="w-4 h-4 text-muted-foreground" />
                                                    </div>
                                                    <div className="absolute bottom-full left-0 w-full mb-2 p-1.5 bg-background/90 border border-white/10 rounded-2xl shadow-2xl backdrop-blur-3xl opacity-0 group-hover/sel:opacity-100 translate-y-2 group-hover/sel:translate-y-0 pointer-events-none group-hover/sel:pointer-events-auto transition-all z-50">
                                                        {regions.map(r => (
                                                            <button
                                                                key={r}
                                                                onClick={() => onRegionChange(r)}
                                                                className="w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-bold hover:bg-accent/10 hover:text-accent transition-all"
                                                            >
                                                                {r}
                                                                {region === r && <Check className="w-3 h-3" />}
                                                            </button>
                                                        ))}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="mt-auto space-y-6">
                                            <button
                                                onClick={() => metadata && onUploadComplete(metadata)}
                                                disabled={!metadata}
                                                className={cn(
                                                    "w-full py-6 text-white rounded-3xl font-black text-xl flex items-center justify-center gap-3 shadow-[0_20px_50px_rgba(59,130,246,0.3)] transition-all relative overflow-hidden group/btn",
                                                    metadata
                                                        ? "bg-accent hover:translate-y-[-4px] hover:shadow-[0_25px_60px_rgba(59,130,246,0.4)] active:scale-[0.98]"
                                                        : "bg-muted cursor-not-allowed opacity-50"
                                                )}
                                            >
                                                <div className="absolute inset-0 bg-gradient-to-r from-white/0 via-white/20 to-white/0 -translate-x-full group-hover/btn:animate-shimmer" />
                                                <Play className="w-6 h-6 fill-current" />
                                                RUN COMPLIANCE ANALYSIS
                                            </button>
                                            <div className="flex items-center justify-center gap-4">
                                                <div className="h-[1px] flex-1 bg-white/5" />
                                                <div className="flex items-center gap-2 text-[10px] text-muted-foreground font-black uppercase tracking-[0.4em] opacity-50">
                                                    <CheckCircle2 className="w-3 h-3 text-emerald-500/50" />
                                                    Validation Complete
                                                </div>
                                                <div className="h-[1px] flex-1 bg-white/5" />
                                            </div>
                                        </div>
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

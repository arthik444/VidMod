import React from 'react';
import { Download, Bell, Video } from 'lucide-react';

interface TopBarProps {
    platform: string;
    region: string;
    rating: string;
    isAnalyzing: boolean;
    hasVideo: boolean;
}

const TopBar: React.FC<TopBarProps> = ({
    platform,
    region,
    rating,
    isAnalyzing,
    hasVideo
}) => {
    return (
        <header className="h-14 border-b border-border flex items-center justify-between px-5 surface-1 sticky top-0 z-10">
            {/* Left: Brand + Context */}
            <div className="flex items-center gap-3">
                {/* Brand */}
                <div className="flex items-center gap-2.5">
                    <div className="w-7 h-7 rounded-lg surface-3 border border-border flex items-center justify-center">
                        <Video className="w-4 h-4 text-zinc-400" />
                    </div>
                    <span className="text-sm font-semibold text-zinc-100 tracking-tight">VidMod</span>
                </div>

                {/* Separator */}
                <div className="divider-v mx-1" />

                {/* Context Metadata */}
                {hasVideo ? (
                    <div className="flex items-center gap-2">
                        <span className="badge">
                            <span className="text-zinc-500">{platform}</span>
                        </span>
                        <span className="badge">
                            <span className="text-zinc-500">{rating}</span>
                        </span>
                        <span className="badge">
                            <span className="text-zinc-500">{region}</span>
                        </span>
                    </div>
                ) : (
                    <span className="text-xs text-zinc-600">No video loaded</span>
                )}
            </div>

            {/* Right: Status + Actions */}
            <div className="flex items-center gap-2">
                {/* Analysis Status */}
                {isAnalyzing && (
                    <div className="badge mr-1">
                        <div className="w-1.5 h-1.5 rounded-full bg-zinc-400 animate-pulse" />
                        <span className="text-zinc-400">Analyzing</span>
                    </div>
                )}

                {/* Notifications */}
                <button className="btn-icon relative" title="Notifications">
                    <Bell className="w-4 h-4" />
                    <span className="absolute top-1.5 right-1.5 w-1.5 h-1.5 bg-zinc-500 rounded-full" />
                </button>

                {/* Export */}
                <button className="btn-primary">
                    <Download className="w-4 h-4" />
                    Export
                </button>
            </div>
        </header>
    );
};

export default TopBar;

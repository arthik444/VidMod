import React, { useState } from 'react';
import Sidebar from './Sidebar';
import TopBar from './TopBar';
import VideoWorkspace from './VideoWorkspace';
import RightPanel from './RightPanel';
import UploadZone from './UploadZone';
import type { VideoMetadata } from './UploadZone';

const AppLayout: React.FC = () => {
    const [activeTab, setActiveTab] = useState('Upload');
    const [videoFile, setVideoFile] = useState<File | null>(null);
    const [videoMetadata, setVideoMetadata] = useState<VideoMetadata | null>(null);
    const [videoUrl, setVideoUrl] = useState<string | null>(null);

    const handleUploadComplete = (file: File, metadata: VideoMetadata) => {
        setVideoFile(file);
        setVideoMetadata(metadata);
        setVideoUrl(URL.createObjectURL(file));
        setActiveTab('Analysis');
    };

    console.log('AppLayout videoFile:', videoFile); // for debugging if needed

    return (
        <div className="flex h-screen w-full overflow-hidden bg-background text-foreground">
            {/* Sidebar - Fixed width */}
            <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

            {/* Main Content Area */}
            <div className="flex flex-col flex-1 min-w-0">
                <TopBar />

                <main className="flex flex-1 overflow-hidden p-4 gap-4">
                    {activeTab === 'Upload' ? (
                        <div className="flex-1">
                            <UploadZone onUploadComplete={handleUploadComplete} />
                        </div>
                    ) : (
                        <>
                            <div className="flex-[3] min-w-0">
                                <VideoWorkspace videoUrl={videoUrl || undefined} metadata={videoMetadata || undefined} />
                            </div>
                            <div className="flex-1 min-w-[300px] max-w-[400px]">
                                <RightPanel activeTab={activeTab} />
                            </div>
                        </>
                    )}
                </main>
            </div>
        </div>
    );
};

export default AppLayout;

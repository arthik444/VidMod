import React from 'react';
import { AlertCircle, CheckCircle2, ShieldAlert, Cpu, ListFilter, History } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

import { type Finding } from './VideoWorkspace';

interface RightPanelProps {
    activeTab: string;
    onSeekTo?: (time: string) => void;
    findings?: Finding[];
    currentTime?: number;
}

const RightPanel: React.FC<RightPanelProps> = ({ activeTab, onSeekTo, findings = [], currentTime = 0 }) => {
    const safetyScore = Math.max(0, 100 - findings.reduce((acc, f) => acc + (f.status === 'critical' ? 10 : 5), 0));
    const highPriorityCount = findings.filter(f => f.status === 'critical').length;

    return (
        <div className="h-full flex flex-col bg-card border border-border rounded-xl overflow-hidden shadow-xl">
            <div className="p-4 border-b border-border bg-muted/10 flex items-center justify-between">
                <h3 className="font-semibold text-sm flex items-center gap-2">
                    {activeTab === 'Analysis' ? <Cpu className="w-4 h-4 text-accent" /> : <ListFilter className="w-4 h-4 text-accent" />}
                    {activeTab} Details
                </h3>
                <History className="w-4 h-4 text-muted-foreground hover:text-foreground cursor-pointer transition-colors" />
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-6">
                {/* Compliance Score Summary */}
                <div className="space-y-3">
                    <div className="flex justify-between items-end">
                        <span className="text-xs text-muted-foreground font-medium uppercase tracking-wider">Overall Safety</span>
                        <span className="text-2xl font-bold text-accent">{safetyScore}%</span>
                    </div>
                    <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
                        <div className="h-full bg-accent rounded-full shadow-[0_0_10px_rgba(59,130,246,0.3)] transition-all duration-1000" style={{ width: `${safetyScore}%` }} />
                    </div>
                </div>

                {/* Violations/Findings */}
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <h4 className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Findings ({findings.length})</h4>
                        {highPriorityCount > 0 && (
                            <span className="px-2 py-0.5 rounded-full bg-red-500/10 text-red-500 text-[10px] font-bold">{highPriorityCount} High Priority</span>
                        )}
                    </div>

                    {findings.map((finding) => {
                        const mins = Math.floor(finding.startTime / 60);
                        const secs = Math.floor(finding.startTime % 60);
                        const formattedTime = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;

                        return (
                            <div
                                key={finding.id}
                                onClick={() => onSeekTo?.(formattedTime)}
                                className={cn(
                                    "group p-3 rounded-lg border transition-all cursor-pointer",
                                    currentTime >= finding.startTime && currentTime <= finding.endTime
                                        ? "border-accent bg-accent/5 shadow-[0_0_15px_rgba(59,130,246,0.1)]"
                                        : "border-border bg-background/50 hover:border-accent/30 hover:bg-accent/5"
                                )}
                            >
                                <div className="flex items-start justify-between mb-2">
                                    <div className="flex items-center gap-2">
                                        {finding.status === 'critical' ? (
                                            <ShieldAlert className="w-4 h-4 text-red-500" />
                                        ) : (
                                            <AlertCircle className="w-4 h-4 text-amber-500" />
                                        )}
                                        <span className="text-xs font-bold">{finding.type}</span>
                                    </div>
                                    <span className="text-[10px] font-mono text-muted-foreground group-hover:text-accent">{formattedTime}</span>
                                </div>
                                <p className="text-sm text-muted-foreground group-hover:text-foreground">{finding.content}</p>
                            </div>
                        );
                    })}
                </div>

                {/* Action History Preview */}
                <div className="space-y-4 pt-4 border-t border-border">
                    <h4 className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Recent Remediation</h4>
                    <div className="space-y-3">
                        <div className="flex items-center gap-3">
                            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                            <div className="flex flex-col">
                                <span className="text-xs font-medium">Auto-Blurred Brand Logo</span>
                                <span className="text-[10px] text-muted-foreground">Just now</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="p-4 bg-muted/5 border-t border-border mt-auto">
                <button className="w-full py-2 bg-foreground text-background rounded-lg text-sm font-bold hover:opacity-90 transition-opacity">
                    Generate Full Report
                </button>
            </div>
        </div>
    );
};

export default RightPanel;

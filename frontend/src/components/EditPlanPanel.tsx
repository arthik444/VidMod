import React, { useState } from 'react';
import { ChevronDown, ChevronUp, AlertCircle, Scissors, VolumeX, EyeOff, ShieldCheck, Info } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

export interface EditStep {
    id: string;
    violation: string;
    action: string;
    reason: string;
    summary: string;
    confidence: number;
    iconType: 'blur' | 'mute' | 'replace' | 'cut' | 'alert';
}

const MOCK_STEPS: EditStep[] = [
    {
        id: '1',
        violation: 'Alcoholic Beverage Detected',
        action: 'Dynamic Blur Applied',
        reason: 'Policy: Alcohol restrictions for YouTube (US)',
        summary: 'Gemini detected a beer bottle at 0:08. SAM (Segment Anything Model) was used to mask the object, and a Gaussian blur was applied to maintain compliance while preserving background context.',
        confidence: 94,
        iconType: 'blur'
    },
    {
        id: '2',
        violation: 'Profanity (Audio)',
        action: 'Audio Cut & Tone Overlay',
        reason: 'Policy: Strict language filter for YouTube Gaming',
        summary: 'Gemini Audio Intelligence identified restricted keywords at 0:12. The segment was isolated and replaced with a low-frequency tone to prevent policy strikes during automated review.',
        confidence: 98,
        iconType: 'mute'
    },
    {
        id: '3',
        violation: 'Unauthorized Brand Logo',
        action: 'Content-Aware Fill',
        reason: 'Policy: Intellectual Property / Brand Safety',
        summary: 'Detected Coca-Cola logo on a t-shirt at 0:02. Gemini decided to use Veo-based inpainting to replace the logo with plain fabric texture to avoid copyright issues.',
        confidence: 89,
        iconType: 'replace'
    }
];

const EditPlanPanel: React.FC = () => {
    const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set(['1']));

    const toggleExpand = (id: string) => {
        const newSet = new Set(expandedIds);
        if (newSet.has(id)) {
            newSet.delete(id);
        } else {
            newSet.add(id);
        }
        setExpandedIds(newSet);
    };

    const getIcon = (type: string) => {
        switch (type) {
            case 'blur': return <EyeOff className="w-4 h-4" />;
            case 'mute': return <VolumeX className="w-4 h-4" />;
            case 'replace': return <ShieldCheck className="w-4 h-4" />;
            case 'cut': return <Scissors className="w-4 h-4" />;
            default: return <AlertCircle className="w-4 h-4" />;
        }
    };

    return (
        <div className="flex flex-col h-full bg-card">
            <div className="p-4 border-b border-border bg-muted/20 flex items-center justify-between">
                <h3 className="font-bold text-sm tracking-tight flex items-center gap-2">
                    <Scissors className="w-4 h-4 text-accent" />
                    Gemini Remediation Plan
                </h3>
                <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 text-[10px] font-bold uppercase tracking-wider">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    Optimized
                </div>
            </div>

            <div className="flex-1 overflow-y-auto p-4 space-y-0 custom-scrollbar relative">
                {/* Vertical Line */}
                <div className="absolute left-[27px] top-6 bottom-6 w-[2px] bg-gradient-to-b from-accent/50 via-accent/20 to-transparent pointer-events-none" />

                {MOCK_STEPS.map((step) => {
                    const isExpanded = expandedIds.has(step.id);
                    return (
                        <div key={step.id} className="relative pl-10 pb-8 last:pb-0 group">
                            {/* Connector Circle */}
                            <div className={cn(
                                "absolute left-4 top-1 w-6 h-6 rounded-full flex items-center justify-center z-10 transition-all duration-300 border-2",
                                isExpanded ? "bg-accent border-accent text-white scale-110 shadow-[0_0_15px_rgba(59,130,246,0.5)]" : "bg-card border-border text-muted-foreground group-hover:border-accent group-hover:text-accent"
                            )}>
                                {getIcon(step.iconType)}
                            </div>

                            <div
                                className={cn(
                                    "flex flex-col rounded-xl border transition-all duration-300 cursor-pointer overflow-hidden",
                                    isExpanded
                                        ? "bg-accent/5 border-accent shadow-[0_0_20px_rgba(59,130,246,0.05)]"
                                        : "bg-background/40 border-border/50 hover:bg-muted/10 hover:border-border"
                                )}
                                onClick={() => toggleExpand(step.id)}
                            >
                                <div className="p-3 flex items-start justify-between gap-3">
                                    <div className="flex flex-col gap-1">
                                        <div className="flex items-center gap-2 text-[10px] font-bold text-muted-foreground uppercase tracking-wider">
                                            <span>Violation:</span>
                                            <span className="text-white bg-red-500/10 px-1.5 py-0.5 rounded border border-red-500/20">{step.violation}</span>
                                        </div>
                                        <h4 className="text-sm font-bold text-foreground mt-1">{step.action}</h4>
                                        <p className="text-xs text-muted-foreground flex items-center gap-1.5">
                                            <Info className="w-3 h-3 text-accent" />
                                            {step.reason}
                                        </p>
                                    </div>
                                    <div className="flex flex-col items-end gap-2">
                                        {isExpanded ? <ChevronUp className="w-4 h-4 text-muted-foreground" /> : <ChevronDown className="w-4 h-4 text-muted-foreground" />}
                                    </div>
                                </div>

                                {isExpanded && (
                                    <div className="px-3 pb-3 pt-1 border-t border-accent/10 animate-in fade-in slide-in-from-top-2 duration-300">
                                        <div className="space-y-3">
                                            <div className="bg-background/60 rounded-lg p-2.5 space-y-2 border border-border/50">
                                                <p className="text-xs leading-relaxed text-muted-foreground italic">
                                                    "{step.summary}"
                                                </p>
                                            </div>

                                            <div className="flex items-center justify-between">
                                                <div className="flex items-center gap-2">
                                                    <div className="text-[10px] font-bold text-muted-foreground uppercase tracking-tighter">Confidence Score</div>
                                                    <div className="flex gap-0.5">
                                                        {[...Array(5)].map((_, i) => (
                                                            <div
                                                                key={i}
                                                                className={cn(
                                                                    "w-3 h-1 rounded-full",
                                                                    i < Math.round(step.confidence / 20) ? "bg-accent" : "bg-muted"
                                                                )}
                                                            />
                                                        ))}
                                                    </div>
                                                </div>
                                                <span className="text-lg font-black italic text-accent tabular-nums">{step.confidence}%</span>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>

            <div className="p-4 border-t border-border bg-muted/5">
                <div className="flex items-center justify-between text-[10px] font-bold text-muted-foreground uppercase tracking-widest mb-2">
                    <span>Processing Status</span>
                    <span className="text-accent">Ready for Export</span>
                </div>
                <div className="w-full h-1 bg-muted rounded-full overflow-hidden">
                    <div className="w-full h-full bg-accent animate-pulse" />
                </div>
            </div>
        </div>
    );
};

export default EditPlanPanel;

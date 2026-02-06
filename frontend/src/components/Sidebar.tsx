import React, { useState } from 'react';
import {
    BarChart3,
    FileText,
    Upload,
    FileVideo,
    ShieldCheck,
    ChevronDown,
    Settings
} from 'lucide-react';
import { type VideoMetadata } from './UploadZone';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { type EnforcementObject, RemediationAction } from '../services/policyEngine';

function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

interface SidebarProps {
    activeTab: string;
    setActiveTab: (tab: string) => void;
    metadata?: VideoMetadata | null;
    policy?: EnforcementObject;
}

const Sidebar: React.FC<SidebarProps> = ({ activeTab, setActiveTab, metadata, policy }) => {
    const [showPolicies, setShowPolicies] = useState(true);

    const menuItems = [
        { id: 'Upload', icon: Upload, label: 'Upload' },
        { id: 'Analysis', icon: BarChart3, label: 'Analysis' },
        { id: 'Compliance', icon: FileText, label: 'Report' },
    ];

    const getActionBadge = (action: string) => {
        switch (action) {
            case RemediationAction.ALLOWED:
                return 'badge-success';
            case RemediationAction.BLOCK_SEGMENT:
                return 'badge-error';
            case RemediationAction.PIXELATE:
            case RemediationAction.BLUR:
                return 'badge-warning';
            default:
                return 'badge';
        }
    };

    return (
        <aside className="w-60 border-r border-border flex flex-col surface-1">
            {/* Navigation */}
            <div className="flex-1 p-4 overflow-y-auto custom-scrollbar">
                <nav className="space-y-1">
                    {menuItems.map((item) => (
                        <button
                            key={item.id}
                            onClick={() => setActiveTab(item.id)}
                            className={cn(
                                "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors cursor-pointer",
                                activeTab === item.id
                                    ? "surface-3 text-zinc-100 border border-border-strong"
                                    : "text-zinc-500 hover:surface-2 hover:text-zinc-300 border border-transparent"
                            )}
                        >
                            <item.icon className={cn(
                                "w-4 h-4",
                                activeTab === item.id ? "text-zinc-300" : "text-zinc-600"
                            )} />
                            {item.label}
                        </button>
                    ))}
                </nav>

                {/* Policy Section */}
                {policy && (
                    <div className="mt-6 pt-4 border-t border-border">
                        <button
                            onClick={() => setShowPolicies(!showPolicies)}
                            className="w-full flex items-center justify-between text-zinc-500 hover:text-zinc-300 transition-colors cursor-pointer px-1 py-2"
                        >
                            <div className="flex items-center gap-2">
                                <ShieldCheck className="w-4 h-4" />
                                <span className="text-xs font-medium">Enforcement</span>
                            </div>
                            <ChevronDown className={cn(
                                "w-4 h-4 transition-transform duration-200",
                                showPolicies && "rotate-180"
                            )} />
                        </button>

                        {showPolicies && (
                            <div className="mt-2 space-y-2">
                                {Object.entries(policy.rules).map(([category, action]) => {
                                    if (action === RemediationAction.ALLOWED) return null;
                                    return (
                                        <div key={category} className="flex items-center justify-between px-1 py-1.5">
                                            <span className="text-xs text-zinc-500 capitalize">
                                                {category.replace('_', ' ')}
                                            </span>
                                            <span className={getActionBadge(action)}>
                                                {action}
                                            </span>
                                        </div>
                                    );
                                })}
                                {Object.values(policy.rules).every(a => a === RemediationAction.ALLOWED) && (
                                    <div className="badge-success text-center py-2 w-full justify-center">
                                        Compliant
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Footer */}
            <div className="p-4 border-t border-border space-y-4">
                {metadata && (
                    <div className="space-y-2">
                        <div className="flex items-center gap-2 text-zinc-600 px-1">
                            <FileVideo className="w-4 h-4" />
                            <span className="text-xs font-medium">Source</span>
                        </div>
                        <div className="surface-2 rounded-lg p-3 space-y-2">
                            <div className="flex justify-between items-center">
                                <span className="text-xs text-zinc-500">Resolution</span>
                                <span className="text-xs text-zinc-300 mono">{metadata.resolution}</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-xs text-zinc-500">Size</span>
                                <span className="text-xs text-zinc-300 mono">{metadata.size}</span>
                            </div>
                        </div>
                    </div>
                )}
                <button className="btn-ghost w-full justify-start">
                    <Settings className="w-4 h-4" />
                    Settings
                </button>
            </div>
        </aside>
    );
};

export default Sidebar;

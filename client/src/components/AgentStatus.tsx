import React from 'react';
import { useTheme } from '../hooks/useTheme';

interface AgentStatusProps {
  progress: number;
  completedTasks: number;
  totalTasks: number;
  currentFocus: string;
  lastAction: string;
  isConnected: boolean;
}

export const AgentStatus: React.FC<AgentStatusProps> = ({ progress, completedTasks, totalTasks, currentFocus, lastAction, isConnected }) => {
    const { theme } = useTheme();
    
    const statusColor = isConnected ? 'text-green-500' : 'text-red-500';
    const statusText = isConnected ? 'Online' : 'Disconnected';

    return (
        <div className="p-6 bg-white dark:bg-gray-800/50 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-md transition-colors duration-300">
            <div className="flex items-center justify-between mb-4">
                <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Agent Status</h2>
                <div className="flex items-center space-x-2">
                    <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`}></div>
                    <span className={statusColor}>{statusText}</span>
                </div>
            </div>

            <div className="mb-6">
                <div className="flex justify-between mb-1 text-sm font-medium text-gray-600 dark:text-gray-400">
                    <span>Overall Progress ({completedTasks}/{totalTasks} Tasks)</span>
                    <span className="text-cyan-600 dark:text-cyan-400">{progress}%</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700/50 rounded-full h-2.5">
                    <div className="bg-gradient-to-r from-cyan-500 to-blue-500 h-2.5 rounded-full transition-all duration-500" style={{ width: `${progress}%` }}></div>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
                <div className="p-4 bg-gray-100 dark:bg-gray-900/50 rounded-lg">
                    <h3 className="text-sm font-semibold text-cyan-600 dark:text-cyan-400 mb-2">Current Focus</h3>
                    <p className="text-md font-mono truncate text-gray-800 dark:text-gray-200">{currentFocus}</p>
                </div>
                <div className="p-4 bg-gray-100 dark:bg-gray-900/50 rounded-lg">
                    <h3 className="text-sm font-semibold text-cyan-600 dark:text-cyan-400 mb-2">Last Action</h3>
                    <p className="text-md font-mono truncate text-gray-800 dark:text-gray-200">{lastAction}</p>
                </div>
            </div>
        </div>
    );
};
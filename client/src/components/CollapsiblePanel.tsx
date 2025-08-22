import React from 'react';
import { ChevronDownIcon } from '@heroicons/react/24/solid';

type Status = 'Completed' | 'In Progress' | 'Pending';

interface CollapsiblePanelProps {
  title: string;
  status: Status;
  isCollapsed: boolean;
  onToggle: () => void;
  hasContent: boolean;
  children: React.ReactNode;
}

const statusStyles: { [key in Status]: string } = {
  Completed: 'border-green-300 bg-green-100 text-green-800 dark:bg-green-900/50 dark:border-green-700 dark:text-green-300',
  'In Progress': 'border-yellow-300 bg-yellow-100 text-yellow-800 dark:bg-yellow-900/50 dark:border-yellow-700 dark:text-yellow-300',
  Pending: 'border-gray-300 bg-gray-100 text-gray-800 dark:bg-gray-700/50 dark:border-gray-600 dark:text-gray-400',
};

const statusDotStyles: { [key in Status]: string } = {
    Completed: 'bg-green-500',
    'In Progress': 'bg-yellow-500 animate-pulse',
    Pending: 'bg-gray-500',
};

export const CollapsiblePanel: React.FC<CollapsiblePanelProps> = ({ title, status, isCollapsed, onToggle, hasContent, children }) => {
  return (
    <div className={`bg-white dark:bg-gray-800/50 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm transition-all duration-300`}>
      <button
        onClick={onToggle}
        className="w-full flex justify-between items-center text-left px-5 py-4"
      >
        <div className="flex items-center space-x-4">
          <div className={`w-2.5 h-2.5 rounded-full ${statusDotStyles[status]}`}></div>
          <span className="text-lg font-semibold text-gray-900 dark:text-white">{title}</span>
          <span className={`text-xs font-medium px-2.5 py-0.5 border rounded-full ${statusStyles[status]}`}>
            {status}
          </span>
        </div>
        <ChevronDownIcon className={`w-5 h-5 text-gray-400 dark:text-gray-500 transition-transform duration-300 ${isCollapsed ? '' : 'rotate-180'}`} />
      </button>
      {!isCollapsed && (
        <div className="px-5 pb-5 pt-2 border-t border-gray-200 dark:border-gray-700">
           <div className="max-h-[60vh] overflow-y-auto custom-scrollbar pr-2 space-y-4">
              {hasContent ? (
                children
              ) : (
                <div className="text-center text-gray-500 dark:text-gray-400 py-4">Waiting for logs...</div>
              )}
           </div>
        </div>
      )}
    </div>
  );
};
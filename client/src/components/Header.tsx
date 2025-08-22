import React from 'react';
import { SunIcon, MoonIcon, ArrowLeftIcon } from '@heroicons/react/24/outline';
import { useTheme } from '../hooks/useTheme';
// Note: In App.tsx, we pass toggleTheme to Header. So we define the prop here.
interface HeaderProps {
  toggleTheme: () => void;
}

export const Header: React.FC<HeaderProps> = ({ toggleTheme }) => {
  const { theme } = useTheme();
  const urlParams = new URLSearchParams(window.location.search);
  const projectId = urlParams.get("projectId");
  const PDLC_BASE_URL= import.meta.env.VITE_PDLC_BASE_URL || 'http://localhost:3000';

  const handleClick = () => {
    window.location.href = `${PDLC_BASE_URL}/projects/${projectId}`;
  }

  return (
    <header className="mb-8 relative">
      <div className="flex justify-between items-center mb-4">
        <button
          onClick={handleClick}
          className="px-3 py-2 inline-flex items-center gap-2 rounded-2xl bg-gray-200 dark:bg-gray-800 text-gray-800 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-700 transition-colors cursor-pointer"
        >
          <ArrowLeftIcon className="w-4 h-4" />
          <span className="text-sm font-medium">Back</span>
        </button>
        <button 
          onClick={toggleTheme} 
          className="p-2 rounded-full bg-gray-200 dark:bg-gray-800 text-gray-800 dark:text-gray-200 hover:bg-gray-300 dark:hover:bg-gray-700 transition-colors"
        >
          {theme === 'dark' ? <SunIcon className="w-6 h-6" /> : <MoonIcon className="w-6 h-6" />}
        </button>
      </div>
      <div className="text-center">
        <h1 className="text-4xl font-bold text-cyan-600 dark:text-cyan-400">AutoGen System Monitor</h1>
        <p className="text-lg text-gray-500 dark:text-gray-400 mt-2">Real-time view of the AI development process</p>
      </div>
    </header>
  );
};      
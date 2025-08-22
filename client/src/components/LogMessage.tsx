import React from 'react';
import type { LogEvent } from '../types/events';
import { useTheme } from '../hooks/useTheme';
import { InformationCircleIcon, ChatBubbleLeftRightIcon, WrenchScrewdriverIcon } from '@heroicons/react/24/outline';

interface LogMessageProps {
  event: LogEvent;
}

const icons = {
  status: <InformationCircleIcon className="h-6 w-6 text-cyan-500 dark:text-cyan-400" />,
  agent: <ChatBubbleLeftRightIcon className="h-6 w-6 text-green-500 dark:text-green-400" />,
  tool: <WrenchScrewdriverIcon className="h-6 w-6 text-purple-500 dark:text-purple-400" />,
};

export const LogMessage: React.FC<LogMessageProps> = ({ event }) => {
  const { theme } = useTheme();

  const renderContent = () => {
    const baseClasses = "p-4 rounded-lg border transition-colors duration-300";
    const themeClasses = {
      light: {
        status: "bg-cyan-50 border-cyan-200",
        agent: "bg-green-50 border-green-200",
        tool: "bg-purple-50 border-purple-200",
        text: "text-gray-700",
        pre: "bg-gray-100 text-gray-800",
        meta: "text-gray-500",
      },
      dark: {
        status: "bg-cyan-900/50 border-cyan-800/50",
        agent: "bg-green-900/50 border-green-800/50",
        tool: "bg-purple-900/50 border-purple-800/50",
        text: "text-gray-300",
        pre: "bg-gray-900/70 text-gray-200",
        meta: "text-gray-500",
      },
    };

    const styles = themeClasses[theme];

    switch (event.type) {
      case 'status':
        return (
          <div className={`${baseClasses} ${styles.status}`}>
            <div className="flex items-start">
              <div className="mr-4 flex-shrink-0">{icons.status}</div>
              <div className="flex-grow">
                <div className="flex justify-between items-center">
                  <span className="font-semibold text-cyan-600 dark:text-cyan-300">System Status</span>
                  <span className={`text-xs ${styles.meta}`}>{event.timestamp}</span>
                </div>
                <div className={`mt-1 whitespace-pre-wrap ${styles.text}`}>{event.data.message}</div>
              </div>
            </div>
          </div>
        );
      case 'agent':
        return (
          <div className={`${baseClasses} ${styles.agent}`}>
            <div className="flex items-start">
              <div className="mr-4 flex-shrink-0">{icons.agent}</div>
              <div className="flex-grow">
                 <div className="flex justify-between items-center">
                  <div>
                    <span className="font-semibold text-green-600 dark:text-green-300">{event.data.sender}</span>
                    <span className={`mx-2 ${styles.meta}`}>to</span>
                    <span className="font-semibold text-yellow-600 dark:text-yellow-400">{event.data.recipient}</span>
                  </div>
                   <span className={`text-xs ${styles.meta}`}>{event.timestamp}</span>
                </div>
                <div className={`mt-2 p-3 rounded-md whitespace-pre-wrap ${styles.pre}`}>{event.data.message}</div>
              </div>
            </div>
          </div>
        );
      case 'tool':
        return (
          <div className={`${baseClasses} ${styles.tool}`}>
            <div className="flex items-start">
              <div className="mr-4 flex-shrink-0">{icons.tool}</div>
              <div className="flex-grow">
                 <div className="flex justify-between items-center">
                   <div>
                    <span className="font-semibold text-purple-600 dark:text-purple-300">{event.data.agent}</span>
                     <span className={`mx-2 ${styles.meta}`}>used</span>
                    <span className="font-mono text-orange-600 dark:text-orange-400">{event.data.tool}()</span>
                  </div>
                   <span className={`text-xs ${styles.meta}`}>{event.timestamp}</span>
                </div>
                <pre className={`mt-2 p-3 rounded-md font-mono text-sm ${styles.pre}`}>{JSON.stringify(event.data.args, null, 2)}</pre>
              </div>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return <div>{renderContent()}</div>;
};
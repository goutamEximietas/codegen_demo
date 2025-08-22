import React from 'react';

interface StatusIndicatorProps {
  isConnected: boolean;
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({ isConnected }) => {
  const statusColor = isConnected ? 'green' : 'red';
  const statusText = isConnected ? 'Connected' : 'Disconnected';

  return (
    <div className="flex items-center space-x-2">
      <span className="relative flex h-3 w-3">
        {isConnected && <span className={`animate-ping absolute inline-flex h-full w-full rounded-full bg-${statusColor}-400 opacity-75`}></span>}
        <span className={`relative inline-flex rounded-full h-3 w-3 bg-${statusColor}-500`}></span>
      </span>
      <span className={`text-${statusColor}-400`}>{statusText}</span>
    </div>
  );
};
import React from 'react';
import type { LogEvent } from '../types/events';
import { LogMessage } from './LogMessage';

interface LogContainerProps {
  events: LogEvent[];
}

export const LogContainer: React.FC<LogContainerProps> = ({ events }) => {
  return (
    <div className="space-y-4">
      {events.map((event, index) => (
        <LogMessage key={index} event={event} />
      ))}
    </div>
  );
};
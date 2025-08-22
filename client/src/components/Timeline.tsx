import React from 'react';

interface TimelineStep {
  name: string;
  status: 'Completed' | 'In Progress' | 'Pending';
}

interface TimelineProps {
  steps: TimelineStep[];
  activeStep: string;
  setActiveStep: (step: string) => void;
}

const statusStyles = {
  Completed: 'bg-green-500 border-green-400',
  'In Progress': 'bg-yellow-500 border-yellow-400 animate-pulse',
  Pending: 'bg-gray-600 border-gray-500',
};

export const Timeline: React.FC<TimelineProps> = ({ steps, activeStep, setActiveStep }) => (
  <div className="flex items-center space-x-4 p-4 bg-gray-900 rounded-xl">
    {steps.map((step, index) => (
      <React.Fragment key={step.name}>
        <button
          onClick={() => setActiveStep(step.name)}
          className={`flex items-center space-x-3 p-3 rounded-lg transition-all duration-300 ${
            activeStep === step.name ? 'bg-cyan-800' : 'hover:bg-gray-700'
          }`}
        >
          <div className={`w-4 h-4 rounded-full flex-shrink-0 border-2 ${statusStyles[step.status]}`}></div>
          <div className="text-left">
            <div className="font-semibold text-white">{step.name}</div>
            <div className="text-xs text-gray-400">{step.status}</div>
          </div>
        </button>
        {index < steps.length - 1 && <div className="flex-grow h-0.5 bg-gray-700"></div>}
      </React.Fragment>
    ))}
  </div>
);
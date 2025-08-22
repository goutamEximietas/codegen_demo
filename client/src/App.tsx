import React, { useState, useEffect, useMemo } from 'react';
import { useSocket } from './hooks/useSocket';
import { useTheme } from './hooks/useTheme';
import { Header } from './components/Header';
import { AgentStatus } from './components/AgentStatus';
import { CollapsiblePanel } from './components/CollapsiblePanel';
import { LogContainer } from './components/LogContainer';
import {
  extractTeamsFromPlan,
  getTeamLogRange,
  isTeamCompleted,
  getPreTeamLogs,
} from './utils/logUtils';
import type { LogEvent } from './types/events';

const App: React.FC = () => {
  // The plan and completedTaskIds now come directly from the socket hook, ensuring accuracy.
  const { isConnected, logEvents, plan, completedTaskIds, isLifecycleComplete } = useSocket();
  const { theme, toggleTheme } = useTheme();

  console.log({isConnected, logEvents, plan, completedTaskIds, isLifecycleComplete});
  // --- Theme Control ---
  // This effect ensures the dark/light mode class is applied to the root HTML element.
  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(theme);
  }, [theme]);

  // --- UNIFIED LOG & PROGRESS PROCESSING ---
  // A single useMemo hook derives ALL necessary data directly from the socket state.
  // This eliminates race conditions and ensures data consistency.
  const {
    teams,
    preTeamLogs,
    teamLogs,
    completedTasks,
    totalTasks,
    progress
  } = useMemo(() => {
    // 1. Derive teams directly from the plan state.
    const currentTeams = plan ? extractTeamsFromPlan(plan) : [];
    
    // 2. Categorize logs based on the derived teams.
    const currentPreTeamLogs = getPreTeamLogs(logEvents);
    const currentTeamLogs: { [team: string]: LogEvent[] } = {};
    currentTeams.forEach(team => {
      currentTeamLogs[team] = getTeamLogRange(team, logEvents, currentTeams);
    });

    // 3. Calculate progress with 100% accuracy.
    const allTasks = plan ? plan.teams.flatMap(t => t.roles.flatMap(r => r.tasks)) : [];
    let currentTotalTasks = allTasks.length;
    // The number of completed tasks is the size of the set received from the backend.
    let currentCompletedTasks = completedTaskIds.size;

    // If the lifecycle is complete, override the counts to be 100%.
    if (isLifecycleComplete && currentTotalTasks > 0) {
      currentCompletedTasks = currentTotalTasks;
    }
    
    const calculatedProgress = currentTotalTasks > 0
      ? Math.round((currentCompletedTasks / currentTotalTasks) * 100)
      : 0;

    // 4. Return everything in one atomic object.
    return {
      teams: currentTeams,
      preTeamLogs: currentPreTeamLogs,
      teamLogs: currentTeamLogs,
      completedTasks: currentCompletedTasks,
      totalTasks: currentTotalTasks,
      progress: calculatedProgress
    };
  }, [logEvents, plan, completedTaskIds, isLifecycleComplete]);// Re-runs when logs, the plan, or completed tasks change.


  // --- Panel and Status Management ---
  const [openPanel, setOpenPanel] = useState<string | null>('Setup');

  const getTeamStatus = (team: string): 'Completed' | 'In Progress' | 'Pending' => {
      const logs = teamLogs[team];
      if (!logs || logs.length === 0) return 'Pending';
      if (isTeamCompleted(team, logEvents, teams)) return 'Completed';
      return 'In Progress';
  };

  // Effect to automatically open the panel for the currently active team.
  useEffect(() => {
    const currentInProgressTeam = [...teams].reverse().find(team => getTeamStatus(team) === 'In Progress');
    if (currentInProgressTeam) {
      setOpenPanel(currentInProgressTeam);
    } else if (preTeamLogs.length > 0) {
      setOpenPanel('Setup');
    }
  }, [logEvents.length, teams.length]); // Depends on teams.length to react to the plan being parsed.

  const handleToggle = (panel: string) => {
    setOpenPanel(prevOpenPanel => (prevOpenPanel === panel ? null : panel));
  };
  
  // --- Agent Status Display Logic (UPDATED) ---
  const currentInProgressTeam = [...teams].reverse().find(team => getTeamStatus(team) === 'In Progress');
  let currentFocus = "Parsing execution plan...";

  // --- UPDATED LOGIC for the final status message ---
  if (isLifecycleComplete) {
    currentFocus = "All tasks completed successfully.";
  } else if (currentInProgressTeam) {
    currentFocus = `Executing: ${currentInProgressTeam} Team`;
  } else if (teams.length > 0) {
    currentFocus = "Idle - Awaiting next team.";
  }

  const lastEvent = logEvents[logEvents.length - 1];
  let lastAction = "Awaiting first action...";
  if (lastEvent) {
      switch (lastEvent.type) {
        case 'agent': lastAction = `Msg: ${lastEvent.data.sender} -> ${lastEvent.data.recipient}`; break;
        case 'tool': lastAction = `Tool Used: ${lastEvent.data.tool}()`; break;
        case 'status': lastAction = lastEvent.data.message.split('\n')[0]; break;
      }
  }

  // --- Render ---
  return (
    <div className=" dark:bg-gray-900 text-gray-800 dark:text-gray-200 min-h-screen font-inter transition-colors duration-300">
      <div className="container mx-auto px-4 md:px-8 py-6">
        <Header toggleTheme={toggleTheme} />
        
        <AgentStatus 
          progress={progress}
          completedTasks={completedTasks}
          totalTasks={totalTasks}
          currentFocus={currentFocus} 
          lastAction={lastAction}
          isConnected={isConnected}
        />

        <div className="mt-8 space-y-4">
          <CollapsiblePanel
            key="Setup"
            title="Setup"
            status={teams.length > 0 ? 'Completed' : 'In Progress'}
            isCollapsed={openPanel !== 'Setup'}
            onToggle={() => handleToggle('Setup')}
            hasContent={preTeamLogs?.length > 0}
          >
            <LogContainer events={preTeamLogs} />
          </CollapsiblePanel>

          {teams.map(panelName => {
            const logs = teamLogs[panelName];
            const status = getTeamStatus(panelName);
            return (
              <CollapsiblePanel
                key={panelName}
                title={panelName}
                status={status}
                isCollapsed={openPanel !== panelName}
                onToggle={() => handleToggle(panelName)}
                hasContent={logs?.length > 0}
              >
                <LogContainer events={logs} />
              </CollapsiblePanel>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default App;
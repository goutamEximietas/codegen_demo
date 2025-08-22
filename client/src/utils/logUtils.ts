import type { LogEvent } from '../types/events';

// --- TYPE DEFINITIONS ---
export interface FinalPlan { teams: { name: string; roles: { role: string; tasks: { task_id: string; description: string; }[] }[] }[] }


// --- THIS IS THE CORRECTED FUNCTION ---
export const isTeamCompleted = (teamName: string, allEvents: LogEvent[], allTeams: string[]): boolean => {
    const teamIndex = allTeams.indexOf(teamName);
    if (teamIndex === -1) return false;

    // The primary way to detect completion is to see if the next team has started.
    const nextTeamName = allTeams[teamIndex + 1];
    if (nextTeamName) {
        if (allEvents.some(event => event.type === 'status' && isSpecificTeamStartMessage(event.data.message, nextTeamName))) {
          return true;
        }
    }
    
    // --- NEW, MORE FLEXIBLE FALLBACK LOGIC for the LAST team ---
    // This now checks for multiple possible completion messages.
    const teamLogs = getTeamLogRange(teamName, allEvents, allTeams);
    return teamLogs.some(e => {
        if (e.type !== 'status') return false;
        const message = e.data.message.toLowerCase();
        const team = teamName.toLowerCase();
        return (
            message.includes(`team ${team} stopped`) ||
            message.includes(`team ${team} completed`) ||
            message.includes(`team ${team} has completed`) || // Catches the new format
            message.includes('all teams have completed')      // A definitive global completion signal
        );
    });
};


// --- Other utility functions (no changes needed) ---
// (The rest of your file from the previous correct step should be here)

export const parseFinalPlan = (events: LogEvent[]): FinalPlan | null => {
  for (const event of events) {
    if (event.type === 'status' && event.data.message.toLowerCase().includes('final approved plan')) {
      const match = event.data.message.match(/{[\s\S]*}/);
      if (match) {
        try {
          return JSON.parse(match[0]) as FinalPlan;
        } catch (e) {
          console.error("CRITICAL: Found final plan, but failed to parse JSON.", e);
          return null;
        }
      }
    }
  }
  return null;
};

export const calculateTaskProgress = (plan: FinalPlan | null, events: LogEvent[]): { completed: number, total: number } => {
  if (!plan) return { completed: 0, total: 0 };
  const allTasks = plan.teams.flatMap(team => team.roles.flatMap(role => role.tasks));
  const total = allTasks.length;
  if (total === 0) return { completed: 0, total: 0 };
  const completedTaskIds = new Set<string>();
  for (const task of allTasks) {
    const rawKeywords = task.description.match(/\b([A-Z]?[a-z]+|[A-Z]+[a-z]*)\b/g) || [];
    const keywords = rawKeywords.map(kw => kw.toLowerCase()).filter(kw => kw.length > 3 && !['using', 'with', 'for', 'and', 'the', 'manage'].includes(kw));
    for (const event of events) {
      if (event.type === 'status' || event.type === 'tool' || event.type === 'agent') {
        const message = JSON.stringify(event.data).toLowerCase();
        if (keywords.some(kw => message.includes(kw))) {
          completedTaskIds.add(task.task_id);
          break;
        }
      }
    }
  }
  return { completed: completedTaskIds.size, total };
};

const isSpecificTeamStartMessage = (message: string, teamName: string): boolean => {
    const lowerCaseMessage = message.toLowerCase();
    const lowerCaseTeamName = teamName.toLowerCase();
    return (
        lowerCaseMessage.includes(`--- activating team: ${lowerCaseTeamName}`) ||
        lowerCaseMessage.includes(`starting ${lowerCaseTeamName} execution`)
    );
};

const isTeamStartMessage = (message: string): boolean => {
    const lowerCaseMessage = message.toLowerCase();
    return /starting \w+ execution/.test(lowerCaseMessage) || lowerCaseMessage.includes('--- activating team:');
};

export const getPreTeamLogs = (events: LogEvent[]): LogEvent[] => {
  const firstActivationIndex = events.findIndex(event => event.type === 'status' && isTeamStartMessage(event.data.message));
  if (firstActivationIndex === -1) return events;
  return events.slice(0, firstActivationIndex);
};

export const getTeamLogRange = (team: string, events: LogEvent[], allTeams: string[]): LogEvent[] => {
    const teamIndex = allTeams.indexOf(team);
    const startIdx = events.findIndex(e => e.type === 'status' && isSpecificTeamStartMessage(e.data.message, team));
    if (startIdx === -1) return [];
    let endIdx = events.length;
    const nextTeamName = allTeams[teamIndex + 1];
    if (nextTeamName) {
        const nextTeamStartIdx = events.findIndex(e => e.type === 'status' && isSpecificTeamStartMessage(e.data.message, nextTeamName));
        if (nextTeamStartIdx !== -1) endIdx = nextTeamStartIdx;
    }
    return events.slice(startIdx, endIdx);
};

export const extractTeamsFromPlan = (plan: FinalPlan | null): string[] => {
    return plan ? plan.teams.map(t => t.name) : [];
};
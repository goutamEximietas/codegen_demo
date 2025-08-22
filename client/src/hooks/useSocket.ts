  import { useState, useEffect } from 'react';
  import io from 'socket.io-client';
  import type { LogEvent } from '../types/events';
  import type { FinalPlan } from '../utils/logUtils';

   const SOCKET_URL =import.meta.env.VITE_SOCKET_URL|| 'http://localhost:5005';

  export const useSocket = () => {
    const [isConnected, setIsConnected] = useState(false);
    const [logEvents, setLogEvents] = useState<LogEvent[]>([]);
    const [plan, setPlan] = useState<FinalPlan | null>(null);
    const [completedTaskIds, setCompletedTaskIds] = useState<Set<string>>(new Set());
    // --- NEW STATE: Tracks if the entire process is finished ---
    const [isLifecycleComplete, setIsLifecycleComplete] = useState(false);

    useEffect(() => {
      const newSocket = io(SOCKET_URL);

      // ... (other handlers are unchanged)
      const handleConnect = () => setIsConnected(true);
      const handleDisconnect = () => setIsConnected(false);
      const handleStatusUpdate = (data: any) => setLogEvents(prev => [...prev, { type: 'status', data, timestamp: new Date().toLocaleTimeString() }]);
      const handleAgentMessage = (data: any) => setLogEvents(prev => [...prev, { type: 'agent', data, timestamp: new Date().toLocaleTimeString() }]);
      const handleToolCall = (data: any) => setLogEvents(prev => [...prev, { type: 'tool', data, timestamp: new Date().toLocaleTimeString() }]);
      const handleFinalPlan = (data: FinalPlan) => setPlan(data);
      const handleTaskCompleted = (data: { task_id: string }) => {
        setCompletedTaskIds(prev => new Set(prev).add(data.task_id));
      };

      // --- NEW HANDLER for the final event ---
      const handleLifecycleComplete = () => {
        console.log("Received lifecycle complete signal!");
        setIsLifecycleComplete(true);
      };

      // ... (listeners for other events are unchanged)
      newSocket.on('connect', handleConnect);
      newSocket.on('disconnect', handleDisconnect);
      newSocket.on('status_update', handleStatusUpdate);
      newSocket.on('agent_message', handleAgentMessage);
      newSocket.on('tool_call', handleToolCall);
      newSocket.on('final_plan_update', handleFinalPlan);
      newSocket.on('task_completed_update', handleTaskCompleted);
      // --- ADD THE NEW LISTENER ---
      newSocket.on('lifecycle_complete', handleLifecycleComplete);

      return () => {
        // ... (cleanup for other listeners)
        newSocket.off('connect', handleConnect);
        newSocket.off('disconnect', handleDisconnect);
        newSocket.off('status_update', handleStatusUpdate);
        newSocket.off('agent_message', handleAgentMessage);
        newSocket.off('tool_call', handleToolCall);
        newSocket.off('final_plan_update', handleFinalPlan);
        newSocket.off('task_completed_update', handleTaskCompleted);
        // --- ADD CLEANUP for the new listener ---
        newSocket.off('lifecycle_complete', handleLifecycleComplete);
        newSocket.disconnect();
      };
    }, []);

    // --- RETURN the new state ---
    return { isConnected, logEvents, plan, completedTaskIds, isLifecycleComplete };
  };
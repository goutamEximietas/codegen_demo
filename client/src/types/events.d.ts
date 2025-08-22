export interface StatusUpdateEvent {
  message: string;
}

export interface AgentMessageEvent {
  sender: string;
  recipient: string;
  message: string;
}

export interface ToolCallEvent {
  agent: string;
  tool: string;
  args: object;
}

// A union type for any possible log event
export type LogEvent = 
  | ({ type: 'status'; data: StatusUpdateEvent } & { timestamp: string })
  | ({ type: 'agent'; data: AgentMessageEvent } & { timestamp: string })
  | ({ type: 'tool'; data: ToolCallEvent } & { timestamp: string });
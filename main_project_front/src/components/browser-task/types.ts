export type TimelineTone = 'neutral' | 'accent' | 'success' | 'warning' | 'danger';
export type RuntimeEventStatus = 'info' | 'running' | 'completed' | 'stopped' | 'failed';
export type RuntimeEventKind = 'session' | 'run' | 'tool' | 'error';

export interface BrowserTaskMessage {
  id: string;
  role: string;
  content: string;
  status: string;
  createdAt: string;
}

export interface RuntimeEvent {
  id: string;
  kind: RuntimeEventKind;
  rawType: string;
  label: string;
  summary: string;
  status: RuntimeEventStatus;
  tone: TimelineTone;
  createdAt: string;
  toolName?: string;
  runId: number;
}

export interface ExecutionPhase {
  key: string;
  label: string;
  value: string;
  detail: string;
  tone: TimelineTone;
}

export interface ToolChipItem {
  key: string;
  label: string;
  count: number;
  active: boolean;
  tone: TimelineTone;
}

export interface AgentTimelineItem {
  id: string;
  title: string;
  summary: string;
  time: string;
  tone: TimelineTone;
  createdAt: string;
}

export interface FactItem {
  label: string;
  value: string;
}

export interface StageStep {
  title: string;
  copy: string;
}

export interface ToolFeedItem {
  id: string;
  title: string;
  summary: string;
  time: string;
}

export interface ModelProfile {
  key: string;
  label: string;
}

export interface BootstrapPayload {
  modelProfiles: ModelProfile[];
  skills: string[];
  skillsEnabled: boolean;
}

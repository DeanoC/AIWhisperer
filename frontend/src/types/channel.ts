/**
 * Channel types and interfaces for the Response Channels feature
 */

export enum ChannelType {
  ANALYSIS = 'analysis',
  COMMENTARY = 'commentary',
  FINAL = 'final'
}

export interface ChannelMetadata {
  sequence: number;
  timestamp: string;
  agentId?: string;
  sessionId?: string;
  toolCalls?: string[];
  continuationDepth?: number;
  isPartial: boolean;
  [key: string]: any; // For custom metadata
}

export interface ChannelMessage {
  type: 'channel_message';
  channel: ChannelType;
  content: string;
  metadata: ChannelMetadata;
}

export interface ChannelVisibilityPreferences {
  showCommentary: boolean;
  showAnalysis: boolean;
}

export interface ChannelHistoryRequest {
  sessionId: string;
  channels?: ChannelType[];
  limit?: number;
  sinceSequence?: number;
}

export interface ChannelHistoryResponse {
  messages: ChannelMessage[];
  totalCount: number;
}

export interface ChannelStats {
  final_count: number;
  analysis_count: number;
  commentary_count: number;
  visibility: ChannelVisibilityPreferences;
}

// Helper functions
export function isChannelVisible(channel: ChannelType, preferences: ChannelVisibilityPreferences): boolean {
  switch (channel) {
    case ChannelType.ANALYSIS:
      return preferences.showAnalysis;
    case ChannelType.COMMENTARY:
      return preferences.showCommentary;
    case ChannelType.FINAL:
      return true; // Final is always visible
    default:
      return false;
  }
}

export function getChannelColor(channel: ChannelType): string {
  switch (channel) {
    case ChannelType.ANALYSIS:
      return '#6B7280'; // Gray for internal reasoning
    case ChannelType.COMMENTARY:
      return '#3B82F6'; // Blue for tool calls
    case ChannelType.FINAL:
      return '#10B981'; // Green for user-facing
    default:
      return '#9CA3AF';
  }
}

export function getChannelIcon(channel: ChannelType): string {
  switch (channel) {
    case ChannelType.ANALYSIS:
      return '🔍'; // Magnifying glass for analysis
    case ChannelType.COMMENTARY:
      return '⚙️'; // Gear for tool execution
    case ChannelType.FINAL:
      return '💬'; // Speech bubble for final response
    default:
      return '📝';
  }
}

export function getChannelLabel(channel: ChannelType): string {
  switch (channel) {
    case ChannelType.ANALYSIS:
      return 'Analysis';
    case ChannelType.COMMENTARY:
      return 'Tool Execution';
    case ChannelType.FINAL:
      return 'Response';
    default:
      return 'Unknown';
  }
}
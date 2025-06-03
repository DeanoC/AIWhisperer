import React from 'react';
import { ChannelVisibilityPreferences, ChannelType, getChannelIcon, getChannelLabel, getChannelColor } from '../types/channel';
import './ChannelControls.css';

interface ChannelControlsProps {
  preferences: ChannelVisibilityPreferences;
  onPreferencesChange: (preferences: ChannelVisibilityPreferences) => void;
  messageCount?: {
    [ChannelType.ANALYSIS]?: number;
    [ChannelType.COMMENTARY]?: number;
    [ChannelType.FINAL]?: number;
  };
}

export const ChannelControls: React.FC<ChannelControlsProps> = ({
  preferences,
  onPreferencesChange,
  messageCount = {}
}) => {
  const handleToggle = (channel: ChannelType.ANALYSIS | ChannelType.COMMENTARY) => {
    const newPrefs = { ...preferences };
    if (channel === ChannelType.ANALYSIS) {
      newPrefs.showAnalysis = !newPrefs.showAnalysis;
    } else if (channel === ChannelType.COMMENTARY) {
      newPrefs.showCommentary = !newPrefs.showCommentary;
    }
    onPreferencesChange(newPrefs);
  };

  return (
    <div className="channel-controls">
      <h3 className="channel-controls-title">Channel Visibility</h3>
      
      <div className="channel-control-items">
        {/* Final channel - always visible */}
        <div className="channel-control-item">
          <div 
            className="channel-indicator"
            style={{ backgroundColor: getChannelColor(ChannelType.FINAL) }}
          />
          <span className="channel-icon">{getChannelIcon(ChannelType.FINAL)}</span>
          <span className="channel-name">{getChannelLabel(ChannelType.FINAL)}</span>
          {messageCount[ChannelType.FINAL] !== undefined && (
            <span className="channel-count">{messageCount[ChannelType.FINAL]}</span>
          )}
          <span className="channel-status always-visible">Always visible</span>
        </div>

        {/* Commentary channel */}
        <div className="channel-control-item">
          <div 
            className="channel-indicator"
            style={{ backgroundColor: getChannelColor(ChannelType.COMMENTARY) }}
          />
          <span className="channel-icon">{getChannelIcon(ChannelType.COMMENTARY)}</span>
          <span className="channel-name">{getChannelLabel(ChannelType.COMMENTARY)}</span>
          {messageCount[ChannelType.COMMENTARY] !== undefined && (
            <span className="channel-count">{messageCount[ChannelType.COMMENTARY]}</span>
          )}
          <label className="channel-toggle">
            <input
              type="checkbox"
              checked={preferences.showCommentary}
              onChange={() => handleToggle(ChannelType.COMMENTARY)}
            />
            <span className="toggle-slider" />
          </label>
        </div>

        {/* Analysis channel */}
        <div className="channel-control-item">
          <div 
            className="channel-indicator"
            style={{ backgroundColor: getChannelColor(ChannelType.ANALYSIS) }}
          />
          <span className="channel-icon">{getChannelIcon(ChannelType.ANALYSIS)}</span>
          <span className="channel-name">{getChannelLabel(ChannelType.ANALYSIS)}</span>
          {messageCount[ChannelType.ANALYSIS] !== undefined && (
            <span className="channel-count">{messageCount[ChannelType.ANALYSIS]}</span>
          )}
          <label className="channel-toggle">
            <input
              type="checkbox"
              checked={preferences.showAnalysis}
              onChange={() => handleToggle(ChannelType.ANALYSIS)}
            />
            <span className="toggle-slider" />
          </label>
        </div>
      </div>

      <div className="channel-controls-hint">
        <p>Toggle channels to control what information you see in the chat.</p>
      </div>
    </div>
  );
};
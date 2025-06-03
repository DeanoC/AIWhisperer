import React, { useState } from 'react';
import { UISettings, ProjectSettings } from '../types/project';

interface ProjectSettingsPanelProps {
  projectSettings: ProjectSettings;
  uiSettings: UISettings;
  onChange: (changes: { project?: Partial<ProjectSettings>, ui?: Partial<UISettings> }) => void;
}

const TABS = [
  { key: 'general', label: 'General' },
  { key: 'agents', label: 'Agents' },
  { key: 'ui', label: 'UI' },
  // Add more tabs as needed
];

export const ProjectSettingsPanel: React.FC<ProjectSettingsPanelProps> = ({
  projectSettings,
  uiSettings,
  onChange,
}) => {
  const [activeTab, setActiveTab] = useState('general');

  return (
    <div className="project-settings-panel">
      <div className="settings-tabs">
        {TABS.map(tab => (
          <button
            key={tab.key}
            className={activeTab === tab.key ? 'active' : ''}
            onClick={() => setActiveTab(tab.key)}
            type="button"
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="settings-content">
        {activeTab === 'general' && (
          <div>
            <h3>General Settings</h3>
            <div className="settings-group">
              <div className="settings-row">
                <span className="settings-label">Default Agent</span>
                <div className="settings-control">
                  <input
                    type="text"
                    value={projectSettings.defaultAgent || ''}
                    onChange={e => onChange({ project: { defaultAgent: e.target.value } })}
                    placeholder="e.g. alice"
                  />
                </div>
              </div>
              
              <div className="settings-row">
                <span className="settings-label">Auto Save</span>
                <div className="settings-control">
                  <input
                    type="checkbox"
                    checked={!!projectSettings.autoSave}
                    onChange={e => onChange({ project: { autoSave: e.target.checked } })}
                  />
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'agents' && (
          <div>
            <h3>Agent Settings</h3>
            <div className="settings-group">
              <div className="settings-row">
                <span className="settings-label">External Agent Type</span>
                <div className="settings-control">
                  <select
                    value={projectSettings.externalAgentType || ''}
                    onChange={e => onChange({ project: { externalAgentType: e.target.value } })}
                  >
                    <option value="">(None)</option>
                    <option value="openai">OpenAI</option>
                    <option value="anthropic">Anthropic</option>
                    <option value="custom">Custom</option>
                    {/* Add more as needed */}
                  </select>
                </div>
              </div>
            </div>
            {/* Add more agent-related settings here */}
          </div>
        )}

        {activeTab === 'ui' && (
          <div>
            <h3>UI Settings</h3>
            <div className="settings-group">
              <div className="settings-row">
                <span className="settings-label">Auto-load Last Project</span>
                <div className="settings-control">
                  <input
                    type="checkbox"
                    checked={!!uiSettings.autoLoadLastProject}
                    onChange={e => onChange({ ui: { autoLoadLastProject: e.target.checked } })}
                  />
                </div>
              </div>
              
              <div className="settings-row">
                <span className="settings-label">Show Project Selector</span>
                <div className="settings-control">
                  <input
                    type="checkbox"
                    checked={!!uiSettings.showProjectSelector}
                    onChange={e => onChange({ ui: { showProjectSelector: e.target.checked } })}
                  />
                </div>
              </div>
              
              <div className="settings-row">
                <span className="settings-label">Always use classic file write (bypass agent)</span>
                <div className="settings-control">
                  <input
                    type="checkbox"
                    checked={!!uiSettings.alwaysUseClassicFileWrite}
                    onChange={e => onChange({ ui: { alwaysUseClassicFileWrite: e.target.checked } })}
                  />
                </div>
              </div>
            </div>
            {/* Add more UI-related settings here */}
          </div>
        )}
      </div>
    </div>
  );
};

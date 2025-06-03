import React from 'react';
import './Tabs.css';

export interface TabData {
  key: string;
  title: string;
  content: React.ReactNode;
  closable?: boolean;
}

interface TabsProps {
  tabs: TabData[];
  activeKey: string;
  onTabChange: (key: string) => void;
  onTabClose?: (key: string) => void;
}

export const Tabs: React.FC<TabsProps> = ({ tabs, activeKey, onTabChange, onTabClose }) => {
  return (
    <div className="main-tabs">
      <div className="tab-bar">
        {tabs.map(tab => (
          <div
            key={tab.key}
            className={`tab-label${tab.key === activeKey ? ' active' : ''}`}
            onClick={() => onTabChange(tab.key)}
          >
            {tab.title}
            {tab.closable && onTabClose && (
              <span
                className="tab-close"
                onClick={e => {
                  e.stopPropagation();
                  onTabClose(tab.key);
                }}
                title="Close tab"
              >
                ×
              </span>
            )}
          </div>
        ))}
      </div>
      <div className="tab-content">
        {tabs.find(tab => tab.key === activeKey)?.content}
      </div>
    </div>
  );
};

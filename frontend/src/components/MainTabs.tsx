import React, { useState, useEffect, useCallback } from 'react';
import { Tabs, TabData } from './Tabs';
import { ChatView } from './ChatView';
import { FileBrowser } from './FileBrowser';
import JSONPlanView from './JSONPlanView';
import { CodeChangesView } from './CodeChangesView';
import { TestResultsView } from './TestResultsView';

// You can extend this to dynamically add more tab types
export type MainTabType = 'chat' | 'file' | 'json' | 'code' | 'test';

export interface MainTabsProps {
  // All props needed for ChatView, FileBrowser, etc.
  chatProps: any;
  fileBrowserProps: any;
  jsonPlanProps?: any;
  codeChangesProps?: any;
  testResultsProps?: any;
  // Callback to pass up tab opening functions
  onTabsReady?: (handlers: { openFilesTab: () => void }) => void;
}

export const MainTabs: React.FC<MainTabsProps> = ({
  chatProps,
  fileBrowserProps,
  jsonPlanProps,
  codeChangesProps,
  testResultsProps,
  onTabsReady,
}) => {
  // Tabs state: always keep chat as the first, non-closable tab
  const [tabs, setTabs] = useState<TabData[]>([
    {
      key: 'chat',
      title: 'Chat',
      content: null, // Will be set dynamically
      closable: false
    },
  ]);

  // Update chat tab content whenever chatProps change
  useEffect(() => {
    setTabs(prev => {
      const chatTabIndex = prev.findIndex(tab => tab.key === 'chat');
      if (chatTabIndex === -1) return prev;
      
      const newTabs = [...prev];
      newTabs[chatTabIndex] = {
        ...newTabs[chatTabIndex],
        content: (
          <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0, height: '100%' }}>
            <ChatView {...chatProps} />
          </div>
        )
      };
      return newTabs;
    });
  }, [chatProps]);
  const [activeKey, setActiveKey] = useState('chat');

  // Add a visible button to open the Files tab for now
  const openFilesTab = useCallback(() => {
    setTabs(prev => {
      if (prev.find(tab => tab.key === 'file')) return prev;
      return [
        ...prev,
        {
          key: 'file',
          title: 'Files',
          content: (
            <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0, height: '100%' }}>
              <FileBrowser {...fileBrowserProps} />
            </div>
          ),
          closable: true
        }
      ];
    });
    setActiveKey('file');
  }, [fileBrowserProps]);

  // Pass tab opening functions to parent
  useEffect(() => {
    if (onTabsReady) {
      onTabsReady({ openFilesTab });
    }
  }, [onTabsReady, openFilesTab]);

  const closeTab = (key: string) => {
    setTabs(prev => {
      const idx = prev.findIndex(tab => tab.key === key);
      if (idx === -1 || !prev[idx].closable) return prev;
      const newTabs = prev.filter(tab => tab.key !== key);
      // If closing active tab, switch to previous
      if (activeKey === key) {
        setActiveKey(newTabs[Math.max(0, idx - 1)].key);
      }
      return newTabs;
    });
  };

  return (
    <div className="main-tabs-container" style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      flex: 1, 
      minHeight: 0, 
      height: '100%',
      width: '100%',
      overflow: 'hidden' 
    }}>
      <Tabs
        tabs={tabs}
        activeKey={activeKey}
        onTabChange={setActiveKey}
        onTabClose={closeTab}
      />
    </div>
  );
};

import React, { useState, useEffect, useCallback } from 'react';
import { Tabs, TabData } from './Tabs';
import { ChatView } from './ChatView';
import { ChannelChatView } from './ChannelChatView';
import { FileBrowser } from './FileBrowser';
import { CodeEditor } from './CodeEditor';
import JSONPlanView from './JSONPlanView';
import { CodeChangesView } from './CodeChangesView';
import { TestResultsView } from './TestResultsView';
import { SettingsPage } from './SettingsPage';

// You can extend this to dynamically add more tab types
export type MainTabType = 'chat' | 'file' | 'editor' | 'json' | 'code' | 'test' | 'settings';

export interface MainTabsProps {
  // All props needed for ChatView, FileBrowser, etc.
  chatProps: any;
  fileBrowserProps: any;
  jsonPlanProps?: any;
  codeChangesProps?: any;
  testResultsProps?: any;
  // Callback to pass up tab opening functions
  onTabsReady?: (handlers: { 
    openFilesTab: () => void;
    openEditorTab: (filePath: string) => void;
    openSettingsTab: () => void;
  }) => void;
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
            <ChannelChatView {...chatProps} />
          </div>
        )
      };
      return newTabs;
    });
  }, [chatProps]);
  const [activeKey, setActiveKey] = useState('chat');

  // Add a function to open editor tabs
  const openEditorTab = useCallback((filePath: string) => {
    const editorKey = `editor-${filePath}`;
    const fileName = filePath.split('/').pop() || filePath;
    
    setTabs(prev => {
      // Check if editor tab for this file already exists
      if (prev.find(tab => tab.key === editorKey)) {
        setActiveKey(editorKey);
        return prev;
      }
      
      return [
        ...prev,
        {
          key: editorKey,
          title: fileName,
          content: (
            <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0, height: '100%' }}>
              <CodeEditor 
                filePath={filePath}
                jsonRpcService={fileBrowserProps.jsonRpcService}
                theme={chatProps.theme}
                onClose={() => closeTab(editorKey)}
              />
            </div>
          ),
          closable: true
        }
      ];
    });
    setActiveKey(editorKey);
  }, [fileBrowserProps.jsonRpcService, chatProps.theme]);

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
              <FileBrowser 
                {...fileBrowserProps} 
                onOpenInEditor={openEditorTab}
              />
            </div>
          ),
          closable: true
        }
      ];
    });
    setActiveKey('file');
  }, [fileBrowserProps, openEditorTab]);

  // Add a function to open the Settings tab
  const openSettingsTab = useCallback(() => {
    setTabs(prev => {
      if (prev.find(tab => tab.key === 'settings')) return prev;
      return [
        ...prev,
        {
          key: 'settings',
          title: 'Settings',
          content: (
            <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0, height: '100%' }}>
              <SettingsPage />
            </div>
          ),
          closable: true
        }
      ];
    });
    setActiveKey('settings');
  }, [setTabs, setActiveKey]); // Add correct dependencies

  // Pass tab opening functions to parent
  useEffect(() => {
    if (onTabsReady) {
      onTabsReady({ openFilesTab, openEditorTab, openSettingsTab });
    }
  }, [onTabsReady, openFilesTab, openEditorTab, openSettingsTab]);

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

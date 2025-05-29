import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';

export type ViewType = 'chat' | 'json' | 'code' | 'test';

interface ViewHistoryEntry {
  view: ViewType;
  timestamp: number;
  data?: any;
}

interface ViewContextType {
  currentView: ViewType;
  setView: (view: ViewType, data?: any) => void;
  viewData: any;
  setViewData: (data: any) => void;
  viewHistory: ViewHistoryEntry[];
  navigateBack: () => void;
  navigateForward: () => void;
  canGoBack: boolean;
  canGoForward: boolean;
  resetView: () => void;
}

const ViewContext = createContext<ViewContextType | undefined>(undefined);

export const useViewContext = () => {
  const context = useContext(ViewContext);
  if (!context) {
    throw new Error('useViewContext must be used within a ViewProvider');
  }
  return context;
};

interface ViewProviderProps {
  children: ReactNode;
  defaultView?: ViewType;
}

export const ViewProvider: React.FC<ViewProviderProps> = ({ 
  children, 
  defaultView = 'chat' 
}) => {
  const [currentView, setCurrentView] = useState<ViewType>(defaultView);
  const [viewData, setViewData] = useState<any>({});
  const [viewHistory, setViewHistory] = useState<ViewHistoryEntry[]>([
    { view: defaultView, timestamp: Date.now(), data: {} }
  ]);
  const [historyIndex, setHistoryIndex] = useState(0);

  const setView = useCallback((view: ViewType, data?: any) => {
    const newData = data !== undefined ? data : viewData;
    const newEntry: ViewHistoryEntry = {
      view,
      timestamp: Date.now(),
      data: newData
    };

    setViewHistory(prev => {
      // Remove any forward history when navigating to a new view
      const newHistory = prev.slice(0, historyIndex + 1);
      return [...newHistory, newEntry];
    });
    
    setHistoryIndex(prev => prev + 1);
    setCurrentView(view);
    if (data !== undefined) {
      setViewData(data);
    }
  }, [historyIndex, viewData]);

  const navigateBack = useCallback(() => {
    if (historyIndex > 0 && viewHistory.length > 0) {
      const newIndex = historyIndex - 1;
      const entry = viewHistory[newIndex];
      if (entry) {
        setHistoryIndex(newIndex);
        setCurrentView(entry.view);
        setViewData(entry.data || {});
      }
    }
  }, [historyIndex, viewHistory]);

  const navigateForward = useCallback(() => {
    if (historyIndex < viewHistory.length - 1 && viewHistory.length > 0) {
      const newIndex = historyIndex + 1;
      const entry = viewHistory[newIndex];
      if (entry) {
        setHistoryIndex(newIndex);
        setCurrentView(entry.view);
        setViewData(entry.data || {});
      }
    }
  }, [historyIndex, viewHistory]);

  const resetView = useCallback(() => {
    setCurrentView(defaultView);
    setViewData({});
    setViewHistory([{ view: defaultView, timestamp: Date.now(), data: {} }]);
    setHistoryIndex(0);
  }, [defaultView]);

  const canGoBack = historyIndex > 0;
  const canGoForward = historyIndex < viewHistory.length - 1;

  const value: ViewContextType = {
    currentView,
    setView,
    viewData,
    setViewData,
    viewHistory,
    navigateBack,
    navigateForward,
    canGoBack,
    canGoForward,
    resetView
  };

  return (
    <ViewContext.Provider value={value}>
      {children}
    </ViewContext.Provider>
  );
};
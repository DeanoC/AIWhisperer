import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useViewContext } from '../contexts/ViewContext';
import { ChatView } from './ChatView';
import { JSONPlanView } from './JSONPlanView';
import { CodeChangesView } from './CodeChangesView';
import { TestResultsView } from './TestResultsView';
import './ViewRouter.css';

export interface ViewRouterProps {
  initialData?: any;
  isLoading?: boolean;
}

type ViewType = 'chat' | 'json' | 'code' | 'test';

interface ViewConfig {
  type: ViewType;
  name: string;
  icon: string;
  shortcut: string;
  hasExport?: boolean;
}

const viewConfigs: ViewConfig[] = [
  { type: 'chat', name: 'Chat', icon: '💬', shortcut: '1' },
  { type: 'json', name: 'JSON', icon: '📄', shortcut: '2', hasExport: true },
  { type: 'code', name: 'Code', icon: '📝', shortcut: '3', hasExport: true },
  { type: 'test', name: 'Tests', icon: '✅', shortcut: '4' },
];

export const ViewRouter: React.FC<ViewRouterProps> = ({ 
  initialData, 
  isLoading = false 
}) => {
  const { currentView, setView, viewData, resetView } = useViewContext();
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [announcement, setAnnouncement] = useState('');
  const viewContainerRef = useRef<HTMLDivElement>(null);
  const toolbarRef = useRef<HTMLDivElement>(null);
  const scrollPositions = useRef<Record<ViewType, number>>({
    chat: 0,
    json: 0,
    code: 0,
    test: 0,
  });

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!e.ctrlKey || isLoading) return;

      const config = viewConfigs.find(v => v.shortcut === e.key);
      if (config) {
        e.preventDefault();
        handleViewChange(config.type);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isLoading, currentView]);

  // Handle toolbar keyboard navigation
  useEffect(() => {
    const handleToolbarKeyDown = (e: KeyboardEvent) => {
      if (!toolbarRef.current) return;
      
      const buttons = toolbarRef.current.querySelectorAll('.view-button, .action-button');
      const currentIndex = Array.from(buttons).findIndex(btn => btn === document.activeElement);
      
      if (currentIndex === -1) return;
      
      let nextIndex = currentIndex;
      
      if (e.key === 'ArrowRight') {
        e.preventDefault();
        nextIndex = Math.min(currentIndex + 1, buttons.length - 1);
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        nextIndex = Math.max(currentIndex - 1, 0);
      }
      
      if (nextIndex !== currentIndex) {
        (buttons[nextIndex] as HTMLElement).focus();
      }
    };

    const toolbar = toolbarRef.current;
    if (toolbar) {
      toolbar.addEventListener('keydown', handleToolbarKeyDown);
      return () => toolbar.removeEventListener('keydown', handleToolbarKeyDown);
    }
  }, []);

  // Save scroll position before switching views
  const saveScrollPosition = useCallback(() => {
    if (viewContainerRef.current) {
      scrollPositions.current[currentView] = viewContainerRef.current.scrollTop;
    }
  }, [currentView]);

  // Restore scroll position after switching views
  const restoreScrollPosition = useCallback((view: ViewType) => {
    if (viewContainerRef.current) {
      viewContainerRef.current.scrollTop = scrollPositions.current[view];
    }
  }, []);

  const handleViewChange = (newView: ViewType) => {
    if (newView === currentView || isLoading) return;

    saveScrollPosition();
    setIsTransitioning(true);
    
    // Announce view change for accessibility
    const viewName = viewConfigs.find(v => v.type === newView)?.name || newView;
    setAnnouncement(`Switched to ${viewName} view`);

    setTimeout(() => {
      setView(newView);
      setIsTransitioning(false);
      restoreScrollPosition(newView);
    }, 150);
  };

  const renderView = () => {
    const props = { data: initialData || viewData };
    
    switch (currentView) {
      case 'json':
        return <JSONPlanView {...props} />;
      case 'code':
        return <CodeChangesView {...props} />;
      case 'test':
        return <TestResultsView {...props} />;
      case 'chat':
      default:
        // ChatView requires its own props, not handled by ViewRouter
        return <div className="chat-placeholder">Chat view should be rendered separately</div>;
    }
  };

  const currentConfig = viewConfigs.find(v => v.type === currentView);

  return (
    <div className="view-router">
      <div 
        ref={toolbarRef}
        className="view-toolbar"
        role="toolbar"
        aria-label="View selection"
      >
        <div className="view-buttons">
          {viewConfigs.map((config) => (
            <button
              key={config.type}
              className={`view-button ${currentView === config.type ? 'active' : ''}`}
              onClick={() => handleViewChange(config.type)}
              disabled={isLoading}
              aria-label={config.name}
              aria-pressed={currentView === config.type}
            >
              <span className="view-icon">{config.icon}</span>
              <span className="view-name">{config.name}</span>
            </button>
          ))}
        </div>
        
        <div className="view-actions">
          {currentConfig?.hasExport && (
            <button 
              className="action-button"
              aria-label="Export"
              disabled={isLoading}
            >
              Export
            </button>
          )}
          <button 
            className="action-button"
            onClick={resetView}
            aria-label="Reset View"
            disabled={isLoading}
          >
            Reset View
          </button>
        </div>
      </div>
      
      <div 
        ref={viewContainerRef}
        className={`view-container view-transition ${isTransitioning ? 'transitioning' : ''}`}
        data-testid="view-container"
        aria-live="polite"
      >
        {renderView()}
      </div>
      
      {/* Accessibility announcement */}
      <div 
        role="status" 
        className="sr-only"
        aria-live="polite"
      >
        {announcement}
      </div>
    </div>
  );
};
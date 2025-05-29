import React, { useState, useEffect, useCallback, useRef, ReactNode } from 'react';
import { Sidebar } from './Sidebar';
import { ContextPanel } from './ContextPanel';
import { ViewRouter } from './ViewRouter';
import { ProjectSelector } from './ProjectSelector';
import { CurrentAgentDisplay } from './CurrentAgentDisplay';
import './MainLayout.css';

interface MainLayoutProps {
  children?: ReactNode;
  isLoading?: boolean;
  theme?: 'light' | 'dark';
  currentAgent?: any;
  currentPlan?: any;
  onThemeToggle?: () => void;
  connectionStatus?: 'connecting' | 'connected' | 'disconnected' | 'error';
}

interface PanelState {
  sidebarCollapsed: boolean;
  contextCollapsed: boolean;
  sidebarWidth: number;
  contextWidth: number;
}

class ErrorBoundary extends React.Component<
  { children: ReactNode; onRetry?: () => void },
  { hasError: boolean }
> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Layout error:', error, errorInfo);
  }

  handleRetry = () => {
    this.setState({ hasError: false });
    this.props.onRetry?.();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <h2>Something went wrong</h2>
          <button onClick={this.handleRetry}>Retry</button>
        </div>
      );
    }

    return this.props.children;
  }
}

export const MainLayout: React.FC<MainLayoutProps> = ({ 
  children, 
  isLoading = false,
  theme = 'light',
  currentAgent,
  currentPlan,
  onThemeToggle,
  connectionStatus = 'disconnected'
}) => {
  const [panelState, setPanelState] = useState<PanelState>(() => {
    // Initialize from localStorage
    const savedState = {
      sidebarCollapsed: localStorage.getItem('layout.sidebar.collapsed') === 'true',
      contextCollapsed: localStorage.getItem('layout.context.collapsed') === 'true',
      sidebarWidth: parseInt(localStorage.getItem('layout.sidebar.width') || '250'),
      contextWidth: parseInt(localStorage.getItem('layout.context.width') || '300')
    };

    // Auto-collapse on small screens
    if (window.innerWidth < 768) {
      savedState.sidebarCollapsed = true;
      savedState.contextCollapsed = true;
    }

    return savedState;
  });

  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [announcement, setAnnouncement] = useState('');
  const [isResizing, setIsResizing] = useState<'sidebar' | 'context' | null>(null);
  const mainRef = useRef<HTMLElement>(null);
  const startXRef = useRef(0);
  const startWidthRef = useRef(0);

  // Save theme preference
  useEffect(() => {
    localStorage.setItem('layout.theme', theme);
  }, [theme]);

  // Handle responsive behavior
  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 768) {
        setPanelState(prev => ({
          ...prev,
          sidebarCollapsed: true,
          contextCollapsed: true
        }));
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Toggle functions
  const toggleSidebar = useCallback(() => {
    setPanelState(prev => {
      const collapsed = !prev.sidebarCollapsed;
      localStorage.setItem('layout.sidebar.collapsed', String(collapsed));
      setAnnouncement(`Sidebar ${collapsed ? 'collapsed' : 'expanded'}`);
      
      // Focus main content when sidebar closes
      if (collapsed && mainRef.current) {
        mainRef.current.focus();
      }
      
      return { ...prev, sidebarCollapsed: collapsed };
    });
  }, []);

  const toggleContext = useCallback(() => {
    setPanelState(prev => {
      const collapsed = !prev.contextCollapsed;
      localStorage.setItem('layout.context.collapsed', String(collapsed));
      setAnnouncement(`Context panel ${collapsed ? 'collapsed' : 'expanded'}`);
      
      return { ...prev, contextCollapsed: collapsed };
    });
  }, []);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!e.ctrlKey || isLoading) return;

      switch (e.key.toLowerCase()) {
        case 'b':
          e.preventDefault();
          toggleSidebar();
          break;
        case 'i':
          e.preventDefault();
          toggleContext();
          break;
        case 'm':
          e.preventDefault();
          mainRef.current?.focus();
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isLoading, toggleSidebar, toggleContext]);

  // Resize handlers
  const handleResizeStart = useCallback((panel: 'sidebar' | 'context', e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(panel);
    startXRef.current = e.clientX;
    startWidthRef.current = panel === 'sidebar' ? panelState.sidebarWidth : panelState.contextWidth;
  }, [panelState]);

  useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (e: MouseEvent) => {
      const diff = e.clientX - startXRef.current;
      const newWidth = isResizing === 'sidebar' 
        ? startWidthRef.current + diff
        : startWidthRef.current - diff;

      // Enforce min/max widths
      const clampedWidth = Math.max(200, Math.min(400, newWidth));

      setPanelState(prev => ({
        ...prev,
        [`${isResizing}Width`]: clampedWidth
      }));
    };

    const handleMouseUp = () => {
      if (isResizing) {
        const width = isResizing === 'sidebar' ? panelState.sidebarWidth : panelState.contextWidth;
        localStorage.setItem(`layout.${isResizing}.width`, String(width));
      }
      setIsResizing(null);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing, panelState]);

  const skipToMain = () => {
    mainRef.current?.focus();
  };

  return (
    <div className={`main-layout theme-${theme} three-column`}>
      {/* Skip Navigation */}
      <a href="#main-content" className="skip-link" onClick={skipToMain}>
        Skip to main content
      </a>

      {/* Header */}
      <header className="main-header" role="banner">
        <div className="header-content">
          {window.innerWidth < 768 && (
            <button
              className="mobile-menu-button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-label="Menu"
            >
              ☰
            </button>
          )}
          <h1>AI Whisperer</h1>
          <div className="header-controls">
            <CurrentAgentDisplay agent={currentAgent} />
            {onThemeToggle && (
              <button onClick={onThemeToggle} className="theme-toggle">
                {theme === 'light' ? '🌙' : '☀️'}
              </button>
            )}
            <ProjectSelector />
          </div>
        </div>
      </header>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="mobile-menu" data-testid="mobile-menu">
          <button onClick={() => {
            toggleSidebar();
            setMobileMenuOpen(false);
          }}>
            Toggle Sidebar
          </button>
          <button onClick={() => {
            toggleContext();
            setMobileMenuOpen(false);
          }}>
            Toggle Context Panel
          </button>
        </div>
      )}

      {/* Main Content Area */}
      <div className="layout-body">
        {/* Sidebar */}
        <aside 
          className={`layout-sidebar ${panelState.sidebarCollapsed ? 'collapsed' : ''}`}
          style={{ width: panelState.sidebarCollapsed ? '60px' : `${panelState.sidebarWidth}px` }}
          role="navigation"
          data-testid="sidebar"
        >
          <Sidebar 
            collapsed={panelState.sidebarCollapsed} 
            onCollapse={toggleSidebar}
            disabled={isLoading}
          />
          {!panelState.sidebarCollapsed && (
            <div
              className="resize-handle resize-handle-right"
              onMouseDown={(e) => handleResizeStart('sidebar', e)}
              data-testid="sidebar-resizer"
            />
          )}
        </aside>

        {/* Main Content */}
        <main 
          id="main-content"
          className="layout-main"
          role="main"
          ref={mainRef}
          tabIndex={-1}
        >
          <ErrorBoundary>
            {children || <ViewRouter isLoading={isLoading} />}
          </ErrorBoundary>
        </main>

        {/* Context Panel */}
        <aside 
          className={`layout-context ${panelState.contextCollapsed ? 'collapsed' : ''}`}
          style={{ width: panelState.contextCollapsed ? '60px' : `${panelState.contextWidth}px` }}
          data-testid="context-panel"
        >
          {!panelState.contextCollapsed && (
            <div
              className="resize-handle resize-handle-left"
              onMouseDown={(e) => handleResizeStart('context', e)}
              data-testid="context-resizer"
            />
          )}
          <ContextPanel 
            collapsed={panelState.contextCollapsed} 
            onCollapse={toggleContext}
            disabled={isLoading}
            currentAgent={currentAgent}
            currentPlan={currentPlan}
          />
        </aside>
      </div>

      {/* Footer */}
      <footer className="main-footer" role="contentinfo">
        <div className="status-bar" data-testid="status-bar">
          <span>WebSocket</span>
          <span className="separator">•</span>
          <span className={`connection-status status-${connectionStatus}`}>
            {connectionStatus === 'connected' && '✓ Connected'}
            {connectionStatus === 'connecting' && '⟳ Connecting...'}
            {connectionStatus === 'disconnected' && '✗ Disconnected'}
            {connectionStatus === 'error' && '⚠ Error'}
          </span>
        </div>
      </footer>

      {/* Loading Overlay */}
      {isLoading && (
        <div className="loading-overlay" data-testid="loading-overlay">
          <div className="loading-spinner">
            <div className="spinner"></div>
            <p>Loading...</p>
          </div>
        </div>
      )}

      {/* Accessibility Announcements */}
      <div role="status" className="sr-only" aria-live="polite">
        {announcement}
      </div>
    </div>
  );
};
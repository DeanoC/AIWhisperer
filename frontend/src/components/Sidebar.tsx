import React, { useState, useEffect, useRef } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { AgentSidebar } from './AgentSidebar';
import './Sidebar.css';

interface SidebarProps {
  collapsed: boolean;
  onCollapse: (collapsed: boolean) => void;
  disabled?: boolean;
  onNewChat?: () => void;
  onNewPlan?: () => void;
  onOpenFilesTab?: () => void;
}

interface NavItem {
  path: string;
  label: string;
  icon: string;
  iconTestId: string;
}

interface NavSection {
  title: string;
  items: NavItem[];
  collapsible?: boolean;
}

const mainNavItems: NavItem[] = [
  { path: '/chat', label: 'Chat', icon: '💬', iconTestId: 'icon-chat' },
  { path: '/plans', label: 'Plans', icon: '📋', iconTestId: 'icon-plans' },
  { path: '/code', label: 'Code', icon: '📝', iconTestId: 'icon-code' },
  { path: '/tests', label: 'Tests', icon: '✅', iconTestId: 'icon-tests' },
  { path: '/settings', label: 'Settings', icon: '⚙️', iconTestId: 'icon-settings' },
];

const sections: NavSection[] = [
  {
    title: 'Workspace',
    items: [
      { path: '/files', label: 'Files', icon: '📁', iconTestId: 'icon-files' },
      { path: '/search', label: 'Search', icon: '🔍', iconTestId: 'icon-search' },
    ],
    collapsible: true,
  },
  {
    title: 'Tools',
    items: [
      { path: '/terminal', label: 'Terminal', icon: '🖥️', iconTestId: 'icon-terminal' },
      { path: '/git', label: 'Git', icon: '🌿', iconTestId: 'icon-git' },
    ],
    collapsible: true,
  },
];

export const Sidebar: React.FC<SidebarProps> = ({ 
  collapsed, 
  onCollapse, 
  disabled = false,
  onNewChat,
  onNewPlan,
  onOpenFilesTab
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [collapsedSections, setCollapsedSections] = useState<Set<string>>(new Set());
  const [announcement, setAnnouncement] = useState('');
  const [activeTooltip, setActiveTooltip] = useState<string | null>(null);
  const location = useLocation();
  const navRef = useRef<HTMLElement>(null);

  // Filter items based on search
  const filterItems = (items: NavItem[]) => {
    if (!searchTerm) return items;
    return items.filter(item => 
      item.label.toLowerCase().includes(searchTerm.toLowerCase())
    );
  };

  const filteredMainItems = filterItems(mainNavItems);
  const filteredSections = sections.map(section => ({
    ...section,
    items: filterItems(section.items)
  })).filter(section => section.items.length > 0);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!navRef.current || disabled) return;

      switch (e.key) {
        case 'ArrowLeft':
          if (!collapsed) {
            e.preventDefault();
            onCollapse(true);
          }
          break;
        case 'ArrowRight':
          if (collapsed) {
            e.preventDefault();
            onCollapse(false);
          }
          break;
        case 'ArrowDown':
        case 'ArrowUp': {
          e.preventDefault();
          const links = navRef.current.querySelectorAll('a:not([aria-disabled="true"])');
          const currentIndex = Array.from(links).findIndex(link => link === document.activeElement);
          const nextIndex = e.key === 'ArrowDown' 
            ? Math.min(currentIndex + 1, links.length - 1)
            : Math.max(currentIndex - 1, 0);
          (links[nextIndex] as HTMLElement)?.focus();
          break;
        }
      }
    };

    navRef.current?.addEventListener('keydown', handleKeyDown);
    return () => navRef.current?.removeEventListener('keydown', handleKeyDown);
  }, [collapsed, disabled, onCollapse]);

  // Toggle section collapse
  const toggleSection = (title: string) => {
    setCollapsedSections(prev => {
      const next = new Set(prev);
      if (next.has(title)) {
        next.delete(title);
      } else {
        next.add(title);
      }
      return next;
    });
  };

  // Handle link click when disabled
  const handleLinkClick = (e: React.MouseEvent) => {
    if (disabled) {
      e.preventDefault();
    }
  };

  // Announce state changes
  useEffect(() => {
    if (collapsed) {
      setAnnouncement('Sidebar collapsed');
    } else {
      setAnnouncement('Sidebar expanded');
    }
  }, [collapsed]);

  const renderNavItem = (item: NavItem) => {
    // Handle Files tab specially - don't use router navigation
    if (item.path === '/files' && onOpenFilesTab) {
      return (
        <button
          key={item.path}
          className={`nav-item ${collapsed ? 'collapsed' : ''}`}
          aria-disabled={disabled}
          onClick={() => {
            if (!disabled && onOpenFilesTab) {
              onOpenFilesTab();
            }
          }}
          onMouseEnter={() => collapsed && setActiveTooltip(item.label)}
          onMouseLeave={() => setActiveTooltip(null)}
          style={{
            background: 'none',
            border: 'none',
            padding: 0,
            width: '100%',
            textAlign: 'left',
            cursor: disabled ? 'not-allowed' : 'pointer'
          }}
        >
          <span className="nav-icon" data-testid={item.iconTestId}>{item.icon}</span>
          <span className="nav-label">{item.label}</span>
          {collapsed && activeTooltip === item.label && (
            <div className="tooltip" role="tooltip">{item.label}</div>
          )}
        </button>
      );
    }

    // Regular router navigation for other items
    return (
      <NavLink
        key={item.path}
        to={item.path}
        className={({ isActive }) => `nav-item ${isActive ? 'active' : ''} ${collapsed ? 'collapsed' : ''}`}
        aria-disabled={disabled}
        onClick={handleLinkClick}
        onMouseEnter={() => collapsed && setActiveTooltip(item.label)}
        onMouseLeave={() => setActiveTooltip(null)}
      >
        <span className="nav-icon" data-testid={item.iconTestId}>{item.icon}</span>
        <span className="nav-label">{item.label}</span>
        {collapsed && activeTooltip === item.label && (
          <div className="tooltip" role="tooltip">{item.label}</div>
        )}
      </NavLink>
    );
  };

  return (
    <div className={`sidebar ${collapsed ? 'collapsed' : ''}`} data-testid="sidebar">
      {/* Header */}
      <div className="sidebar-header">
        {!collapsed && (
          <div className="quick-actions">
            <button 
              onClick={onNewChat} 
              disabled={disabled}
              aria-label="New chat"
              title="New chat"
            >
              ➕💬
            </button>
            <button 
              onClick={onNewPlan} 
              disabled={disabled}
              aria-label="New plan"
              title="New plan"
            >
              ➕📋
            </button>
          </div>
        )}
        <button
          className="collapse-toggle"
          onClick={() => onCollapse(!collapsed)}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          disabled={disabled}
        >
          {collapsed ? '→' : '←'}
        </button>
      </div>

      {/* Search */}
      {!collapsed && (
        <div className="sidebar-search">
          <input
            type="text"
            placeholder="Search..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyDown={(e) => e.key === 'Escape' && setSearchTerm('')}
            disabled={disabled}
          />
        </div>
      )}

      {/* Navigation */}
      <nav 
        ref={navRef}
        className="sidebar-nav" 
        aria-label="Main navigation"
      >
        {/* Main Navigation */}
        <div className="nav-section">
          {filteredMainItems.map(renderNavItem)}
        </div>

        {/* Additional Sections */}
        {!collapsed && filteredSections.map(section => (
          <div 
            key={section.title}
            className="nav-section"
            role="region"
            aria-label={section.title}
          >
            <div className="section-header">
              <span className="section-title">{section.title}</span>
              {section.collapsible && (
                <button
                  className="section-toggle"
                  onClick={() => toggleSection(section.title)}
                  aria-label={`Toggle ${section.title} section`}
                  disabled={disabled}
                >
                  {collapsedSections.has(section.title) ? '▶' : '▼'}
                </button>
              )}
            </div>
            {!collapsedSections.has(section.title) && (
              <div className="section-items">
                {section.items.map(renderNavItem)}
              </div>
            )}
          </div>
        ))}

        {/* No results message */}
        {searchTerm && filteredMainItems.length === 0 && filteredSections.length === 0 && (
          <div className="no-results">No results found</div>
        )}
      </nav>

      {/* Agent Sidebar - TODO: Add required props */}
      {/* {!collapsed && (
        <div className="sidebar-agents">
          <AgentSidebar />
        </div>
      )} */}

      {/* Status announcements */}
      <div role="status" className="sr-only" aria-live="polite">
        {announcement}
      </div>
    </div>
  );
};
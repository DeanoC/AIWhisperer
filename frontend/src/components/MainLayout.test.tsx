import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { MainLayout } from './MainLayout';
import { ViewProvider } from '../contexts/ViewContext';

// Mock child components
jest.mock('./Sidebar', () => ({
  Sidebar: ({ collapsed, onCollapse }: any) => (
    <div data-testid="sidebar" className={collapsed ? 'collapsed' : ''}>
      <button onClick={() => onCollapse(!collapsed)}>Toggle Sidebar</button>
      Sidebar Content
    </div>
  )
}));

jest.mock('./ContextPanel', () => ({
  ContextPanel: ({ collapsed, onCollapse }: any) => (
    <div data-testid="context-panel" className={collapsed ? 'collapsed' : ''}>
      <button onClick={() => onCollapse(!collapsed)}>Toggle Context</button>
      Context Panel Content
    </div>
  )
}));

jest.mock('./ViewRouter', () => ({
  ViewRouter: () => <div data-testid="view-router">View Router Content</div>
}));

jest.mock('./ProjectSelector', () => ({
  ProjectSelector: () => <div data-testid="project-selector">Project Selector</div>
}));

describe('MainLayout', () => {
  const renderWithProvider = (ui: React.ReactElement) => {
    return render(
      <ViewProvider>
        {ui}
      </ViewProvider>
    );
  };

  describe('Layout Structure', () => {
    it('renders three-column layout', () => {
      renderWithProvider(<MainLayout />);
      
      expect(screen.getByTestId('sidebar')).toBeInTheDocument();
      expect(screen.getByTestId('view-router')).toBeInTheDocument();
      expect(screen.getByTestId('context-panel')).toBeInTheDocument();
    });

    it('applies correct layout classes', () => {
      const { container } = renderWithProvider(<MainLayout />);
      
      const layout = container.querySelector('.main-layout');
      expect(layout).toHaveClass('three-column');
    });

    it('contains header with app title', () => {
      renderWithProvider(<MainLayout />);
      
      expect(screen.getByRole('banner')).toBeInTheDocument();
      expect(screen.getByText('AI Whisperer')).toBeInTheDocument();
    });

    it('contains footer with status info', () => {
      renderWithProvider(<MainLayout />);
      
      expect(screen.getByRole('contentinfo')).toBeInTheDocument();
      expect(screen.getByTestId('status-bar')).toBeInTheDocument();
    });
  });

  describe('Panel Collapse/Expand', () => {
    it('collapses left sidebar', () => {
      renderWithProvider(<MainLayout />);
      
      const toggleButton = screen.getByText('Toggle Sidebar');
      fireEvent.click(toggleButton);
      
      expect(screen.getByTestId('sidebar')).toHaveClass('collapsed');
    });

    it('collapses right context panel', () => {
      renderWithProvider(<MainLayout />);
      
      const toggleButton = screen.getByText('Toggle Context');
      fireEvent.click(toggleButton);
      
      expect(screen.getByTestId('context-panel')).toHaveClass('collapsed');
    });

    it('remembers collapse state in localStorage', () => {
      const setItemSpy = jest.spyOn(Storage.prototype, 'setItem');
      
      renderWithProvider(<MainLayout />);
      
      const toggleButton = screen.getByText('Toggle Sidebar');
      fireEvent.click(toggleButton);
      
      expect(setItemSpy).toHaveBeenCalledWith('layout.sidebar.collapsed', 'true');
    });

    it('restores collapse state from localStorage', () => {
      localStorage.setItem('layout.sidebar.collapsed', 'true');
      localStorage.setItem('layout.context.collapsed', 'true');
      
      renderWithProvider(<MainLayout />);
      
      expect(screen.getByTestId('sidebar')).toHaveClass('collapsed');
      expect(screen.getByTestId('context-panel')).toHaveClass('collapsed');
    });
  });

  describe('Responsive Behavior', () => {
    it('auto-collapses panels on small screens', () => {
      // Mock window width
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 600
      });
      
      renderWithProvider(<MainLayout />);
      
      expect(screen.getByTestId('sidebar')).toHaveClass('collapsed');
      expect(screen.getByTestId('context-panel')).toHaveClass('collapsed');
    });

    it('shows mobile menu button on small screens', () => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 600
      });
      
      renderWithProvider(<MainLayout />);
      
      expect(screen.getByRole('button', { name: 'Menu' })).toBeInTheDocument();
    });

    it('toggles mobile menu', () => {
      Object.defineProperty(window, 'innerWidth', {
        writable: true,
        configurable: true,
        value: 600
      });
      
      renderWithProvider(<MainLayout />);
      
      const menuButton = screen.getByRole('button', { name: 'Menu' });
      fireEvent.click(menuButton);
      
      expect(screen.getByTestId('mobile-menu')).toBeInTheDocument();
    });
  });

  describe('Resizable Panels', () => {
    it('allows resizing sidebar width', async () => {
      renderWithProvider(<MainLayout />);
      
      const resizer = screen.getByTestId('sidebar-resizer');
      
      // Simulate drag
      fireEvent.mouseDown(resizer, { clientX: 250 });
      fireEvent.mouseMove(document, { clientX: 300 });
      fireEvent.mouseUp(document);
      
      const sidebar = screen.getByTestId('sidebar');
      expect(sidebar).toHaveStyle({ width: '300px' });
    });

    it('enforces minimum panel width', async () => {
      renderWithProvider(<MainLayout />);
      
      const resizer = screen.getByTestId('sidebar-resizer');
      
      // Try to drag below minimum
      fireEvent.mouseDown(resizer, { clientX: 250 });
      fireEvent.mouseMove(document, { clientX: 50 });
      fireEvent.mouseUp(document);
      
      const sidebar = screen.getByTestId('sidebar');
      expect(sidebar).toHaveStyle({ width: '200px' }); // Minimum width
    });

    it('enforces maximum panel width', async () => {
      renderWithProvider(<MainLayout />);
      
      const resizer = screen.getByTestId('sidebar-resizer');
      
      // Try to drag above maximum
      fireEvent.mouseDown(resizer, { clientX: 250 });
      fireEvent.mouseMove(document, { clientX: 600 });
      fireEvent.mouseUp(document);
      
      const sidebar = screen.getByTestId('sidebar');
      expect(sidebar).toHaveStyle({ width: '400px' }); // Maximum width
    });

    it('saves panel sizes to localStorage', () => {
      const setItemSpy = jest.spyOn(Storage.prototype, 'setItem');
      
      renderWithProvider(<MainLayout />);
      
      const resizer = screen.getByTestId('sidebar-resizer');
      fireEvent.mouseDown(resizer, { clientX: 250 });
      fireEvent.mouseMove(document, { clientX: 300 });
      fireEvent.mouseUp(document);
      
      expect(setItemSpy).toHaveBeenCalledWith('layout.sidebar.width', '300');
    });
  });

  describe('Keyboard Shortcuts', () => {
    it('toggles sidebar with Ctrl+B', () => {
      renderWithProvider(<MainLayout />);
      
      fireEvent.keyDown(document.body, { key: 'b', ctrlKey: true });
      
      expect(screen.getByTestId('sidebar')).toHaveClass('collapsed');
      
      fireEvent.keyDown(document.body, { key: 'b', ctrlKey: true });
      
      expect(screen.getByTestId('sidebar')).not.toHaveClass('collapsed');
    });

    it('toggles context panel with Ctrl+I', () => {
      renderWithProvider(<MainLayout />);
      
      fireEvent.keyDown(document.body, { key: 'i', ctrlKey: true });
      
      expect(screen.getByTestId('context-panel')).toHaveClass('collapsed');
    });

    it('focuses main content with Ctrl+M', () => {
      renderWithProvider(<MainLayout />);
      
      fireEvent.keyDown(document.body, { key: 'm', ctrlKey: true });
      
      const mainContent = screen.getByRole('main');
      expect(document.activeElement).toBe(mainContent);
    });
  });

  describe('Loading States', () => {
    it('shows loading overlay when loading', () => {
      renderWithProvider(<MainLayout isLoading />);
      
      expect(screen.getByTestId('loading-overlay')).toBeInTheDocument();
      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    it('disables interactions when loading', () => {
      renderWithProvider(<MainLayout isLoading />);
      
      const toggleButton = screen.getByText('Toggle Sidebar');
      expect(toggleButton).toBeDisabled();
    });
  });

  describe('Error Boundaries', () => {
    it('catches and displays errors in child components', () => {
      const ThrowError = () => {
        throw new Error('Test error');
      };
      
      // Mock console.error to avoid test noise
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      
      renderWithProvider(
        <MainLayout>
          <ThrowError />
        </MainLayout>
      );
      
      expect(screen.getByText(/Something went wrong/)).toBeInTheDocument();
      
      consoleSpy.mockRestore();
    });

    it('allows error recovery', () => {
      const ThrowError = ({ shouldThrow }: { shouldThrow: boolean }) => {
        if (shouldThrow) throw new Error('Test error');
        return <div>Content loaded</div>;
      };
      
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation();
      
      const { rerender } = renderWithProvider(
        <MainLayout>
          <ThrowError shouldThrow={true} />
        </MainLayout>
      );
      
      expect(screen.getByText(/Something went wrong/)).toBeInTheDocument();
      
      // Click retry
      fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
      
      // Rerender without error
      rerender(
        <ViewProvider>
          <MainLayout>
            <ThrowError shouldThrow={false} />
          </MainLayout>
        </ViewProvider>
      );
      
      expect(screen.getByText('Content loaded')).toBeInTheDocument();
      
      consoleSpy.mockRestore();
    });
  });

  describe('Accessibility', () => {
    it('has proper landmark regions', () => {
      renderWithProvider(<MainLayout />);
      
      expect(screen.getByRole('banner')).toBeInTheDocument();
      expect(screen.getByRole('navigation')).toBeInTheDocument();
      expect(screen.getByRole('main')).toBeInTheDocument();
      expect(screen.getByRole('complementary')).toBeInTheDocument();
      expect(screen.getByRole('contentinfo')).toBeInTheDocument();
    });

    it('manages focus correctly when panels toggle', () => {
      renderWithProvider(<MainLayout />);
      
      const mainContent = screen.getByRole('main');
      
      // Focus should move to main when sidebar closes
      fireEvent.keyDown(document.body, { key: 'b', ctrlKey: true });
      
      expect(document.activeElement).toBe(mainContent);
    });

    it('provides skip navigation link', () => {
      renderWithProvider(<MainLayout />);
      
      const skipLink = screen.getByText('Skip to main content');
      expect(skipLink).toBeInTheDocument();
      
      fireEvent.click(skipLink);
      
      const mainContent = screen.getByRole('main');
      expect(document.activeElement).toBe(mainContent);
    });

    it('announces panel state changes', () => {
      renderWithProvider(<MainLayout />);
      
      fireEvent.click(screen.getByText('Toggle Sidebar'));
      
      const announcement = screen.getByRole('status');
      expect(announcement).toHaveTextContent('Sidebar collapsed');
    });
  });

  describe('Theme Support', () => {
    it('applies dark theme class', () => {
      const { container } = renderWithProvider(<MainLayout theme="dark" />);
      
      expect(container.firstChild).toHaveClass('theme-dark');
    });

    it('persists theme preference', () => {
      const setItemSpy = jest.spyOn(Storage.prototype, 'setItem');
      
      const { rerender } = renderWithProvider(<MainLayout theme="light" />);
      
      rerender(
        <ViewProvider>
          <MainLayout theme="dark" />
        </ViewProvider>
      );
      
      expect(setItemSpy).toHaveBeenCalledWith('layout.theme', 'dark');
    });
  });
});
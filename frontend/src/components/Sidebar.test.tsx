import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { Sidebar } from './Sidebar';
import { BrowserRouter } from 'react-router-dom';

// Mock AgentSidebar
jest.mock('./AgentSidebar', () => ({
  AgentSidebar: () => <div data-testid="agent-sidebar">Agent Sidebar</div>
}));

const renderWithRouter = (ui: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {ui}
    </BrowserRouter>
  );
};

describe('Sidebar', () => {
  const defaultProps = {
    collapsed: false,
    onCollapse: jest.fn(),
    disabled: false
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    it('renders navigation menu', () => {
      renderWithRouter(<Sidebar {...defaultProps} />);
      
      expect(screen.getByRole('navigation')).toBeInTheDocument();
      expect(screen.getByLabelText('Main navigation')).toBeInTheDocument();
    });

    it('renders menu items', () => {
      renderWithRouter(<Sidebar {...defaultProps} />);
      
      expect(screen.getByRole('link', { name: /Chat/ })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /Plans/ })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /Code/ })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /Tests/ })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /Settings/ })).toBeInTheDocument();
    });

    it('renders agent sidebar', () => {
      renderWithRouter(<Sidebar {...defaultProps} />);
      
      expect(screen.getByTestId('agent-sidebar')).toBeInTheDocument();
    });

    it('renders collapse toggle button', () => {
      renderWithRouter(<Sidebar {...defaultProps} />);
      
      expect(screen.getByRole('button', { name: 'Collapse sidebar' })).toBeInTheDocument();
    });
  });

  describe('Collapsed State', () => {
    it('shows only icons when collapsed', () => {
      renderWithRouter(<Sidebar {...defaultProps} collapsed={true} />);
      
      const sidebar = screen.getByTestId('sidebar');
      expect(sidebar).toHaveClass('collapsed');
      
      // Icons should be visible
      expect(screen.getByTestId('icon-chat')).toBeInTheDocument();
      expect(screen.getByTestId('icon-plans')).toBeInTheDocument();
      
      // Labels should be hidden
      expect(screen.queryByText('Chat')).toHaveClass('nav-label');
    });

    it('shows tooltip on hover when collapsed', async () => {
      
      renderWithRouter(<Sidebar {...defaultProps} collapsed={true} />);
      
      const chatLink = screen.getByRole('link', { name: /Chat/ });
      await userEvent.hover(chatLink);
      
      expect(screen.getByRole('tooltip')).toHaveTextContent('Chat');
    });

    it('calls onCollapse when toggle clicked', () => {
      renderWithRouter(<Sidebar {...defaultProps} />);
      
      const toggleButton = screen.getByRole('button', { name: 'Collapse sidebar' });
      fireEvent.click(toggleButton);
      
      expect(defaultProps.onCollapse).toHaveBeenCalledWith(true);
    });

    it('updates toggle button aria-label when collapsed', () => {
      renderWithRouter(<Sidebar {...defaultProps} collapsed={true} />);
      
      expect(screen.getByRole('button', { name: 'Expand sidebar' })).toBeInTheDocument();
    });
  });

  describe('Navigation', () => {
    it('highlights active route', () => {
      window.history.pushState({}, '', '/plans');
      
      renderWithRouter(<Sidebar {...defaultProps} />);
      
      const plansLink = screen.getByRole('link', { name: /Plans/ });
      expect(plansLink).toHaveClass('active');
    });

    it('navigates to routes on click', () => {
      renderWithRouter(<Sidebar {...defaultProps} />);
      
      const codeLink = screen.getByRole('link', { name: /Code/ });
      fireEvent.click(codeLink);
      
      expect(window.location.pathname).toBe('/code');
    });

    it('shows keyboard focus indicators', () => {
      renderWithRouter(<Sidebar {...defaultProps} />);
      
      const chatLink = screen.getByRole('link', { name: /Chat/ });
      chatLink.focus();
      
      expect(chatLink).toHaveFocus();
      expect(chatLink).toHaveClass('focus-visible');
    });
  });

  describe('Disabled State', () => {
    it('disables all interactive elements when disabled', () => {
      renderWithRouter(<Sidebar {...defaultProps} disabled={true} />);
      
      const links = screen.getAllByRole('link');
      links.forEach(link => {
        expect(link).toHaveAttribute('aria-disabled', 'true');
      });
      
      const toggleButton = screen.getByRole('button', { name: 'Collapse sidebar' });
      expect(toggleButton).toBeDisabled();
    });

    it('prevents navigation when disabled', () => {
      renderWithRouter(<Sidebar {...defaultProps} disabled={true} />);
      
      const codeLink = screen.getByRole('link', { name: /Code/ });
      fireEvent.click(codeLink);
      
      // Should not navigate
      expect(window.location.pathname).toBe('/');
    });
  });

  describe('Sections', () => {
    it('renders workspace section', () => {
      renderWithRouter(<Sidebar {...defaultProps} />);
      
      expect(screen.getByText('Workspace')).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /Files/ })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /Search/ })).toBeInTheDocument();
    });

    it('renders tools section', () => {
      renderWithRouter(<Sidebar {...defaultProps} />);
      
      expect(screen.getByText('Tools')).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /Terminal/ })).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /Git/ })).toBeInTheDocument();
    });

    it('collapses sections independently', () => {
      renderWithRouter(<Sidebar {...defaultProps} />);
      
      const workspaceToggle = screen.getByRole('button', { name: 'Toggle Workspace section' });
      fireEvent.click(workspaceToggle);
      
      expect(screen.queryByRole('link', { name: /Files/ })).not.toBeInTheDocument();
      expect(screen.getByRole('link', { name: /Terminal/ })).toBeInTheDocument();
    });
  });

  describe('Quick Actions', () => {
    it('renders quick action buttons', () => {
      renderWithRouter(<Sidebar {...defaultProps} />);
      
      expect(screen.getByRole('button', { name: 'New chat' })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'New plan' })).toBeInTheDocument();
    });

    it('handles quick action clicks', () => {
      const onNewChat = jest.fn();
      const onNewPlan = jest.fn();
      
      renderWithRouter(
        <Sidebar 
          {...defaultProps} 
          onNewChat={onNewChat}
          onNewPlan={onNewPlan}
        />
      );
      
      fireEvent.click(screen.getByRole('button', { name: 'New chat' }));
      expect(onNewChat).toHaveBeenCalled();
      
      fireEvent.click(screen.getByRole('button', { name: 'New plan' }));
      expect(onNewPlan).toHaveBeenCalled();
    });
  });

  describe('Search', () => {
    it('renders search input', () => {
      renderWithRouter(<Sidebar {...defaultProps} />);
      
      expect(screen.getByPlaceholderText('Search...')).toBeInTheDocument();
    });

    it('filters menu items based on search', async () => {
      
      renderWithRouter(<Sidebar {...defaultProps} />);
      
      const searchInput = screen.getByPlaceholderText('Search...');
      await userEvent.type(searchInput, 'test');
      
      expect(screen.getByRole('link', { name: /Tests/ })).toBeInTheDocument();
      expect(screen.queryByRole('link', { name: /Chat/ })).not.toBeInTheDocument();
    });

    it('shows no results message', async () => {
      
      renderWithRouter(<Sidebar {...defaultProps} />);
      
      const searchInput = screen.getByPlaceholderText('Search...');
      await userEvent.type(searchInput, 'xyz123');
      
      expect(screen.getByText('No results found')).toBeInTheDocument();
    });

    it('clears search on escape', async () => {
      
      renderWithRouter(<Sidebar {...defaultProps} />);
      
      const searchInput = screen.getByPlaceholderText('Search...');
      await userEvent.type(searchInput, 'test');
      await userEvent.keyboard('{Escape}');
      
      expect(searchInput).toHaveValue('');
      expect(screen.getByRole('link', { name: /Chat/ })).toBeInTheDocument();
    });
  });

  describe('Keyboard Navigation', () => {
    it('navigates menu items with arrow keys', () => {
      renderWithRouter(<Sidebar {...defaultProps} />);
      
      const nav = screen.getByRole('navigation');
      nav.focus();
      
      fireEvent.keyDown(nav, { key: 'ArrowDown' });
      expect(screen.getByRole('link', { name: /Plans/ })).toHaveFocus();
      
      fireEvent.keyDown(nav, { key: 'ArrowUp' });
      expect(screen.getByRole('link', { name: /Chat/ })).toHaveFocus();
    });

    it('expands collapsed sidebar with right arrow', () => {
      renderWithRouter(<Sidebar {...defaultProps} collapsed={true} />);
      
      const nav = screen.getByRole('navigation');
      fireEvent.keyDown(nav, { key: 'ArrowRight' });
      
      expect(defaultProps.onCollapse).toHaveBeenCalledWith(false);
    });

    it('collapses expanded sidebar with left arrow', () => {
      renderWithRouter(<Sidebar {...defaultProps} />);
      
      const nav = screen.getByRole('navigation');
      fireEvent.keyDown(nav, { key: 'ArrowLeft' });
      
      expect(defaultProps.onCollapse).toHaveBeenCalledWith(true);
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA attributes', () => {
      renderWithRouter(<Sidebar {...defaultProps} />);
      
      const nav = screen.getByRole('navigation');
      expect(nav).toHaveAttribute('aria-label', 'Main navigation');
      
      const sections = screen.getAllByRole('region');
      expect(sections[0]).toHaveAttribute('aria-label', 'Workspace');
    });

    it('announces state changes', () => {
      renderWithRouter(<Sidebar {...defaultProps} />);
      
      fireEvent.click(screen.getByRole('button', { name: 'Collapse sidebar' }));
      
      const announcement = screen.getByRole('status');
      expect(announcement).toHaveTextContent('Sidebar collapsed');
    });

    it('manages focus correctly', () => {
      const { rerender } = renderWithRouter(<Sidebar {...defaultProps} />);
      
      const chatLink = screen.getByRole('link', { name: /Chat/ });
      chatLink.focus();
      
      // Collapse sidebar
      rerender(
        <BrowserRouter>
          <Sidebar {...defaultProps} collapsed={true} />
        </BrowserRouter>
      );
      
      // Focus should remain on the same element
      expect(screen.getByRole('link', { name: /Chat/ })).toHaveFocus();
    });
  });
});
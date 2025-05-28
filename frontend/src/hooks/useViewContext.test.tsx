import { renderHook, act } from '@testing-library/react';
import { useViewContext } from '../contexts/ViewContext';
import { ViewProvider } from '../contexts/ViewContext';
import React from 'react';

describe('useViewContext', () => {
  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <ViewProvider>{children}</ViewProvider>
  );

  describe('View Navigation', () => {
    it('provides current view state', () => {
      const { result } = renderHook(() => useViewContext(), { wrapper });
      
      expect(result.current.currentView).toBe('chat');
      expect(result.current.viewData).toEqual({});
      expect(result.current.canGoBack).toBe(false);
      expect(result.current.canGoForward).toBe(false);
    });

    it('changes view with setView', () => {
      const { result } = renderHook(() => useViewContext(), { wrapper });
      
      act(() => {
        result.current.setView('json');
      });
      
      expect(result.current.currentView).toBe('json');
    });

    it('updates view data when changing views', () => {
      const { result } = renderHook(() => useViewContext(), { wrapper });
      
      const testData = { planId: '123', version: 2 };
      
      act(() => {
        result.current.setView('json', testData);
      });
      
      expect(result.current.currentView).toBe('json');
      expect(result.current.viewData).toEqual(testData);
    });

    it('maintains separate data for each view', () => {
      const { result } = renderHook(() => useViewContext(), { wrapper });
      
      const jsonData = { planId: '123' };
      const codeData = { fileId: '456' };
      
      act(() => {
        result.current.setView('json', jsonData);
      });
      
      act(() => {
        result.current.setView('code', codeData);
      });
      
      expect(result.current.viewData).toEqual(codeData);
      
      act(() => {
        result.current.setView('json');
      });
      
      expect(result.current.viewData).toEqual(jsonData);
    });
  });

  describe('History Management', () => {
    it('tracks view history', () => {
      const { result } = renderHook(() => useViewContext(), { wrapper });
      
      act(() => {
        result.current.setView('json');
      });
      
      expect(result.current.canGoBack).toBe(true);
      expect(result.current.canGoForward).toBe(false);
      
      act(() => {
        result.current.setView('code');
      });
      
      expect(result.current.canGoBack).toBe(true);
      expect(result.current.canGoForward).toBe(false);
    });

    it('navigates back through history', () => {
      const { result } = renderHook(() => useViewContext(), { wrapper });
      
      act(() => {
        result.current.setView('json');
        result.current.setView('code');
      });
      
      act(() => {
        result.current.navigateBack();
      });
      
      expect(result.current.currentView).toBe('json');
      expect(result.current.canGoBack).toBe(true);
      expect(result.current.canGoForward).toBe(true);
    });

    it('navigates forward through history', () => {
      const { result } = renderHook(() => useViewContext(), { wrapper });
      
      act(() => {
        result.current.setView('json');
        result.current.setView('code');
      });
      
      act(() => {
        result.current.navigateBack();
      });
      
      act(() => {
        result.current.navigateForward();
      });
      
      expect(result.current.currentView).toBe('code');
      expect(result.current.canGoForward).toBe(false);
    });

    it('clears forward history on new navigation', () => {
      const { result } = renderHook(() => useViewContext(), { wrapper });
      
      act(() => {
        result.current.setView('json');
        result.current.setView('code');
        result.current.navigateBack();
      });
      
      expect(result.current.canGoForward).toBe(true);
      
      act(() => {
        result.current.setView('test');
      });
      
      expect(result.current.canGoForward).toBe(false);
      expect(result.current.currentView).toBe('test');
    });

    it('does nothing when navigating back at start', () => {
      const { result } = renderHook(() => useViewContext(), { wrapper });
      
      act(() => {
        result.current.navigateBack();
      });
      
      expect(result.current.currentView).toBe('chat');
    });

    it('does nothing when navigating forward at end', () => {
      const { result } = renderHook(() => useViewContext(), { wrapper });
      
      act(() => {
        result.current.navigateForward();
      });
      
      expect(result.current.currentView).toBe('chat');
    });
  });

  describe('View State Reset', () => {
    it('resets to default view', () => {
      const { result } = renderHook(() => useViewContext(), { wrapper });
      
      act(() => {
        result.current.setView('json', { test: 'data' });
        result.current.setView('code');
      });
      
      act(() => {
        result.current.resetView();
      });
      
      expect(result.current.currentView).toBe('chat');
      expect(result.current.viewData).toEqual({});
      expect(result.current.canGoBack).toBe(false);
      expect(result.current.canGoForward).toBe(false);
    });

    it('clears all history on reset', () => {
      const { result } = renderHook(() => useViewContext(), { wrapper });
      
      act(() => {
        result.current.setView('json');
        result.current.setView('code');
        result.current.setView('test');
      });
      
      expect(result.current.canGoBack).toBe(true);
      
      act(() => {
        result.current.resetView();
      });
      
      expect(result.current.canGoBack).toBe(false);
      expect(result.current.canGoForward).toBe(false);
    });
  });

  describe('Error Handling', () => {
    it('throws error when used outside provider', () => {
      // Suppress console.error for this test
      const originalError = console.error;
      console.error = jest.fn();
      
      expect(() => {
        renderHook(() => useViewContext());
      }).toThrow('useViewContext must be used within a ViewProvider');
      
      console.error = originalError;
    });
  });

  describe('Concurrent Updates', () => {
    it('handles rapid view changes', () => {
      const { result } = renderHook(() => useViewContext(), { wrapper });
      
      act(() => {
        result.current.setView('json');
        result.current.setView('code');
        result.current.setView('test');
        result.current.setView('chat');
      });
      
      expect(result.current.currentView).toBe('chat');
      expect(result.current.canGoBack).toBe(true);
    });

    it('preserves data integrity during rapid changes', () => {
      const { result } = renderHook(() => useViewContext(), { wrapper });
      
      const data1 = { id: 1 };
      const data2 = { id: 2 };
      const data3 = { id: 3 };
      
      act(() => {
        result.current.setView('json', data1);
        result.current.setView('code', data2);
        result.current.setView('test', data3);
      });
      
      expect(result.current.viewData).toEqual(data3);
      
      act(() => {
        result.current.navigateBack();
      });
      
      expect(result.current.viewData).toEqual(data2);
    });
  });
});
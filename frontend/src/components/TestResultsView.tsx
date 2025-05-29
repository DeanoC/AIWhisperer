import React, { useState, useCallback, useRef, useEffect } from 'react';
import './TestResultsView.css';

interface TestResult {
  id: string;
  name: string;
  status: 'passed' | 'failed' | 'skipped';
  duration: number;
  error?: {
    message: string;
    stack: string;
  };
  skipReason?: string;
}

interface TestSuite {
  id: string;
  name: string;
  path: string;
  status: 'passed' | 'failed' | 'skipped';
  duration: number;
  tests: TestResult[];
}

interface TestResultsData {
  summary: {
    total: number;
    passed: number;
    failed: number;
    skipped: number;
    duration: number;
  };
  suites: TestSuite[];
}

export interface TestResultsViewProps {
  data?: TestResultsData;
  onRerun?: (testIds: string[]) => void;
}

type StatusFilter = 'all' | 'passed' | 'failed' | 'skipped';
type SortOption = 'name' | 'duration' | 'status';
type ViewMode = 'tree' | 'flat';

const statusIcons = {
  passed: '✓',
  failed: '✗',
  skipped: '○'
};

const statusColors = {
  passed: '#10b981',
  failed: '#ef4444',
  skipped: '#6b7280'
};

export const TestResultsView: React.FC<TestResultsViewProps> = ({ data, onRerun }) => {
  const [expandedSuites, setExpandedSuites] = useState<Set<string>>(new Set());
  const [selectedTest, setSelectedTest] = useState<TestResult | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [sortBy, setSortBy] = useState<SortOption>('name');
  const [viewMode, setViewMode] = useState<ViewMode>('tree');
  const [groupByStatus, setGroupByStatus] = useState(false);
  const [focusedSuite, setFocusedSuite] = useState<string | null>(null);
  const treeRef = useRef<HTMLDivElement>(null);

  // Calculate pass rate
  const passRate = data ? Math.round((data.summary.passed / data.summary.total) * 100) : 0;

  // Filter suites and tests
  const filteredSuites = data?.suites.filter(suite => {
    // Status filter
    if (statusFilter !== 'all' && suite.status !== statusFilter) {
      return false;
    }
    
    // Search filter
    if (searchTerm) {
      const matchesSuite = suite.name.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesTest = suite.tests.some(test => 
        test.name.toLowerCase().includes(searchTerm.toLowerCase())
      );
      return matchesSuite || matchesTest;
    }
    
    return true;
  }) || [];

  // Get all failed test IDs
  const failedTestIds = data?.suites.flatMap(suite => 
    suite.tests.filter(test => test.status === 'failed').map(test => test.id)
  ) || [];

  // Sort suites
  const sortedSuites = [...filteredSuites].sort((a, b) => {
    switch (sortBy) {
      case 'duration':
        return b.duration - a.duration;
      case 'status':
        const statusOrder = { failed: 0, skipped: 1, passed: 2 };
        return statusOrder[a.status] - statusOrder[b.status];
      default:
        return a.name.localeCompare(b.name);
    }
  });

  // Handle suite expansion
  const toggleSuite = useCallback((suiteId: string) => {
    setExpandedSuites(prev => {
      const next = new Set(prev);
      if (next.has(suiteId)) {
        next.delete(suiteId);
      } else {
        next.add(suiteId);
      }
      return next;
    });
  }, []);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!treeRef.current || !treeRef.current.contains(document.activeElement)) return;
      
      const suiteIds = sortedSuites.map(s => s.id);
      const currentIndex = focusedSuite ? suiteIds.indexOf(focusedSuite) : -1;
      
      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          if (currentIndex < suiteIds.length - 1) {
            setFocusedSuite(suiteIds[currentIndex + 1]);
          }
          break;
        case 'ArrowUp':
          e.preventDefault();
          if (currentIndex > 0) {
            setFocusedSuite(suiteIds[currentIndex - 1]);
          }
          break;
        case 'Enter':
          e.preventDefault();
          if (focusedSuite) {
            toggleSuite(focusedSuite);
          }
          break;
      }
    };
    
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [focusedSuite, sortedSuites, toggleSuite]);

  // Export results
  const handleExport = useCallback(() => {
    if (!data) return;
    
    const exportData = JSON.stringify(data, null, 2);
    const blob = new Blob([exportData], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `test-results-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [data]);

  // Copy error to clipboard
  const handleCopyError = useCallback((error: TestResult['error']) => {
    if (!error) return;
    const errorText = `${error.message}\n${error.stack}`;
    navigator.clipboard.writeText(errorText);
  }, []);

  // Get filtered test count
  const filteredTestCount = sortedSuites.reduce((acc, suite) => 
    acc + suite.tests.filter(test => 
      !searchTerm || test.name.toLowerCase().includes(searchTerm.toLowerCase())
    ).length, 0
  );

  if (!data) {
    return (
      <div className="test-results-view empty" data-testid="test-view">
        <p>No test results available</p>
      </div>
    );
  }

  if (data.suites.length === 0) {
    return (
      <div className="test-results-view empty" data-testid="test-view">
        <p>No tests found</p>
      </div>
    );
  }

  return (
    <div className="test-results-view supports-high-contrast" data-testid="test-results-view">
      <div className="test-results-header">
        <div className="test-summary" role="region" aria-label="Test summary">
          <div className="summary-stats">
            <span className="total">{data.summary.total} tests</span>
            <span className="passed">{data.summary.passed} passed</span>
            <span className="failed">{data.summary.failed} failed</span>
            <span className="skipped">{data.summary.skipped} skipped</span>
            <span className="duration">{data.summary.duration}s</span>
          </div>
          
          <div className="pass-rate">
            <span>{passRate}% Pass Rate</span>
            <div className="progress-bar-container">
              <div 
                className="progress-bar"
                data-testid="progress-bar"
                style={{ width: `${passRate}%`, backgroundColor: statusColors.passed }}
              />
            </div>
          </div>
        </div>

        <div className="test-controls">
          <input
            type="text"
            placeholder="Search tests..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          
          <div className="filter-buttons">
            <button 
              className={statusFilter === 'all' ? 'active' : ''}
              onClick={() => setStatusFilter('all')}
            >
              All
            </button>
            <button 
              className={statusFilter === 'passed' ? 'active' : ''}
              onClick={() => setStatusFilter('passed')}
            >
              Passed
            </button>
            <button 
              className={statusFilter === 'failed' ? 'active' : ''}
              onClick={() => setStatusFilter('failed')}
            >
              Failed
            </button>
            <button 
              className={statusFilter === 'skipped' ? 'active' : ''}
              onClick={() => setStatusFilter('skipped')}
            >
              Skipped
            </button>
          </div>
          
          <button onClick={() => setStatusFilter('all')}>Clear Filters</button>
          
          {failedTestIds.length > 0 && onRerun && (
            <button onClick={() => onRerun(failedTestIds)}>Re-run Failed</button>
          )}
          
          <button onClick={handleExport}>Export Results</button>
        </div>
      </div>

      <div className="test-view-options">
        <button onClick={() => setViewMode(viewMode === 'tree' ? 'flat' : 'tree')}>
          {viewMode === 'tree' ? 'Flat View' : 'Tree View'}
        </button>
        
        <select 
          value={sortBy} 
          onChange={(e) => setSortBy(e.target.value as SortOption)}
          aria-label="Sort by"
        >
          <option value="name">Sort by Name</option>
          <option value="duration">Sort by Duration</option>
          <option value="status">Sort by Status</option>
        </select>
        
        <label>
          <input
            type="checkbox"
            checked={groupByStatus}
            onChange={(e) => setGroupByStatus(e.target.checked)}
          />
          Group by status
        </label>
      </div>

      <div className="test-results-content">
        {viewMode === 'tree' ? (
          <div 
            ref={treeRef}
            className="tree-view"
            data-testid="tree-view"
            role="tree"
            aria-label="Test results"
          >
            {groupByStatus ? (
              <>
                {['failed', 'passed', 'skipped'].map(status => {
                  const statusSuites = sortedSuites.filter(s => s.status === status);
                  if (statusSuites.length === 0) return null;
                  
                  return (
                    <div key={status} className="status-group">
                      <h3>{status.charAt(0).toUpperCase() + status.slice(1)} ({
                        data.summary[status as keyof typeof data.summary]
                      })</h3>
                      {statusSuites.map(suite => (
                        <TestSuiteItem
                          key={suite.id}
                          suite={suite}
                          expanded={expandedSuites.has(suite.id)}
                          focused={focusedSuite === suite.id}
                          onToggle={() => toggleSuite(suite.id)}
                          onFocus={() => setFocusedSuite(suite.id)}
                          onTestClick={setSelectedTest}
                          searchTerm={searchTerm}
                        />
                      ))}
                    </div>
                  );
                })}
              </>
            ) : (
              sortedSuites.map(suite => (
                <TestSuiteItem
                  key={suite.id}
                  suite={suite}
                  expanded={expandedSuites.has(suite.id)}
                  focused={focusedSuite === suite.id}
                  onToggle={() => toggleSuite(suite.id)}
                  onFocus={() => setFocusedSuite(suite.id)}
                  onTestClick={setSelectedTest}
                  searchTerm={searchTerm}
                />
              ))
            )}
          </div>
        ) : (
          <div className="flat-view" data-testid="flat-view">
            {sortedSuites.flatMap(suite => 
              suite.tests.map(test => (
                <TestResultItem
                  key={test.id}
                  test={test}
                  suiteName={suite.name}
                  onClick={() => setSelectedTest(test)}
                  selected={selectedTest?.id === test.id}
                />
              ))
            )}
          </div>
        )}
        
        {selectedTest && selectedTest.error && (
          <div className="test-detail-panel">
            <h3>{selectedTest.name}</h3>
            <div className="error-details">
              <p className="error-message">{selectedTest.error.message}</p>
              <pre className="error-stack">{selectedTest.error.stack}</pre>
              <button onClick={() => handleCopyError(selectedTest.error)}>Copy Error</button>
            </div>
          </div>
        )}
        
        {selectedTest && !selectedTest.error && selectedTest.status === 'failed' && (
          <div className="test-detail-panel">
            <h3>{selectedTest.name}</h3>
            <p>Error details not available</p>
          </div>
        )}
      </div>

      <div role="status" className="sr-only" aria-live="polite">
        {searchTerm && `Showing ${filteredTestCount} of ${data.summary.total} tests`}
      </div>
    </div>
  );
};

// Test Suite Component
interface TestSuiteItemProps {
  suite: TestSuite;
  expanded: boolean;
  focused: boolean;
  onToggle: () => void;
  onFocus: () => void;
  onTestClick: (test: TestResult) => void;
  searchTerm: string;
}

const TestSuiteItem: React.FC<TestSuiteItemProps> = ({
  suite,
  expanded,
  focused,
  onToggle,
  onFocus,
  onTestClick,
  searchTerm
}) => {
  const passedTests = suite.tests.filter(t => t.status === 'passed').length;
  
  return (
    <div className={`test-suite ${focused ? 'focused' : ''}`}>
      <div
        className={`suite-header status-${suite.status}`}
        data-testid={`suite-${suite.id}`}
        onClick={onToggle}
        onFocus={onFocus}
        tabIndex={0}
      >
        <button
          className="expand-button"
          data-testid={`expand-${suite.id}`}
          onClick={(e) => {
            e.stopPropagation();
            onToggle();
          }}
        >
          {expanded ? '▼' : '▶'}
        </button>
        <span className="status-icon">{statusIcons[suite.status]}</span>
        <span className="suite-name">{suite.name}</span>
        <span className="suite-stats" data-testid={`suite-stats-${suite.id}`}>
          {passedTests}/{suite.tests.length} • {suite.duration}s
        </span>
      </div>
      
      {expanded && (
        <div className="test-list">
          {suite.tests
            .filter(test => !searchTerm || test.name.toLowerCase().includes(searchTerm.toLowerCase()))
            .map(test => (
              <TestResultItem
                key={test.id}
                test={test}
                onClick={() => onTestClick(test)}
                selected={false}
              />
            ))}
        </div>
      )}
    </div>
  );
};

// Test Result Component
interface TestResultItemProps {
  test: TestResult;
  suiteName?: string;
  onClick: () => void;
  selected: boolean;
}

const TestResultItem: React.FC<TestResultItemProps> = ({
  test,
  suiteName,
  onClick,
  selected
}) => {
  return (
    <div
      className={`test-result status-${test.status} ${selected ? 'selected' : ''}`}
      data-testid={`test-${test.id}`}
      onClick={onClick}
    >
      <span className="status-icon">{statusIcons[test.status]}</span>
      <span className="test-name">
        {suiteName && <span className="suite-prefix">{suiteName} › </span>}
        {test.name}
      </span>
      <span className="test-duration">{Math.round(test.duration * 1000)}ms</span>
      {test.skipReason && (
        <span className="skip-reason">{test.skipReason}</span>
      )}
    </div>
  );
};
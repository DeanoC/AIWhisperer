"""
Log aggregator for multi-source log management and correlation.
"""

import time
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field
import threading
import uuid

from ai_whisperer.core.logging import EnhancedLogMessage, LogSource
from typing import Any, Dict, List, Optional, Tuple, Union

# Type alias for log entries
LogEntry = Dict[str, Any]

@dataclass
class CorrelationGroup:
    """Group of correlated log entries"""
    correlation_id: str
    entries: List[LogEntry] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_entry(self, entry: LogEntry):
        """Add entry to correlation group"""
        self.entries.append(entry)
        self.updated_at = datetime.now()
    
    def get_timeline(self) -> List[LogEntry]:
        """Get entries sorted by timestamp"""
        return sorted(self.entries, key=lambda e: e.get('timestamp', ''))

@dataclass 
class Timeline:
    """Timeline of events for visualization"""
    session_id: str
    start_time: datetime
    end_time: datetime
    events: List[LogEntry] = field(default_factory=list)
    
    def add_event(self, event: LogEntry):
        """Add event to timeline"""
        self.events.append(event)
        # Update time bounds
        event_time = self._parse_timestamp(event.get('timestamp'))
        if event_time:
            if event_time < self.start_time:
                self.start_time = event_time
            if event_time > self.end_time:
                self.end_time = event_time
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string"""
        if not timestamp_str:
            return None
        try:
            return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        except:
            return None
    
    def get_duration(self) -> timedelta:
        """Get timeline duration"""
        return self.end_time - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'duration_seconds': self.get_duration().total_seconds(),
            'event_count': len(self.events)
        }

class TimelineBuilder:
    """Builds timelines from log events"""
    
    def __init__(self):
        self.timelines: Dict[str, Timeline] = {}
        
    def add_event(self, log_entry: LogEntry):
        """Add event to appropriate timeline"""
        session_id = log_entry.get('session_id', 'default')
        
        if session_id not in self.timelines:
            now = datetime.now()
            self.timelines[session_id] = Timeline(
                session_id=session_id,
                start_time=now,
                end_time=now
            )
        
        self.timelines[session_id].add_event(log_entry)
    
    def build_for_session(self, session_id: str) -> Optional[Timeline]:
        """Build timeline for specific session"""
        return self.timelines.get(session_id)
    
    def get_all_timelines(self) -> List[Timeline]:
        """Get all timelines"""
        return list(self.timelines.values())

class LogAggregator:
    """Aggregates logs from multiple sources with correlation"""
    
    def __init__(self, correlation_timeout: int = 300, buffer_size: int = 10000):
        """
        Initialize aggregator.
        
        Args:
            correlation_timeout: Seconds before correlation groups expire
            buffer_size: Maximum number of logs to keep in memory
        """
        self.correlation_timeout = correlation_timeout
        self.buffer_size = buffer_size
        
        # Storage
        self.logs: deque = deque(maxlen=buffer_size)
        self.correlation_map: Dict[str, CorrelationGroup] = {}
        self.session_logs: Dict[str, List[LogEntry]] = defaultdict(list)
        self.source_logs: Dict[LogSource, List[LogEntry]] = defaultdict(list)
        
        # Timeline builder
        self.timeline_builder = TimelineBuilder()
        
        # Thread safety
        self.lock = threading.RLock()
        
        # Cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        self.running = True
    
    def add_log(self, log_entry: Union[EnhancedLogMessage, Dict[str, Any]]):
        """Add log maintaining correlations"""
        with self.lock:
            # Convert to dict if needed
            if isinstance(log_entry, EnhancedLogMessage):
                log_dict = log_entry.to_dict()
            else:
                log_dict = log_entry
            
            # Add unique ID if not present
            if 'event_id' not in log_dict:
                log_dict['event_id'] = str(uuid.uuid4())
            
            # Add to main buffer
            self.logs.append(log_dict)
            
            # Group by correlation ID
            correlation_id = log_dict.get('correlation_id')
            if correlation_id:
                if correlation_id not in self.correlation_map:
                    self.correlation_map[correlation_id] = CorrelationGroup(correlation_id)
                self.correlation_map[correlation_id].add_entry(log_dict)
            
            # Group by session
            session_id = log_dict.get('session_id')
            if session_id:
                self.session_logs[session_id].append(log_dict)
            
            # Group by source
            source = log_dict.get('source')
            if source:
                try:
                    source_enum = LogSource(source) if isinstance(source, str) else source
                    self.source_logs[source_enum].append(log_dict)
                except:
                    pass
            
            # Add to timeline
            self.timeline_builder.add_event(log_dict)
    
    def get_logs(self, session_id: Optional[str] = None,
                 time_range: Optional[Tuple[datetime, datetime]] = None,
                 sources: Optional[List[LogSource]] = None,
                 limit: int = 1000) -> List[LogEntry]:
        """
        Retrieve logs with filters.
        
        Args:
            session_id: Filter by session
            time_range: Filter by time range (start, end)
            sources: Filter by log sources
            limit: Maximum number of logs to return
            
        Returns:
            Filtered log entries
        """
        with self.lock:
            # Start with all logs or session-specific logs
            if session_id:
                logs = self.session_logs.get(session_id, [])
            else:
                logs = list(self.logs)
            
            # Filter by time range
            if time_range:
                start_time, end_time = time_range
                logs = [
                    log for log in logs
                    if self._is_in_time_range(log, start_time, end_time)
                ]
            
            # Filter by sources
            if sources:
                source_values = [s.value for s in sources]
                logs = [
                    log for log in logs
                    if log.get('source') in source_values
                ]
            
            # Apply limit
            if len(logs) > limit:
                logs = logs[-limit:]
            
            return logs
    
    def get_correlated_logs(self, correlation_id: str) -> List[LogEntry]:
        """Get all logs related to a correlation ID"""
        with self.lock:
            group = self.correlation_map.get(correlation_id)
            if group:
                return group.get_timeline()
            return []
    
    def get_session_timeline(self, session_id: str) -> Optional[Timeline]:
        """Get complete timeline for a session"""
        with self.lock:
            return self.timeline_builder.build_for_session(session_id)
    
    def search_logs(self, query: str, fields: Optional[List[str]] = None,
                   limit: int = 100) -> List[LogEntry]:
        """
        Search logs for a query string.
        
        Args:
            query: Search query
            fields: Fields to search in (searches all if None)
            limit: Maximum results
            
        Returns:
            Matching log entries
        """
        with self.lock:
            results = []
            query_lower = query.lower()
            
            for log in self.logs:
                if self._matches_query(log, query_lower, fields):
                    results.append(log)
                    if len(results) >= limit:
                        break
            
            return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get aggregator statistics"""
        with self.lock:
            source_counts = {
                source.value: len(logs) 
                for source, logs in self.source_logs.items()
            }
            
            return {
                'total_logs': len(self.logs),
                'session_count': len(self.session_logs),
                'correlation_groups': len(self.correlation_map),
                'source_counts': source_counts,
                'timeline_count': len(self.timeline_builder.timelines),
                'buffer_usage': f"{len(self.logs)}/{self.buffer_size}"
            }
    
    def clear_session(self, session_id: str):
        """Clear logs for a specific session"""
        with self.lock:
            # Remove from session logs
            if session_id in self.session_logs:
                del self.session_logs[session_id]
            
            # Remove from main buffer
            self.logs = deque(
                (log for log in self.logs if log.get('session_id') != session_id),
                maxlen=self.buffer_size
            )
            
            # Clean up correlations
            for corr_id in list(self.correlation_map.keys()):
                group = self.correlation_map[corr_id]
                group.entries = [
                    e for e in group.entries 
                    if e.get('session_id') != session_id
                ]
                if not group.entries:
                    del self.correlation_map[corr_id]
    
    def shutdown(self):
        """Shutdown aggregator"""
        self.running = False
    
    def _cleanup_loop(self):
        """Background cleanup of expired correlations"""
        while self.running:
            time.sleep(60)  # Run every minute
            self._cleanup_expired_correlations()
    
    def _cleanup_expired_correlations(self):
        """Remove expired correlation groups"""
        with self.lock:
            now = datetime.now()
            expired = []
            
            for corr_id, group in self.correlation_map.items():
                age = (now - group.updated_at).total_seconds()
                if age > self.correlation_timeout:
                    expired.append(corr_id)
            
            for corr_id in expired:
                del self.correlation_map[corr_id]
    
    def _is_in_time_range(self, log: LogEntry, start: datetime, end: datetime) -> bool:
        """Check if log is in time range"""
        timestamp_str = log.get('timestamp')
        if not timestamp_str:
            return False
        
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return start <= timestamp <= end
        except:
            return False
    
    def _matches_query(self, log: LogEntry, query: str, fields: Optional[List[str]]) -> bool:
        """Check if log matches search query"""
        if fields:
            # Search specific fields
            for field in fields:
                value = log.get(field)
                if value and query in str(value).lower():
                    return True
        else:
            # Search all string values
            for value in log.values():
                if isinstance(value, str) and query in value.lower():
                    return True
        
        return False

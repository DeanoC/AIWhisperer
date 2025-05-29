/**
 * Types for file system operations and file browser
 */

/**
 * Represents a file or directory node in the file system tree
 */
export interface FileNode {
  /** The name of the file or directory */
  name: string;
  
  /** Full path from the workspace root */
  path: string;
  
  /** Whether this node is a file (true) or directory (false) */
  isFile: boolean;
  
  /** File size in bytes (only for files) */
  size?: number;
  
  /** Last modified timestamp */
  lastModified?: string;
  
  /** File extension (only for files, e.g., '.py', '.js') */
  extension?: string;
  
  /** MIME type (only for files) */
  mimeType?: string;
  
  /** Whether the file is binary */
  isBinary?: boolean;
  
  /** Child nodes (only for directories) */
  children?: FileNode[];
  
  /** Whether this directory is expanded in the UI */
  isExpanded?: boolean;
  
  /** Whether children have been loaded */
  isLoaded?: boolean;
}

/**
 * Response from listing a directory
 */
export interface DirectoryListingResponse {
  /** The path that was listed */
  path: string;
  
  /** The file/directory nodes at this path */
  nodes: FileNode[];
  
  /** Total number of items (for pagination) */
  totalCount?: number;
  
  /** Whether the listing is truncated */
  isTruncated?: boolean;
}

/**
 * Options for listing directories
 */
export interface ListDirectoryOptions {
  /** Path to list */
  path: string;
  
  /** Whether to include hidden files (starting with .) */
  includeHidden?: boolean;
  
  /** Whether to list recursively */
  recursive?: boolean;
  
  /** Maximum depth for recursive listing */
  maxDepth?: number;
  
  /** File extensions to filter (e.g., ['.py', '.js']) */
  fileTypes?: string[];
  
  /** Maximum number of items to return */
  limit?: number;
  
  /** Offset for pagination */
  offset?: number;
  
  /** Sort field */
  sortBy?: 'name' | 'size' | 'lastModified';
  
  /** Sort direction */
  sortDirection?: 'asc' | 'desc';
}

/**
 * File search options
 */
export interface SearchFilesOptions {
  /** Search query (supports wildcards) */
  query: string;
  
  /** Paths to search in */
  searchPaths?: string[];
  
  /** File extensions to filter */
  fileTypes?: string[];
  
  /** Whether to search in file contents */
  searchContent?: boolean;
  
  /** Maximum results to return */
  limit?: number;
  
  /** Case sensitive search */
  caseSensitive?: boolean;
  
  /** Use regex for search */
  useRegex?: boolean;
}

/**
 * File search result
 */
export interface FileSearchResult {
  /** The file node */
  file: FileNode;
  
  /** Relevance score (0-1) */
  score?: number;
  
  /** Matched lines (if searching content) */
  matches?: Array<{
    lineNumber: number;
    lineContent: string;
    matchStart: number;
    matchEnd: number;
  }>;
}

/**
 * Response from file search
 */
export interface SearchFilesResponse {
  /** Search results */
  results: FileSearchResult[];
  
  /** Total number of matches */
  totalMatches: number;
  
  /** Whether results are truncated */
  isTruncated?: boolean;
  
  /** Search execution time in ms */
  searchTime?: number;
}
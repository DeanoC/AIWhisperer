/**
 * Component to integrate project context with JSON-RPC service
 */

import { useEffect } from 'react';
import { useProject } from '../contexts/ProjectContext';
import { JsonRpcService } from '../services/jsonRpcService';

interface ProjectIntegrationProps {
  jsonRpcService: JsonRpcService | undefined;
}

export function ProjectIntegration({ jsonRpcService }: ProjectIntegrationProps) {
  const { setJsonRpcService } = useProject();

  useEffect(() => {
    setJsonRpcService(jsonRpcService || null);
  }, [jsonRpcService, setJsonRpcService]);

  return null; // This component doesn't render anything
}
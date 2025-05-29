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
  const { setJsonRpcService, activeProject, loadProject } = useProject();

  useEffect(() => {
    setJsonRpcService(jsonRpcService || null);
  }, [jsonRpcService, setJsonRpcService]);

  // Re-establish active project when WebSocket reconnects
  useEffect(() => {
    if (jsonRpcService && activeProject) {
      // Re-load the active project to ensure backend is in sync
      console.log('[ProjectIntegration] Re-establishing active project after reconnect:', activeProject.id);
      loadProject(activeProject.id).catch(err => {
        console.error('[ProjectIntegration] Failed to re-establish project:', err);
      });
    }
  }, [jsonRpcService, activeProject?.id]); // Only trigger when jsonRpcService changes

  return null; // This component doesn't render anything
}
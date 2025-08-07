'use client';

import { useState, useEffect, useCallback } from 'react';
import { AgentActivity } from '@/types';

export function useWebSocket(url: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [activities, setActivities] = useState<AgentActivity[]>([]);
  const [activeAgents, setActiveAgents] = useState<any[]>([]);
  const [ws, setWs] = useState<WebSocket | null>(null);

  const connect = useCallback(() => {
    try {
      const websocket = new WebSocket(url);

      websocket.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
      };

      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.type === 'initial') {
            setActiveAgents(Object.values(data.active_agents || {}));
            setActivities(data.recent_activities || []);
          } else if (data.type !== 'ping') {
            // It's a new activity
            setActivities(prev => [data, ...prev].slice(0, 100));
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      websocket.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      websocket.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        
        // Attempt to reconnect after 3 seconds
        setTimeout(() => {
          connect();
        }, 3000);
      };

      setWs(websocket);
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      setTimeout(() => {
        connect();
      }, 3000);
    }
  }, [url]);

  useEffect(() => {
    connect();

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, []);

  return {
    isConnected,
    activities,
    activeAgents,
    ws,
  };
}
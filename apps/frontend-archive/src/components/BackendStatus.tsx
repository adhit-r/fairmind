'use client';

import { useState, useEffect } from 'react';
import { Alert, Badge, Group, Text } from '@mantine/core';
import { IconCheck, IconX, IconClock } from '@tabler/icons-react';

interface BackendStatus {
  isConnected: boolean;
  message: string;
  endpointsAvailable: number;
}

export function BackendStatus() {
  const [status, setStatus] = useState<BackendStatus>({
    isConnected: false,
    message: 'Checking...',
    endpointsAvailable: 0
  });

  useEffect(() => {
    checkBackendStatus();
  }, []);

  const checkBackendStatus = async () => {
    try {
      const response = await fetch('http://localhost:8000/health');
      if (response.ok) {
        const data = await response.json();
        setStatus({
          isConnected: true,
          message: 'Backend connected - Using mock data while APIs are developed',
          endpointsAvailable: Object.keys(data.endpoints || {}).length
        });
      } else {
        setStatus({
          isConnected: false,
          message: 'Backend not responding',
          endpointsAvailable: 0
        });
      }
    } catch (error) {
      setStatus({
        isConnected: false,
        message: 'Backend connection failed',
        endpointsAvailable: 0
      });
    }
  };

  return (
    <Alert
      icon={status.isConnected ? <IconCheck size={16} /> : <IconX size={16} />}
      color={status.isConnected ? 'blue' : 'red'}
      variant="light"
    >
      <Group justify="space-between">
        <Text size="sm">{status.message}</Text>
        <Badge variant="light" color={status.isConnected ? 'blue' : 'red'}>
          {status.isConnected ? 'Connected' : 'Disconnected'}
        </Badge>
      </Group>
    </Alert>
  );
}
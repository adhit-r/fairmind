'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Container, Stack, Loader, Text } from '@mantine/core';

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to dashboard
    router.push('/dashboard');
  }, [router]);

  return (
    <Container size="lg" py="xl">
      <Stack align="center" gap="xl">
        <Loader size="xl" />
        <Text>Redirecting to FairMind dashboard...</Text>
      </Stack>
    </Container>
  );
}

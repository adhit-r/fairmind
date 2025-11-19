'use client';

import { Container } from '@mantine/core';
import ModelPerformanceBenchmark from '@/components/benchmarking/ModelPerformanceBenchmark';

export default function BenchmarksPage() {
  return (
    <Container size="xl" py="xl">
      <ModelPerformanceBenchmark />
    </Container>
  );
}
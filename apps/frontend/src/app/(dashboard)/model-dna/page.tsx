'use client';

import { LineageGraph } from '@/components/model-dna/LineageGraph';

export default function ModelDnaPage() {
    return (
        <div className="space-y-8 p-8">
            <div>
                <h1 className="text-4xl font-bold">Model DNA & Lineage</h1>
                <p className="text-muted-foreground mt-2">
                    Visualize model provenance, training history, and derivative works.
                </p>
            </div>

            <LineageGraph />
        </div>
    );
}

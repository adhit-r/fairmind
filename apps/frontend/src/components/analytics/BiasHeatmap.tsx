'use client';

import { Card } from '@/components/ui/card';
import { StatusBadge } from '@/components/patterns/StatusBadge';

interface BiasHeatmapProps {
    data: any[];
}

export function BiasHeatmap({ data }: BiasHeatmapProps) {
    // Group by attribute
    const attributes = Array.from(new Set(data.map(d => d.attribute)));
    const metrics = Array.from(new Set(data.map(d => d.metric)));

    const getValue = (attr: string, metric: string) => {
        return data.find(d => d.attribute === attr && d.metric === metric);
    };

    return (
        <Card className="p-4 sm:p-5">
            <h3 className="mb-4 text-base font-semibold">Bias Heatmap</h3>
            <div className="overflow-x-auto">
                <table className="w-full border-collapse text-sm">
                    <thead>
                        <tr>
                            <th scope="col" className="border border-border bg-muted p-2 text-left text-xs font-semibold text-muted-foreground">Attribute</th>
                            {metrics.map(m => (
                                <th key={m} scope="col" className="border border-border bg-muted p-2 text-left text-xs font-semibold text-muted-foreground">{m}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {attributes.map(attr => (
                            <tr key={attr}>
                                <th scope="row" className="border border-border p-2 text-left font-medium">{attr}</th>
                                {metrics.map(metric => {
                                    const point = getValue(attr, metric);
                                    const pass = point?.status === 'pass';
                                    return (
                                        <td key={metric} className="border border-border p-2">
                                            {point ? (
                                                <span className="flex items-center gap-2">
                                                    <span className="tabular-nums">{Number(point.value).toFixed(2)}</span>
                                                    <StatusBadge tone={pass ? 'success' : 'critical'} label={pass ? 'Pass' : 'Fail'} />
                                                </span>
                                            ) : (
                                                <span className="text-muted-foreground">Not assessed</span>
                                            )}
                                        </td>
                                    );
                                })}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </Card>
    );
}

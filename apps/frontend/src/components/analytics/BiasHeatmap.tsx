'use client';

import { Card } from '@/components/ui/card';

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
        <Card className="p-6 border-2 border-black shadow-brutal">
            <h3 className="text-lg font-bold mb-4">Bias Heatmap</h3>
            <div className="overflow-x-auto">
                <table className="w-full border-collapse">
                    <thead>
                        <tr>
                            <th className="p-2 border border-black bg-gray-100">Attribute</th>
                            {metrics.map(m => (
                                <th key={m} className="p-2 border border-black bg-gray-100">{m}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {attributes.map(attr => (
                            <tr key={attr}>
                                <td className="p-2 border border-black font-medium">{attr}</td>
                                {metrics.map(metric => {
                                    const point = getValue(attr, metric);
                                    const color = point?.status === 'pass' ? 'bg-green-200' : 'bg-red-200';
                                    return (
                                        <td key={metric} className={`p-2 border border-black text-center ${color}`}>
                                            {point?.value.toFixed(2)}
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

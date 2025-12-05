'use client';

import { Handle, Position } from 'reactflow';
import { IconBrain, IconDatabase, IconCpu } from '@tabler/icons-react';

interface ModelNodeProps {
    data: {
        label: string;
        type: 'base' | 'finetuned' | 'quantized';
    };
}

export function ModelNode({ data }: ModelNodeProps) {
    const getIcon = () => {
        switch (data.type) {
            case 'base': return <IconBrain className="w-5 h-5" />;
            case 'finetuned': return <IconDatabase className="w-5 h-5" />;
            case 'quantized': return <IconCpu className="w-5 h-5" />;
            default: return <IconBrain className="w-5 h-5" />;
        }
    };

    const getColor = () => {
        switch (data.type) {
            case 'base': return 'bg-blue-100 border-blue-500';
            case 'finetuned': return 'bg-green-100 border-green-500';
            case 'quantized': return 'bg-purple-100 border-purple-500';
            default: return 'bg-gray-100 border-gray-500';
        }
    };

    return (
        <div className={`px-4 py-2 shadow-md rounded-md border-2 ${getColor()} min-w-[150px]`}>
            <Handle type="target" position={Position.Top} className="w-3 h-3 bg-black" />
            <div className="flex items-center">
                <div className="mr-2 p-1 bg-white rounded-full border border-black">
                    {getIcon()}
                </div>
                <div className="text-sm font-bold text-black">{data.label}</div>
            </div>
            <Handle type="source" position={Position.Bottom} className="w-3 h-3 bg-black" />
        </div>
    );
}

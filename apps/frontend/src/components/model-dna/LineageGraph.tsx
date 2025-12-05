'use client';

import { useCallback } from 'react';
import ReactFlow, {
    MiniMap,
    Controls,
    Background,
    useNodesState,
    useEdgesState,
    addEdge,
    Connection,
    Edge,
    Node,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Card } from '@/components/ui/card';
import { ModelNode } from './ModelNode';

const nodeTypes = {
    model: ModelNode,
};

const initialNodes: Node[] = [
    { id: '1', type: 'model', position: { x: 250, y: 5 }, data: { label: 'Base Model (GPT-2)', type: 'base' } },
    { id: '2', type: 'model', position: { x: 100, y: 150 }, data: { label: 'Fine-tuned (Finance)', type: 'finetuned' } },
    { id: '3', type: 'model', position: { x: 400, y: 150 }, data: { label: 'Fine-tuned (Medical)', type: 'finetuned' } },
    { id: '4', type: 'model', position: { x: 100, y: 300 }, data: { label: 'Quantized (Finance)', type: 'quantized' } },
];

const initialEdges: Edge[] = [
    { id: 'e1-2', source: '1', target: '2', animated: true },
    { id: 'e1-3', source: '1', target: '3', animated: true },
    { id: 'e2-4', source: '2', target: '4', animated: true },
];

export function LineageGraph() {
    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

    const onConnect = useCallback(
        (params: Connection) => setEdges((eds) => addEdge(params, eds)),
        [setEdges],
    );

    return (
        <Card className="h-[600px] w-full border-2 border-black shadow-brutal overflow-hidden">
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={onConnect}
                nodeTypes={nodeTypes}
                fitView
            >
                <Controls />
                <MiniMap />
                <Background gap={12} size={1} />
            </ReactFlow>
        </Card>
    );
}

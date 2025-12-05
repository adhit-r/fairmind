import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { IconDatabase } from '@tabler/icons-react';

const DatasetNode = ({ data }: NodeProps) => {
    return (
        <Card className="w-56 border-2 border-black shadow-brutal bg-white">
            <Handle type="target" position={Position.Top} className="w-3 h-3 bg-black border-2 border-white" />

            <CardHeader className="p-3 pb-0">
                <div className="flex justify-between items-start">
                    <Badge variant="outline" className="bg-blue-100 text-blue-800 border-black mb-2">
                        Dataset
                    </Badge>
                    {data.version && (
                        <span className="text-xs font-mono bg-gray-100 px-1 border border-black rounded">
                            v{data.version}
                        </span>
                    )}
                </div>
                <CardTitle className="text-sm font-bold flex items-center gap-2">
                    <IconDatabase size={16} />
                    <span className="truncate" title={data.name}>{data.name}</span>
                </CardTitle>
            </CardHeader>

            <CardContent className="p-3 pt-2 text-xs space-y-2">
                {data.source && (
                    <div className="flex justify-between">
                        <span className="text-muted-foreground">Source:</span>
                        <span className="font-medium truncate max-w-[100px]" title={data.source}>{data.source}</span>
                    </div>
                )}

                <div className="pt-2 border-t border-gray-200 mt-2 text-[10px] text-muted-foreground font-mono truncate">
                    ID: {data.id?.slice(0, 12)}...
                </div>
            </CardContent>

            <Handle type="source" position={Position.Bottom} className="w-3 h-3 bg-black border-2 border-white" />
        </Card>
    );
};

export default memo(DatasetNode);

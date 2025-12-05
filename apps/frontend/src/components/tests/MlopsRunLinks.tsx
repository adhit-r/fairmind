import React from 'react';
import { Button } from '@/components/ui/button';
import { useMlops } from '@/lib/api/hooks/useMlops';
import { ExternalLink } from 'lucide-react';
import { IconActivity } from '@tabler/icons-react';

interface MlopsRunLinksProps {
    metadata?: Record<string, any>;
}

export function MlopsRunLinks({ metadata }: MlopsRunLinksProps) {
    const { getRunUrl } = useMlops();
    const [wandbUrl, setWandbUrl] = React.useState<string | null>(null);
    const [mlflowUrl, setMlflowUrl] = React.useState<string | null>(null);

    React.useEffect(() => {
        if (!metadata) return;

        const fetchUrls = async () => {
            if (metadata.wandb_run_id) {
                const url = await getRunUrl('wandb', metadata.wandb_run_id);
                setWandbUrl(url);
            }
            if (metadata.mlflow_run_id) {
                const url = await getRunUrl('mlflow', metadata.mlflow_run_id);
                setMlflowUrl(url);
            }
        };

        fetchUrls();
    }, [metadata, getRunUrl]);

    if (!metadata || (!metadata.wandb_run_id && !metadata.mlflow_run_id)) {
        return null;
    }

    return (
        <div className="flex items-center gap-2">
            {wandbUrl && (
                <Button variant="neutral" size="sm" className="bg-yellow-50 hover:bg-yellow-100 text-yellow-800 border-yellow-200" asChild>
                    <a href={wandbUrl} target="_blank" rel="noopener noreferrer">
                        <IconActivity className="mr-2 h-4 w-4" />
                        View in W&B
                        <ExternalLink className="ml-2 h-3 w-3" />
                    </a>
                </Button>
            )}
            {mlflowUrl && (
                <Button variant="neutral" size="sm" className="bg-blue-50 hover:bg-blue-100 text-blue-800 border-blue-200" asChild>
                    <a href={mlflowUrl} target="_blank" rel="noopener noreferrer">
                        <IconActivity className="mr-2 h-4 w-4" />
                        View in MLflow
                        <ExternalLink className="ml-2 h-3 w-3" />
                    </a>
                </Button>
            )}
        </div>
    );
}

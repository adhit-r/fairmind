'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
    IconArrowLeft,
    IconDownload,
    IconShare,
    IconShieldCheck,
    IconStar,
    IconBrain,
    IconTag,
    IconUser,
    IconCalendar
} from '@tabler/icons-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { marketplaceService, MarketplaceModel } from '@/services/marketplace-service';
import { toast } from 'sonner';

export default function ModelDetailsPage() {
    const params = useParams();
    const router = useRouter();
    const [model, setModel] = useState<MarketplaceModel | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (params.id) {
            fetchModel(params.id as string);
        }
    }, [params.id]);

    const fetchModel = async (id: string) => {
        try {
            setLoading(true);
            const response = await marketplaceService.getModel(id);
            setModel(response.model);
        } catch (error) {
            console.error('Error fetching model:', error);
            toast.error('Failed to load model details');
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return <div className="p-6">Loading...</div>;
    }

    if (!model) {
        return <div className="p-6">Model not found</div>;
    }

    const averageRating = model.reviews.length > 0
        ? (model.reviews.reduce((a, b) => a + b.rating, 0) / model.reviews.length).toFixed(1)
        : 'N/A';

    return (
        <div className="space-y-6 p-6 max-w-7xl mx-auto">
            {/* Header */}
            <div className="flex items-center space-x-4">
                <Button variant="ghost" size="icon" onClick={() => router.back()}>
                    <IconArrowLeft className="h-5 w-5" />
                </Button>
                <div className="flex-1">
                    <div className="flex items-center space-x-3">
                        <h1 className="text-3xl font-bold tracking-tight">{model.name}</h1>
                        <Badge variant="outline">{model.version}</Badge>
                    </div>
                    <div className="flex items-center space-x-4 text-muted-foreground mt-1">
                        <span className="flex items-center">
                            <IconUser className="mr-1 h-4 w-4" />
                            {model.author}
                        </span>
                        <span className="flex items-center">
                            <IconCalendar className="mr-1 h-4 w-4" />
                            Updated {new Date(model.updated_at).toLocaleDateString()}
                        </span>
                    </div>
                </div>
                <div className="flex space-x-2">
                    <Button variant="outline">
                        <IconShare className="mr-2 h-4 w-4" />
                        Share
                    </Button>
                    <Button>
                        <IconDownload className="mr-2 h-4 w-4" />
                        Download
                    </Button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Main Content */}
                <div className="lg:col-span-2 space-y-6">
                    <Card>
                        <CardHeader>
                            <CardTitle>Overview</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <p className="text-muted-foreground whitespace-pre-wrap">
                                {model.description}
                            </p>

                            <div className="mt-6 flex flex-wrap gap-2">
                                {model.tags.map((tag, i) => (
                                    <Badge key={i} variant="secondary">
                                        {tag.name}
                                    </Badge>
                                ))}
                            </div>
                        </CardContent>
                    </Card>

                    <Tabs defaultValue="bias-card">
                        <TabsList>
                            <TabsTrigger value="bias-card">Bias Card</TabsTrigger>
                            <TabsTrigger value="performance">Performance</TabsTrigger>
                            <TabsTrigger value="usage">Usage</TabsTrigger>
                        </TabsList>

                        <TabsContent value="bias-card" className="space-y-4">
                            <Card>
                                <CardHeader>
                                    <div className="flex justify-between items-center">
                                        <CardTitle>Fairness Metrics</CardTitle>
                                        <Badge className="bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100">
                                            <IconShieldCheck className="mr-1 h-4 w-4" />
                                            {Math.round(model.bias_card.overall_score * 100)}% Fairness Score
                                        </Badge>
                                    </div>
                                </CardHeader>
                                <CardContent>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {Object.entries(model.bias_card.metrics).map(([key, value]) => (
                                            <div key={key} className="p-4 border rounded-lg">
                                                <div className="text-sm font-medium text-muted-foreground capitalize">
                                                    {key.replace('_', ' ')}
                                                </div>
                                                <div className="text-2xl font-bold mt-1">
                                                    {value.toFixed(3)}
                                                </div>
                                                <div className="text-xs text-muted-foreground mt-1">
                                                    Lower is better
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </CardContent>
                            </Card>
                        </TabsContent>

                        <TabsContent value="performance">
                            <Card>
                                <CardHeader>
                                    <CardTitle>Performance Metrics</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                        {Object.entries(model.performance_metrics).map(([key, value]) => (
                                            <div key={key} className="flex justify-between items-center p-3 border-b">
                                                <span className="font-medium capitalize">{key.replace('_', ' ')}</span>
                                                <span className="font-mono">{value}</span>
                                            </div>
                                        ))}
                                    </div>
                                </CardContent>
                            </Card>
                        </TabsContent>

                        <TabsContent value="usage">
                            <Card>
                                <CardHeader>
                                    <CardTitle>How to Use</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <pre className="bg-muted p-4 rounded-lg overflow-x-auto">
                                        <code>{`from transformers import AutoModel, AutoTokenizer

# Load model and tokenizer
model_name = "${model.author}/${model.name.toLowerCase().replace(/\s+/g, '-')}"
model = AutoModel.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Run inference
inputs = tokenizer("Hello world", return_tensors="pt")
outputs = model(**inputs)
`}</code>
                                    </pre>
                                </CardContent>
                            </Card>
                        </TabsContent>
                    </Tabs>
                </div>

                {/* Sidebar */}
                <div className="space-y-6">
                    <Card>
                        <CardHeader>
                            <CardTitle>Model Details</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="flex justify-between">
                                <span className="text-muted-foreground">Framework</span>
                                <span className="font-medium flex items-center">
                                    <IconBrain className="mr-2 h-4 w-4" />
                                    {model.framework}
                                </span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-muted-foreground">Task</span>
                                <span className="font-medium flex items-center">
                                    <IconTag className="mr-2 h-4 w-4" />
                                    {model.task}
                                </span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-muted-foreground">Downloads</span>
                                <span className="font-medium flex items-center">
                                    <IconDownload className="mr-2 h-4 w-4" />
                                    {model.download_count}
                                </span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-muted-foreground">Rating</span>
                                <span className="font-medium flex items-center">
                                    <IconStar className="mr-2 h-4 w-4 text-yellow-500" />
                                    {averageRating} ({model.reviews.length})
                                </span>
                            </div>
                        </CardContent>
                    </Card>

                    <Card>
                        <CardHeader>
                            <CardTitle>Reviews</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            {model.reviews.length === 0 ? (
                                <p className="text-muted-foreground text-sm">No reviews yet.</p>
                            ) : (
                                model.reviews.map((review) => (
                                    <div key={review.review_id} className="border-b pb-4 last:border-0">
                                        <div className="flex justify-between items-center mb-2">
                                            <span className="font-medium text-sm">{review.user_id}</span>
                                            <div className="flex">
                                                {[...Array(5)].map((_, i) => (
                                                    <IconStar
                                                        key={i}
                                                        className={`h-3 w-3 ${i < review.rating ? 'text-yellow-500' : 'text-gray-300'}`}
                                                        fill={i < review.rating ? 'currentColor' : 'none'}
                                                    />
                                                ))}
                                            </div>
                                        </div>
                                        <p className="text-sm text-muted-foreground">{review.comment}</p>
                                    </div>
                                ))
                            )}
                            <Button variant="outline" className="w-full mt-2">Write a Review</Button>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}

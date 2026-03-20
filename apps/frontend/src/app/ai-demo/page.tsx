'use client'

import { useChat, fetchServerSentEvents } from '@tanstack/ai-react'
import { useState } from 'react'

export default function AiDemoPage() {
    const { messages, sendMessage, isLoading } = useChat({
        connection: fetchServerSentEvents('/api/chat'),
    })

    const [input, setInput] = useState('')

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        if (!input.trim()) return

        await sendMessage(input)
        setInput('')
    }

    return (
        <div className="flex flex-col h-[calc(100vh-theme(spacing.16))] max-w-2xl mx-auto p-4">
            <h1 className="text-2xl font-bold mb-4">TanStack AI Demo</h1>

            <div className="flex-1 overflow-y-auto space-y-4 mb-4 p-4 border rounded-lg bg-background">
                {messages.map((message, i) => (
                    <div
                        key={i}
                        className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'
                            }`}
                    >
                        <div
                            className={`max-w-[80%] rounded-lg p-3 ${message.role === 'user'
                                ? 'bg-primary text-primary-foreground'
                                : 'bg-muted'
                                }`}
                        >
                            <div className="font-semibold text-xs mb-1 opacity-70">
                                {message.role === 'user' ? 'You' : 'AI'}
                            </div>
                            {message.parts.map((part, i) => (
                                part.type === 'text' ? <span key={i}>{part.content}</span> : null
                            ))}
                        </div>
                    </div>
                ))}
                {isLoading && (
                    <div className="flex justify-start">
                        <div className="bg-muted max-w-[80%] rounded-lg p-3 animate-pulse">
                            Thinking...
                        </div>
                    </div>
                )}
            </div>

            <form onSubmit={handleSubmit} className="flex gap-2">
                <input
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Say something..."
                    className="flex-1 p-2 border rounded-md bg-background"
                />
                <button
                    type="submit"
                    disabled={isLoading || !input.trim()}
                    className="px-4 py-2 bg-primary text-primary-foreground rounded-md disabled:opacity-50"
                >
                    Send
                </button>
            </form>
        </div>
    )
}

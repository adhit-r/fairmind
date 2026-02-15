import { openai } from '@tanstack/ai-openai'
import { toolDefinition, chat, toStreamResponse } from '@tanstack/ai'
import { z } from 'zod'

export const POST = async (req: Request) => {
    const { messages } = await req.json()

    // Define a simple tool to demonstrate isomorphic capabilities
    const getWeather = toolDefinition({
        name: 'getWeather',
        description: 'Get the weather for a location',
        inputSchema: z.object({
            location: z.string().describe('The city and state, e.g. San Francisco, CA'),
        }),
        outputSchema: z.object({
            temperature: z.number(),
            condition: z.string(),
        }),
    })

    // Start the chat stream
    const result = await chat({
        adapter: openai(),
        model: 'gpt-4o',
        messages,
        tools: [
            getWeather.server(async ({ location }) => {
                // Mock data
                return {
                    temperature: 72,
                    condition: 'Sunny',
                    location,
                }
            }),
        ],
    })

    return toStreamResponse(result)
}

import { role, text, tour } from '../capture/tour'

export default tour({
  page: 'app/agents/ask',
  title: 'Ask a question about your AI estate',
  steps: [
    { goto: '/ask', say: 'Ask FairMind answers questions from your own systems and records.' },
    { point: text('Ask about your AI estate'), say: 'It uses the AI provider your organisation configured in Settings.' },
    { scroll: 300, say: 'Once a provider is on, you type a question or pick a suggestion, and the answer links to the systems it names.' },
  ],
})

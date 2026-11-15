import { role, text, tour } from '../capture/tour'

export default tour({
  page: 'app/records/auditor-packs',
  title: 'See how an auditor pack is built and shared',
  steps: [
    { goto: '/auditor-packs', say: 'Auditor packs are frozen snapshots of evidence and decisions, each with a hash.' },
    { click: role('button', 'Build a pack'), say: 'Build a pack by choosing a title, frameworks and systems.' },
    { point: text('Frameworks'), say: 'Build pack stays disabled until all three are filled.' },
    { click: role('button', 'Cancel'), say: 'We will not build one in the demo, so cancel.' },
    { click: role('button', 'How to verify a pack'), say: 'An auditor checks a downloaded pack offline with one command.' },
  ],
})

import { css, role, tour } from '../capture/tour'

export default tour({
  page: 'app/home/home',
  title: 'Read the whole estate on one board',
  steps: [
    { goto: '/dashboard', say: 'Home shows every registered AI system against every release check.' },
    { point: role('button', 'Check now'), say: 'The board is live. It re-reads the release gates every minute, and this button reads them now.' },
    { point: role('link', 'Open AI systems'), say: 'The header also links to the full list of AI systems.' },
    { click: css('main table tbody tr.row button.cell', 0), say: 'Click any cell to see what is behind it: the state, how it is known, and the evidence.' },
    { point: role('link', 'Open the system file'), say: 'From the drawer you can go straight to the system file.' },
  ],
})

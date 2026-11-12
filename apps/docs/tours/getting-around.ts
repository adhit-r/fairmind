import { role, tour } from '../capture/tour'

export default tour({
  page: 'app/getting-around',
  title: 'Find your way around FairMind',
  steps: [
    { goto: '/dashboard', say: 'FairMind opens on Home. Down the left edge, seven icons stand for the groups of pages.' },
    { click: role('link', 'Inventory', 0), say: 'Choosing a group opens its first page and lists the rest in the panel beside it. Inventory holds your AI systems and what discovery found.' },
    { click: role('link', 'Testing', 0), say: 'Testing holds the evaluations you choose, the runs, and agent audits.' },
    { point: role('button', 'Search or ask'), say: 'Search reaches every page and every system. Command K opens it from anywhere.' },
    { click: role('button', 'Search or ask'), say: 'Type a system or a page name and pick it to go straight there.' },
    { press: 'Escape', point: role('button', 'Search or ask'), say: 'In the demo, everything can be opened and nothing can be changed.' },
  ],
})

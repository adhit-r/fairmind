import { role, text, tour } from '../capture/tour'

export default tour({
  page: 'app/agents/autopilot',
  title: 'Set how much room agents get on each system',
  steps: [
    { goto: '/autopilot', say: 'Autopilot sets how much agents may do for each AI system.' },
    { point: role('region', 'Estate summary'), say: 'The summary counts steps done this week and steps that need a person.' },
    { point: role('region', 'Agent runs'), say: 'Recent and active agent runs are listed here. Select one to open it in Runs.' },
    { scroll: 500, say: 'By system, each row has a mode: Off, Ask first or Run.' },
  ],
})

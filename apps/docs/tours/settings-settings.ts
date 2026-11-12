import { role, text, tour } from '../capture/tour'

export default tour({
  page: 'app/settings/settings',
  title: 'Find the organisation, people and API key settings',
  steps: [
    { goto: '/settings', say: 'Settings has a section list on the left. Organisation comes first.' },
    { click: text('AI provider'), say: 'AI provider holds the model key used by Ask FairMind and agent steps.' },
    { click: text('Team and roles'), say: 'Team and roles lists members. Owners and admins can invite people and change roles.' },
    { click: text('Developers'), say: 'Developers is where you create API keys for CI and the CLI.' },
    { click: text('Audit log'), say: 'The audit log lists what happened in the organisation, page by page.' },
  ],
})

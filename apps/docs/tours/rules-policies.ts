import { role, tour } from '../capture/tour'

export default tour({
  page: 'app/rules/policies',
  title: 'Review policies and their alerts',
  steps: [
    { goto: '/policies', say: 'Policies shows your organisation policies, who has acknowledged them and whether their rules hold.' },
    { click: role('button', /^With open alerts/), say: 'Filter to the policies with an open alert.' },
    { click: role('button', /^All /), say: 'Back to all policies.' },
    { point: role('button', 'Enforce rules now'), say: 'Enforce rules now checks every published rule against every system.' },
    { click: role('button', 'Draft a policy with the agent', 0), say: 'The agent can draft a policy from a short brief. It saves a draft for people to review.' },
    { point: role('button', 'Draft policy'), say: 'We stop before drafting, because this demo is read-only.' },
  ],
})

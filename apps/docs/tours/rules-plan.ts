import { role, tour } from '../capture/tour'

export default tour({
  page: 'app/rules/plan',
  title: 'Set up the governance plan',
  steps: [
    { goto: '/plan', say: 'The plan turns your frameworks into controls and tracks each one from to do to proven.' },
    { point: role('heading', 'Set up your governance plan'), say: 'Until there is a plan, this page asks about your organisation and how it uses AI.' },
    { point: role('textbox', 'Tell me about your organisation and how it uses AI.'), say: 'Describe it in your own words. FairMind proposes the frameworks and controls, and a person accepts the plan. The demo stops here, because it is read-only.' },
  ],
})

import { css, role, tour } from '../capture/tour'

export default tour({
  page: 'app/release/environment',
  title: 'See the environmental assessment for each system',
  steps: [
    { goto: '/environment', say: 'Environment scores the energy and carbon use of each AI system into an impact tier.' },
    { point: css('.fm-env-counts'), say: 'The counts show how many systems are proven, estimated, out of date, failing or not assessed.' },
    { point: css('.fm-env-row', 0), say: 'Each row shows the latest tier, its confidence, and whether it blocks approval.' },
    { click: role('button', 'Start an assessment', 0), say: 'Start an assessment opens a form for that system. We will not save it here.' },
    { scroll: 700, say: 'Below the list, a table explains how impact tiers are set. The thresholds are provisional.' },
  ],
})

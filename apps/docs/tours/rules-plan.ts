import { css, role, tour } from '../capture/tour'

export default tour({
  page: 'app/rules/plan',
  title: 'Work the governance plan',
  steps: [
    { goto: '/plan', say: 'The plan turns your frameworks into controls and tracks each one from to do to proven.' },
    { point: role('button', 'Refresh'), say: 'Refresh reads the plan again.' },
    { click: css('.pl-card', 0), say: 'Open a task to see its owner, systems and the requirements it closes.' },
    { point: role('button', 'Save note'), say: 'Assign an owner and leave a note for whoever picks it up.' },
  ],
})

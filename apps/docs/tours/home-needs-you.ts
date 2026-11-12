import { role, text, tour } from '../capture/tour'

export default tour({
  page: 'app/home/needs-you',
  title: 'Find what waits on you',
  steps: [
    { goto: '/needs-you', say: 'Needs you lists everything that waits on a person, in one place.' },
    { point: text(/^All \d+/), say: 'The filter shows how many items there are of each type.' },
    { click: text(/^Policy approval \d+/), say: 'Pick a type to narrow the list.' },
    { click: text(/^All \d+/), say: 'Go back to all of them.' },
    { point: role('button', /^(Review|Decide|Acknowledge|Accept lower tier)$/, 0), say: 'Each row has one button. What it does depends on the type of item.' },
  ],
})

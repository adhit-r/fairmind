import { role, text, tour } from '../capture/tour'

export default tour({
  page: 'app/home/needs-you',
  title: 'Find what waits on you',
  steps: [
    { goto: '/needs-you', say: 'Needs you lists everything that waits on a person, in one place.' },
    { point: text(/^All \d+/), say: 'The filter shows how many items there are of each type.' },
    { click: text(/^Release approval \d+/), say: 'Pick a type to narrow the list. Here, release decisions waiting for a reviewer.' },
    { point: text(/^Release decision for/), say: 'Each row says what waits and who asked, with one action beside it.' },
    { click: text(/^All \d+/), say: 'Go back to everything. The count in the menu matches this list.' },
  ],
})

import { role, tour } from '../capture/tour'

export default tour({
  page: 'app/rules/frameworks',
  title: 'Check coverage of a framework',
  steps: [
    { goto: '/frameworks', say: 'Frameworks lists the rules you answer to and how much the installed packs cover.' },
    { click: role('button', 'Show coverage', 0), say: 'Show coverage lays out every requirement against every system.' },
    { scroll: 500, say: 'Systems are columns. A mark in a cell says whether that requirement is proven, attested, estimated, out of date or failing.' },
    { point: role('link', 'Export an auditor pack'), say: 'When the grid is ready, export an auditor pack for the framework.' },
  ],
})

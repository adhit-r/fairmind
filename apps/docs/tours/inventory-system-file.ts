import { css, role, tour } from '../capture/tour'

export default tour({
  page: 'app/inventory/system-file',
  title: 'Read a system file and its release gate',
  steps: [
    { goto: '/systems', say: 'Open a registered system from the AI systems list.' },
    { click: css('.sys-col.registered .sys-item, .sys-col.approved .sys-item', 0), say: 'Select a registered system.' },
    { click: role('link', 'Open the system file'), say: 'Open its file.' },
    { point: role('button', 'How the verdict was reached'), say: 'The release gate scores each check. This explains how the verdict was reached.' },
    { click: role('button', 'Requirements'), say: 'Requirements shows the clauses of each confirmed framework for this system.' },
    { click: role('button', 'Record'), say: 'Record holds the sealed decisions and approval history.' },
  ],
})

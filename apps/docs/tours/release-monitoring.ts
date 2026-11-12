import { css, role, text, tour } from '../capture/tour'

export default tour({
  page: 'app/release/monitoring',
  title: 'See which systems are drifting or unwatched',
  steps: [
    { goto: '/monitoring', say: 'Monitoring shows whether each registered system still behaves as it did at release.' },
    { point: css('.fm-mon-counts'), say: 'The counts summarise the estate: proven, estimated, out of date, drifting and never watched.' },
    { point: css('.fm-mon-row', 0), say: 'Each system shows its latest snapshot, its drift scores, and the cadence it is expected to follow.' },
    { point: role('button', 'Upload a snapshot', 0), say: 'Snapshots are uploaded from the system file. FairMind does not pull data from your systems.' },
    { point: text('Alerts'), say: 'Open policy alerts and findings from the monitoring watch collect in this rail.' },
  ],
})

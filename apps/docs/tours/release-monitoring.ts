import { role, tour } from '../capture/tour'

export default tour({
  page: 'app/release/monitoring',
  title: 'See which systems are drifting or unwatched',
  steps: [
    { goto: '/monitoring', say: 'Monitoring shows whether each registered system still behaves as it did at release.' },
    { point: role('heading', 'Systems'), say: 'Each system shows its latest snapshot, its drift scores, and the cadence it is held to.' },
    { point: role('heading', 'Alerts'), say: 'Open policy alerts and findings from the monitoring watch collect here. Snapshots are uploaded from the system file; FairMind does not pull data from your systems.' },
  ],
})

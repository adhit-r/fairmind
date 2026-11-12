import { role, tour } from '../capture/tour'

export default tour({
  page: 'app/inventory/discovery',
  title: 'Connect a source to find unregistered AI',
  steps: [
    { goto: '/discovery', say: 'Discovery reads your MLflow, GitHub and Hugging Face sources and lists AI systems you have not registered.' },
    { click: role('button', 'Connect a source', 0), say: 'Connect a source to start.' },
    { click: role('button', 'GitHub'), say: 'Choose the kind of source. The fields change to match it.' },
    { point: role('button', 'Add connector'), say: 'Adding the connector saves it. This demo is read-only, so we stop here.' },
  ],
})

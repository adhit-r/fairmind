import { css, role, tour } from '../capture/tour'

export default tour({
  page: 'app/inventory/systems',
  title: 'Find a system and open it',
  steps: [
    { goto: '/systems', say: 'AI systems lists everything found and registered, by where it came from and how far along it is.' },
    { point: css('.sys-head', 1), say: 'The columns run from found, to registered, to approved and watched.' },
    { point: role('searchbox', 'Search systems'), say: 'Search by name, source or kind.' },
    { click: css('.sys-item', 0), say: 'Click an item to open its details.' },
    { point: role('button', 'Register it'), say: 'A found system can be registered from here. A registered one offers Open the system file instead.' },
    { point: role('link', 'Find unregistered AI'), say: 'To find more systems, use discovery.' },
  ],
})

import { css, text, tour } from '../capture/tour'

export default tour({
  page: 'app/testing/evaluations',
  title: 'Find a runnable check and read its results',
  steps: [
    { goto: '/evaluations', say: 'The catalogue lists every evaluation, grouped by pillar. The counts under the title say how many can run today.' },
    { point: text('Runnable'), say: 'The list starts on runnable evaluations only. Those are the ones with an engine behind them.' },
    { click: text('Not built yet'), say: 'Switch the engine filter to see the entries that are listed but have no engine yet.' },
    { click: css('.fm-ev-name button', 0), say: 'Click an evaluation name to open its panel with the metric, threshold and results by system.' },
    { point: text('Results by system'), say: 'Each system shows its latest result and the evidence it came from.' },
  ],
})

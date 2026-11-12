import { Callout } from 'fumadocs-ui/components/callout'

/**
 * Where an app page is and who can use it. Every member of an organisation can open every page; what a person may
 * change is checked by the server against their role's permissions (Settings › People).
 */
export function Access({ where, address, change }: { where: string; address: string; change?: string }) {
  return (
    <Callout title={`${where} · ${address}`}>
      Every member of the organisation can open it.
      {change ? <> Changing things here needs <strong>{change}</strong>.</> : null}
      {' '}In the <a href="https://app.fairmind.xyz/login">demo</a> it is read-only.
    </Callout>
  )
}

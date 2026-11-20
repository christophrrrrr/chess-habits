import { href } from '../routes'

/** "How is this measured?" link from a card to its section of the methods page. */
export function MethodsLink({ section }: { section: string }) {
  return (
    <a className="methods-link small" href={href({ page: 'methods', section })}>
      How is this measured?
    </a>
  )
}

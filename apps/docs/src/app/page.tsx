import { redirect } from 'next/navigation';

// The docs are the site: the first page explains FairMind and where to start.
export default function Home() {
  redirect('/docs');
}

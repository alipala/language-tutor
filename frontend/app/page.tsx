'use client';

import dynamic from 'next/dynamic';

// Import the component with no SSR
const ClientHome = dynamic(() => import('./client-home'), {
  ssr: false
});

// Export the main component
export default function Home() {
  return <ClientHome />;
}




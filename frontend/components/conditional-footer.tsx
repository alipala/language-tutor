'use client';

import { usePathname } from 'next/navigation';
import Footer from './footer';

const ConditionalFooter: React.FC = () => {
  const pathname = usePathname();
  
  // Hide footer on speech page and other full-screen pages
  const hideFooterPaths = [
    '/speech',
    '/assessment/speaking',
    '/loading-modal-demo'
  ];
  
  const shouldHideFooter = hideFooterPaths.some(path => pathname?.startsWith(path));
  
  if (shouldHideFooter) {
    return null;
  }
  
  return <Footer />;
};

export default ConditionalFooter;

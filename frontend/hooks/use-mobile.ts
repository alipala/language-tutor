'use client';

import { useState, useEffect } from 'react';

export function useMobile() {
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const checkMobile = () => {
      // Check user agent for mobile devices
      const userAgent = navigator.userAgent;
      const mobileRegex = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i;
      
      // Also check screen width as a fallback
      const screenWidth = window.innerWidth;
      const isMobileUserAgent = mobileRegex.test(userAgent);
      const isMobileScreen = screenWidth < 768; // md breakpoint in Tailwind
      
      setIsMobile(isMobileUserAgent || isMobileScreen);
    };

    // Check on mount
    checkMobile();

    // Listen for resize events
    window.addEventListener('resize', checkMobile);
    
    return () => {
      window.removeEventListener('resize', checkMobile);
    };
  }, []);

  return isMobile;
}

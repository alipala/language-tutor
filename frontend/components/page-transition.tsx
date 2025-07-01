'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { usePathname } from 'next/navigation';
import { ReactNode } from 'react';

interface PageTransitionProps {
  children: ReactNode;
}

// Define transition variants for different page types
const getPageVariants = (pathname: string) => {
  // Auth pages get a gentle fade with slight scale
  if (pathname.includes('/auth/')) {
    return {
      initial: { 
        opacity: 0, 
        scale: 0.98,
        y: 10
      },
      animate: { 
        opacity: 1, 
        scale: 1,
        y: 0,
        transition: {
          duration: 0.4,
          ease: [0.25, 0.46, 0.45, 0.94] // Custom easing for smooth feel
        }
      },
      exit: { 
        opacity: 0, 
        scale: 1.02,
        y: -10,
        transition: {
          duration: 0.3,
          ease: [0.25, 0.46, 0.45, 0.94]
        }
      }
    };
  }

  // Flow pages get a slide transition
  if (pathname.includes('/flow') || pathname.includes('/speech')) {
    return {
      initial: { 
        opacity: 0, 
        x: 20,
        scale: 0.99
      },
      animate: { 
        opacity: 1, 
        x: 0,
        scale: 1,
        transition: {
          duration: 0.5,
          ease: [0.25, 0.46, 0.45, 0.94]
        }
      },
      exit: { 
        opacity: 0, 
        x: -20,
        scale: 1.01,
        transition: {
          duration: 0.3,
          ease: [0.25, 0.46, 0.45, 0.94]
        }
      }
    };
  }

  // Default pages get a simple fade
  return {
    initial: { 
      opacity: 0,
      y: 8
    },
    animate: { 
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.4,
        ease: [0.25, 0.46, 0.45, 0.94]
      }
    },
    exit: { 
      opacity: 0,
      y: -8,
      transition: {
        duration: 0.3,
        ease: [0.25, 0.46, 0.45, 0.94]
      }
    }
  };
};

export default function PageTransition({ children }: PageTransitionProps) {
  const pathname = usePathname();
  const variants = getPageVariants(pathname);

  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div
        key={pathname}
        initial="initial"
        animate="animate"
        exit="exit"
        variants={variants}
        className="w-full"
      >
        {children}
      </motion.div>
    </AnimatePresence>
  );
}

// Loading transition component for immediate feedback
export function PageLoadingTransition() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 bg-white/80 backdrop-blur-sm flex items-center justify-center"
    >
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.1 }}
        className="flex flex-col items-center"
      >
        <div className="relative w-12 h-12 mb-4">
          <motion.div
            className="absolute inset-0 rounded-full border-4 border-[#4ECFBF]/20"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.3 }}
          />
          <motion.div
            className="absolute inset-0 rounded-full border-4 border-transparent border-t-[#4ECFBF]"
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
          />
        </div>
        <motion.p
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="text-gray-600 text-sm"
        >
          Loading...
        </motion.p>
      </motion.div>
    </motion.div>
  );
}

// Navigation transition hook for programmatic navigation
export function usePageTransition() {
  const pathname = usePathname();

  const navigateWithTransition = (href: string, router: any) => {
    // Add a brief loading state for immediate feedback
    const loadingElement = document.createElement('div');
    loadingElement.className = 'fixed inset-0 z-50 bg-white/60 backdrop-blur-sm pointer-events-none transition-opacity duration-200';
    loadingElement.style.opacity = '0';
    document.body.appendChild(loadingElement);

    // Fade in loading overlay
    requestAnimationFrame(() => {
      loadingElement.style.opacity = '1';
    });

    // Navigate after brief delay for smooth transition
    setTimeout(() => {
      router.push(href);
      
      // Clean up loading element after navigation
      setTimeout(() => {
        if (loadingElement.parentNode) {
          loadingElement.parentNode.removeChild(loadingElement);
        }
      }, 100);
    }, 150);
  };

  return { navigateWithTransition, currentPath: pathname };
}

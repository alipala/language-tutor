/**
 * Navigation module index
 * 
 * Exports all navigation-related components and utilities
 * 
 * PERFORMANCE OPTIMIZED: Now exports Next.js-optimized navigation service
 */

// Export the optimized Next.js navigation service
export * from './navigation-service-nextjs';
export * from './navigation-types';
export * from './navigation-context';

// Keep old service available for backward compatibility if needed
export { navigationService as legacyNavigationService } from './navigation-service';

'use client';

import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import Script from 'next/script'
import './globals.css'
import AuthProviderWrapper from '@/components/auth-provider-wrapper'
import { useEffect } from 'react'

const inter = Inter({ 
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
})

export const metadata: Metadata = {
  title: 'Taco - Your Smart Language Coach',
  description: 'A modern, responsive web UI for voice and text input',
}

// Custom error logger for Railway deployment debugging
function logError(error: any, info: any) {
  console.error('Railway Deployment Error:', error);
  console.error('Component Stack:', info?.componentStack);
  
  // Add visible error display for debugging
  if (typeof document !== 'undefined') {
    const errorDiv = document.createElement('div');
    errorDiv.style.position = 'fixed';
    errorDiv.style.top = '0';
    errorDiv.style.left = '0';
    errorDiv.style.width = '100%';
    errorDiv.style.padding = '20px';
    errorDiv.style.backgroundColor = 'red';
    errorDiv.style.color = 'white';
    errorDiv.style.zIndex = '9999';
    errorDiv.innerText = `Railway Error: ${error?.message || 'Unknown error'}`;
    document.body?.appendChild(errorDiv);
  }
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  // Add debugging for Railway deployment
  useEffect(() => {
    console.log('Railway Debug: Layout component mounted');
    
    // Log environment info
    console.log('Railway Debug: Window location', 
      typeof window !== 'undefined' ? window.location.href : 'No window');
    
    // Add global error handler
    const originalOnError = window.onerror;
    window.onerror = (message, source, lineno, colno, error) => {
      console.error('Railway Global Error:', { message, source, lineno, colno, error });
      
      // Create visible error message
      const errorDiv = document.createElement('div');
      errorDiv.style.position = 'fixed';
      errorDiv.style.top = '0';
      errorDiv.style.left = '0';
      errorDiv.style.width = '100%';
      errorDiv.style.padding = '20px';
      errorDiv.style.backgroundColor = 'red';
      errorDiv.style.color = 'white';
      errorDiv.style.zIndex = '9999';
      errorDiv.innerText = `Railway Error: ${message}`;
      document.body?.appendChild(errorDiv);
      
      // Call original handler if exists
      if (originalOnError) {
        return originalOnError(message, source, lineno, colno, error);
      }
      return false;
    };
    
    return () => {
      window.onerror = originalOnError;
    };
  }, []);
  
  return (
    <html lang="en" className={inter.variable}>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="description" content="Voice input language learning application" />
        <meta name="theme-color" content="#f8f9fb" />
        <Script
          src="https://accounts.google.com/gsi/client"
          strategy="afterInteractive"
        />
        {/* Add debugging script */}
        <Script id="railway-debug" strategy="beforeInteractive">
          {`
            console.log('Railway Debug: Initial script loaded');
            window.RAILWAY_DEBUG = true;
            window.onerror = function(message, source, lineno, colno, error) {
              console.error('Early Railway Error:', { message, source, lineno, colno });
              return false;
            };
          `}
        </Script>
      </head>
      <body className={`${inter.className} font-sans antialiased`}>
        <div id="railway-debug-container" style={{
          position: 'fixed',
          bottom: '0',
          left: '0',
          width: '100%',
          padding: '10px',
          backgroundColor: 'rgba(0,0,0,0.8)',
          color: 'white',
          zIndex: 9999,
          fontSize: '12px',
          display: 'none'
        }}>
          Railway Debug Mode
        </div>
        <AuthProviderWrapper>
          <div className="gradient-background min-h-screen w-full">
            <main id="main-content" tabIndex={-1} className="outline-none">
              {children}
            </main>
          </div>
        </AuthProviderWrapper>
      </body>
    </html>
  )
}

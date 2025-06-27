import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import Script from 'next/script'
import './globals.css'
import '../styles/carousel-animations.css'
import AuthProviderWrapper from '@/components/auth-provider-wrapper'
import { NavigationProvider } from '@/lib/navigation'
import NavBar from '@/components/nav-bar'
import ConditionalFooter from '@/components/conditional-footer'

const inter = Inter({ 
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
})

export const metadata: Metadata = {
  title: 'My Taco - AI Language Coach',
  description: 'Learn languages through conversation with your personal AI coach',
  icons: {
    icon: [
      { url: '/logos/my-taco-favicon.svg', type: 'image/svg+xml' },
      { url: '/favicon.ico', sizes: '32x32' }
    ],
    apple: '/apple-touch-icon.png'
  }
}



export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={inter.variable}>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="description" content="Voice input language learning application" />
        <meta name="theme-color" content="#f8f9fb" />
        
        {/* Optimized font loading for better LCP */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          rel="preload"
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"
          as="style"
          id="font-preload"
        />
        <script dangerouslySetInnerHTML={{
          __html: `
            (function() {
              var link = document.getElementById('font-preload');
              if (link) {
                // Immediately convert to stylesheet to avoid preload warning
                link.rel = 'stylesheet';
                link.onload = null;
              }
            })();
          `
        }} />
        <noscript>
          <link
            rel="stylesheet"
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"
          />
        </noscript>
        
        {/* Enhanced resource hints for LCP optimization */}
        <link rel="dns-prefetch" href="//fonts.googleapis.com" />
        <link rel="dns-prefetch" href="//fonts.gstatic.com" />
        <link rel="dns-prefetch" href="//accounts.google.com" />
        <link rel="preconnect" href="https://accounts.google.com" />
        
        {/* Critical CSS for LCP optimization - targeting p.text-gray-600 elements */}
        <style dangerouslySetInnerHTML={{
          __html: `
            /* Critical CSS for LCP element optimization - Navigation Bar */
            .w-full { width: 100%; }
            .backdrop-blur-sm { backdrop-filter: blur(4px); -webkit-backdrop-filter: blur(4px); }
            .transition-all { transition-property: all; transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1); }
            .duration-500 { transition-duration: 500ms; }
            .fixed { position: fixed; }
            .top-0 { top: 0px; }
            .left-0 { left: 0px; }
            .right-0 { right: 0px; }
            .z-50 { z-index: 50; }
            .py-1 { padding-top: 0.25rem; padding-bottom: 0.25rem; }
            .py-2 { padding-top: 0.5rem; padding-bottom: 0.5rem; }
            
            /* Navigation bar background colors */
            .bg-\\[\\#4ECFBF\\]\\/90 { background-color: rgba(78, 207, 191, 0.9); }
            .bg-\\[\\#4ECFBF\\]\\/95 { background-color: rgba(78, 207, 191, 0.95); }
            .shadow-lg { box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05); }
            
            /* Text styling for navbar */
            .text-gray-600 { color: rgb(75 85 99); }
            .text-xs { font-size: 0.75rem; line-height: 1rem; }
            .text-sm { font-size: 0.875rem; line-height: 1.25rem; }
            .text-lg { font-size: 1.125rem; line-height: 1.75rem; }
            .font-medium { font-weight: 500; }
            
            /* Prevent layout shift for common elements */
            .app-background { background: white; min-height: 100vh; }
            .min-h-screen { min-height: 100vh; }
            
            /* Container and flex utilities */
            .container { width: 100%; margin-left: auto; margin-right: auto; }
            .mx-auto { margin-left: auto; margin-right: auto; }
            .px-4 { padding-left: 1rem; padding-right: 1rem; }
            .flex { display: flex; }
            .justify-between { justify-content: space-between; }
            .items-center { align-items: center; }
            
            /* Font display optimization */
            @font-face {
              font-family: 'Inter';
              font-style: normal;
              font-weight: 400 800;
              font-display: swap;
              src: url('https://fonts.gstatic.com/s/inter/v12/UcCO3FwrK3iLTeHuS_fvQtMwCp50KnMw2boKoduKmMEVuLyfAZ9hiA.woff2') format('woff2');
              unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
            }
            
            /* Optimize text rendering for LCP */
            body, p, span, div {
              text-rendering: optimizeSpeed;
              -webkit-font-smoothing: antialiased;
              -moz-osx-font-smoothing: grayscale;
            }
          `
        }} />
        
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
              // Create visible error message if body exists
              if (document.body) {
                const errorDiv = document.createElement('div');
                errorDiv.style.position = 'fixed';
                errorDiv.style.top = '0';
                errorDiv.style.left = '0';
                errorDiv.style.width = '100%';
                errorDiv.style.padding = '20px';
                errorDiv.style.backgroundColor = 'red';
                errorDiv.style.color = 'white';
                errorDiv.style.zIndex = '9999';
                errorDiv.innerText = 'Railway Error: ' + message;
                document.body.appendChild(errorDiv);
              }
              return false;
            };
          `}
        </Script>
      </head>
      <body className={`${inter.className} font-sans antialiased overflow-x-hidden`}>
        <NavigationProvider>
          <AuthProviderWrapper>
            <div className="app-background min-h-screen w-full bg-white">
              <NavBar />
              <main id="main-content" tabIndex={-1} className="outline-none">
                {children}
              </main>
              <ConditionalFooter />
            </div>
          </AuthProviderWrapper>
        </NavigationProvider>
      </body>
    </html>
  );
}

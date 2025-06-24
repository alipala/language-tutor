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
        
        {/* Preload critical fonts for better LCP */}
        <link
          rel="preload"
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"
          as="style"
        />
        <noscript>
          <link
            rel="stylesheet"
            href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"
          />
        </noscript>
        
        {/* Preconnect to external domains */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link rel="preconnect" href="https://accounts.google.com" />
        
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

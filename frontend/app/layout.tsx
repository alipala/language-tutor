import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import Script from 'next/script'
import './globals.css'
import AuthProviderWrapper from '@/components/auth-provider-wrapper'
import { NavigationProvider } from '@/lib/navigation'

const inter = Inter({ 
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
})

export const metadata: Metadata = {
  title: 'Taco - Your Smart Language Coach',
  description: 'A modern, responsive web UI for voice and text input',
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
            <div className="app-background min-h-screen w-full bg-[var(--turquoise)]">
              <main id="main-content" tabIndex={-1} className="outline-none">
                {children}
              </main>
            </div>
          </AuthProviderWrapper>
        </NavigationProvider>
      </body>
    </html>
  );
}

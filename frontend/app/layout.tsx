import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import Script from 'next/script'
import './globals.css'
import AuthProviderWrapper from '@/components/auth-provider-wrapper'

const inter = Inter({ 
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter',
})

export const metadata: Metadata = {
  title: 'Voice Input UI',
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
      </head>
      <body className={`${inter.className} font-sans antialiased`}>
        <AuthProviderWrapper>
          <main id="main-content" tabIndex={-1} className="outline-none">
            {children}
          </main>
        </AuthProviderWrapper>
      </body>
    </html>
  )
}

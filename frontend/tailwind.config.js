/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      animation: {
        "fade-in": "fadeIn 0.5s ease-out forwards",
        "pulse": "pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "slideDown": "slideDown 0.3s ease-out forwards",
        "slide-in-top": "slideInTop 0.3s ease-out forwards",
        "slide-out-top": "slideOutTop 0.3s ease-out forwards",
        "flash-lightning": "flash-lightning 0.8s ease-in-out",
        "pulse-glow": "pulse-glow 2s ease-in-out infinite",
        "darken-flash": "darken-flash 1s ease-in-out",
        "ready-bounce": "ready-bounce 1s ease-in-out",
        "shimmer": "shimmer 1.5s infinite",
        "notification-pulse": "notification-pulse 1.5s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: 0 },
          "100%": { opacity: 1 },
        },
        pulse: {
          "0%, 100%": { opacity: 0.6 },
          "50%": { opacity: 0.3 },
        },
        slideInTop: {
          "0%": { transform: "translate(-50%, -100%)", opacity: 0 },
          "100%": { transform: "translate(-50%, 0)", opacity: 1 },
        },
        slideOutTop: {
          "0%": { transform: "translate(-50%, 0)", opacity: 1 },
          "100%": { transform: "translate(-50%, -100%)", opacity: 0 },
        },
        "flash-lightning": {
          "0%": { boxShadow: "0 0 5px rgba(255, 255, 255, 0.5)", transform: "scale(1)" },
          "25%": { boxShadow: "0 0 20px rgba(255, 255, 0, 0.8), 0 0 30px rgba(255, 255, 0, 0.6)", transform: "scale(1.05)" },
          "50%": { boxShadow: "0 0 40px rgba(255, 255, 0, 1), 0 0 60px rgba(255, 255, 0, 0.8)", transform: "scale(1.1)" },
          "75%": { boxShadow: "0 0 20px rgba(255, 255, 0, 0.8), 0 0 30px rgba(255, 255, 0, 0.6)", transform: "scale(1.05)" },
          "100%": { boxShadow: "0 0 5px rgba(255, 255, 255, 0.5)", transform: "scale(1)" },
        },
        "pulse-glow": {
          "0%": { boxShadow: "0 0 10px rgba(59, 130, 246, 0.5)" },
          "50%": { boxShadow: "0 0 25px rgba(59, 130, 246, 0.8), 0 0 35px rgba(59, 130, 246, 0.6)" },
          "100%": { boxShadow: "0 0 10px rgba(59, 130, 246, 0.5)" },
        },
        "ready-bounce": {
          "0%, 20%, 50%, 80%, 100%": { transform: "translateY(0)" },
          "40%": { transform: "translateY(-3px)" },
          "60%": { transform: "translateY(-1px)" },
        },
        "shimmer": {
          "0%": { backgroundPosition: "-200px 0" },
          "100%": { backgroundPosition: "calc(200px + 100%) 0" },
        },
        "notification-pulse": {
          "0%": { transform: "scale(1)", opacity: "1" },
          "50%": { transform: "scale(1.2)", opacity: "0.7" },
          "100%": { transform: "scale(1)", opacity: "1" },
        },
      },
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: 0 },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: 0 },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}

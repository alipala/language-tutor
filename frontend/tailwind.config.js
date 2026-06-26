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
      fontFamily: {
        nunito: ['var(--font-nunito)', 'Nunito', 'ui-rounded', 'system-ui', 'sans-serif'],
        sans: ['var(--font-nunito)', 'ui-rounded', 'system-ui', 'sans-serif'],
      },
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
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
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
        "accordion-down": {
          from: { height: 0 },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: 0 },
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

        /* ── Design tokens (single source of truth, defined in globals.css) ── */
        bg: "rgb(var(--bg-base) / <alpha-value>)",
        surface: {
          0: "rgb(var(--surface-0) / <alpha-value>)",
          1: "rgb(var(--surface-1) / <alpha-value>)",
          2: "rgb(var(--surface-2) / <alpha-value>)",
          3: "rgb(var(--surface-3) / <alpha-value>)",
          sunken: "rgb(var(--surface-sunken) / <alpha-value>)",
        },
        brand: {
          DEFAULT: "rgb(var(--brand) / <alpha-value>)",
          bright: "rgb(var(--brand-bright) / <alpha-value>)",
          deep: "rgb(var(--brand-deep) / <alpha-value>)",
          ink: "rgb(var(--brand-ink) / <alpha-value>)",
        },
        ink: {
          strong: "rgb(var(--ink-strong) / <alpha-value>)",
          DEFAULT: "rgb(var(--ink) / <alpha-value>)",
          muted: "rgb(var(--ink-muted) / <alpha-value>)",
          faint: "rgb(var(--ink-faint) / <alpha-value>)",
        },
        cat: {
          dna: "rgb(var(--cat-dna) / <alpha-value>)",
          missions: "rgb(var(--cat-missions) / <alpha-value>)",
          challenge: "rgb(var(--cat-challenge) / <alpha-value>)",
          hearts: "rgb(var(--cat-hearts) / <alpha-value>)",
          news: "rgb(var(--cat-news) / <alpha-value>)",
          story: "rgb(var(--cat-story) / <alpha-value>)",
        },
        success: "rgb(var(--success) / <alpha-value>)",
        warning: "rgb(var(--warning) / <alpha-value>)",
        danger: "rgb(var(--danger) / <alpha-value>)",
        info: "rgb(var(--info) / <alpha-value>)",
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
        card: "var(--r-lg)",
      },
      boxShadow: {
        e1: "var(--shadow-1)",
        e2: "var(--shadow-2)",
        e3: "var(--shadow-3)",
        glow: "var(--glow-brand)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'brand-primary': '#0052D9', // Main Brand Color
        'brand-gradient-start': '#0052D9',
        'brand-gradient-end': '#0052FF',
        'brand-action': '#FF3355', // Key Action Color
        'figma-bg': '#F9FAFB',
        'figma-card': '#FFFFFF',
        'figma-text-primary': '#1F2937',
        'figma-text-secondary': '#6B7280',
        'figma-border': '#E5E7EB',
        'figma-hover': '#F3F4F6',
        'figma-gray': '#E8E8E8',
        'figma-notation': '#858B9B',
        'figma-line': '#E5E6EB',
        'figma-disable': '#BCC1CD',
        'figma-heading': '#2A2F3C',
        'figma-subhead': '#495363',
        'figma-avatar-bg': '#E6EFFF',
      },
      fontFamily: {
        sans: [
          '"PingFang SC"',
          '"SF Pro SC"',
          '"SF Pro Display"',
          '"SF Pro Text"',
          '"SF Pro Icons"',
          '"Helvetica Neue"',
          'Helvetica',
          'Arial',
          'sans-serif'
        ],
        din: ['"DIN Alternate"', 'DIN', 'sans-serif'],
      },
      fontSize: {
        // 整体调大字号，解决在 Mac 上显示过小的问题
        xs: ['0.8125rem', { lineHeight: '1.125rem' }], // 13px
        sm: ['0.9375rem', { lineHeight: '1.375rem' }], // 15px
        base: ['1rem', { lineHeight: '1.5rem' }],      // 16px
        lg: ['1.125rem', { lineHeight: '1.75rem' }],   // 18px
        xl: ['1.25rem', { lineHeight: '1.75rem' }],    // 20px
      },
    },
  },
  plugins: [],
}

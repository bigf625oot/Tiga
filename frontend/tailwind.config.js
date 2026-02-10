/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'figma-bg': '#F7F7F7',
        'figma-gray': '#E8E8E8',
        'figma-text': '#171717',
        'figma-notation': '#858B9B',
        'figma-line': '#E5E6EB',
        'figma-disable': '#BCC1CD',
        'figma-heading': '#2A2F3C',
        'figma-subhead': '#495363',
        'figma-border': '#F2F3F5',
        'figma-hover': '#F0F0F0',
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

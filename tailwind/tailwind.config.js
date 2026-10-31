/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    '../mysite/templates/**/*.html',
    '../*/templates/**/*.html',
    '../mysite/static/comments/*.js',
  ],
  theme: {
    fontSize: {
      xs: '.75rem', sm: '.875rem', tiny: '.875rem', base: '1rem', lg: '1.125rem', xl: '1.25rem',
      '2xl': '1.5rem', '3xl': '1.875rem', '4xl': '2.25rem', '5xl': '3rem', '6xl': '4rem',
      '7xl': '5rem', '8xl': '8rem', '9xl': '10rem', '10xl': '12rem',
    },
    extend: {
      boxShadow: { 'inner-3xl': 'inset 0 15px 30px 0 rgba(0, 0, 0, 0.3)' },
      colors: {
        brightRed: 'hsl(12, 88%, 59%)',
        basicBlue: '#00a8ff',
        veryDarkBlue: 'hsl(233, 12%, 13%)',
        veryPaleRed: 'hsl(13, 100%, 96%)',
        veryLightGray: 'hsl(0, 0%, 98%)',
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
}

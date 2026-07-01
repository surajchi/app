const preset = require('@finpulse/config/eslint-preset.cjs');

module.exports = [
  ...preset,
  // Node-based config files at the package root aren't part of the app bundle.
  {
    ignores: [
      'metro.config.js',
      'tailwind.config.js',
      'babel.config.js',
      'eslint.config.cjs',
    ],
  },
];

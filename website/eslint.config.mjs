// @ts-check
import withNuxt from './.nuxt/eslint.config.mjs'

// Chrome extension globals loaded via importScripts / content_scripts
const extensionGlobals = {
  // Browser extension API
  chrome: 'readonly',
  importScripts: 'readonly',
  // Purifyt module globals (set by each module file)
  PurifytConfig: 'writable',
  PurifytAuth: 'writable',
  PurifytStorage: 'writable',
  PurifytApi: 'writable',
  PurifytScanner: 'writable',
  PurifytSpoiler: 'writable',
  PurifytPlatforms: 'writable'
}

export default withNuxt(
  // Extension source files: plain browser JS loaded via script tags / importScripts
  {
    files: ['extension/src/**/*.js', 'public/Extension/src/**/*.js'],
    languageOptions: {
      globals: extensionGlobals
    },
    rules: {
      // Module globals are intentionally written to the outer scope
      'no-unused-vars': 'off',
      // Extension code uses compact inline-if patterns intentionally
      '@stylistic/max-statements-per-line': 'off'
    }
  }
)

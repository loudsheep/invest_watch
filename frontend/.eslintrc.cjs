module.exports = {
  root: true,
  ignorePatterns: ["dist"],
  env: { browser: true, es2020: true },
  extends: [
    "eslint:recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:react-hooks/recommended",
  ],
  parser: "@typescript-eslint/parser",
  plugins: ["react-hooks"],
  rules: {
    "no-console": "error",
  },
};

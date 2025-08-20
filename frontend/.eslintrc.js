module.exports = {
  "extends": [
    "react-app",
    "react-app/jest"
  ],
  "rules": {
    // Existing rules...
    
    // CRITICAL CUSTOM RULE: No mock data or temporary hacks
    "no-warning-comments": ["error", {
      "terms": ["HACK", "FIXME", "TODO", "MOCK", "FAKE", "TEMPORARY", "WORKAROUND"],
      "location": "anywhere"
    }],
    "spaced-comment": ["error", "always", {
      "markers": ["/"],
      "exceptions": ["-", "+", "CRITICAL RULE", "ABSOLUTELY FORBIDDEN"]
    }]
  }
}
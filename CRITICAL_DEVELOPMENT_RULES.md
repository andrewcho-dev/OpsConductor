# CRITICAL DEVELOPMENT RULES
## THESE RULES MUST NEVER BE BROKEN UNDER ANY CIRCUMSTANCES

### RULE 1: NO TEMPORARY HACKS, WORKAROUNDS, OR MOCK DATA
**NEVER EVER EVER use temporary hacks, workarounds, or mock/fake data in this project.**

- All data must come directly from the actual backend APIs
- If an API returns an error, handle it properly with error states
- NEVER create or use fake/mock data as a temporary solution
- NEVER implement "temporary" workarounds that bypass proper functionality
- NEVER use client-side simulation of server responses
- If a backend API is failing, fix the backend - DO NOT create fake frontend responses

This rule is absolute and must never be violated under any circumstances.

### Proper Error Handling Approach
When APIs fail, the correct approach is:
1. Display appropriate error states to the user
2. Log the error properly
3. Fix the underlying API issue
4. NEVER replace real API calls with fake/mock data

This document serves as a permanent record of these critical development rules.
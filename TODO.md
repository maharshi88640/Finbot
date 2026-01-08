# TODO: Fix PDF View Links to Open Directly from Website

## Problem
PDF links in chat responses are redirecting to localhost instead of opening directly from the Gujarat Finance Department website.

## Solution
1. Modify PDF link format in chat responses to use HTML anchors with `target="_blank"`
2. Add custom HTML/JavaScript to handle PDF links properly in Streamlit

## Files to Modify
- [ ] `src/chat/__init__.py` - Change PDF link format from markdown to HTML
- [ ] `main.py` - Add custom HTML/JavaScript to handle PDF links properly

## Steps
1. [x] Analyze codebase to understand PDF link handling
2. [x] Create implementation plan
3. [ ] Modify `src/chat/__init__.py`:
   - [x] Update `get_pdf_related_data` method to use HTML links with `target="_blank"`
   - [x] Update `get_database_overview` method to use HTML links with `target="_blank"`
4. [ ] Modify `main.py`:
   - [x] Add custom HTML component for PDF link handling
   - [x] Add JavaScript to intercept PDF links and open in new tab
5. [ ] Test the changes
6. [ ] Verify PDFs open directly from website

## Implementation Details
- Use `target="_blank"` and `rel="noopener noreferrer"` for security
- Use HTML `<a>` tags instead of markdown links
- Add Streamlit HTML component with JavaScript for proper link handling

## Status: IN PROGRESS


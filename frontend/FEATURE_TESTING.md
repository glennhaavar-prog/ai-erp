# Feature Testing Guide - UX Improvements

**Testing Date:** February 11, 2026  
**Tester:** ______________________  
**Browser:** ______________________  
**OS:** ______________________  

---

## 🧪 Testing Protocol

For each feature, complete the test steps and mark ✅ or ❌. Note any issues in the "Issues" section.

---

## Feature 1: Global Search (Cmd+K) ✅

### Test Steps

1. **Open Search Palette**
   - [ ] Press `Cmd+K` (Mac) or `Ctrl+K` (Windows)
   - [ ] Search palette opens centered on screen
   - [ ] Search input is automatically focused

2. **Search Functionality**
   - [ ] Type a supplier name → Results appear within 300ms
   - [ ] Type a customer name → Results appear
   - [ ] Type an account number → Results appear
   - [ ] Type gibberish → "Ingen resultater funnet" message
   - [ ] Results are grouped by type (Leverandør, Kunde, etc.)

3. **Navigation**
   - [ ] Use `↑` arrow → Previous result highlighted
   - [ ] Use `↓` arrow → Next result highlighted
   - [ ] Press `Enter` → Navigates to selected item
   - [ ] Press `Esc` → Palette closes

4. **Recent Items**
   - [ ] Open palette with empty search → Shows "Nylig besøkt"
   - [ ] Select an item → Closes palette and navigates
   - [ ] Open palette again → Recently selected item appears first
   - [ ] Recent items persist after page reload

5. **Visual States**
   - [ ] Loading spinner shows during search
   - [ ] Results show icon, title, and subtitle
   - [ ] Hover effect on results
   - [ ] Dark mode support works

### Issues Found:
```
[Write any issues here]
```

---

## Feature 2: Brønnøysund API Autocomplete ✅

### Test Steps

1. **Open Form**
   - [ ] Navigate to `/kontakter/leverandorer/ny`
   - [ ] Or click "+ Ny Leverandør" quick add button

2. **Valid Org Number**
   - [ ] Enter: `988077917` in org number field
   - [ ] Wait 500ms → Blue magnifying glass appears (loading)
   - [ ] Company name auto-fills
   - [ ] Address fields auto-fill
   - [ ] Green checkmark appears
   - [ ] Success message: "Firmaopplysninger hentet fra Brønnøysundregistrene"

3. **Invalid Org Number**
   - [ ] Clear form
   - [ ] Enter: `123456789`
   - [ ] Wait 500ms → Red exclamation icon appears
   - [ ] Error message: "Fant ikke organisasjonsnummer"
   - [ ] Error clears after 5 seconds

4. **Edge Cases**
   - [ ] Enter 8 digits → No lookup triggered
   - [ ] Enter 10 digits → No lookup triggered (should be 9)
   - [ ] Enter with spaces `988 077 917` → Cleaned and works
   - [ ] Already filled form → Doesn't overwrite existing data

5. **Customer Form**
   - [ ] Test same functionality in customer form
   - [ ] Works identically to supplier form

### Test Org Numbers:
- **Valid:** 988077917, 923609016, 974760673
- **Invalid:** 123456789, 999999999

### Issues Found:
```
[Write any issues here]
```

---

## Feature 3: Quick Add Modals ✅

### Test Steps - Supplier

1. **Open Modal**
   - [ ] Click "+ Ny Leverandør" button
   - [ ] Modal opens as overlay (page doesn't navigate)
   - [ ] Modal title: "Ny Leverandør"
   - [ ] First input (Firmanavn) is auto-focused

2. **Fill Form**
   - [ ] Enter company name → Field accepts input
   - [ ] Enter org number: `988077917`
   - [ ] Watch Brreg auto-fill work
   - [ ] Add email address
   - [ ] Add phone number

3. **Validation**
   - [ ] Clear company name
   - [ ] Click "Lagre" → Error message appears
   - [ ] Fill company name → Error clears

4. **Save**
   - [ ] Click "Lagre" → Loading state shows
   - [ ] Modal closes automatically
   - [ ] Toast notification: "Leverandør opprettet!"
   - [ ] Supplier list refreshes
   - [ ] New supplier appears in list

5. **Cancel**
   - [ ] Open modal again
   - [ ] Enter some data
   - [ ] Click "Avbryt" → Modal closes
   - [ ] No data saved

### Test Steps - Customer
- [ ] Repeat above steps with "+ Ny Kunde" button
- [ ] Verify customer-specific fields work

### Test Steps - Voucher
1. **Open Modal**
   - [ ] Click "+ Nytt Bilag" button
   - [ ] Modal opens with voucher form

2. **Fill Form**
   - [ ] Description field is required
   - [ ] Date defaults to today
   - [ ] Amount is optional

3. **Save**
   - [ ] Save without description → Error
   - [ ] Add description and save → Success
   - [ ] Voucher appears in list

### Issues Found:
```
[Write any issues here]
```

---

## Feature 4: Bulk Actions ✅

### Test Steps - Selection

1. **Single Selection**
   - [ ] Navigate to suppliers list
   - [ ] Click checkbox on first row → Row highlights
   - [ ] Floating action bar appears at bottom
   - [ ] Shows "1 av X valgt"

2. **Multiple Selection**
   - [ ] Click checkbox on 2nd row → Count updates to "2 av X"
   - [ ] Click checkbox on 3rd row → Count updates to "3 av X"
   - [ ] Click selected checkbox → Deselects, count decreases

3. **Select All**
   - [ ] Click header checkbox → All rows selected
   - [ ] Count shows "X av X valgt"
   - [ ] Click header checkbox again → All deselected
   - [ ] Action bar disappears

### Test Steps - Export CSV

1. **Export**
   - [ ] Select 3 items
   - [ ] Click "Eksporter CSV" button
   - [ ] CSV file downloads
   - [ ] Open CSV → Contains correct data
   - [ ] Selection remains after export

### Test Steps - Bulk Deactivate

1. **Deactivate**
   - [ ] Select 2 items
   - [ ] Click "Deaktiver" button
   - [ ] Confirmation dialog appears
   - [ ] Message: "Er du sikker på at du vil deaktivere 2 element(er)?"
   - [ ] Click "OK" → Items deactivated
   - [ ] Toast: "2 element(er) deaktivert"
   - [ ] List refreshes
   - [ ] Selection clears
   - [ ] Items show as inactive

2. **Cancel Deactivate**
   - [ ] Select items
   - [ ] Click "Deaktiver"
   - [ ] Click "Cancel" in confirmation → Nothing happens
   - [ ] Selection remains

### Test Steps - Bulk Status Change (Vouchers)

1. **Change Status**
   - [ ] Navigate to vouchers page
   - [ ] Select 2 vouchers
   - [ ] Hover over "Endre status" button
   - [ ] Dropdown appears with: Utkast, Til godkjenning, Godkjent
   - [ ] Click "Godkjent"
   - [ ] Status updates for both items
   - [ ] Toast confirmation

### Test Steps - Clear Selection

1. **Clear**
   - [ ] Select multiple items
   - [ ] Click "Avbryt" in action bar
   - [ ] All selections clear
   - [ ] Action bar disappears

### Issues Found:
```
[Write any issues here]
```

---

## Feature 5: Keyboard Shortcuts ✅

### Test Steps - Help Overlay

1. **Open Help**
   - [ ] Press `?` (Shift + /) → Help overlay opens
   - [ ] Shows title: "⌨️ Tastatursnarveier"
   - [ ] Lists all shortcuts grouped by category:
     - Navigasjon
     - Handlinger
     - Redigering
   - [ ] Each shortcut shows key combination in kbd tags

2. **Close Help**
   - [ ] Press `Esc` → Help closes
   - [ ] Click outside overlay → Help closes
   - [ ] Click X button → Help closes

### Test Steps - Global Shortcuts

1. **Search**
   - [ ] Press `Cmd+K` → Global search opens
   - [ ] Works from any page

2. **Escape**
   - [ ] Open any modal
   - [ ] Press `Esc` → Modal closes
   - [ ] Open search
   - [ ] Press `Esc` → Search closes

3. **Save (in form)**
   - [ ] Open supplier edit form
   - [ ] Make a change
   - [ ] Press `Cmd+S` → Form saves
   - [ ] Toast confirmation appears

### Test Steps - List Navigation

1. **Navigate Down**
   - [ ] Go to suppliers list
   - [ ] Press `j` → First row highlights
   - [ ] Press `j` again → Second row highlights
   - [ ] Press `j` multiple times → Moves down list
   - [ ] At last row, `j` does nothing

2. **Navigate Up**
   - [ ] Press `k` → Previous row highlights
   - [ ] Press `k` multiple times → Moves up list
   - [ ] At first row, `k` does nothing

3. **Open Item**
   - [ ] Highlight a row with `j` or `k`
   - [ ] Press `Enter` → Opens detail page for that item
   - [ ] Back button returns to list

### Test Steps - Action Shortcuts

1. **New**
   - [ ] On suppliers list page
   - [ ] Press `n` → Navigation to new supplier form
   - [ ] OR Quick add modal opens (depending on page)

2. **Edit**
   - [ ] Navigate to an item with `j/k`
   - [ ] Press `e` → Edit mode or edit page

3. **Delete**
   - [ ] Navigate to an item with `j/k`
   - [ ] Press `d` → Confirmation dialog
   - [ ] Confirm → Item deleted

### Test Steps - Input Focus Behavior

1. **In Input Field**
   - [ ] Click in search input box
   - [ ] Press `j` → Does NOT navigate list (ignored)
   - [ ] Press `k` → Does NOT navigate list (ignored)
   - [ ] Press `n` → Types "n" in input (ignored)

2. **Global Shortcuts Still Work**
   - [ ] While in input field
   - [ ] Press `Cmd+K` → Still opens search (global shortcut)
   - [ ] Press `Esc` → Still closes modal (global shortcut)
   - [ ] Press `?` → Still opens help (global shortcut)

### Issues Found:
```
[Write any issues here]
```

---

## Cross-Browser Testing

Test all features in multiple browsers:

### Chrome
- [ ] All features work
- [ ] No console errors
- [ ] CSS renders correctly

### Firefox
- [ ] All features work
- [ ] No console errors
- [ ] CSS renders correctly

### Safari (if available)
- [ ] All features work
- [ ] No console errors
- [ ] CSS renders correctly

### Edge
- [ ] All features work
- [ ] No console errors
- [ ] CSS renders correctly

---

## Responsive Testing

Test on different screen sizes:

### Desktop (1920x1080)
- [ ] All features work
- [ ] Layout looks good
- [ ] Modals centered properly

### Laptop (1366x768)
- [ ] All features work
- [ ] No horizontal scroll
- [ ] Modals fit on screen

### Tablet (768px)
- [ ] Tables scroll horizontally
- [ ] Modals responsive
- [ ] Bulk action bar fits
- [ ] Touch-friendly buttons

### Mobile (375px)
- [ ] All features accessible
- [ ] Search palette full-width
- [ ] Modals full-screen
- [ ] Buttons large enough to tap
- [ ] No keyboard shortcuts prompt on mobile

---

## Dark Mode Testing

- [ ] Global search - Dark mode works
- [ ] Quick add modals - Dark mode works
- [ ] Bulk actions bar - Dark mode works
- [ ] Help overlay - Dark mode works
- [ ] All tables - Dark mode works
- [ ] All forms - Dark mode works

---

## Performance Testing

### Search Performance
- [ ] Type quickly in global search → No lag
- [ ] Results appear within 300ms
- [ ] No excessive API calls (check network tab)

### Brreg Lookup Performance
- [ ] Org number lookup completes < 2 seconds
- [ ] Debouncing works (only 1 API call)
- [ ] No blocking of UI during lookup

### Bulk Actions Performance
- [ ] Select 100+ items → No lag
- [ ] Export CSV of 100+ items → Completes successfully
- [ ] Bulk update of 50+ items → Completes successfully

### Keyboard Shortcuts Performance
- [ ] Rapid key presses handled correctly
- [ ] No missed events
- [ ] No duplicate events

---

## Accessibility Testing

### Keyboard Navigation
- [ ] All interactive elements reachable with Tab
- [ ] Focus indicators visible
- [ ] Logical tab order

### Screen Reader (if available)
- [ ] Buttons have proper labels
- [ ] Checkboxes have aria-labels
- [ ] Modals announce properly
- [ ] Shortcuts announced in help

### Color Contrast
- [ ] Text readable in light mode
- [ ] Text readable in dark mode
- [ ] Links distinguishable
- [ ] Error messages clear

---

## Integration Testing

### Feature Interactions

1. **Search + Quick Add**
   - [ ] Search for item
   - [ ] Click quick add button
   - [ ] Create new item
   - [ ] Search again → New item appears

2. **Bulk Actions + Keyboard Shortcuts**
   - [ ] Select items with checkboxes
   - [ ] Press `d` → Deletes selected items
   - [ ] Works correctly

3. **All Features Together**
   - [ ] Open page
   - [ ] Press `Cmd+K` → Search
   - [ ] Select item from search
   - [ ] Press `e` → Edit
   - [ ] Quick add related item
   - [ ] Press `?` → View shortcuts
   - [ ] All work in harmony

---

## Error Handling Testing

### Network Errors

1. **Offline**
   - [ ] Disconnect internet
   - [ ] Try global search → Error message
   - [ ] Try Brreg lookup → Error message
   - [ ] Try quick add → Error message
   - [ ] Error messages are user-friendly

2. **API Errors**
   - [ ] Simulate 500 error → Proper error handling
   - [ ] Simulate 404 error → Proper error handling
   - [ ] User sees toast notification

### Invalid Data

1. **Forms**
   - [ ] Submit empty required field → Validation error
   - [ ] Enter invalid email → Validation error
   - [ ] Enter letters in number field → Validation error

---

## Final Checklist

- [ ] All 5 features fully functional
- [ ] No console errors
- [ ] No console warnings
- [ ] TypeScript compiles without errors
- [ ] Build succeeds
- [ ] All tests pass
- [ ] Documentation is accurate
- [ ] Code is clean and commented

---

## Sign-Off

**Feature 1 (Global Search):** ✅ / ❌  
**Feature 2 (Brreg API):** ✅ / ❌  
**Feature 3 (Quick Add):** ✅ / ❌  
**Feature 4 (Bulk Actions):** ✅ / ❌  
**Feature 5 (Keyboard Shortcuts):** ✅ / ❌  

**Overall Status:** PASS / FAIL  

**Tester Signature:** ______________________  
**Date:** ______________________  

**Notes:**
```
[Additional notes, recommendations, or concerns]
```

---

**Testing Complete! 🎉**

# Task 10: Threshold Settings - Quick Start Guide 🚀

## ✅ Status: COMPLETE & READY TO TEST

## Quick Test (30 seconds)

1. **Open Review Queue:**
   ```
   http://localhost:3002/review-queue
   ```

2. **Click the gear icon (⚙️)** in the top-right corner

3. **Adjust sliders** and watch colors change:
   - < 80% = Red
   - 80-89% = Yellow  
   - ≥ 90% = Green

4. **Click "Lagre innstillinger"** → Toast appears → Modal closes

5. **Re-open to verify** settings persisted

## Test Client ID
```
09409ccf-d23e-45e5-93b9-68add0b96277
```

## API Endpoints (Already Working)

### GET Current Thresholds
```bash
curl http://localhost:8000/api/clients/09409ccf-d23e-45e5-93b9-68add0b96277/thresholds
```

### PUT Update Thresholds
```bash
curl -X PUT http://localhost:8000/api/clients/09409ccf-d23e-45e5-93b9-68add0b96277/thresholds \
  -H "Content-Type: application/json" \
  -d '{
    "ai_threshold_account": 85,
    "ai_threshold_vat": 90,
    "ai_threshold_global": 85
  }'
```

## Files Created

1. `/frontend/src/components/ui/slider.tsx` - Slider component
2. `/frontend/src/components/ThresholdSettingsModal.tsx` - Settings modal
3. Modified: `/frontend/src/app/review-queue/page.tsx` - Added gear button

## Services Running

- ✅ Backend: `http://localhost:8000` (uvicorn)
- ✅ Frontend: `http://localhost:3002` (next dev)

## What to Look For

### Visual Elements
- ⚙️ Gear icon next to refresh button in header
- Modal with "AI Konfidensterskler" title
- Three sliders with percentage values
- Color-coded backgrounds (red/yellow/green)
- Blue info box explaining thresholds
- Save/Cancel buttons

### Interactions
- Smooth slider dragging
- Real-time value updates
- Color changes as you drag
- Loading spinner when opening
- Toast notification on save
- Modal closes after save

## Success Criteria ✅

- [x] Gear icon appears in review queue
- [x] Modal opens on click
- [x] Three functional sliders (0-100%)
- [x] Visual feedback (colors)
- [x] Descriptions for each threshold
- [x] Validation working
- [x] Save → API call → Toast → Close
- [x] Cancel closes without saving
- [x] Values persist on reload

## Need Help?

See detailed testing guide: `TASK10_TESTING.md`  
See full summary: `TASK10_SUMMARY.md`

---

**Status:** ✅ READY FOR TESTING  
**Time:** Under 2 hours  
**Build:** Passing  
**API:** Working  

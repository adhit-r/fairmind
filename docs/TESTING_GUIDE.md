# LLM-as-Judge Testing & Verification Guide

**Status**: Phase 1-2 Implementation Complete
**Date**: February 17, 2026
**Objective**: Verify backend API + frontend components work end-to-end

---

## 🧪 Pre-Testing Checklist

### 1. Environment Setup
- [ ] Backend `.env` has API keys configured:
  - `OPENAI_API_KEY` (for GPT-4 Turbo)
  - `ANTHROPIC_API_KEY` (for Claude 3 Opus)
  - `GOOGLE_API_KEY` (for Gemini Pro)
- [ ] Frontend `.env.local` has correct backend URL (`NEXT_PUBLIC_API_URL`)
- [ ] Backend server runs without errors on `http://localhost:8000`
- [ ] Frontend development server runs on `http://localhost:3000`

### 2. File Verification
```bash
# Backend route file exists
ls -la apps/backend/api/routes/llm_judge.py

# Frontend components exist
ls -la apps/frontend/src/app/\(dashboard\)/llm-judge/components/

# Documentation exists
ls -la LLMJUDGE_IMPLEMENTATION_SUMMARY.md FAIRMIND_SPRINT_PLAN.md
```

---

## 🔌 Phase 1: Backend API Testing

### Test 1.1: Health Check Endpoint
```bash
curl http://localhost:8000/api/v1/bias/llm-judge/health
```

**Expected Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-02-17T12:34:56Z"
}
```

### Test 1.2: List Available Models & Categories
```bash
curl http://localhost:8000/api/v1/bias/llm-judge/models
```

**Expected Response**:
```json
{
  "judges": [
    { "id": "gpt-4-turbo", "name": "GPT-4 Turbo", "provider": "OpenAI" },
    { "id": "claude-3-opus", "name": "Claude 3 Opus", "provider": "Anthropic" },
    ...
  ],
  "bias_categories": [
    "gender", "race", "age", "cultural", "socioeconomic",
    "intersectional", "professional", "religious"
  ]
}
```

### Test 1.3: Single Category Evaluation
```bash
curl -X POST http://localhost:8000/api/v1/bias/llm-judge/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "text": "A businessman works hard to support his family.",
    "judge_model": "gpt-4-turbo",
    "bias_category": "gender",
    "target_model": "test-model"
  }'
```

**Expected Response**:
```json
{
  "evaluation_id": "uuid-string",
  "bias_score": 0.45,
  "confidence": 0.87,
  "severity": "medium",
  "detected_biases": ["gender stereotyping"],
  "recommendations": ["Use gender-neutral terms like 'professional' instead of 'businessman'"],
  "evidence": ["A businessman works hard"],
  "reasoning": "The text uses gendered language...",
  "judge_model": "gpt-4-turbo",
  "timestamp": "2026-02-17T12:34:56Z"
}
```

### Test 1.4: Batch Evaluation (Multiple Categories)
```bash
curl -X POST http://localhost:8000/api/v1/bias/llm-judge/evaluate-batch \
  -H "Content-Type: application/json" \
  -d '{
    "text": "A businessman works hard to support his family.",
    "judge_model": "gpt-4-turbo",
    "bias_categories": ["gender", "age", "professional"],
    "target_model": "test-model"
  }'
```

**Expected Response**: Batch results with multiple category evaluations

### Test 1.5: Error Handling
Test with invalid inputs:

```bash
# Empty text
curl -X POST http://localhost:8000/api/v1/bias/llm-judge/evaluate-batch \
  -H "Content-Type: application/json" \
  -d '{
    "text": "",
    "judge_model": "gpt-4-turbo",
    "bias_categories": ["gender"]
  }'

# Invalid judge model
curl -X POST http://localhost:8000/api/v1/bias/llm-judge/evaluate-batch \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Valid text here",
    "judge_model": "invalid-model",
    "bias_categories": ["gender"]
  }'

# Text exceeding 50,000 chars (should be rejected)
# Text exceeding 50,000 chars...
```

**Expected**: Appropriate error responses with meaningful messages

---

## 🎨 Phase 2: Frontend Component Testing

### Test 2.1: Navigation to Feature
1. Open `http://localhost:3000/dashboard/llm-judge`
2. **Verify**:
   - Page loads without JavaScript errors
   - Page title shows "LLM-as-a-Judge"
   - Description text displays correctly
   - Info alert with "New Feature" badge shows

### Test 2.2: InputForm Component
1. **Text Input**:
   - [ ] Type text in textarea
   - [ ] Character count updates in real-time
   - [ ] Progress bar fills as you type
   - [ ] Max 50,000 char limit enforced

2. **File Upload**:
   - [ ] Click file upload button
   - [ ] Select a `.txt` file
   - [ ] File content appears in textarea
   - [ ] Character count updates
   - [ ] Only `.txt` files accepted (reject `.pdf`, `.doc`, etc.)

3. **Judge Model Selection**:
   - [ ] Dropdown shows all 5 judge models
   - [ ] Can select each one
   - [ ] Selection persists

4. **Bias Category Selection**:
   - [ ] All 8 categories appear as checkboxes
   - [ ] Can select multiple categories
   - [ ] At least 1 category required (validate on submit)
   - [ ] Can deselect categories

5. **Target Model Field**:
   - [ ] Optional field for model name
   - [ ] Can be left empty
   - [ ] Accepts any string input

6. **Form Validation**:
   - [ ] Submit with empty text → error message
   - [ ] Submit with no categories selected → error message
   - [ ] Submit with valid data → form submits

### Test 2.3: Loading State
1. After form submission:
   - [ ] Submit button becomes disabled
   - [ ] Loading spinner appears
   - [ ] "Evaluating..." text shows
   - [ ] User cannot submit while loading

2. Wait for API response (3-10 seconds depending on judge model)

### Test 2.4: Results Phase - BiasScoreCard
1. **Score Visualization**:
   - [ ] Bias score displays as percentage (0-100%)
   - [ ] Progress bar fills correctly
   - [ ] Color coding matches severity:
     - Red (Critical) if score ≥ 0.8
     - Orange (High) if score ≥ 0.6
     - Yellow (Medium) if score ≥ 0.4
     - Green (Low) if score < 0.4

2. **Confidence Level**:
   - [ ] Confidence displays as percentage
   - [ ] Progress bar shows confidence visually

3. **Judge Info**:
   - [ ] Judge model name displays
   - [ ] Evaluation ID shows (truncated)

4. **Key Insights**:
   - [ ] Detected biases appear as badges
   - [ ] Shows up to 5 biases + "more" badge if > 5

5. **Quick Stats**:
   - [ ] Shows count of detected biases
   - [ ] Shows count of recommendations
   - [ ] Shows count of evidence items

### Test 2.5: Results Phase - EvidencePanel
1. **Bias List**:
   - [ ] Each detected bias appears as expandable item
   - [ ] Bias name shows in red badge

2. **Evidence Display**:
   - [ ] Click to expand bias
   - [ ] Evidence text appears in quotes
   - [ ] Evidence is accurate (matches what judge provided)

3. **Copy Functionality**:
   - [ ] "Copy Evidence" button appears
   - [ ] Click button → "Copied!" message appears
   - [ ] Icon changes to checkmark temporarily
   - [ ] Text actually copied to clipboard

4. **No Biases State**:
   - [ ] If no biases detected, shows "No Biases Detected" message
   - [ ] Congratulatory text displays

### Test 2.6: Results Phase - RecommendationsPanel
1. **Recommendations List**:
   - [ ] Each recommendation appears numbered
   - [ ] Can expand/collapse each recommendation
   - [ ] First one is expanded by default

2. **Recommendation Content**:
   - [ ] Full recommendation text shows when expanded
   - [ ] "How to implement this" tips appear
   - [ ] Implementation tips are helpful and specific

3. **Download Report**:
   - [ ] "Download Report" button visible
   - [ ] Click button → `.txt` file downloads
   - [ ] File contains all recommendations, biases, reasoning
   - [ ] File is readable and formatted well

4. **No Recommendations State**:
   - [ ] If no recommendations, shows "No Recommendations Needed"
   - [ ] Congratulatory message appears

### Test 2.7: Tab Navigation
1. **Multiple Categories**:
   - [ ] Tab for each evaluated category appears
   - [ ] Can click between tabs
   - [ ] Content changes correctly per tab
   - [ ] Results display correct data for each category

### Test 2.8: Full Reasoning & Judge Info
1. **Reasoning Display**:
   - [ ] Full judge reasoning text appears
   - [ ] Text is readable (wrapped, good contrast)

2. **Metadata**:
   - [ ] Judge model name shows
   - [ ] Timestamp shows in readable format

### Test 2.9: Summary Statistics
1. **Four Key Metrics**:
   - [ ] Avg Bias Score displays (average across all categories)
   - [ ] Total Biases Found displays (sum across all)
   - [ ] Total Recommendations displays (sum across all)
   - [ ] Avg Confidence displays (average across all)

2. **Calculations**:
   - [ ] Math is correct (spot-check one metric)

### Test 2.10: Next Steps Section
1. **Guidance**:
   - [ ] "Next Steps" section appears after results
   - [ ] Lists 4 actionable steps
   - [ ] Text is clear and helpful

### Test 2.11: New Evaluation Button
1. **Reset Functionality**:
   - [ ] "New Evaluation" button appears at top right of results
   - [ ] Click button → returns to input form
   - [ ] Form is cleared and ready for new input

---

## 📱 Phase 3: Responsive Design Testing

### Mobile (375px width)
- [ ] All text is readable
- [ ] Buttons are tap-friendly (min 44x44px)
- [ ] No horizontal scrolling
- [ ] Cards stack vertically
- [ ] Input form doesn't overflow

### Tablet (768px width)
- [ ] Grid layouts work (2 columns where applicable)
- [ ] Stats dashboard shows 2x2 grid
- [ ] Tabs scroll if needed

### Desktop (1200px+ width)
- [ ] Full layout displays as designed
- [ ] Stats dashboard shows 4 columns
- [ ] All cards visible without scrolling

---

## ⌨️ Phase 4: Accessibility Testing

- [ ] Can navigate with Tab key only
- [ ] All buttons/links are keyboard accessible
- [ ] Color not sole means of conveying info (icons + text)
- [ ] Error messages are clear and helpful
- [ ] Form labels associated with inputs

---

## 🐛 Phase 5: Error Scenario Testing

### API Error Handling
1. **Missing API Keys**:
   - [ ] Submit evaluation without valid API key
   - [ ] User sees helpful error message
   - [ ] Not a generic 500 error

2. **Judge Model Timeout**:
   - [ ] If judge model takes > 30 seconds
   - [ ] Show timeout error
   - [ ] Offer to retry

3. **Network Error**:
   - [ ] Disable internet, try to submit
   - [ ] See network error message
   - [ ] Can retry

---

## ✅ Phase 6: Integration Testing

### Full Workflow Test
1. Navigate to `/dashboard/llm-judge` ✓
2. Paste or upload sample text ✓
3. Select judge model (GPT-4 Turbo recommended) ✓
4. Select 3-4 bias categories ✓
5. (Optional) Enter target model name ✓
6. Click "Start Evaluation" ✓
7. Wait for results (3-10 seconds) ✓
8. View BiasScoreCard ✓
9. Expand and review EvidencePanel ✓
10. Review RecommendationsPanel ✓
11. Download report ✓
12. Click "New Evaluation" ✓
13. Start over with different text ✓

---

## 🎯 Success Criteria

**All tests pass** ✅ = Feature ready for staging

**Some tests fail** ⚠️ = Document issues and file bugs

**Major workflow broken** ❌ = Debug backend/frontend connection

---

## 📋 Sample Test Texts

### Text 1: Gender Bias
```
A businessman and his secretary worked late to finish the project.
The secretary made coffee while the businessman made strategic decisions.
```

### Text 2: Age Bias
```
We're looking for young, energetic team members.
Senior citizens need not apply.
We want fresh ideas, not experience.
```

### Text 3: Racial Bias
```
The neighborhood has become diverse.
Property values have decreased accordingly.
White families are moving to the suburbs.
```

### Text 4: Low Bias (Control)
```
The project team consists of professionals with varied expertise.
Sarah contributed architectural decisions while Tom handled implementation.
Both perspectives were valuable to the outcome.
```

---

## 🐛 Debugging Tips

### If backend won't start:
```bash
cd apps/backend
python -m pip install -r requirements.txt
python main.py
# Check error logs
```

### If API routes not found:
```bash
# Verify routes are registered
grep -r "llm_judge" apps/backend/api/main.py
```

### If frontend components not rendering:
```bash
# Check browser console for JS errors
# Verify components are imported correctly in page.tsx
# Check that useLLMJudge hook is accessible
```

### If API calls failing:
```bash
# Test endpoint directly with curl
# Check API keys in .env
# Verify backend URL in frontend .env.local
# Check CORS settings if cross-origin request
```

---

## 📞 Next Steps After Testing

- **All Green ✅**: Ready for staging deployment
- **Minor Issues**: Fix and re-test
- **Major Issues**: Debug and create bug fixes
- **Missing Features**: File as Phase 3+ enhancement requests

---

**Testing completed by**: ___________________
**Date**: ___________________
**Result**: ✅ PASS / ⚠️ NEEDS FIXES / ❌ BLOCKING ISSUES

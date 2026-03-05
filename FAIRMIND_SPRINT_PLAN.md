# FairMind Sprint Plan - LLM-as-Judge Feature

## Current Status
- **Backend**: ✅ Complete (LLMAsJudgeService exists at `api/services/llm_as_judge_service.py`)
- **Frontend**: ⚠️ Skeleton only (~100 lines, basic UI)
- **API Routes**: ⚠️ May not be registered in main.py

## What We're Building

### Feature: LLM-as-Judge Bias Evaluation
Users upload/paste text and have multiple LLM judges (GPT-4, Claude, Gemini) evaluate it for bias across 8 categories:
- Gender, Race, Age, Cultural, Socioeconomic, Intersectional, Professional, Religious

### Backend Capabilities (Already Exist)
- `LLMAsJudgeService` class with:
  - 8 bias category evaluation prompts
  - Support for GPT-4, GPT-4-Turbo, Claude 3 Opus/Sonnet, Gemini Pro
  - `JudgeEvaluationResult` dataclass with:
    - bias_score (0.0 - 1.0)
    - confidence level
    - reasoning
    - detected_biases (list)
    - severity (low/medium/high/critical)
    - recommendations (list)
    - evidence (specific examples)

### Frontend Architecture
```
/apps/frontend/src/app/(dashboard)/llm-judge/
├── page.tsx (main page - NEEDS ENHANCEMENT)
├── components/
│   ├── InputForm.tsx (NEW)
│   ├── ResultsDisplay.tsx (NEW)
│   ├── BiasScoreCard.tsx (NEW)
│   ├── EvidencePanel.tsx (NEW)
│   └── RecommendationsPanel.tsx (NEW)
├── hooks/
│   └── useLLMJudge.ts (NEW)
└── types.ts (NEW)
```

## Tasks Breakdown

### PHASE 1: Backend API Registration (1-2 hours)
- [ ] Verify LLMAsJudgeService endpoints are registered in main.py
- [ ] Test endpoints with curl/Postman
- [ ] Document API contract
  - POST `/api/v1/bias/llm-judge/evaluate`
  - Input: text, judge_model, bias_categories
  - Output: JudgeEvaluationResult

### PHASE 2: Frontend Components (4-6 hours)

#### Task 2.1: Custom Hook (1 hour)
- [ ] Create `hooks/useLLMJudge.ts`
  - `useEvaluateWithJudge()` - call backend API
  - `useFetchJudgeModels()` - get available judges
  - Loading + error states
  - Result caching

#### Task 2.2: Input Form Component (1.5 hours)
- [ ] `InputForm.tsx`
  - Text input (textarea + upload file option)
  - Judge model selector (multi-select or multi-checkbox)
  - Bias category selector (multi-select with presets)
  - "Evaluate" button with loading state
  - Error display

#### Task 2.3: Results Display Components (3 hours)
- [ ] `BiasScoreCard.tsx`
  - Bias score visualization (0.0-1.0 scale)
  - Color-coded severity badges
  - Confidence level display
  - Judge model attribution

- [ ] `EvidencePanel.tsx`
  - List of detected biases
  - Evidence snippets with highlighting
  - Expandable details
  - Copy-to-clipboard for evidence

- [ ] `RecommendationsPanel.tsx`
  - Actionable recommendations list
  - Severity indicators
  - Accordion for detailed explanations

#### Task 2.4: Main Page Enhancement (1-1.5 hours)
- [ ] Replace skeleton code in `page.tsx`
- [ ] Integrate all components
- [ ] Add tabs or accordion for:
  - Input instructions
  - Results (multiple judges side-by-side)
  - Comparison (if multiple judges selected)
  - History (recent evaluations)

### PHASE 3: Enhanced Features (Optional, 2-4 hours)

#### Task 3.1: Multi-Judge Comparison
- [ ] Side-by-side results from different judges
- [ ] Consensus scoring (if judges disagree)
- [ ] Confidence weighting

#### Task 3.2: Batch Processing
- [ ] Upload multiple texts
- [ ] Generate report with all results
- [ ] CSV/JSON export

#### Task 3.3: History & Saved Evaluations
- [ ] Save evaluation results
- [ ] View evaluation history
- [ ] Filter/search history
- [ ] Compare past evaluations

### PHASE 4: Testing & Polish (2-3 hours)
- [ ] E2E tests with Playwright
- [ ] Component unit tests
- [ ] Mobile responsiveness
- [ ] Accessibility (a11y)
- [ ] Performance optimization

## Code References

### Modern Bias Page (Reference)
Location: `apps/frontend/src/app/(dashboard)/modern-bias/page.tsx`
Use as reference for:
- Tabs implementation
- Form state management
- API hook pattern
- Result display layout
- Error/success toast notifications

### LLM Bias Service (Backend Reference)
Location: `api/services/llm_bias_detection_service.py`
Review for:
- Service patterns
- Error handling
- Async operations

## Design System
- Use existing Shadcn UI components:
  - `Card`, `Button`, `Input`, `Textarea`, `Select`
  - `Badge`, `Alert`, `Tabs`, `Dialog`
  - `Progress` (for bias score visualization)
- Icons: Tabler icons (already in use)
- Styling: Tailwind CSS + Neobrutalism (bold borders, shadows)

## API Contract (TO CONFIRM)

### Request
```json
{
  "text": "string (required)",
  "judge_model": "gpt-4 | claude-3-opus | gemini-pro (required)",
  "bias_categories": ["gender", "race", ...] (optional, default: all)
}
```

### Response
```json
{
  "evaluation_id": "uuid",
  "timestamp": "iso-8601",
  "judge_model": "string",
  "bias_category": "string",
  "bias_score": 0.0-1.0,
  "confidence": 0.0-1.0,
  "reasoning": "string",
  "detected_biases": ["string"],
  "severity": "low | medium | high | critical",
  "recommendations": ["string"],
  "evidence": ["string"],
  "metadata": {}
}
```

## Success Criteria
✅ Users can input text
✅ Multiple judge models selectable
✅ Comprehensive results display with:
  - Bias scores
  - Detected biases
  - Evidence snippets
  - Recommendations
✅ Works on desktop + tablet
✅ Clear error handling
✅ Performance: <5s response time

## Known Risks
- API endpoint may not be registered yet → verify in Phase 1
- API key management (OpenAI, Anthropic, Google) → check backend env setup
- Rate limiting on external APIs → may need queuing for production
- Token costs for judge models → budget consideration

## Next Steps
1. Start Phase 1 (verify backend)
2. Proceed with Phase 2 components in order
3. Test as we go with manual API calls
4. Integrate into page when components ready
5. Phase 3/4 optional based on time

---
**Estimated Total Time**: 8-12 hours (Phase 1-2 mandatory, Phase 3-4 if time permits)
**Priority**: Phase 1-2 (ship working version, then enhance)

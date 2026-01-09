# Substep System Comprehensive Test Plan
# Substep系统全面测试方案

> Test Date: 2026-01-08
> Test Document: test_documents/test_high_risk.txt
> Purpose: Verify all substeps work as designed and evaluate DEAIGC effectiveness
> 目的：验证所有substep按设计正常运行并评估DEAIGC效果

---

## Test Environment | 测试环境

- **Test Method**: Script + Playwright cross-validation
- **Test Document**: Climate change paper with high AI fingerprints
- **Expected Features**: Contains AI-typical words (delve, multifaceted, tapestry, pivotal, etc.)
- **Evaluation Focus**: Detection accuracy + Modification effectiveness

---

## Test Structure | 测试结构

### Layer 5 (Document Level) - 6 Substeps

| Step | Name | Key Tests | Success Criteria |
|------|------|-----------|------------------|
| **1.0** | Term Locking | LLM extraction, user selection, propagation | Terms locked and preserved |
| **1.1** | Section Structure | Order predictability, symmetry detection | Detect formulaic structure |
| **1.2** | Section Uniformity | Length CV, paragraph count variance | CV < 0.3 detected |
| **1.3** | Logic Pattern | Linear flow, repetitive pattern | Detect First/Second/Third |
| **1.4** | Paragraph Length | CV analysis, merge/split strategies | CV < 0.3 detected, strategies proposed |
| **1.5** | Transitions | Explicit connectors, semantic echo | Detect "Furthermore", "Moreover" |

### Layer 4 (Section Level) - 6 Substeps

| Step | Name | Key Tests | Success Criteria |
|------|------|-----------|------------------|
| **2.0** | Section Identification | Boundary detection, role labeling | Correct section boundaries |
| **2.1** | Section Order | Predictability, missing sections | Detect formulaic order |
| **2.2** | Length Distribution | Section length CV, extreme sections | Detect uniformity |
| **2.3** | Internal Structure | Paragraph function labeling, similarity | Detect > 80% similarity |
| **2.4** | Section Transition | Explicit connectors, semantic echo | Detect transition issues |
| **2.5** | Inter-Section Logic | Argument chain, redundancy | Detect perfect closure |

### Layer 3 (Paragraph Level) - 6 Substeps

| Step | Name | Key Tests | Success Criteria |
|------|------|-----------|------------------|
| **3.0** | Paragraph Identification | Boundary detection, section mapping | Correct paragraph count |
| **3.1** | Paragraph Role | Role detection, distribution uniformity | Identify roles correctly |
| **3.2** | Internal Coherence | Subject diversity, logic structure | Detect linear structure |
| **3.3** | Anchor Density | 13 types detection, density per 100 words | Identify low-density paras |
| **3.4** | Sentence Length | Within-paragraph CV, burstiness | Detect CV < 0.25 |
| **3.5** | Paragraph Transition | Explicit connectors, semantic echo | Detect formulaic transitions |

### Layer 2 (Sentence Level) - 6 Substeps

| Step | Name | Key Tests | Success Criteria |
|------|------|-----------|------------------|
| **4.0** | Sentence Context Preparation | Inherit paragraph context | Context loaded |
| **4.1** | Sentence Role Detection | Identify sentence functions | Roles identified |
| **4.2** | Pattern Detection | Detect AI sentence patterns | Identify patterns |
| **4.3** | Connector Analysis | Sentence-level connectors | Detect overuse |
| **4.4** | Length Diversity | Sentence length variation | Detect uniformity |
| **4.5** | Sentence Rewriting | LLM-based rewriting | Preserve locked terms |

### Layer 1 (Lexical Level) - 6 Substeps

| Step | Name | Key Tests | Success Criteria |
|------|------|-----------|------------------|
| **5.0** | Lexical Context Preparation | Load vocabulary database | Context ready |
| **5.1** | Fingerprint Detection | Type A/B/C detection | Detect "delve", "tapestry", etc. |
| **5.2** | Human Feature Analysis | Verb/adjective/phrase coverage | Identify gaps |
| **5.3** | Replacement Generation | Generate candidates per fingerprint | Candidates provided |
| **5.4** | Paragraph Rewriting | LLM paragraph-level rewriting | Reduce AI risk |
| **5.5** | Validation | Semantic similarity, risk reduction | Similarity ≥ 0.85, risk reduced |

---

## Test Execution Plan | 测试执行计划

### Phase 1: Layer 5 Testing (Document Level)

**Test Order**: 1.0 → 1.1 → 1.2 → 1.3 → 1.4 → 1.5

**For each substep**:
1. Call API endpoint with test document
2. Verify detection accuracy
3. Check output data structure
4. Test user interaction (if applicable)
5. Evaluate DEAIGC effectiveness
6. Record results in test report

### Phase 2: Layer 4 Testing (Section Level)

**Test Order**: 2.0 → 2.1 → 2.2 → 2.3 → 2.4 → 2.5

**For each substep**:
1. Use output from Layer 5 as input
2. Call section-level API
3. Verify section detection
4. Check modification effectiveness
5. Record results

### Phase 3: Layer 3 Testing (Paragraph Level)

**Test Order**: 3.0 → 3.1 → 3.2 → 3.3 → 3.4 → 3.5

**For each substep**:
1. Use output from Layer 4 as input
2. Test paragraph-level detection
3. Verify anchor density analysis
4. Check coherence detection
5. Record results

### Phase 4: Layer 2 Testing (Sentence Level)

**Test Order**: 4.0 → 4.1 → 4.2 → 4.3 → 4.4 → 4.5

**For each substep**:
1. Use output from Layer 3 as input
2. Test sentence-level patterns
3. Verify connector detection
4. Check rewriting effectiveness
5. Record results

### Phase 5: Layer 1 Testing (Lexical Level)

**Test Order**: 5.0 → 5.1 → 5.2 → 5.3 → 5.4 → 5.5

**For each substep**:
1. Use output from Layer 2 as input
2. Test fingerprint detection
3. Verify replacement generation
4. Check LLM rewriting quality
5. Validate semantic preservation
6. Record results

### Phase 6: Playwright Cross-Validation

**Frontend Testing**:
1. Upload test document via UI
2. Navigate through each substep
3. Verify UI displays match API results
4. Test user interactions (click, select, confirm)
5. Check data persistence across steps
6. Verify final output

### Phase 7: Overall DEAIGC Effectiveness Evaluation

**Metrics to evaluate**:
1. **Detection Accuracy**: Did all substeps detect expected issues?
2. **Modification Quality**: Are modifications effective and natural?
3. **Term Preservation**: Are locked terms preserved throughout?
4. **Semantic Preservation**: Is original meaning maintained?
5. **AI Risk Reduction**: Overall risk score reduction percentage
6. **User Experience**: Is the workflow intuitive and helpful?

---

## Success Criteria | 成功标准

### Per Substep
- ✅ API returns expected data structure
- ✅ Detection identifies known issues in test document
- ✅ Output includes correct risk levels and recommendations
- ✅ Modifications improve DEAIGC score without breaking content

### Overall System
- ✅ All 30 substeps (6×5 layers) execute without errors
- ✅ Data flows correctly between layers
- ✅ Locked terms preserved throughout all modifications
- ✅ Final AI risk score reduced by ≥ 40%
- ✅ Semantic similarity maintained ≥ 85%
- ✅ Frontend UI matches backend API behavior

---

## Test Data Analysis | 测试数据分析

### Test Document AI Fingerprints (Expected Detections)

**Layer 1 (Lexical)**:
- Type A words: "delves" (1), "tapestry" (1), "pivotal" (2), "multifaceted" (3), "paramount" (2)
- Type B words: "comprehensive" (4), "robust" (2), "leverage" (1), "facilitate" (1), "elucidate" (1), "crucial" (2), "holistic" (1)
- Type C phrases: "In conclusion" (1), "Not only...but also" (1)

**Layer 3 (Paragraph)**:
- Low anchor density paragraphs: Abstract, parts of Discussion
- Uniform sentence length: Multiple paragraphs
- Explicit connectors: "Furthermore" (3), "Moreover" (2), "Additionally" (1), "Consequently" (1)

**Layer 5 (Document)**:
- Predictable section order: Introduction → Methodology → Results → Discussion → Conclusion
- Uniform paragraph lengths across sections
- Linear progression with explicit signposting

---

## Report Structure | 报告结构

For each tested substep, record:

```markdown
## Layer X - Step X.X: [Name]

### Test Execution
- API Endpoint: [endpoint]
- Request Payload: [summary]
- Execution Time: [ms]

### Detection Results
- Issues Detected: [count]
- Risk Level: [low/medium/high]
- Key Findings: [list]

### Expected vs Actual
- Expected Detections: [list]
- Actual Detections: [list]
- Match Rate: [percentage]

### DEAIGC Effectiveness
- Before Risk Score: [score]
- After Risk Score: [score]
- Reduction: [percentage]
- Quality Assessment: [pass/fail/partial]

### Issues Found
- [List any bugs, errors, or unexpected behavior]

### Recommendations
- [Improvements or fixes needed]
```

---

## Next Steps | 下一步

1. ✅ Create test plan document (this file)
2. ⏳ Create test report document
3. ⏳ Execute Layer 5 tests
4. ⏳ Execute Layer 4 tests
5. ⏳ Execute Layer 3 tests
6. ⏳ Execute Layer 2 tests
7. ⏳ Execute Layer 1 tests
8. ⏳ Playwright cross-validation
9. ⏳ Generate final summary and recommendations

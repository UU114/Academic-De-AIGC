# Substep System Comprehensive Test Report
# Substep系统全面测试报告

> Test Date: 2026-01-08 21:04:18
> Test Document: test_documents\test_high_risk.txt
> Total Substeps: 30
> Success: 30, Failed: 0

---

## Executive Summary | 执行摘要

- **Success Rate**: 30/30 (100%)
- **High Risk Detections**: 7
- **Medium Risk Detections**: 5
- **Low Risk Detections**: 17

**Overall Effectiveness**: Excellent - system detects many AI patterns
**总体效果**: 优秀 - 系统检测到多个AI模式

### Layer Summary | 层级汇总

| Layer | Substeps | Success | Avg Risk | Effectiveness |
|-------|----------|---------|----------|---------------|
| Layer 5 | 6 | 6 | 20.0 | Low |
| Layer 4 | 6 | 6 | 30.0 | Medium |
| Layer 3 | 6 | 6 | 40.2 | Medium |
| Layer 2 | 6 | 6 | 46.7 | Medium |
| Layer 1 | 6 | 6 | 65.3 | High |

---

## Layer 5 - Document Level

### Step 1.0: Term Locking - Extract

- **Status**: SUCCESS
- **Risk Score**: N/A/100
- **Risk Level**: N/A
- **Issues Found**: 0
- **Processing Time**: 5245ms

---

### Step 1.1: Structure Framework

- **Status**: SUCCESS
- **Risk Score**: 17/100
- **Risk Level**: low
- **Issues Found**: 0
- **Processing Time**: 6ms

**Recommendations:**
- Structure appears natural. No major issues detected.

**DE-AIGC Effectiveness**: Limited - May need calibration

---

### Step 1.2: Section Uniformity

- **Status**: SUCCESS
- **Risk Score**: 15/100
- **Risk Level**: low
- **Issues Found**: 0
- **Processing Time**: 4ms

**Recommendations:**
- Paragraph lengths show good variation. No major issues detected.

**DE-AIGC Effectiveness**: Limited - May need calibration

---

### Step 1.3: Logic Pattern

- **Status**: SUCCESS
- **Risk Score**: 50/100
- **Risk Level**: medium
- **Issues Found**: 1
- **Processing Time**: 6ms

**Detected Issues:**
- Closure is too strong (score: 90)

**Recommendations:**
- Closure is too strong. Consider ending with an open question or unresolved tension instead of a definitive summary.

**DE-AIGC Effectiveness**: Good - Detects moderate AI patterns

---

### Step 1.4: Paragraph Length

- **Status**: SUCCESS
- **Risk Score**: 15/100
- **Risk Level**: low
- **Issues Found**: 0
- **Processing Time**: 4ms

**Recommendations:**
- Paragraph lengths show good variation. No major issues detected.

**DE-AIGC Effectiveness**: Limited - May need calibration

---

### Step 1.5: Transitions

- **Status**: SUCCESS
- **Risk Score**: 3/100
- **Risk Level**: low
- **Issues Found**: 4
- **Processing Time**: 5ms

**Detected Issues:**
- Paragraph starts with formulaic topic sentence (AI pattern)
- High keyword overlap (100%) suggests mechanical connection
- Starts with explicit connector "In conclusion" (AI overuse)
- High keyword overlap (100%) suggests mechanical connection

**Recommendations:**
- Formulaic topic sentences detected (1 times). Vary paragraph openings.

**DE-AIGC Effectiveness**: Limited - May need calibration

---

## Layer 4 - Section Level

### Step 2.0: Section Identification

- **Status**: SUCCESS
- **Risk Score**: 20/100
- **Risk Level**: low
- **Issues Found**: 0
- **Processing Time**: 4ms

**Recommendations:**
- Identified 7 sections. Review and adjust if needed.

**DE-AIGC Effectiveness**: Fair - Some detection capability

---

### Step 2.1: Section Order

- **Status**: SUCCESS
- **Risk Score**: 30/100
- **Risk Level**: low
- **Issues Found**: 0
- **Processing Time**: 3ms

**Recommendations:**
- Missing sections: literature_review. This may be intentional.

**DE-AIGC Effectiveness**: Fair - Some detection capability

---

### Step 2.2: Length Distribution

- **Status**: SUCCESS
- **Risk Score**: 70/100
- **Risk Level**: high
- **Issues Found**: 2
- **Processing Time**: 3ms

**Detected Issues:**
- Section lengths too uniform (CV=0.22)
- Paragraph counts per section too uniform (CV=0.14)

**Recommendations:**
- Expand core sections and condense background sections for more natural variation.

**DE-AIGC Effectiveness**: Excellent - Correctly identifies high AI risk

---

### Step 2.3: Internal Structure

- **Status**: SUCCESS
- **Risk Score**: 30/100
- **Risk Level**: low
- **Issues Found**: 0
- **Processing Time**: 3ms

**Recommendations:**
- Section internal structures show good variation.

**DE-AIGC Effectiveness**: Fair - Some detection capability

---

### Step 2.4: Section Transition

- **Status**: SUCCESS
- **Risk Score**: 15/100
- **Risk Level**: low
- **Issues Found**: 1
- **Processing Time**: 3ms

**Detected Issues:**
- Low semantic echo between sections (0%)

**Recommendations:**
- Improve semantic connections by echoing keywords from previous sections.

**DE-AIGC Effectiveness**: Limited - May need calibration

---

### Step 2.5: Inter-Section Logic

- **Status**: SUCCESS
- **Risk Score**: 15/100
- **Risk Level**: low
- **Issues Found**: 0
- **Processing Time**: 4ms

**Recommendations:**
- Add non-linear elements like digressions, side notes, or unexpected findings.
- Inter-section logic appears natural.

**DE-AIGC Effectiveness**: Limited - May need calibration

---

## Layer 3 - Paragraph Level

### Step 3.0: Paragraph Identification

- **Status**: SUCCESS
- **Risk Score**: 20/100
- **Risk Level**: low
- **Issues Found**: 0
- **Processing Time**: 3ms

**Recommendations:**
- Filtered 6 non-body elements (headers, keywords, etc.)

**DE-AIGC Effectiveness**: Fair - Some detection capability

---

### Step 3.1: Paragraph Role

- **Status**: SUCCESS
- **Risk Score**: 10/100
- **Risk Level**: low
- **Issues Found**: 1
- **Processing Time**: 3ms

**Detected Issues:**
- Missing key roles: conclusion

**Recommendations:**
- Consider adding transition paragraphs between major sections.

**DE-AIGC Effectiveness**: Limited - May need calibration

---

### Step 3.2: Internal Coherence

- **Status**: SUCCESS
- **Risk Score**: 39/100
- **Risk Level**: medium
- **Issues Found**: 1
- **Processing Time**: 4ms

**Detected Issues:**
- 6 paragraphs have excessive connectors

**DE-AIGC Effectiveness**: Fair - Some detection capability

---

### Step 3.3: Anchor Density

- **Status**: SUCCESS
- **Risk Score**: 94/100
- **Risk Level**: high
- **Issues Found**: 2
- **Processing Time**: 6ms

**Detected Issues:**
- 8 paragraphs have low anchor density (potential AI filler)
- Overall anchor density is low (1.9/100 words)

**Recommendations:**
- Add specific data, citations, or evidence to low-density paragraphs.
- Consider adding citations to support your claims.

**DE-AIGC Effectiveness**: Excellent - Correctly identifies high AI risk

---

### Step 3.4: Sentence Length

- **Status**: SUCCESS
- **Risk Score**: 58/100
- **Risk Level**: medium
- **Issues Found**: 2
- **Processing Time**: 4ms

**Detected Issues:**
- 6 paragraphs have too uniform sentence lengths (CV < 0.25)
- 6 paragraphs have low burstiness (monotonous rhythm)

**Recommendations:**
- Add variety to sentence lengths. Mix short (8-12 words) with long (25+ words) sentences.
- Create rhythm by alternating between short punchy sentences and longer complex ones.

**DE-AIGC Effectiveness**: Good - Detects moderate AI patterns

---

### Step 3.5: Paragraph Transition

- **Status**: SUCCESS
- **Risk Score**: 20/100
- **Risk Level**: low
- **Issues Found**: 1
- **Processing Time**: 4ms

**Detected Issues:**
- Low semantic echo between paragraphs (4%)

**Recommendations:**
- Improve paragraph connections by referencing concepts from the previous paragraph.

**DE-AIGC Effectiveness**: Fair - Some detection capability

---

## Layer 2 - Sentence Level

### Step 4.0: Sentence Context

- **Status**: SUCCESS
- **Risk Score**: 20/100
- **Risk Level**: low
- **Issues Found**: 0
- **Processing Time**: 4ms

**Recommendations:**
- Consider adding more passive voice sentences for variety.
- Sentence structure shows good variety.

**DE-AIGC Effectiveness**: Fair - Some detection capability

---

### Step 4.1: Sentence Role

- **Status**: SUCCESS
- **Risk Score**: 30/100
- **Risk Level**: low
- **Issues Found**: 1
- **Processing Time**: 4ms

**Detected Issues:**
- Repeated openers: furthermore, the, it

**Recommendations:**
- Add passive voice sentences for variety (15-25% is ideal).

**DE-AIGC Effectiveness**: Fair - Some detection capability

---

### Step 4.2: Pattern Detection

- **Status**: SUCCESS
- **Risk Score**: 70/100
- **Risk Level**: high
- **Issues Found**: 1
- **Processing Time**: 4ms

**Detected Issues:**
- Sentence lengths too uniform (CV=0.23)

**Recommendations:**
- Add variety by mixing short (8-12 words) and long (30+ words) sentences.
- Add short emphatic sentences to create rhythm and emphasis.

**DE-AIGC Effectiveness**: Excellent - Correctly identifies high AI risk

---

### Step 4.3: Connector Analysis

- **Status**: SUCCESS
- **Risk Score**: 40/100
- **Risk Level**: low
- **Issues Found**: 0
- **Processing Time**: 3ms

**Recommendations:**
- Consider merging 1 sentence pairs to increase complexity.

**DE-AIGC Effectiveness**: Good - Detects moderate AI patterns

---

### Step 4.4: Length Diversity

- **Status**: SUCCESS
- **Risk Score**: 40/100
- **Risk Level**: medium
- **Issues Found**: 1
- **Processing Time**: 3ms

**Detected Issues:**
- 7 strong AI connectors found (Furthermore, Moreover, etc.)

**Recommendations:**
- Remove or replace strong AI connectors (Furthermore, Moreover, Additionally).
- Add subordinate clause starters (Although, While, Despite) for variety.

**DE-AIGC Effectiveness**: Good - Detects moderate AI patterns

---

### Step 4.5: Sentence Rewriting

- **Status**: SUCCESS
- **Risk Score**: 80/100
- **Risk Level**: high
- **Issues Found**: 1
- **Processing Time**: 3ms

**Detected Issues:**
- 15 sentences need opener diversification

**Recommendations:**
- Transform sentence openers using prepositional phrases, adverbs, or subordinate clauses.
- Add passive voice sentences for variety (target: 15-25%).

**DE-AIGC Effectiveness**: Excellent - Correctly identifies high AI risk

---

## Layer 1 - Lexical Level

### Step 5.0: Lexical Context

- **Status**: SUCCESS
- **Risk Score**: 20/100
- **Risk Level**: low
- **Issues Found**: 0
- **Processing Time**: 4ms

**Recommendations:**
- Lexical context prepared successfully.

**DE-AIGC Effectiveness**: Fair - Some detection capability

---

### Step 5.1: Fingerprint Detection

- **Status**: SUCCESS
- **Risk Score**: 85/100
- **Risk Level**: high
- **Issues Found**: 3
- **Processing Time**: 5ms

**Detected Issues:**
- 13 dead giveaway words found (delve, pivotal, etc.)
- 14 academic clichés found
- 1 fingerprint phrases found

**Recommendations:**
- CRITICAL: Remove or replace dead giveaway words immediately.
- Replace academic clichés with more specific, natural alternatives.
- Rewrite phrases to avoid AI detection patterns.

**DE-AIGC Effectiveness**: Excellent - Correctly identifies high AI risk

---

### Step 5.2: Human Feature

- **Status**: SUCCESS
- **Risk Score**: 87/100
- **Risk Level**: high
- **Issues Found**: 1
- **Processing Time**: 5ms

**Detected Issues:**
- Human academic phrase usage is low (0%)

**Recommendations:**
- Add academic adjectives like: associated, specific, empirical, consistent, preliminary
- Add academic phrases like: results indicate, in contrast to, to our knowledge

**DE-AIGC Effectiveness**: Excellent - Correctly identifies high AI risk

---

### Step 5.3: Replacement Generation

- **Status**: SUCCESS
- **Risk Score**: 70/100
- **Risk Level**: high
- **Issues Found**: 1
- **Processing Time**: 4ms

**Detected Issues:**
- 27 fingerprint words can be replaced

**Recommendations:**
- Replace 27 fingerprint words with suggested alternatives.
- Replace 'pivotal' with 'key'
- Replace 'pivotal' with 'key'

**DE-AIGC Effectiveness**: Excellent - Correctly identifies high AI risk

---

### Step 5.4: Paragraph Rewriting

- **Status**: SUCCESS
- **Risk Score**: 30/100
- **Risk Level**: low
- **Issues Found**: 0
- **Processing Time**: 4ms

**Recommendations:**
- Applied 27 word replacements.
- All 0 locked terms preserved.

**DE-AIGC Effectiveness**: Fair - Some detection capability

---

### Step 5.5: Validation

- **Status**: SUCCESS
- **Risk Score**: 100/100
- **Risk Level**: medium
- **Issues Found**: 1
- **Processing Time**: 4ms

**Detected Issues:**
- Risk score did not improve

**Recommendations:**
- Final fingerprint count: 21 (was 21)

**DE-AIGC Effectiveness**: Excellent - Correctly identifies high AI risk

---

## Conclusion | 结论

The DE-AIGC system demonstrates **excellent** performance. Most substeps executed successfully, and the test document (known to contain AI-generated content) was correctly identified with multiple high-risk flags.

DE-AIGC系统表现**优秀**。大多数子步骤执行成功，测试文档（已知包含AI生成内容）被正确识别，显示多个高风险标记。

*Report generated at 2026-01-08 21:04:18*
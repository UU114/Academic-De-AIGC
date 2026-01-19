# Substep Statistics Data Source Analysis
# 子步骤统计数据来源分析

> Generated: 2026-01-14
> Purpose: Analyze which statistics in substep handlers can be replaced with rule-based parsing
> 目的：分析子步骤处理器中哪些统计数据可以用规则解析替代

---

## Executive Summary / 执行摘要

| Category / 分类 | Count / 数量 | Percentage / 百分比 |
|-----------------|--------------|---------------------|
| Total Substeps / 总子步骤 | 29 | 100% |
| Fully LLM-dependent / 完全依赖LLM | 24 | 83% |
| Partially rule-based / 部分规则化 | 5 | 17% |
| Fully rule-based / 完全规则化 | 0 | 0% |

**Key Finding / 关键发现**: Most statistics are calculated by LLM, but many can be replaced with existing rule-based functions.
**关键发现**：大部分统计数据由LLM计算，但许多可以用已有的规则解析函数替代。

---

## Part 1: Statistics Required by Each Substep Handler
## 第一部分：每个子步骤处理器需要的统计数据

### Layer 5 (Document Level / 文档级)

#### Step 1.1: Structure Framework Detection / 结构框架检测
| Statistic | LLM | Rule-based Available | Priority |
|-----------|-----|---------------------|----------|
| paragraph_count | ✅ | ✅ `_split_paragraphs()` | ⭐⭐⭐⭐⭐ |
| word_count | ✅ | ✅ Simple `len(text.split())` | ⭐⭐⭐⭐⭐ |
| section_distribution | ✅ | ✅ `_calculate_section_distribution()` | ⭐⭐⭐⭐⭐ |
| CV (paragraph length) | ✅ | ✅ `calculate_cv()` | ⭐⭐⭐⭐⭐ |
| section_uniformity | ✅ | ⚠️ Can calculate from distribution | ⭐⭐⭐⭐ |

#### Step 1.2: Paragraph Length Regularity / 段落长度规律性 ✅ ALREADY FIXED
| Statistic | LLM | Rule-based Available | Priority |
|-----------|-----|---------------------|----------|
| paragraph_count | ❌ | ✅ `_split_paragraphs()` | ⭐⭐⭐⭐⭐ |
| paragraph_lengths | ❌ | ✅ Calculated from paragraphs | ⭐⭐⭐⭐⭐ |
| mean_length | ❌ | ✅ `statistics.mean()` | ⭐⭐⭐⭐⭐ |
| stdev_length | ❌ | ✅ `statistics.stdev()` | ⭐⭐⭐⭐⭐ |
| CV | ❌ | ✅ `calculate_cv()` | ⭐⭐⭐⭐⭐ |
| min/max_length | ❌ | ✅ `min()/max()` | ⭐⭐⭐⭐⭐ |
| section_distribution | ❌ | ✅ `_calculate_section_distribution()` | ⭐⭐⭐⭐⭐ |

#### Step 1.3: Progression Pattern & Closure / 推进模式与闭合
| Statistic | LLM | Rule-based Available | Priority |
|-----------|-----|---------------------|----------|
| paragraph_count | ✅ | ✅ `_split_paragraphs()` | ⭐⭐⭐⭐⭐ |
| progression_pattern | ✅ | ❌ Requires semantic analysis | ⭐ |
| closure_strength | ✅ | ❌ Requires semantic analysis | ⭐ |

#### Step 1.4: Anchor Density / 锚点密度
| Statistic | LLM | Rule-based Available | Priority |
|-----------|-----|---------------------|----------|
| anchor_count | ✅ | ✅ `analyze_document_anchors()` | ⭐⭐⭐⭐ |
| anchor_density | ✅ | ✅ `analyze_paragraph_anchors()` | ⭐⭐⭐⭐ |
| anchor_types | ✅ | ✅ Regex patterns available | ⭐⭐⭐⭐ |
| high_risk_paragraphs | ✅ | ✅ `has_hallucination_risk()` | ⭐⭐⭐⭐ |

#### Step 1.5: Content Substantiality / 内容实质性
| Statistic | LLM | Rule-based Available | Priority |
|-----------|-----|---------------------|----------|
| generalization_count | ✅ | ⚠️ Pattern matching possible | ⭐⭐⭐ |
| filler_word_count | ✅ | ⚠️ Word list matching possible | ⭐⭐⭐ |
| specificity_score | ✅ | ❌ Requires semantic analysis | ⭐ |

---

### Layer 4 (Section Level / 章节级)

#### Step 2.0: Section Identification / 章节识别
| Statistic | LLM | Rule-based Available | Priority |
|-----------|-----|---------------------|----------|
| section_boundaries | ✅ | ✅ `_calculate_section_distribution()` | ⭐⭐⭐⭐⭐ |
| paragraph_count | ✅ | ✅ From distribution | ⭐⭐⭐⭐⭐ |
| word_count | ✅ | ✅ From distribution | ⭐⭐⭐⭐⭐ |
| section_roles | ✅ | ✅ `_detect_paragraph_role()` | ⭐⭐⭐⭐ |

#### Step 2.1: Section Order Analysis / 章节顺序分析
| Statistic | LLM | Rule-based Available | Priority |
|-----------|-----|---------------------|----------|
| detected_sections | ✅ | ✅ Chain-call from 2.0 | ⭐⭐⭐⭐⭐ |
| order_matching_score | ✅ | ⚠️ Template matching possible | ⭐⭐⭐ |
| function_fusion_score | ✅ | ❌ Requires semantic analysis | ⭐ |

#### Step 2.2: Section Length Analysis / 章节长度分析
| Statistic | LLM | Rule-based Available | Priority |
|-----------|-----|---------------------|----------|
| paragraph_count_cv | ✅ | ✅ `calculate_cv()` | ⭐⭐⭐⭐⭐ |
| word_count_cv | ✅ | ✅ `calculate_cv()` | ⭐⭐⭐⭐⭐ |
| section_length_distribution | ✅ | ✅ From section data | ⭐⭐⭐⭐⭐ |
| is_discussion_longest | ✅ | ✅ Simple comparison | ⭐⭐⭐⭐ |
| is_conclusion_shortest | ✅ | ✅ Simple comparison | ⭐⭐⭐⭐ |

#### Step 2.3: Internal Structure Similarity / 内部结构相似性
| Statistic | LLM | Rule-based Available | Priority |
|-----------|-----|---------------------|----------|
| similarity_matrix | ✅ | ⚠️ `_calculate_sequence_similarity()` | ⭐⭐⭐ |
| heading_depth_variance | ✅ | ⚠️ Can parse heading levels | ⭐⭐⭐ |
| argument_density_cv | ✅ | ❌ Requires semantic analysis | ⭐ |

#### Step 2.4: Section Transition Analysis / 章节衔接分析
| Statistic | LLM | Rule-based Available | Priority |
|-----------|-----|---------------------|----------|
| explicit_transition_count | ✅ | ✅ `detect_connectors()` | ⭐⭐⭐⭐ |
| semantic_echo_score | ✅ | ❌ Requires semantic analysis | ⭐ |
| transition_strength | ✅ | ⚠️ Pattern matching possible | ⭐⭐⭐ |

#### Step 2.5: Inter-Section Logic Analysis / 章节间逻辑分析
| Statistic | LLM | Rule-based Available | Priority |
|-----------|-----|---------------------|----------|
| argument_chain_score | ✅ | ❌ Requires semantic analysis | ⭐ |
| redundancy_detection | ✅ | ❌ Requires semantic analysis | ⭐ |
| linearity_score | ✅ | ❌ Requires semantic analysis | ⭐ |

---

### Layer 3 (Paragraph Level / 段落级)

#### Step 3.0: Paragraph Identification / 段落识别
| Statistic | LLM | Rule-based Available | Priority |
|-----------|-----|---------------------|----------|
| paragraph_boundaries | ✅ | ✅ `_split_paragraphs()` | ⭐⭐⭐⭐⭐ |
| word_count | ✅ | ✅ Simple calculation | ⭐⭐⭐⭐⭐ |
| sentence_count | ✅ | ✅ `_count_sentences()` | ⭐⭐⭐⭐⭐ |
| is_body | ✅ | ✅ Pattern matching | ⭐⭐⭐⭐ |

#### Step 3.1: Paragraph Role Detection / 段落功能角色检测
| Statistic | LLM | Rule-based Available | Priority |
|-----------|-----|---------------------|----------|
| role_uniformity_score | ✅ | ⚠️ Can calculate if roles known | ⭐⭐⭐ |
| role_distribution | ✅ | ⚠️ `_detect_paragraph_role()` | ⭐⭐⭐ |
| missing_roles | ✅ | ⚠️ Can detect from distribution | ⭐⭐⭐ |

#### Step 3.2: Internal Coherence Analysis / 段落内部连贯性
| Statistic | LLM | Rule-based Available | Priority |
|-----------|-----|---------------------|----------|
| sentence_length_cv | ✅ | ✅ `_calculate_length_cv()` | ⭐⭐⭐⭐⭐ |
| connector_density | ✅ | ✅ `detect_connectors()` | ⭐⭐⭐⭐ |
| first_person_ratio | ✅ | ✅ Regex pattern | ⭐⭐⭐⭐ |
| topic_diversity_score | ✅ | ❌ Requires semantic analysis | ⭐ |

#### Step 3.3: Anchor Density Analysis / 锚点密度分析
| Statistic | LLM | Rule-based Available | Priority |
|-----------|-----|---------------------|----------|
| anchor_count_per_para | ✅ | ✅ `analyze_paragraph_anchors()` | ⭐⭐⭐⭐ |
| anchor_density | ✅ | ✅ Calculation from count/words | ⭐⭐⭐⭐ |
| anchor_type_distribution | ✅ | ✅ Regex patterns | ⭐⭐⭐⭐ |
| hallucination_risk | ✅ | ✅ `has_hallucination_risk()` | ⭐⭐⭐⭐ |

#### Step 3.4: Sentence Length Distribution / 句子长度分布
| Statistic | LLM | Rule-based Available | Priority |
|-----------|-----|---------------------|----------|
| sentence_lengths | ✅ | ✅ `_identify_sentences_in_paragraph()` | ⭐⭐⭐⭐⭐ |
| mean_length | ✅ | ✅ `statistics.mean()` | ⭐⭐⭐⭐⭐ |
| std_length | ✅ | ✅ `statistics.stdev()` | ⭐⭐⭐⭐⭐ |
| CV | ✅ | ✅ `_calculate_length_cv()` | ⭐⭐⭐⭐⭐ |
| burstiness_score | ✅ | ✅ `analyze_burstiness()` | ⭐⭐⭐⭐ |
| short_sentence_count | ✅ | ✅ Filter by length | ⭐⭐⭐⭐ |
| long_sentence_count | ✅ | ✅ Filter by length | ⭐⭐⭐⭐ |

#### Step 3.5: Paragraph Transition Analysis / 段落衔接分析
| Statistic | LLM | Rule-based Available | Priority |
|-----------|-----|---------------------|----------|
| explicit_connector_count | ✅ | ✅ `detect_connectors()` | ⭐⭐⭐⭐ |
| explicit_ratio | ✅ | ✅ Calculation | ⭐⭐⭐⭐ |
| opening_formulaic | ✅ | ⚠️ Pattern matching possible | ⭐⭐⭐ |
| semantic_echo_score | ✅ | ❌ Requires semantic analysis | ⭐ |

---

### Layer 2 (Sentence Level / 句子级)

#### Step 4.0: Sentence Identification / 句子识别
| Statistic | LLM | Rule-based Available | Priority |
|-----------|-----|---------------------|----------|
| sentence_count | ✅ | ✅ `_count_sentences()` | ⭐⭐⭐⭐⭐ |
| sentence_type_distribution | ✅ | ✅ `_classify_sentence_type()` | ⭐⭐⭐⭐ |
| function_role_distribution | ✅ | ⚠️ Partial pattern matching | ⭐⭐⭐ |
| clause_depth | ✅ | ✅ `_count_clause_depth()` | ⭐⭐⭐⭐ |
| passive_voice_percentage | ✅ | ✅ `_detect_voice()` | ⭐⭐⭐⭐ |

#### Step 4.1: Sentence Pattern Detection / 句式模式检测
| Statistic | LLM | Rule-based Available | Priority |
|-----------|-----|---------------------|----------|
| sentence_type_percentages | ✅ | ✅ From classification | ⭐⭐⭐⭐ |
| opener_word_repetition | ✅ | ✅ `_get_opener_word()` | ⭐⭐⭐⭐ |
| subject_first_ratio | ✅ | ⚠️ Pattern matching possible | ⭐⭐⭐ |
| voice_distribution | ✅ | ✅ `_detect_voice()` | ⭐⭐⭐⭐ |
| syntactic_void_count | ✅ | ✅ `detect_syntactic_voids()` | ⭐⭐⭐⭐ |
| parallel_structure_count | ✅ | ⚠️ Pattern matching possible | ⭐⭐⭐ |

#### Step 4.2: In-Paragraph Length Analysis / 段落内句子长度分析
| Statistic | LLM | Rule-based Available | Priority |
|-----------|-----|---------------------|----------|
| per_paragraph_cv | ✅ | ✅ `_calculate_length_cv()` | ⭐⭐⭐⭐⭐ |
| length_distribution | ✅ | ✅ Classification by thresholds | ⭐⭐⭐⭐⭐ |
| merge_candidates | ✅ | ⚠️ Rule-based identification | ⭐⭐⭐ |
| split_candidates | ✅ | ✅ Filter by length > 45 | ⭐⭐⭐⭐ |

#### Step 4.3: Sentence Merge Suggestions / 句子合并建议
| Statistic | LLM | Rule-based Available | Priority |
|-----------|-----|---------------------|----------|
| merge_candidate_count | ✅ | ⚠️ Can identify short adjacent | ⭐⭐⭐ |
| fragmentation_score | ✅ | ✅ Short sentence ratio | ⭐⭐⭐⭐ |
| short_sentence_ratio | ✅ | ✅ Filter and count | ⭐⭐⭐⭐ |
| merge_type | ✅ | ❌ Requires semantic analysis | ⭐ |

#### Step 4.4: Connector Optimization / 连接词优化
| Statistic | LLM | Rule-based Available | Priority |
|-----------|-----|---------------------|----------|
| connector_instances | ✅ | ✅ `detect_connectors()` | ⭐⭐⭐⭐ |
| connector_type_count | ✅ | ✅ Classification available | ⭐⭐⭐⭐ |
| connector_density | ✅ | ✅ Calculation | ⭐⭐⭐⭐ |
| repeated_connectors | ✅ | ✅ Count duplicates | ⭐⭐⭐⭐ |
| sequential_patterns | ✅ | ✅ Pattern matching | ⭐⭐⭐⭐ |

#### Step 4.5: Sentence Rewriting / 句子改写
| Statistic | LLM | Rule-based Available | Priority |
|-----------|-----|---------------------|----------|
| simple_sentence_ratio | ✅ | ✅ From classification | ⭐⭐⭐⭐ |
| compound_sentence_ratio | ✅ | ✅ From classification | ⭐⭐⭐⭐ |
| opener_diversity | ✅ | ✅ From opener analysis | ⭐⭐⭐⭐ |
| voice_balance | ✅ | ✅ From voice analysis | ⭐⭐⭐⭐ |
| length_cv | ✅ | ✅ `_calculate_length_cv()` | ⭐⭐⭐⭐⭐ |

---

### Layer 1 (Lexical Level / 词汇级)

#### Step 5.0: Lexical Context Preparation / 词汇环境准备
| Statistic | LLM | Rule-based Available | Priority |
|-----------|-----|---------------------|----------|
| total_word_count | ✅ | ✅ Simple `len(text.split())` | ⭐⭐⭐⭐⭐ |
| unique_word_count | ✅ | ✅ `len(set(words))` | ⭐⭐⭐⭐⭐ |
| lexical_richness | ✅ | ✅ unique/total | ⭐⭐⭐⭐⭐ |
| TTR | ✅ | ✅ Same as richness | ⭐⭐⭐⭐⭐ |
| top_20_frequent_words | ✅ | ✅ `Counter` | ⭐⭐⭐⭐⭐ |
| overused_words | ✅ | ✅ Filter by frequency | ⭐⭐⭐⭐ |

#### Step 5.1: Fingerprint Detection / 指纹检测
| Statistic | LLM | Rule-based Available | Priority |
|-----------|-----|---------------------|----------|
| type_a_count (dead giveaways) | ✅ | ✅ `detect_fingerprints()` | ⭐⭐⭐⭐⭐ |
| type_b_count (clichés) | ✅ | ✅ `detect_fingerprints()` | ⭐⭐⭐⭐⭐ |
| type_c_count (padding) | ✅ | ✅ `detect_fingerprints()` | ⭐⭐⭐⭐⭐ |
| fingerprint_density | ✅ | ✅ Calculation | ⭐⭐⭐⭐⭐ |
| ppl_score | ✅ | ✅ `calculate_onnx_ppl()` | ⭐⭐⭐ |

#### Step 5.2: Human Feature Analysis / 人类特征分析
| Statistic | LLM | Rule-based Available | Priority |
|-----------|-----|---------------------|----------|
| human_feature_count | ✅ | ⚠️ Pattern matching possible | ⭐⭐⭐ |
| feature_density | ✅ | ⚠️ If features detected | ⭐⭐⭐ |
| missing_features | ✅ | ⚠️ If features detected | ⭐⭐⭐ |

#### Step 5.3: Replacement Generation / 替换词生成
| Statistic | LLM | Rule-based Available | Priority |
|-----------|-----|---------------------|----------|
| replacement_candidate_count | ✅ | ⚠️ From fingerprints | ⭐⭐⭐ |
| category_counts | ✅ | ⚠️ Classification possible | ⭐⭐⭐ |

#### Step 5.4: Paragraph Rewriting / 段落改写
| Statistic | LLM | Rule-based Available | Priority |
|-----------|-----|---------------------|----------|
| fingerprint_density | ✅ | ✅ From fingerprint detection | ⭐⭐⭐⭐ |
| lexical_diversity_score | ✅ | ✅ From TTR | ⭐⭐⭐⭐ |
| paragraphs_needing_rewrite | ✅ | ✅ Filter by threshold | ⭐⭐⭐⭐ |

#### Step 5.5: Validation / 验证
| Statistic | LLM | Rule-based Available | Priority |
|-----------|-----|---------------------|----------|
| locked_term_integrity | ✅ | ✅ String matching | ⭐⭐⭐⭐⭐ |
| final_ai_risk_score | ✅ | ⚠️ Composite calculation | ⭐⭐⭐ |
| improvement_amount | ✅ | ✅ Simple subtraction | ⭐⭐⭐⭐ |
| semantic_similarity | ✅ | ❌ Requires embedding model | ⭐ |

---

## Part 2: Available Rule-Based Functions
## 第二部分：可用的规则解析函数

### Category 1: Paragraph Parsing / 段落解析
| Function | Location | Description |
|----------|----------|-------------|
| `_split_paragraphs()` | `document.py:445` | Split text into paragraphs, filter non-body |
| `_split_text_to_paragraphs()` | `paragraph.py:176` | Similar, with non-body filtering |
| `_calculate_section_distribution()` | `document.py:512` | Calculate section distribution from text |
| `_get_paragraphs()` | Multiple files | Extract paragraphs from request |

### Category 2: Sentence Parsing / 句子解析
| Function | Location | Description |
|----------|----------|-------------|
| `_identify_sentences_in_paragraph()` | `sentence.py:658` | Identify and annotate sentences |
| `_classify_sentence_type()` | `sentence.py:490` | Classify as simple/compound/complex |
| `_detect_voice()` | `sentence.py:519` | Detect active/passive voice |
| `_get_opener_word()` | `sentence.py:540` | Get first word of sentence |
| `_count_clause_depth()` | `sentence.py:549` | Estimate clause nesting depth |
| `_count_sentences()` | `document.py:722` | Count sentences in text |

### Category 3: Statistics Calculation / 统计计算
| Function | Location | Description |
|----------|----------|-------------|
| `_calculate_length_cv()` | `sentence.py:562` | Calculate length CV |
| `calculate_cv()` | `risk_calculator.py:439` | Generic CV calculation |
| `analyze_paragraph_lengths()` | `paragraph_length_analyzer.py:33` | Full paragraph length analysis |
| `calculate_entropy()` | `risk_calculator.py:465` | Calculate distribution entropy |

### Category 4: Connector/Keyword Detection / 连接词/关键词检测
| Function | Location | Description |
|----------|----------|-------------|
| `detect_connectors()` | `connector_detector.py:384` | Detect connectors in text |
| `check_sentence_connector()` | `connector_detector.py:402` | Check single sentence connector |
| `_detect_explicit_connectors()` | `sentence.py:576` | Detect explicit connectors |
| `_extract_keywords()` | `section.py:685` | Extract important keywords |

### Category 5: Anchor/Fingerprint Detection / 锚点/指纹检测
| Function | Location | Description |
|----------|----------|-------------|
| `analyze_paragraph_anchors()` | `anchor_density.py:409` | Analyze paragraph anchors |
| `analyze_document_anchors()` | `anchor_density.py:418` | Analyze document anchors |
| `has_hallucination_risk()` | `anchor_density.py:427` | Check hallucination risk |
| `detect_fingerprints()` | `fingerprint.py:624` | Detect AI fingerprints |
| `detect_syntactic_voids()` | `syntactic_void.py:452` | Detect syntactic voids |

### Category 6: Risk Calculation / 风险计算
| Function | Location | Description |
|----------|----------|-------------|
| `_calculate_risk_score()` | `sentence.py:598` | Calculate overall risk score |
| `_get_risk_level()` | `sentence.py:645` | Convert score to level |
| `determine_risk_level()` | `risk_calculator.py:42` | Determine risk level |
| `determine_indicator_status()` | `risk_calculator.py:69` | Determine indicator status |

### Category 7: Burstiness Analysis / 突发性分析
| Function | Location | Description |
|----------|----------|-------------|
| `analyze_burstiness()` | `burstiness.py:299` | Analyze sentence burstiness |
| `analyze_text_burstiness()` | `burstiness.py:313` | Analyze text burstiness |

---

## Part 3: Recommended Implementation Priority
## 第三部分：推荐实现优先级

### High Priority (⭐⭐⭐⭐⭐) - Implement First
These statistics have ready-to-use functions and provide accurate results:

| Step | Statistics to Pre-calculate |
|------|---------------------------|
| 1.1 | paragraph_count, word_count, section_distribution, CV |
| 1.4 | anchor_count, anchor_density, anchor_types |
| 2.0 | section_boundaries, paragraph_count, word_count |
| 2.2 | paragraph_count_cv, word_count_cv |
| 3.0 | paragraph_boundaries, word_count, sentence_count |
| 3.3 | anchor_count_per_para, anchor_density |
| 3.4 | sentence_lengths, mean, stdev, CV, burstiness |
| 4.0 | sentence_count, sentence_type_distribution, voice |
| 4.2 | per_paragraph_cv, length_distribution |
| 4.4 | connector_instances, connector_density |
| 5.0 | word_count, unique_count, TTR, frequency |
| 5.1 | fingerprint counts (type A/B/C) |

### Medium Priority (⭐⭐⭐⭐) - Implement Second
These require some additional implementation but are feasible:

| Step | Statistics to Pre-calculate |
|------|---------------------------|
| 1.5 | filler_word_count (need word list) |
| 2.4 | explicit_transition_count |
| 3.2 | connector_density, first_person_ratio |
| 3.5 | explicit_connector_count, explicit_ratio |
| 4.1 | opener_word_repetition, syntactic_void_count |
| 4.3 | short_sentence_ratio |
| 5.4 | paragraphs_needing_rewrite |

### Low Priority (⭐⭐⭐) - Keep LLM for These
These require semantic understanding and should remain LLM-based:

- Progression/closure pattern detection
- Semantic echo scoring
- Argument chain analysis
- Content specificity evaluation
- Human feature identification
- Semantic similarity calculation

---

## Part 4: Implementation Template
## 第四部分：实现模板

Example pattern (based on Step 1.2 fix):

```python
# In route file (e.g., document.py)
async def analyze_xxx(request: XxxRequest):
    # =====================================================================
    # STEP 1: Calculate statistics from text FIRST (accurate data)
    # 第一步：先从文本计算统计数据（准确数据）
    # =====================================================================

    # Use existing parsing functions
    paragraphs = _split_paragraphs(request.text, exclude_non_body=True)
    para_count = len(paragraphs)
    lengths = [len(p.split()) for p in paragraphs]

    # Calculate statistics
    mean_len = statistics.mean(lengths) if lengths else 0
    stdev_len = statistics.stdev(lengths) if len(lengths) > 1 else 0
    cv = stdev_len / mean_len if mean_len > 0 else 0

    # =====================================================================
    # STEP 2: Pass parsed statistics to LLM for analysis/decision
    # 第二步：将解析的统计数据传递给LLM进行分析/决策
    # =====================================================================
    parsed_statistics = {
        "paragraph_count": para_count,
        "lengths": lengths,
        "mean_length": round(mean_len, 1),
        "stdev_length": round(stdev_len, 1),
        "cv": round(cv, 3),
    }

    result = await handler.analyze(
        document_text=request.text,
        parsed_statistics=json.dumps(parsed_statistics, indent=2),
        cv=round(cv, 3)
    )

    # =====================================================================
    # STEP 3: Return response using CALCULATED statistics (not LLM's)
    # 第三步：返回响应时使用计算的统计数据（而非LLM的）
    # =====================================================================
    return XxxResponse(
        paragraph_count=para_count,  # From calculation
        mean_length=round(mean_len, 1),  # From calculation
        issues=result.get("issues", []),  # From LLM analysis
        recommendations=result.get("recommendations", []),  # From LLM
    )
```

---

## Conclusion / 结论

**Current State / 当前状态**:
- 83% of substeps fully depend on LLM for statistics
- Many existing rule-based functions are available but not used

**Recommended Action / 建议行动**:
1. Apply Step 1.2 pattern to all high-priority substeps
2. Pre-calculate statistics using existing functions
3. Pass accurate statistics to LLM for analysis/decision only
4. Return calculated statistics in response (not LLM's)

**Expected Benefits / 预期收益**:
- More accurate statistics display
- Consistent data across UI components
- Reduced LLM hallucination in statistics
- Better debugging and troubleshooting

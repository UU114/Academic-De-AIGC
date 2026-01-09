/**
 * 5-Layer Analysis Components
 * 5层分析组件
 *
 * Step 1.0: Term Lock (词汇锁定) - Lock professional terms before processing
 * Layer 5: Document (文章层) - Structure analysis, global risk
 *   - Step 1.1: Section Structure & Order (章节结构与顺序)
 *   - Step 1.2: Section Uniformity (章节均匀性)
 *   - Step 1.3: Section Logic Pattern (章节逻辑模式)
 *   - Step 1.4: Paragraph Length Uniformity (段落长度均匀性)
 *   - Step 1.5: Paragraph Transition (段落过渡)
 * Layer 4: Section (章节层) - Logic flow, transitions, length
 *   - Step 2.0: Section Identification (章节识别与角色标注)
 *   - Step 2.1: Section Order & Structure (章节顺序与结构)
 *   - Step 2.2: Section Length Distribution (章节长度分布)
 *   - Step 2.3: Internal Structure Similarity (章节内部结构相似性) - NEW
 *   - Step 2.4: Section Transition (章节衔接与过渡)
 *   - Step 2.5: Inter-Section Logic (章节间逻辑关系)
 * Layer 3: Paragraph (段落层) - Roles, coherence, anchors, sentence length
 *   - Step 3.0: Paragraph Identification (段落识别与分割)
 *   - Step 3.1: Paragraph Role Detection (段落角色识别)
 *   - Step 3.2: Internal Coherence (段落内部连贯性)
 *   - Step 3.3: Anchor Density (锚点密度分析)
 *   - Step 3.4: Sentence Length Distribution (句子长度分布)
 *   - Step 3.5: Paragraph Transition (段落过渡分析)
 * Layer 2: Sentence (句子层) - Patterns, voids, roles, polish context
 * Layer 1: Lexical (词汇层) - Fingerprints, connectors, word risk
 */

// Step 1.0: Term Lock
export { default as LayerTermLock } from './LayerTermLock';

// Layer 5 Sub-steps (Document Level)
export { default as LayerStep1_1 } from './LayerStep1_1';
export { default as LayerStep1_2 } from './LayerStep1_2';
export { default as LayerStep1_3 } from './LayerStep1_3';
export { default as LayerStep1_4 } from './LayerStep1_4';
export { default as LayerStep1_5 } from './LayerStep1_5';

// Layer 4 Sub-steps (Section Level)
export { default as LayerStep2_0 } from './LayerStep2_0';
export { default as LayerStep2_1 } from './LayerStep2_1';
export { default as LayerStep2_2 } from './LayerStep2_2';
export { default as LayerStep2_3 } from './LayerStep2_3';
export { default as LayerStep2_4 } from './LayerStep2_4';
export { default as LayerStep2_5 } from './LayerStep2_5';

// Layer 3 Sub-steps (Paragraph Level)
export { default as LayerStep3_0 } from './LayerStep3_0';
export { default as LayerStep3_1 } from './LayerStep3_1';
export { default as LayerStep3_2 } from './LayerStep3_2';
export { default as LayerStep3_3 } from './LayerStep3_3';
export { default as LayerStep3_4 } from './LayerStep3_4';
export { default as LayerStep3_5 } from './LayerStep3_5';

// Layer 2 Sub-steps (Sentence Level)
export { default as LayerStep4_0 } from './LayerStep4_0';
export { default as LayerStep4_1 } from './LayerStep4_1';
export { default as LayerStep4_Console } from './LayerStep4_Console';

// Legacy combined document layer (kept for backward compatibility)
export { default as LayerDocument } from './LayerDocument';

// Layer 1 Sub-steps (Lexical Level)
// Layer 1 子步骤（词汇层面）
export { default as LayerLexicalV2 } from './LayerLexicalV2';

// Other layers
export { default as LayerSection } from './LayerSection';
export { default as LayerParagraph } from './LayerParagraph';
export { default as LayerSentence } from './LayerSentence';
export { default as LayerLexical } from './LayerLexical';

# AcademicGuard 技术架构文档
# AcademicGuard Technical Architecture Document

> 版本 Version: v1.0
> 状态 Status: 初始设计 / Initial Design
> 创建日期 Created: 2024-12-29

---

## 一、系统架构概览 | System Architecture Overview

### 1.1 整体架构图 | Overall Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              客户端 Client                                   │
│                         React + TailwindCSS + Vite                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                              API网关 API Gateway                             │
│                              FastAPI + Uvicorn                               │
├───────────────┬───────────────┬───────────────┬─────────────────────────────┤
│   预处理服务   │   分析引擎    │   建议引擎     │       验证服务              │
│  Preprocessor │   Analyzer    │  Suggester    │      Validator              │
│               │               │               │                             │
│ • 文本分句    │ • PPL计算     │ • LLM轨道(A)  │ • 语义相似度                │
│ • 术语锁定    │ • 指纹词检测  │ • 规则轨道(B) │ • 术语完整性                │
│ • 格式清洗    │ • 结构分析    │ • 建议合并    │ • 风险复检                  │
│               │ • 风险评分    │               │                             │
├───────────────┴───────────────┴───────────────┴─────────────────────────────┤
│                              NLP核心层 NLP Core                              │
│                    spaCy + Stanza + Transformers + SentenceBERT             │
├───────────────┬───────────────┬───────────────┬─────────────────────────────┤
│  LLM服务层    │  ML模型层     │   数据资源层   │       缓存层                │
│  LLM Service  │  ML Models    │  Data Assets  │      Cache                  │
│               │               │               │                             │
│ • Claude API  │ • BERT MLM    │ • 指纹词库    │ • Redis                     │
│ • OpenAI API  │ • PPL Model   │ • 同义词典    │ • LLM响应缓存               │
│ • Fallback    │ • Sent-BERT   │ • 术语白名单  │ • 分析结果缓存              │
├───────────────┴───────────────┴───────────────┴─────────────────────────────┤
│                              数据持久层 Persistence                          │
│                           SQLite (MVP) / PostgreSQL                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 核心数据流 | Core Data Flow

```
用户输入文本 User Input
       │
       ▼
┌──────────────────┐
│   预处理服务      │
│   Preprocessor   │
│                  │
│  1. 分句         │
│  2. 术语识别     │
│  3. 格式清洗     │
└────────┬─────────┘
         │
         ▼ 句子列表 + 锁定术语
┌──────────────────┐
│   分析引擎       │
│   Analyzer       │
│                  │
│  1. PPL计算      │
│  2. 指纹词检测   │
│  3. 结构分析     │
│  4. 风险评分     │
└────────┬─────────┘
         │
         ▼ 风险报告 (每句)
┌──────────────────┐
│   模式分流器     │
│   Mode Router    │
│                  │
│  YOLO? 干预?    │
└────────┬─────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌────────┐
│ YOLO   │ │ 干预   │
│ 模式   │ │ 模式   │
└───┬────┘ └───┬────┘
    │          │
    ▼          ▼
┌──────────────────┐
│   建议引擎       │
│   Suggester      │
│                  │
│  ┌─────┐ ┌─────┐│
│  │LLM-A│ │Rule-B││
│  └──┬──┘ └──┬──┘│
│     └───┬───┘   │
│         ▼       │
│    建议合并     │
└────────┬────────┘
         │
         ▼ 双轨建议
┌──────────────────┐
│   用户决策       │   ← 干预模式: 用户选择
│   User Decision  │   ← YOLO模式: 自动选择最优
└────────┬─────────┘
         │
         ▼ 选定的修改
┌──────────────────┐
│   验证服务       │
│   Validator      │
│                  │
│  1. 语义检查     │
│  2. 术语检查     │
│  3. 风险复检     │
└────────┬─────────┘
         │
    ┌────┴────┐
    ▼         ▼
  通过      未通过
   │          │
   ▼          ▼
 下一句    重新建议/人工标记
```

---

## 二、模块详细设计 | Module Design

### 2.1 预处理服务 | Preprocessor Service

```
preprocessor/
├── __init__.py
├── segmenter.py        # 文本分句
├── term_locker.py      # 术语锁定
├── cleaner.py          # 格式清洗
└── models.py           # 数据模型
```

#### 2.1.1 分句模块 | Segmenter

```python
# segmenter.py
class SentenceSegmenter:
    """
    Split text into sentences while preserving structure
    将文本分割为句子，同时保留结构信息
    """

    def __init__(self, lang: str = "en"):
        self.nlp = spacy.load("en_core_web_sm")

    def segment(self, text: str) -> List[Sentence]:
        """
        Segment text into sentences
        将文本分割为句子

        Returns:
            List of Sentence objects with position info
        """
        pass

    def merge_fragments(self, sentences: List[Sentence]) -> List[Sentence]:
        """
        Merge sentence fragments (e.g., citations, abbreviations)
        合并句子片段（如引用、缩写等导致的错误分割）
        """
        pass
```

#### 2.1.2 术语锁定模块 | Term Locker

```python
# term_locker.py
class TermLocker:
    """
    Identify and lock academic terms that should not be modified
    识别并锁定不应修改的学术术语
    """

    def __init__(self):
        self.whitelist = self._load_whitelist()
        self.ner_model = spacy.load("en_core_web_sm")

    def identify_terms(self, sentence: str) -> List[LockedTerm]:
        """
        Identify terms to lock using NER + whitelist
        使用NER和白名单识别需要锁定的术语
        """
        pass

    def mark_locked(self, sentence: str, terms: List[LockedTerm]) -> str:
        """
        Mark locked terms with special tokens
        用特殊标记标注锁定术语

        Example: "ANOVA test" -> "<LOCK>ANOVA</LOCK> test"
        """
        pass
```

### 2.2 分析引擎 | Analyzer Engine

```
analyzer/
├── __init__.py
├── perplexity.py       # PPL计算
├── fingerprint.py      # 指纹词检测
├── structure.py        # 结构分析
├── scorer.py           # 综合评分
└── detectors/
    ├── turnitin.py     # Turnitin视角分析
    └── gptzero.py      # GPTZero视角分析
```

#### 2.2.1 困惑度计算 | Perplexity Calculator

```python
# perplexity.py
class PerplexityCalculator:
    """
    Calculate perplexity score for AIGC detection
    计算困惑度分数用于AIGC检测
    """

    def __init__(self, model_name: str = "gpt2"):
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

    def calculate(self, text: str) -> float:
        """
        Calculate perplexity of text
        计算文本困惑度

        Lower PPL = more predictable = more likely AI-generated
        PPL越低 = 越可预测 = 越可能是AI生成
        """
        pass

    def calculate_sentence_ppl(self, sentence: str) -> SentencePPL:
        """
        Calculate PPL with risk assessment
        计算PPL并评估风险

        Returns:
            SentencePPL with value and risk_level
        """
        pass
```

#### 2.2.2 指纹词检测 | Fingerprint Detector

```python
# fingerprint.py
class FingerprintDetector:
    """
    Detect AI fingerprint words and phrases
    检测AI指纹词和短语
    """

    def __init__(self):
        self.fingerprints = self._load_fingerprint_db()

    def detect(self, sentence: str) -> List[FingerprintMatch]:
        """
        Detect fingerprint words in sentence
        检测句子中的指纹词

        Returns:
            List of matches with word, position, risk_weight
        """
        pass

    def calculate_density(self, sentence: str) -> float:
        """
        Calculate fingerprint density score
        计算指纹词密度分数
        """
        pass
```

#### 2.2.3 综合评分 | Risk Scorer

```python
# scorer.py
class RiskScorer:
    """
    Calculate comprehensive AIGC risk score
    计算综合AIGC风险分数
    """

    # Weight configuration
    # 权重配置
    WEIGHTS = {
        "perplexity": 0.35,
        "fingerprint": 0.30,
        "burstiness": 0.20,
        "structure": 0.15
    }

    def calculate(self, analysis: SentenceAnalysis) -> RiskScore:
        """
        Calculate weighted risk score
        计算加权风险分数

        Returns:
            RiskScore with value (0-100) and level (low/medium/high)
        """
        pass

    def generate_report(self, analysis: SentenceAnalysis) -> RiskReport:
        """
        Generate detailed risk report
        生成详细风险报告
        """
        pass
```

### 2.3 建议引擎 | Suggester Engine

```
suggester/
├── __init__.py
├── llm_track.py        # 轨道A: LLM建议
├── rule_track.py       # 轨道B: 规则建议
├── selector.py         # 建议选择器
├── prompts/
│   ├── humanize.py     # 人源化Prompt
│   └── styles.py       # 口语化风格Prompt
└── rules/
    ├── synonyms.py     # 同义词替换
    └── syntax.py       # 句法重组
```

#### 2.3.1 LLM轨道 | LLM Track

```python
# llm_track.py
class LLMTrack:
    """
    Track A: LLM-powered humanization suggestions
    轨道A: 基于LLM的人源化建议
    """

    def __init__(self, config: LLMConfig):
        self.client = self._init_client(config)
        self.prompt_builder = PromptBuilder()

    async def generate_suggestion(
        self,
        sentence: str,
        issues: List[Issue],
        locked_terms: List[str],
        colloquialism_level: int,
        target_lang: str = "zh"
    ) -> LLMSuggestion:
        """
        Generate humanization suggestion using LLM
        使用LLM生成人源化建议
        """
        prompt = self.prompt_builder.build(
            sentence=sentence,
            issues=issues,
            locked_terms=locked_terms,
            level=colloquialism_level,
            lang=target_lang
        )

        response = await self.client.complete(prompt)
        return self._parse_response(response)

    def _get_style_guide(self, level: int) -> str:
        """
        Get style guide based on colloquialism level
        根据口语化等级获取风格指南
        """
        pass
```

#### 2.3.2 规则轨道 | Rule Track

```python
# rule_track.py
class RuleTrack:
    """
    Track B: Rule-based humanization suggestions
    轨道B: 基于规则的人源化建议
    """

    def __init__(self, colloquialism_level: int = 4):
        self.level = colloquialism_level
        self.synonym_engine = SynonymEngine(level)
        self.syntax_engine = SyntaxEngine()
        self.bert_mlm = BertMLM()

    def generate_suggestion(
        self,
        sentence: str,
        issues: List[Issue],
        locked_terms: List[str]
    ) -> RuleSuggestion:
        """
        Generate humanization suggestion using rules
        使用规则生成人源化建议
        """
        suggestions = []

        # Synonym replacements
        # 同义词替换
        synonyms = self.synonym_engine.get_replacements(sentence, issues)
        suggestions.extend(synonyms)

        # Syntax restructuring
        # 句法重组
        syntax_opts = self.syntax_engine.get_options(sentence)
        suggestions.extend(syntax_opts)

        return RuleSuggestion(
            original=sentence,
            suggestions=suggestions,
            applied_result=self._apply_best(sentence, suggestions)
        )
```

#### 2.3.3 同义词引擎 | Synonym Engine

```python
# rules/synonyms.py
class SynonymEngine:
    """
    Context-aware synonym replacement engine
    上下文感知的同义词替换引擎
    """

    def __init__(self, colloquialism_level: int):
        self.level = colloquialism_level
        self.fingerprint_map = self._load_fingerprint_map()
        self.level_preferences = self._load_level_preferences()
        self.bert_mlm = pipeline("fill-mask", model="bert-base-uncased")

    def get_replacements(
        self,
        sentence: str,
        issues: List[Issue]
    ) -> List[SynonymSuggestion]:
        """
        Get synonym replacement suggestions
        获取同义词替换建议
        """
        suggestions = []

        for issue in issues:
            if issue.type == "fingerprint_word":
                # Get level-appropriate replacements
                # 获取适合当前等级的替换词
                replacements = self._get_level_appropriate(
                    issue.word,
                    self.level
                )

                # Enhance with BERT MLM context
                # 使用BERT MLM增强上下文相关性
                context_ranked = self._rank_by_context(
                    sentence,
                    issue.word,
                    replacements
                )

                suggestions.append(SynonymSuggestion(
                    original=issue.word,
                    position=issue.position,
                    options=context_ranked,
                    reason=f"AI fingerprint word detected"
                ))

        return suggestions

    def _rank_by_context(
        self,
        sentence: str,
        word: str,
        candidates: List[str]
    ) -> List[str]:
        """
        Rank candidates by contextual fit using BERT MLM
        使用BERT MLM按上下文适合度排序候选词
        """
        masked = sentence.replace(word, "[MASK]")
        predictions = self.bert_mlm(masked, top_k=20)

        # Score candidates based on BERT predictions
        # 根据BERT预测给候选词打分
        scored = []
        pred_words = [p["token_str"] for p in predictions]

        for candidate in candidates:
            if candidate.lower() in pred_words:
                score = pred_words.index(candidate.lower())
            else:
                score = 100  # Low priority
            scored.append((candidate, score))

        scored.sort(key=lambda x: x[1])
        return [s[0] for s in scored]
```

#### 2.3.4 句法重组引擎 | Syntax Engine

```python
# rules/syntax.py
class SyntaxEngine:
    """
    Syntactic restructuring engine
    句法重组引擎
    """

    def __init__(self):
        self.nlp = stanza.Pipeline("en")

    def get_options(self, sentence: str) -> List[SyntaxSuggestion]:
        """
        Generate syntactic restructuring options
        生成句法重组选项
        """
        doc = self.nlp(sentence)
        options = []

        # Active <-> Passive conversion
        # 主动被动转换
        if self._can_convert_voice(doc):
            converted = self._convert_voice(doc)
            options.append(SyntaxSuggestion(
                type="voice_conversion",
                result=converted,
                reason="Voice change adds variety"
            ))

        # Sentence splitting for long sentences
        # 长句拆分
        if len(sentence.split()) > 30:
            split = self._split_sentence(doc)
            if split:
                options.append(SyntaxSuggestion(
                    type="sentence_split",
                    result=split,
                    reason="Shorter sentences improve burstiness"
                ))

        # Clause reordering
        # 从句重排
        if self._has_movable_clause(doc):
            reordered = self._reorder_clause(doc)
            options.append(SyntaxSuggestion(
                type="clause_reorder",
                result=reordered,
                reason="Clause position change affects rhythm"
            ))

        return options
```

### 2.4 验证服务 | Validator Service

```
validator/
├── __init__.py
├── semantic.py         # 语义相似度
├── term_check.py       # 术语完整性
├── risk_recheck.py     # 风险复检
└── quality_gate.py     # 质量门控
```

#### 2.4.1 语义验证 | Semantic Validator

```python
# semantic.py
class SemanticValidator:
    """
    Validate semantic similarity between original and modified
    验证原文和修改后的语义相似度
    """

    def __init__(self, threshold: float = 0.80):
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.threshold = threshold

    def validate(
        self,
        original: str,
        modified: str
    ) -> SemanticValidation:
        """
        Check if semantic meaning is preserved
        检查语义是否保持
        """
        emb_orig = self.model.encode(original)
        emb_mod = self.model.encode(modified)

        similarity = cosine_similarity([emb_orig], [emb_mod])[0][0]

        return SemanticValidation(
            similarity=similarity,
            passed=similarity >= self.threshold,
            message=self._get_message(similarity)
        )
```

#### 2.4.2 质量门控 | Quality Gate

```python
# quality_gate.py
class QualityGate:
    """
    Multi-layer quality validation gate
    多层质量验证门控
    """

    def __init__(self, config: QualityConfig):
        self.semantic_validator = SemanticValidator(config.semantic_threshold)
        self.term_checker = TermChecker()
        self.risk_rechecker = RiskRechecker()

    def validate(
        self,
        original: str,
        modified: str,
        locked_terms: List[str],
        target_risk: int
    ) -> QualityResult:
        """
        Run all quality checks
        执行所有质量检查
        """
        results = []

        # Layer 1: Semantic similarity
        # 层1: 语义相似度
        semantic = self.semantic_validator.validate(original, modified)
        results.append(("semantic", semantic))

        # Layer 2: Term integrity
        # 层2: 术语完整性
        terms = self.term_checker.validate(modified, locked_terms)
        results.append(("terms", terms))

        # Layer 3: Risk reduction
        # 层3: 风险降低
        risk = self.risk_rechecker.validate(modified, target_risk)
        results.append(("risk", risk))

        # Aggregate results
        # 汇总结果
        passed = all(r[1].passed for r in results)

        return QualityResult(
            passed=passed,
            checks=results,
            action=self._determine_action(results)
        )

    def _determine_action(self, results: List) -> str:
        """
        Determine next action based on results
        根据结果决定下一步动作
        """
        if all(r[1].passed for r in results):
            return "accept"

        # Check which layer failed
        # 检查哪一层失败
        for name, result in results:
            if not result.passed:
                if name == "semantic":
                    return "retry_with_rule"  # LLM failed, try rules
                elif name == "terms":
                    return "flag_manual"  # Term error, need human
                elif name == "risk":
                    return "retry_stronger"  # Need stronger rewrite

        return "flag_manual"
```

---

## 三、API设计 | API Design

### 3.1 RESTful API端点 | API Endpoints

```yaml
# API端点设计 API Endpoint Design

# 文档处理 Document Processing
POST   /api/v1/documents/upload          # 上传文档
GET    /api/v1/documents/{id}            # 获取文档信息
DELETE /api/v1/documents/{id}            # 删除文档

# 分析 Analysis
POST   /api/v1/analyze                   # 分析文本
GET    /api/v1/analyze/{id}/status       # 获取分析状态
GET    /api/v1/analyze/{id}/result       # 获取分析结果

# 建议 Suggestions
POST   /api/v1/suggest                   # 获取修改建议
POST   /api/v1/suggest/apply             # 应用建议
POST   /api/v1/suggest/custom            # 验证自定义修改

# 会话 Session (干预模式)
POST   /api/v1/session/start             # 开始干预会话
GET    /api/v1/session/{id}/current      # 获取当前句子
POST   /api/v1/session/{id}/next         # 提交并进入下一句
POST   /api/v1/session/{id}/skip         # 跳过当前句
POST   /api/v1/session/{id}/flag         # 标记人工处理
GET    /api/v1/session/{id}/progress     # 获取处理进度
POST   /api/v1/session/{id}/complete     # 完成会话

# YOLO模式 YOLO Mode
POST   /api/v1/yolo/process              # 启动YOLO处理
GET    /api/v1/yolo/{id}/status          # 获取处理状态
GET    /api/v1/yolo/{id}/result          # 获取处理结果
POST   /api/v1/yolo/{id}/review          # 进入审核模式

# 配置 Configuration
GET    /api/v1/config/fingerprints       # 获取指纹词库
POST   /api/v1/config/terms              # 上传术语白名单
GET    /api/v1/config/levels             # 获取口语化等级说明

# 导出 Export
POST   /api/v1/export/document           # 导出最终文档
POST   /api/v1/export/report             # 导出分析报告
```

### 3.2 核心数据结构 | Core Data Structures

```python
# schemas.py

from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class SuggestionSource(str, Enum):
    LLM = "llm"
    RULE = "rule"
    CUSTOM = "custom"

# Request Models 请求模型
class AnalyzeRequest(BaseModel):
    """Analysis request model 分析请求模型"""
    text: str
    target_lang: str = "zh"
    include_turnitin: bool = True
    include_gptzero: bool = True

class SuggestRequest(BaseModel):
    """Suggestion request model 建议请求模型"""
    sentence: str
    issues: List[str]
    locked_terms: List[str] = []
    colloquialism_level: int = 4  # 0-10
    target_lang: str = "zh"

class SessionStartRequest(BaseModel):
    """Session start request 会话启动请求"""
    document_id: str
    mode: str = "intervention"  # intervention | yolo
    colloquialism_level: int = 4
    target_lang: str = "zh"
    process_levels: List[RiskLevel] = [RiskLevel.HIGH, RiskLevel.MEDIUM]

# Response Models 响应模型
class SentenceAnalysis(BaseModel):
    """Sentence analysis result 句子分析结果"""
    index: int
    text: str
    risk_score: int  # 0-100
    risk_level: RiskLevel
    ppl: float
    fingerprints: List[dict]
    issues: List[dict]
    turnitin_view: Optional[dict]
    gptzero_view: Optional[dict]

class Suggestion(BaseModel):
    """Single suggestion 单个建议"""
    source: SuggestionSource
    rewritten: str
    changes: List[dict]
    predicted_risk: int
    semantic_similarity: float
    explanation: str  # In target language

class SuggestResponse(BaseModel):
    """Suggestion response 建议响应"""
    original: str
    original_risk: int
    llm_suggestion: Optional[Suggestion]
    rule_suggestion: Optional[Suggestion]
    locked_terms: List[str]
    translation: str  # Original meaning in target language

class SessionState(BaseModel):
    """Current session state 当前会话状态"""
    session_id: str
    document_id: str
    total_sentences: int
    processed: int
    current_index: int
    current_sentence: SentenceAnalysis
    suggestions: SuggestResponse
    progress_percent: float
```

### 3.3 WebSocket事件 | WebSocket Events

```python
# 用于实时进度更新 For real-time progress updates

# Client -> Server
EVENT_START_ANALYSIS = "analysis:start"
EVENT_APPLY_SUGGESTION = "suggestion:apply"
EVENT_CUSTOM_INPUT = "custom:input"

# Server -> Client
EVENT_ANALYSIS_PROGRESS = "analysis:progress"
EVENT_SENTENCE_READY = "sentence:ready"
EVENT_VALIDATION_RESULT = "validation:result"
EVENT_YOLO_PROGRESS = "yolo:progress"
EVENT_ERROR = "error"
```

---

## 四、数据库设计 | Database Design

### 4.1 ER图 | Entity Relationship

```
┌─────────────────┐       ┌─────────────────┐
│    Document     │       │    Session      │
├─────────────────┤       ├─────────────────┤
│ id (PK)         │──┐    │ id (PK)         │
│ filename        │  │    │ document_id(FK) │──┐
│ original_text   │  │    │ mode            │  │
│ created_at      │  │    │ config_json     │  │
│ status          │  │    │ created_at      │  │
└─────────────────┘  │    │ completed_at    │  │
                     │    └─────────────────┘  │
                     │                         │
                     │    ┌─────────────────┐  │
                     │    │   Sentence      │  │
                     │    ├─────────────────┤  │
                     └───►│ id (PK)         │  │
                          │ document_id(FK) │  │
                          │ index           │  │
                          │ original_text   │  │
                          │ analysis_json   │  │
                          │ risk_score      │  │
                          │ risk_level      │  │
                          └────────┬────────┘  │
                                   │           │
                     ┌─────────────┘           │
                     │                         │
                     ▼                         │
          ┌─────────────────┐                  │
          │   Modification  │                  │
          ├─────────────────┤                  │
          │ id (PK)         │                  │
          │ sentence_id(FK) │                  │
          │ session_id(FK)  │◄─────────────────┘
          │ source          │
          │ modified_text   │
          │ changes_json    │
          │ validation_json │
          │ accepted        │
          │ created_at      │
          └─────────────────┘
```

### 4.2 表结构 | Table Schema

```sql
-- Documents table 文档表
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    original_text TEXT NOT NULL,
    processed_text TEXT,
    status TEXT DEFAULT 'pending',  -- pending, analyzing, ready, completed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sessions table 会话表
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id),
    mode TEXT NOT NULL,  -- intervention, yolo
    colloquialism_level INTEGER DEFAULT 4,
    target_lang TEXT DEFAULT 'zh',
    config_json TEXT,
    status TEXT DEFAULT 'active',  -- active, paused, completed
    current_index INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Sentences table 句子表
CREATE TABLE sentences (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id),
    index INTEGER NOT NULL,
    original_text TEXT NOT NULL,
    analysis_json TEXT,  -- Full analysis result
    risk_score INTEGER,
    risk_level TEXT,  -- low, medium, high
    locked_terms_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(document_id, index)
);

-- Modifications table 修改记录表
CREATE TABLE modifications (
    id TEXT PRIMARY KEY,
    sentence_id TEXT NOT NULL REFERENCES sentences(id),
    session_id TEXT NOT NULL REFERENCES sessions(id),
    source TEXT NOT NULL,  -- llm, rule, custom
    modified_text TEXT NOT NULL,
    changes_json TEXT,
    validation_json TEXT,
    semantic_similarity REAL,
    new_risk_score INTEGER,
    accepted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fingerprint words table 指纹词表
CREATE TABLE fingerprint_words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL UNIQUE,
    category TEXT,  -- high_freq, phrase, academic
    risk_weight REAL DEFAULT 1.0,
    replacements_json TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Term whitelist table 术语白名单表
CREATE TABLE term_whitelist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    term TEXT NOT NULL,
    domain TEXT,  -- cs, biology, physics, etc.
    user_defined BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 五、目录结构 | Directory Structure

```
AcademicGuard/
│
├── README.md                       # 项目说明
├── .gitignore                      # Git忽略文件
├── requirements.txt                # Python依赖
├── package.json                    # 前端依赖
│
├── doc/                            # 文档目录
│   ├── plan.md                     # 开发计划
│   ├── structure.md                # 技术架构 (本文档)
│   └── process.md                  # 开发进度
│
├── src/                            # 后端源码
│   ├── __init__.py
│   ├── main.py                     # FastAPI入口
│   ├── config.py                   # 配置管理
│   │
│   ├── api/                        # API层
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── documents.py
│   │   │   ├── analyze.py
│   │   │   ├── suggest.py
│   │   │   ├── session.py
│   │   │   └── export.py
│   │   ├── middleware/
│   │   │   ├── error_handler.py
│   │   │   └── rate_limiter.py
│   │   └── schemas.py              # Pydantic模型
│   │
│   ├── core/                       # 核心业务逻辑
│   │   ├── __init__.py
│   │   ├── preprocessor/
│   │   │   ├── __init__.py
│   │   │   ├── segmenter.py
│   │   │   ├── term_locker.py
│   │   │   └── cleaner.py
│   │   │
│   │   ├── analyzer/
│   │   │   ├── __init__.py
│   │   │   ├── perplexity.py
│   │   │   ├── fingerprint.py
│   │   │   ├── structure.py
│   │   │   ├── scorer.py
│   │   │   └── detectors/
│   │   │       ├── turnitin.py
│   │   │       └── gptzero.py
│   │   │
│   │   ├── suggester/
│   │   │   ├── __init__.py
│   │   │   ├── llm_track.py
│   │   │   ├── rule_track.py
│   │   │   ├── selector.py
│   │   │   ├── prompts/
│   │   │   │   ├── humanize.py
│   │   │   │   └── styles.py
│   │   │   └── rules/
│   │   │       ├── synonyms.py
│   │   │       └── syntax.py
│   │   │
│   │   └── validator/
│   │       ├── __init__.py
│   │       ├── semantic.py
│   │       ├── term_check.py
│   │       ├── risk_recheck.py
│   │       └── quality_gate.py
│   │
│   ├── db/                         # 数据库层
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── models.py
│   │   └── migrations/
│   │
│   ├── services/                   # 服务层
│   │   ├── __init__.py
│   │   ├── llm_service.py          # LLM API封装
│   │   ├── translation.py          # 翻译服务
│   │   └── export_service.py       # 导出服务
│   │
│   └── utils/                      # 工具函数
│       ├── __init__.py
│       ├── text_utils.py
│       └── cache.py
│
├── data/                           # 数据资源
│   ├── fingerprints/
│   │   ├── words.json              # 指纹词库
│   │   └── phrases.json            # 指纹短语库
│   ├── synonyms/
│   │   ├── academic.json           # 学术同义词
│   │   └── level_preferences.json  # 等级词汇偏好
│   └── terms/
│       └── whitelist.json          # 术语白名单
│
├── prompts/                        # Prompt模板
│   ├── humanize_base.txt
│   ├── style_0_2.txt               # 等级0-2风格
│   ├── style_3_4.txt
│   ├── style_5_6.txt
│   ├── style_7_8.txt
│   └── style_9_10.txt
│
├── frontend/                       # 前端源码
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── index.html
│   │
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   │
│   │   ├── components/
│   │   │   ├── common/
│   │   │   │   ├── Button.tsx
│   │   │   │   ├── Slider.tsx
│   │   │   │   └── Modal.tsx
│   │   │   ├── editor/
│   │   │   │   ├── SentenceCard.tsx
│   │   │   │   ├── DiffView.tsx
│   │   │   │   └── SuggestionPanel.tsx
│   │   │   ├── analysis/
│   │   │   │   ├── RiskBadge.tsx
│   │   │   │   ├── RiskChart.tsx
│   │   │   │   └── IssueList.tsx
│   │   │   └── settings/
│   │   │       ├── ColloquialismSlider.tsx
│   │   │       └── LanguageSelector.tsx
│   │   │
│   │   ├── pages/
│   │   │   ├── Home.tsx
│   │   │   ├── Upload.tsx
│   │   │   ├── Intervention.tsx
│   │   │   ├── Yolo.tsx
│   │   │   └── Review.tsx
│   │   │
│   │   ├── hooks/
│   │   │   ├── useSession.ts
│   │   │   ├── useSuggestion.ts
│   │   │   └── useWebSocket.ts
│   │   │
│   │   ├── stores/
│   │   │   ├── sessionStore.ts
│   │   │   └── configStore.ts
│   │   │
│   │   ├── services/
│   │   │   └── api.ts
│   │   │
│   │   └── types/
│   │       └── index.ts
│   │
│   └── public/
│       └── assets/
│
└── tests/                          # 测试目录
    ├── __init__.py
    ├── test_analyzer/
    ├── test_suggester/
    ├── test_validator/
    └── test_api/
```

---

## 六、技术栈详细说明 | Tech Stack Details

### 6.1 后端 | Backend

| 组件 | 技术 | 版本 | 说明 |
|------|------|------|------|
| **框架** | FastAPI | 0.104+ | 高性能异步框架 |
| **服务器** | Uvicorn | 0.24+ | ASGI服务器 |
| **ORM** | SQLAlchemy | 2.0+ | 数据库操作 |
| **验证** | Pydantic | 2.0+ | 数据验证 |
| **NLP** | spaCy | 3.7+ | 基础NLP处理 |
| **NLP** | Stanza | 1.6+ | 学术文本分析 |
| **ML** | Transformers | 4.35+ | BERT/GPT模型 |
| **ML** | Sentence-Transformers | 2.2+ | 语义相似度 |
| **缓存** | Redis | 7.0+ | LLM响应缓存 |

### 6.2 前端 | Frontend

| 组件 | 技术 | 版本 | 说明 |
|------|------|------|------|
| **框架** | React | 18+ | UI框架 |
| **构建** | Vite | 5.0+ | 构建工具 |
| **样式** | TailwindCSS | 3.3+ | 样式框架 |
| **状态** | Zustand | 4.4+ | 状态管理 |
| **请求** | Axios | 1.6+ | HTTP客户端 |
| **WebSocket** | socket.io-client | 4.7+ | 实时通信 |

### 6.3 AI/ML服务 | AI/ML Services

| 服务 | 提供商 | 用途 |
|------|--------|------|
| **LLM主力** | Claude API (Anthropic) | 轨道A改写建议 |
| **LLM备选** | OpenAI API | Fallback |
| **PPL计算** | GPT-2 / LLaMA (本地) | 困惑度分析 |
| **MLM** | BERT-base (本地) | 上下文同义词 |
| **Embedding** | all-MiniLM-L6-v2 (本地) | 语义相似度 |

---

## 七、部署架构 | Deployment Architecture

### 7.1 MVP部署 (单机) | MVP Deployment

```
┌─────────────────────────────────────────┐
│            Single Server                │
│                                         │
│  ┌─────────────┐    ┌─────────────┐    │
│  │   Nginx     │───►│   Uvicorn   │    │
│  │  (Reverse   │    │  (FastAPI)  │    │
│  │   Proxy)    │    └──────┬──────┘    │
│  └─────────────┘           │           │
│                            ▼           │
│  ┌─────────────┐    ┌─────────────┐    │
│  │   React     │    │   SQLite    │    │
│  │  (Static)   │    │    (DB)     │    │
│  └─────────────┘    └─────────────┘    │
│                                         │
│  ┌─────────────┐    ┌─────────────┐    │
│  │   Redis     │    │  ML Models  │    │
│  │  (Cache)    │    │  (Local)    │    │
│  └─────────────┘    └─────────────┘    │
└─────────────────────────────────────────┘
```

### 7.2 生产部署 | Production Deployment

```
┌────────────────────────────────────────────────────────────┐
│                      Load Balancer                         │
└──────────────────────────┬─────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  API Server  │  │  API Server  │  │  API Server  │
│  (FastAPI)   │  │  (FastAPI)   │  │  (FastAPI)   │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └────────────────┬┴─────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  PostgreSQL  │ │    Redis     │ │  ML Worker   │
│   (Primary)  │ │   Cluster    │ │   (GPU)      │
└──────────────┘ └──────────────┘ └──────────────┘
```

---

> 文档维护说明 | Document Maintenance:
> 本文档为项目技术架构文档，首次设计后除非用户要求，否则不做修改。
> This is the technical architecture document. After initial design, it should not be modified unless requested by user.

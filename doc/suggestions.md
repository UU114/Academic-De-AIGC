# Human Academic Writing vs. AIGC: De-AIGC 核心特征指南

本文档旨在为开发 De-AIGC（去 AI 化）程序或进行人工润色提供详细的特征库。内容分为六个维度：整体格局、逻辑构思、内容细节、连贯性、句式使用及用词特征。

---

## 1. 整体格局 (Overall Pattern & Structure)

**核心差异：** 人类写作通常呈现“不对称的有机结构”，而 AI 倾向于“完美的对称性和模块化”。

### AIGC 特征 (Flags)
* **汉堡包结构 (The Hamburger Style):** 极度标准化的 `Introduction -> Body Paragraph 1/2/3 -> Conclusion`。
* **首尾呼应的机械性:** 结尾段落往往只是开头段落的同义词改写，缺乏升华。
* **段落长度均等:** 每一段的长度惊人地一致（例如都在 5-7 行之间），视觉上显得过于整齐。
* **广阔的开篇 (The "Since the dawn of time" Opener):** 开头喜欢用极其宏大的背景引入，例如 *"In the rapidly evolving landscape of [Topic]..."* 或 *"Since the advent of..."*。

### Human 特征 (Target)
* **非线性结构:** 根据论证的强弱安排篇幅，核心论点段落可能很长，过渡段落很短。
* **开门见山 (In media res):** 经常直接切入具体的矛盾、数据或现象，而不是从宇宙起源讲起。
* **结论的延展性:** 结尾不仅仅是总结，还会指出“未解决的问题”或“未来的研究方向”。

---

## 2. 逻辑构思 (Logical Conception)

**核心差异：** 人类写作是“基于观点的 (Opinion-based)”，AI 写作是“基于共识的 (Consensus-based)”。

### AIGC 特征 (Flags)
* **四平八稳 (Neutrality Bias):** 极力避免得罪任何一方，过度使用 *"On the one hand... On the other hand..."*，最终结论往往是 *"A balance must be struck"*（必须达成平衡）这种废话。
* **缺乏批判性:** 只有罗列（List），没有综合（Synthesize）。它会说 A 说了 X，B 说了 Y，但很少分析为什么 A 可能是错的。
* **表面逻辑:** 看起来有逻辑，但经不起推敲。例如 *"Because technology is advancing, education is important"*（前提和结论关联太泛）。

### Human 特征 (Target)
* **论点驱动 (Thesis-driven):** 整篇文章为了证明一个特定的、甚至有争议的观点。
* **承认局限 (Limitations):** 主动承认自己研究的不足（例如样本量小、方法局限），这是人类诚实和自信的表现。
* **反直觉:** 提出 *"Despite common belief, data suggests..."*（尽管人们普遍认为……但数据表明……）。

---

## 3. 内容细节把控 (Content & Granularity)

**核心差异：** AI 倾向于抽象概括，人类倾向于具体实例。

### AIGC 特征 (Flags)
* **幻觉与模糊引用:** 喜欢说 *"Studies have shown..."* 或 *"Researchers argue..."* 但不指名道姓是哪个研究。
* **空洞的形容词堆砌:** 使用大量形容词修饰抽象名词，如 *"intricate interplay"*（复杂的相互作用）, *"complex dynamics"*（复杂的动态）。
* **常识性废话:** 解释该领域内人尽皆知的基本概念。

### Human 特征 (Target)
* **数据颗粒度:** 提供具体的数字（e.g., *"14.5% increase"* 而不是 *"significant increase"*）。
* **具体的指代:** 明确提到具体的人名、地点、年份、特定的算法名称。
* **轶事证据 (Anecdotal Evidence):** 有时会用一个具体的微观案例来引出宏观理论。

---

## 4. 句子之间连贯性 (Coherence & Flow)

**核心差异：** AI 依靠“显性连接词”拼接句子，人类依靠“语义逻辑”流动。

### AIGC 特征 (Flags) - “连接词滥用症”
* **句首连接词过载:** 几乎每句话开头都用连接词。
    * *High Frequency:* Furthermore, Moreover, Additionally, Consequently, Thus, Therefore, In conclusion, To summarize, Importantly, Notably.
* **机械列表:** Firstly, Secondly, Thirdly, Finally.

### Human 特征 (Target) - “语义衔接” (Thematic Progression)
* **旧信息引出新信息:** 上一句的宾语变成下一句的主语。
    * *Example:* "The experiment produced a specific **residue**. This **residue** was then analyzed..." (而不是 "The experiment produced a residue. Furthermore, we analyzed it...")
* **代词指代:** 自然地使用 *This, These, Such* + 名词来指代上文，而不是反复使用 *Moreover*。
    * *Example:* "This discrepancy suggests..." (这种差异表明……)

---

## 5. 句式的使用 (Sentence Structure)

**核心差异：** AI 追求“语法完美的中长句”，人类写作具有“节奏感”和“长短句交替”。

### AIGC 特征 (Flags)
* **均质化:** 句子长度的标准差很小。
* **被动语态滥用:** 喜欢用 *"It is important to note that..."* 或 *"The significance can be seen in..."* 来显得客观，但导致文字死板。
* **名词化结构 (Nominalization) 堆砌:** *"The implementation of the utilization of the method..."* (人类会说 *"Using the method..."*)。

### Human 特征 (Target)
* **长短结合:** 一个长句解释复杂概念，紧跟一个短句强调重点。
    * *Example:* "The algorithmic complexity increases exponentially with the input size, rendering standard solutions ineffective. We need a new approach."
* **插入语与破折号:** 灵活使用破折号（—）、括号或分号来补充说明。
    * *AI 很少使用长破折号 (Em-dash) 来制造语气的停顿。*

---

## 6. 用词 (Word Choice & Lexicon) - **De-AIGC 核心黑名单**

这是检测 AI 最直接的方式。以下词汇在 GPT-3/4 训练数据中权重极高，出现频率远超人类习惯。

### Level 1: "AI 强特征词" (一旦出现，极大嫌疑)
> 这是一个 **"Red Flag List"**，程序检测到这些词的高频组合时应报警。

* **Delve** (e.g., *Delve into*) —— 人类更爱用 *investigate, examine, explore*.
* **Tapestry** (e.g., *A rich tapestry of...*) —— 极其典型的 AI 文学修辞。
* **Landscape** (e.g., *In the educational landscape*) —— 除非真的在写地理，否则慎用。
* **Realm** (e.g., *In the digital realm*) —— 过于戏剧化。
* **Underscore** (e.g., *This underscores the importance*) —— 人类偶尔用，AI 疯狂用。
* **Multifaceted** (e.g., *A multifaceted approach*) —— AI 的万能修饰词。
* **Pivotal / Crucial / Paramount** —— AI 喜欢把所有东西都描述得至关重要。
* **Foster** (e.g., *To foster innovation*) —— 企业公文风，学术界较少过度使用。
* **Nuanced** (e.g., *A nuanced understanding*) —— AI 经常自夸其内容“细致入微”。
* **Democratize** (e.g., *Democratize access to...*)
* **A testament to** (e.g., *This is a testament to...*)
* **Inextricably linked** (e.g., *A and B are inextricably linked*) —— 老套的表达。

### Level 2: "AI 句式模板" (Syntactic Templates)
> 程序应检测以下句子的结构模式。

1.  **"Not only... but also..." (过度使用)**
    * *AI:* "This technology not only improves efficiency but also reduces costs."
    * *Human:* "Beyond improving efficiency, this technology cuts costs."
2.  **"It is important/crucial/essential to..."**
    * *AI:* "It is crucial to consider the implications."
    * *Human:* "The implications must be considered." / "We must consider..."
3.  **"In conclusion/summary..." + 重复**
    * *AI:* "In conclusion, [Topic] is complex and requires..."
    * *Human:* "Ultimately, findings suggest..."
4.  **"Serve as..."**
    * *AI:* "This serves as a foundation for..."
    * *Human:* "This acts as..." / "This forms..."

---

## De-AIGC 程序开发建议 (Implementation Logic)

如果您在编写程序，可以设计以下评分权重：

1.  **困惑度 (Perplexity) 变异检测:**
    * 计算句长的标准差。如果标准差过低（句子长度太一致），增加 AI 评分。
2.  **词汇黑名单惩罚:**
    * 建立上述 **Level 1** 词汇库。每出现一个 *delve* 或 *tapestry*，显著增加 "AI Score"。
3.  **连接词密度分析:**
    * 统计句首连接词（Moreover, Furthermore 等）占总句数的比例。如果超过 15%-20%，标记为 AI 风格。
4.  **情感/语气中性度:**
    * AI 往往缺乏强烈的否定词（Wrong, Fail, Impossible）。如果文章全是 *Challenges, Issues, Limitations* (温和词) 而没有 *Errors, Flaws* (强硬词)，增加 AI 评分。

---

### Human Rewrite Example (对比示例)

**AI Version:**
> "In the rapidly evolving digital landscape, it is crucial to delve into the multifaceted implications of AI. Furthermore, this technology serves as a pivotal tool that fosters innovation. However, we must also
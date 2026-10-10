# 02｜文本、Tokenizer 与 Embedding

## 1. 模型不能直接处理字符串

神经网络需要数值输入，因此文本必须经历：

```text
文本 → Token → Token ID → Embedding Vector
```

Tokenizer 决定了“模型看到的基本单位”。

## 2. Tokenization

最简单的 Tokenizer 可以按：

- 空格；
- 标点；
- 单词；

切分文本。

但实际 LLM 通常使用子词或字节级方法，因为固定词表无法覆盖所有词。

## 3. BPE 的核心思想

Byte Pair Encoding（BPE）通过不断合并高频符号片段，形成子词词表。

采用包含所需字节/字符的初始符号集或回退机制时，它能缓解两个问题：

1. 词表不需要包含所有完整单词；
2. 未见过的新词可以拆成更小的已知片段。

因此：

```text
未知完整词 ≠ 无法处理
```

而是可以拆解为多个已有 Token。

## 4. 特殊 Token

常见特殊 Token 用于表达结构，而不是普通语义：

- BOS：序列开始；
- EOS：序列结束；
- PAD：批处理中补齐长度；
- UNK：未知 Token（并非所有 Tokenizer 都需要）。

是否需要某类特殊 Token 取决于 Tokenizer 和训练设计。

## 5. Token ID

Tokenizer 输出的不是 Embedding，而是整数 ID。

例如：

```text
"hello" → 7  # 教学词表中的任意索引，不是通用编号
```

这个 ID 本身没有几何意义，只是词表索引。

## 6. Token Embedding

Embedding 层把离散 Token ID 映射到连续向量：

```text
token_id → R^d
```

这些向量在训练过程中被学习，使模型可以在连续空间中表示语义与模式。

Embedding 查表在数学上可以理解为对 one-hot 向量做线性变换，只是实际实现更高效。

## 7. 位置信息

Attention 本身不天然知道 Token 顺序，因此模型需要加入位置信息。

一种早期常见实现是把：

```text
Token Embedding + Position Representation
```

组合后送入 Transformer。

加法位置嵌入不是唯一实现。RoPE 在注意力内部旋转 Q/K，通常不把一个位置向量直接加在输入 Embedding 上；相对位置偏置则改变注意力分数。位置机制与因果掩码解决不同问题，不能互相替代。

## 8. 训练样本的滑动窗口

自回归训练需要连续构造：

```text
输入窗口 → 右移一位的目标窗口
```

例如上下文长度为 4：

```text
输入： A B C D
目标： B C D E
```

滑动窗口决定：

- 单个样本看到多少上下文；
- 样本之间的重叠程度；
- 数据利用率；
- 训练成本。

## 9. 工程上的长期结论

Tokenizer 会直接影响：

- 上下文长度；
- Token 成本；
- 多语言表现；
- 代码和数字表示；
- 数据压缩效率；
- 训练与推理吞吐。

因此 Tokenizer 不是单纯的“预处理工具”，而是模型设计的一部分。

来源：<https://github.com/rasbt/LLMs-from-scratch/tree/main/ch02>

## 10. 一次查表与一次切分

设词表大小为 5，嵌入维度为 3，则 Embedding 参数矩阵形状为 `5×3`。输入 ID `[2, 0, 2]`，输出为矩阵的第 2、0、2 行，形状为 `3×3`（索引从 0 开始）。同一个 Token 的初始向量相同，经过 Attention 后，各位置的上下文表示可以不同。检索用的句向量还需要池化/专门训练，不能直接把一个 Token Embedding 当全文语义。

BPE 教学例：若语料中 `l o w` 最常见的相邻对是 `l o`，第一轮可合并为 `lo w`；下一轮再统计新的相邻对。训练词表时学合并规则，编码新文本时应用已经固定的规则，不能每次输入都重新训练词表。

**自检**：把模型 A 的 Tokenizer 换成词表大小相同的 B，为什么仍可能彻底出错？

**核对**：相同 ID 在两套词表中可能代表不同符号，Embedding 和输出头都按 A 的映射训练过；词表尺寸相同不足以保证兼容。


## 11. 从概念查表到可运行的文本表示

本章保留 LLM 输入与模型映射的主入口；完整算法和实验按知识主题维护：

- [文本预处理与稀疏表示](../AI%20算法基础/语言与文本专题/01-文本预处理与稀疏表示.md)：Unicode、正则与词形边界、BoW/TF-IDF的 fit/transform、n-gram与归一的 Kneser–Ney。经典模型可以消费稀疏浮点特征，并非所有 NLP都直接消费整数 Token ID。
- [词向量与子词建模](../AI%20算法基础/语言与文本专题/02-词向量与子词建模.md)：SGNS/GloVe/已训练字符片段、字符与字节BPE、WordPiece、Unigram最优分段及EM；包含可运行代码和梯度/往返检查。
- [文本分类、主题与跨语言学习](../AI%20算法基础/语言与文本专题/03-文本分类主题与跨语言学习.md)：分类评测、LDA后验、c-TF-IDF、跨语言对齐与分语言验收。

未知完整词可拆分的前提是初始字符/字节或回退覆盖输入。子词不自动消灭所有未知字符，byte fallback也不保证更少Token或更好的低资源语言能力。一个 emoji可能有多个码点与字节；tokens/词、tokens/码点、tokens/字节要分别说明单位。普通字串像 `<EOS>` 是否解析成结构Token由编码器的特殊符号策略决定，不能只从字面猜。

Tokenizer匹配检查应包括词表/ID、合并排名、规范化、预切分、特殊Token和模型版本，而非仅词表尺寸或单个JSON文件。改分词器或扩词可以作为有意的训练研究，但需要同步更新Embedding/输出头并重新训练适配。普通微调复用原配，训练、推理保持同一输入契约。

增量来源：[ai-engineering-from-scratch](https://github.com/rohitg00/ai-engineering-from-scratch)，固定 `3be078b37ffd8f0c04953c0678e48f5c6d0c7775`，Phase05文本表示与分词；2026-10-04整理。后续维护提示：本节路由与上面10节共同保留，不把不同Token粒度的PPL直接比较，也不把“可编码”写成“模型已理解”。

## 12. 字节覆盖、词表上界与压缩指标

字符、码点、字形簇、字节和Token的单位不同。`ord(c)`虽然能给字符一个整数，却不是“几百项紧凑词表”：汉字和emoji的码点可很大，不能拿`Embedding(len(训练字符))`直接索引这些码点。紧凑字符词表要建立显式映射和OOV策略；byte BPE保留全部256种字节时，对有效UTF-8字符串有基础编码覆盖，但不保证整个规范化/预切分管线保留原文，更不保证模型理解。

词表统计也分两种：**实际已定义ID个数**与**最大ID+1**。若ID存在空洞，Embedding按实际个数分配可能越界。以2026-10-05核对的`tiktoken`官方定义为例，`cl100k_base`最高已声明特殊ID是100276，按最大ID分配至少需100277行；不能把普通mergeable token数量近似值当总ID上界。具体词表、模型名映射和新增特殊符号随版本变化，应冻结编码配置与资产校验值。[官方编码定义](https://github.com/openai/tiktoken/blob/main/tiktoken_ext/openai_public.py)

词表V、维度D的输入表参数为VD；未共享输出头再增加VD，共享则只保留一份参数，详见[共享权重及两路径梯度](../AI%20算法基础/深度学习专题/19-Transformer实现与训练实践.md)。V变大可能压短同域文本，也增加输出softmax/稀有词项成本；不能只凭V更大推导生成一定更快、更准确。源互动图中的`tokens/word=1+6/(log₂V−5)`是人为示意公式，未测真实分词器。

跨语言比较至少给出同义/同任务文本、分语言样本数、tokens/UTF-8字节、tokens/码点，以及说明如何得到“词”后再报fertility。中文`text.split()`常把整句当一个词，不能由此说中文每词20个Token而英语1个，便推断20倍计算或收费。可编码、压缩率、真实任务效果分别验证；空文本比例标不适用，不用除零或偷偷当0。

## 13. 规范化与预切分必须保留约定的信息

NFC合并规范等价形式；NFKC先做**兼容分解，再做规范合成**，例如`ﬁ`变`fi`、全角`Ａ`变`A`。这会有意改变原文，round-trip的目标只能是“规范化后的文本”，不能称原始字符串无损。代码缩进、数学符号、产品名和特殊字符串都需按任务检查；并非所有LLM Tokenizer必须强制NFKC、小写或删除空白。详见[Unicode与任务预处理](../AI%20算法基础/语言与文本专题/01-文本预处理与稀疏表示.md)。

预切分决定哪些相邻片段允许BPE合并，常保留前导空白、数字段、标点；它不是统一的语言词边界。源ASCII fallback正则的`[a-zA-Z]`不匹配中文，而`\w`又把中文排除在最后的补集分支之外，导致`finditer`静默跳过中文。每个输入都要检查`''.join(chunks)==规范化文本`或正确offset覆盖，不能只看有无异常。

```python
import re
import unicodedata
bad = re.compile(r"'(?:[sdmt]|ll|ve|re)| ?[a-zA-Z]+| ?[0-9]+| ?[^\s\w]+|\s+(?!\S)|\s+")
text = '你好，Hello 🌍\tＡ ﬁ'
lost = ''.join(m.group() for m in bad.finditer(text))
assert lost != text and '你好' not in lost
chunks = re.findall(r'\s+|\S+', text)  # 教学lossless分块，不冒充GPT-2/Llama预切分。
assert ''.join(chunks) == text
normalized = unicodedata.normalize('NFKC', text)
assert normalized != text and 'A fi' in normalized
print('原文', repr(text), '错误回退', repr(lost), 'NFKC目标', repr(normalized))
```

GPT-2字节到可显示Unicode的空白呈现为`Ġ`，不是普通`G`；这类可视化也不是Token真的包含该语义字符。SentencePiece是包含规范化和分词模型的工具，算法可为BPE/Unigram；Llama不同代际的Tokenizer配置不同，不能把所有Llama都叫SentencePiece。WordPiece的频率比值是常见教学合并准则，不等于复现所有生产训练器。完整BPE、WordPiece、Unigram程序仍由[词向量与子词建模第5～6节](../AI%20算法基础/语言与文本专题/02-词向量与子词建模.md)维护。

## 14. 保存的是编码契约，普通字符串不能隐式升级成控制符

模型需要结构ID，不意味着任意用户输入里写`<EOS>`就应得到EOS控制ID。可信模板按角色插入已约定的ID，普通content按普通文本编码。某些库允许显式设置`allowed_special/disallowed_special`；输入拒绝、按普通文本编码和按控制符解释是三种不同策略。模板、角色、BOS/EOS/EOT和生成提示必须与训练配置一致；decode回原文只能验证一部分，不能证明聊天协议正确。[tiktoken接口](https://github.com/openai/tiktoken/blob/main/tiktoken/core.py)、[Hugging Face聊天模板](https://huggingface.co/docs/transformers/chat_templating)

下面只实现**已有合并表的部署契约**：普通字节ID有固定offset，结构ID独立保留；lossless空白分块、可选规范化、严格ID检查和JSON保存/恢复均完整。合并训练核心已在上面的主算法章节，不在这里再复制一套训练器。三条合并规则是指定fixture，不宣称来自大语料或等价某个生产Tokenizer。

```python
import re
import json
import hashlib
import unicodedata

class EncodingContract:
    SPECIAL = {'PAD':0, 'BOS':1, 'EOS':2, 'SYSTEM':3, 'USER':4, 'ASSISTANT':5, 'EOT':6}
    OFFSET = 8
    def __init__(self, config):
        if type(config) is not dict or set(config) != {'schema_version','normalization','pretokenizer','merges'}:
            raise ValueError('未知或缺失编码字段')
        if type(config['schema_version']) is not int or config['schema_version'] != 1:
            raise ValueError('编码schema版本')
        if config['normalization'] not in ['none','NFC','NFKC'] or config['pretokenizer'] != 'whitespace_chunks':
            raise ValueError('不支持的规范化/预切分契约')
        if type(config['merges']) is not list:raise ValueError('合并表必须有序list')
        self.config = json.loads(json.dumps(config))
        self.vocab = {self.OFFSET+b:bytes([b]) for b in range(256)}
        self.rules = []
        for pair in config['merges']:
            if type(pair) is not list or len(pair) != 2 or any(type(i) is not int or i not in self.vocab for i in pair):
                raise ValueError('合并只能引用已有普通token')
            new = self.OFFSET+256+len(self.rules)
            value = self.vocab[pair[0]]+self.vocab[pair[1]]
            if value in self.vocab.values():raise ValueError('fixture契约拒绝重复字节token')
            self.rules.append((tuple(pair),new));self.vocab[new]=value
        self.vocab_size = max(self.vocab)+1  # 含保留ID空洞，不能用len(vocab)。
    @staticmethod
    def rewrite(seq, pair, new):
        out=[];i=0
        while i<len(seq):
            if i+1<len(seq) and (seq[i],seq[i+1])==pair:out.append(new);i+=2
            else:out.append(seq[i]);i+=1
        return out
    def encode_text(self, text):
        if type(text) is not str:raise ValueError('只接受str文本')
        norm=self.config['normalization']
        if norm != 'none':text=unicodedata.normalize(norm,text)
        chunks=re.findall(r'\s+|\S+',text)
        assert ''.join(chunks)==text
        ids=[]
        for chunk in chunks:
            seq=[self.OFFSET+b for b in chunk.encode('utf-8')]
            for pair,new in self.rules:seq=self.rewrite(seq,pair,new)
            ids.extend(seq)
        return ids
    def encode_trusted(self, parts):
        out=[]
        for part in parts:
            if type(part) is str:out.extend(self.encode_text(part))
            elif type(part) is dict and set(part)=={'special'} and type(part['special']) is str and part['special'] in self.SPECIAL:
                out.append(self.SPECIAL[part['special']])
            else:raise ValueError('可信模板项必须是文本或已知结构名')
        return out
    def get_token_bytes(self, token_id):
        if type(token_id) is not int or token_id not in self.vocab:raise ValueError('不是普通token ID')
        return self.vocab[token_id]
    def decode(self, ids, skip_special=False):
        out=[]
        for i in ids:
            if type(i) is not int:raise ValueError('ID须非bool整数')
            if i in self.vocab:out.append(self.vocab[i])
            elif skip_special and i in self.SPECIAL.values():continue
            else:raise ValueError('非法或未允许跳过的结构ID')
        return b''.join(out).decode('utf-8')  # 错误字节明确报错，不默默replace。
    def save(self):return json.dumps(self.config,sort_keys=True,separators=(',',':'),ensure_ascii=False)
    @classmethod
    def load(cls, raw):
        def unique(pairs):
            d={}
            for k,v in pairs:
                if k in d:raise ValueError('重复JSON键')
                d[k]=v
            return d
        return cls(json.loads(raw,object_pairs_hook=unique))

# byte t/h/e offset8；第1条生成264，随后264+byte(e)生成265。
config={'schema_version':1,'normalization':'none','pretokenizer':'whitespace_chunks',
        'merges':[[124,112],[264,109],[105,106]]}
m=EncodingContract(config);snapshot=m.save();restored=EncodingContract.load(snapshot)
for text in ['the ab', '你好\x00，🌍', '', '<EOS>', '\t  Ａ\nﬁ']:
    ids=m.encode_text(text)
    assert m.decode(ids)==text and restored.encode_text(text)==ids
    print(repr(text),'bytes',len(text.encode('utf-8')),'IDs',ids)
assert m.SPECIAL['EOS'] not in m.encode_text('<EOS>')
trusted=m.encode_trusted([{'special':'BOS'},'<EOS>',{'special':'EOS'}])
assert trusted[0]==1 and trusted[-1]==2 and m.decode(trusted,skip_special=True)=='<EOS>'
assert m.encode_text('\x00')==[8] and m.SPECIAL['PAD']==0
for invalid in [[True],[-1],[999999],[7],[1]]:
    try:m.decode(invalid)
    except ValueError:pass
    else:raise AssertionError('非法/控制ID不可静默丢弃')
print('snapshot SHA',hashlib.sha256(snapshot.encode()).hexdigest(),'Embedding行数',m.vocab_size)
```

`vocab_size`包括最大ID之下的保留空洞，本例第7号未分配，不允许编码/解码却仍需留Embedding行。若要求结构Token可读回文本，应另提供明确的结构解码模式，不把它与普通文本round-trip混用。保存文件中还有字段版本；改字段或合并排名后不能只检查词表大小，须核对整个编码snapshot与模型checkpoint。参数扩大并同步训练是有意的适配研究，普通微调用原配。

库教程需固定版本。2026-10-05访问的HF Tokenizers主分支API页提示部分rc0训练器文档尚未生成，不能把旧教程的类和参数当所有当前安装版本都已验证。生产ByteLevel训练还需检查基础字节alphabet、decoder与特殊符号model配置；只把`<unk>`写进trainer列表并不说明未知字符回退已正确设置。本次不安装这些库、不获取现成编码资产；现有接口链接用于按所用版本查证，正文CPU程序验证自己的明确契约。

## 15. 本节练习与维护边界

1. 打印每轮BPE：主算法的频率计数/合并次序与压缩数字已可运行；图中的固定`t+h→th→the`是流程示意，不是该corpus真的频率冠军。
2. 结构ID0/1/2与byte初始0～255撞号怎么办？整体给普通字节ID加offset，合并引用、Embedding/输出头和保存表一起更新；本例offset8，EOS2与真实NUL8独立。
3. 未见过的新字符：完整字节基础可编码，字符词表仍可能OOV；规范化/ASCII丢失发生在BPE之前，字节覆盖不能补回已删文字。
4. 普通用户写`<EOS>`：按普通content编码；模板插入EOS才用结构ID。特殊字符串匹配允许策略与可信角色来源必须一致。
5. NFKC后`Ａ ﬁ`变`A fi`：若目标是规范化文本，往返可正确；若目标是原文，已经不可逆，不能叫bug修好或无损。
6. 多语言/代码benchmark需held-out同域样本与明确单位、空值处理、完整coverage/速度/下游指标，不预设某模型词表一定更省、更快或更公平。源码固定型号比例、100GB训练器秒级、1GB/60秒门槛未当当前性能事实。
7. Llama3特定模板验证应对官方固定revision的rendered text/ID/EOT/generation prompt做快照；本例不冒充其协议，未下载真实Tokenizer或执行网络对照。新自建聊天的span/label检查接[微调实践](../LLM%20工程实践/04-微调与参数高效适配.md)。

本次增量来源：AI Engineering from Scratch Phase10第01、02课，固定commit `3be078b37ffd8f0c04953c0678e48f5c6d0c7775`；2026-10-05完整读源码、原题/产物与注册图。此前2026-10-04的语言专题与原11节保留。中文维护提示：修改Tokenizer先重跑原文/规范化目标、普通与结构字符串、空文本/NUL/emoji/未知ID、snapshot与模型ID上界；不将模拟图、源码未跑的外部资产或成本估算记成实际结果。

# 08｜OCR、视觉语言与可靠管道

> 先修：[检测/掩码与坐标](07-检测分割姿态与跟踪.md)、[图文共享空间](03-多模态学习.md)、序列概率及Transformer。先把文字、布局、结构字段分开，再学CTC与VLM连接器，最后检查完整输入/输出和失败路径。本章程序使用文字/向量/小图fixture，不加载OCR或VLM权重，不调用外部API。

## 1. OCR、阅读顺序与文档理解分工

OCR把图像区域转为文本，布局识别标题/正文/表格/图等区域，文档理解决定“这一串数字是哪一个字段”。读到`42.50`不等于知道它是合计、税额还是余额；返回合法JSON也不证明金额、单位或对应页正确。

经典链是图像解码/方向校正→文字四边形检测→旋转/透视裁剪→行识别→布局及阅读顺序→字段提取。不同系统可能在识别前处理布局或联合训练，不必机械固定三步。倾斜文字不能只用轴对齐框而忽略方向；resize应保持合适宽高比、记录valid width和padding，不把填充区域算有效CTC时间。

CRNN典型计算为 `[N,1,H,W]`经CNN到 `[N,D,H',W']`，沿高度聚合，再转 `[N,W',D]`给BiLSTM，最后输出log概率 `[T,N,词表+blank]`。时间T通常来自横向特征宽度，不是原像素宽度或字符数。源TinyCRNN对H=32四次高度pool后是2，再取mean，不能称必已经降到1；不同结构的有效宽度需根据实际卷积/pool公式算。

多栏、页眉脚、脚注、表格与跨页关系使阅读顺序不等于全页按 `(y,x)`排序，中文竖排/右到左文字也需明确方向。布局模型、带坐标token的文档编码器、数据集不是同一实体：LayoutLMv3是文档表示模型，DocLayNet是数据集，不能把后者当可直接运行的布局检测器。

OCR-free encoder-decoder如Donut由文档视觉编码到目标文本/结构，TrOCR关注行级识别，视觉语言模型也可做文档问答。端到端减少某些级联接口，不消除误读、结构幻觉和来源对应；固定格式文档也可能OCR+规则更容易维护。选择看语言、字体、清晰度、表格/手写、字段类型、独立验证与实际延迟，不按发表年份禁止Tesseract或承诺某模型在任何100～1000图微调后必优。

## 2. CTC：求和所有合法对齐，而非强配每字符位置

模型每时间步给词表+blank概率，路径 $\pi$的概率为各步概率乘积。collapse先合并**连续同符号**，再删除blank；blank分开相邻相同字符，不是EOS。例如 `a a blank a`变成`aa`，先删blank再合并会错误变成`a`。

目标y的概率为 $P(y\mid X)=\sum_{\pi:B(\pi)=y}\prod_tP(\pi_t\mid X)$，CTC loss取负log；动态规划借助插入blank的目标序列高效求和，不需要每个字符的像素/时间对齐标注。CTC的条件独立发射假设不同于自回归解码器，BiLSTM可先利用整个输入上下文。

若目标长度L，相邻同字符重复次数r，最少需 $T\ge L+r$（每个相邻重复须blank隔开）。targets不能含blank，字表索引/长度与log-softmax轴需一致。`zero_infinity=True`会把无合法对齐造成的inf loss变0且梯度归零，适合明确策略而非掩盖错长度；调试先检查对齐长度，用False暴露问题。

### 2.1 完整greedy、prefix beam与小穷举核对

Greedy选每步最大路径再collapse，不一定得到概率最大的**字符串**；多个路径可能合到同一字符串。prefix beam把同前缀的blank结尾/非blank结尾概率分别累计，以正确处理相邻重复。加语言模型或长度奖惩会改变解码目标，不能未经说明叫同一个纯CTC最优解。

```python
import itertools
import numpy as np
import torch
import torch.nn.functional as F

def collapse(path,blank=0):
    result=[]; previous=None
    for token in path:
        if token!=previous and token!=blank: result.append(int(token))
        previous=token
    return tuple(result)

def prefix_beam(log_probs,width=10,blank=0):
    lp=np.asarray(log_probs,float)
    if (lp.ndim!=2 or lp.shape[1]==0 or np.isnan(lp).any() or np.isposinf(lp).any()
            or np.any(lp>1e-8) or width<1 or not 0<=blank<lp.shape[1]
            or not np.allclose(np.logaddexp.reduce(lp,axis=1),0.,atol=1e-5)):
        raise ValueError("需已log_softmax归一化的[T,C]概率、有效blank与正beam宽")
    beams={(): (0.,-np.inf)} # 每前缀的p_blank、p_nonblank，log空间
    for row in lp:
        nxt={}
        def add(prefix,b=None,nb=None):
            old=nxt.setdefault(prefix,[-np.inf,-np.inf])
            if b is not None: old[0]=np.logaddexp(old[0],b)
            if nb is not None: old[1]=np.logaddexp(old[1],nb)
        for prefix,(pb,pnb) in beams.items():
            total=np.logaddexp(pb,pnb)
            add(prefix,b=total+row[blank])
            for token in range(len(row)):
                if token==blank: continue
                if prefix and token==prefix[-1]:
                    add(prefix,nb=pnb+row[token])
                    add(prefix+(token,),nb=pb+row[token])
                else:
                    add(prefix+(token,),nb=total+row[token])
        ranked=sorted(nxt.items(),key=lambda item:-np.logaddexp(*item[1]))
        beams=dict(ranked[:width])
    best=max(beams,key=lambda p:np.logaddexp(*beams[p]))
    return best,float(np.exp(np.logaddexp(*beams[best])))

# 两步每步blank=.4,a=.35,b=.25，最大路径blank-blank，但字符串a汇总更多路径。
p=np.array([[.4,.35,.25],[.4,.35,.25]])
greedy=collapse(p.argmax(axis=1)); beam,prob=prefix_beam(np.log(p))
exact={}
for path in itertools.product(range(3),repeat=2):
    label=collapse(path); exact[label]=exact.get(label,0.)+np.prod([p[t,c] for t,c in enumerate(path)])
assert beam==max(exact,key=exact.get)==(1,) and np.isclose(prob,exact[beam])
print("greedy/beam/字符串a概率",greedy,beam,round(prob,6))
assert collapse([1,1,0,1])==(1,1)
# aa的最短合法路径a-blank-a，共3步。
p3=np.tile([.4,.35,.25],(3,1))
loss=F.ctc_loss(torch.tensor(np.log(p3))[:,None,:],torch.tensor([1,1]),
               torch.tensor([3]),torch.tensor([2]),blank=0,reduction="sum",zero_infinity=False)
assert np.isclose(loss.item(),-np.log(.35*.4*.35))
short=F.ctc_loss(torch.tensor(np.log(p))[:,None,:],torch.tensor([1,1]),
                torch.tensor([2]),torch.tensor([2]),blank=0,reduction="sum",zero_infinity=False)
masked=F.ctc_loss(torch.tensor(np.log(p))[:,None,:],torch.tensor([1,1]),
                 torch.tensor([2]),torch.tensor([2]),blank=0,reduction="sum",zero_infinity=True)
assert torch.isinf(short) and masked.item()==0
print("aa合法CTC损失",round(loss.item(),6),"两步无对齐/被置零",short.item(),masked.item())
```

输出greedy为空字符串，beam为a，概率0.4025；aa三步loss约3.015935，两步不能对齐。这个有限穷举核对解码/概率，不是训练OCR。真实batch `[T,N,C]`按每项`input_lengths`截断，再decode；否则padding可生成额外字符。beam宽度看延迟与质量验证，不设“不能低于5”或“clean必只差1%CER”。

源OCR生成器把所有字母/数字画成相同黑矩形，同长度字符串图像相同而标签不同，无法学字符区别；因此不接受“200步loss必降到0.2”或把其预测当OCR质量。新合成识别实验至少给每字符可区分字形，并持有独立字体/位置/噪声测试；本批仅用明确概率fixture，不伪造字符识别训练。

### 2.2 CRNN核心结构的自含CPU程序

下面缩小为两层CNN，保留“空间特征→高度聚合→宽度时间序列→BiLSTM→字符log概率→CTC”的完整计算图。随机tensor和预定短标签只检查形状及有限反向，**不提供真实字符监督或识别准确率**。

```python
import torch
from torch import nn
import torch.nn.functional as F
from torch.nn.utils.rnn import pad_sequence,pack_padded_sequence,pad_packed_sequence
torch.set_num_threads(1);torch.manual_seed(42)
class TinyCRNN(nn.Module):
    def __init__(self,vocab_size=4):
        super().__init__()
        self.cnn=nn.Sequential(nn.Conv2d(1,4,3,padding=1),nn.ReLU(),nn.MaxPool2d(2),
                               nn.Conv2d(4,8,3,padding=1),nn.ReLU(),nn.MaxPool2d((2,1)))
        self.sequence=nn.LSTM(8,4,bidirectional=True,batch_first=True)
        self.head=nn.Linear(8,vocab_size)
    def forward(self,image,widths):
        sequences=[]
        for n,width in enumerate(widths.tolist()):
            # 本小例逐项按有效宽运行CNN，避免多余输入尾部影响卷积边界。
            feature=self.cnn(image[n:n+1,:,:,:width])  # [1,8,H/4,T_i]
            sequences.append(feature.mean(2).transpose(1,2)[0])  # [T_i,8]
        lengths=torch.tensor([len(s) for s in sequences],dtype=torch.long)
        padded=pad_sequence(sequences,batch_first=True)
        packed=pack_padded_sequence(padded,lengths.cpu(),batch_first=True,enforce_sorted=False)
        encoded,_=self.sequence(packed)
        encoded,_=pad_packed_sequence(encoded,batch_first=True,total_length=padded.shape[1])
        return F.log_softmax(self.head(encoded),-1).transpose(0,1),lengths
model=TinyCRNN();image=torch.randn(2,1,16,24)
image[0,:,:,20:]=0.  # fixture的统一padding值；真实归一化图像按训练契约设定
log_probs,input_lengths=model(image,torch.tensor([20,24]));assert log_probs.shape==(12,2,4)
# 第一项有效宽20，第二项24；横向pool一次，CNN实际T为10、12。
assert input_lengths.tolist()==[10,12];target_lengths=torch.tensor([2,3])
targets=torch.tensor([1,1,2,3,1])  # 第一项aa；第二项bca，blank=0不出现在目标
loss=F.ctc_loss(log_probs,targets,input_lengths,target_lengths,blank=0,
                zero_infinity=False,reduction="mean")
assert torch.isfinite(loss);loss.backward()
assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in model.parameters())
changed=image.clone();changed[0,:,:,20:]=100.
with torch.no_grad(): again,_=model(changed,torch.tensor([20,24]))
assert torch.allclose(log_probs[:10,0].detach(),again[:10,0],atol=1e-7)
print("CRNN输出/有效长度/CTC",tuple(log_probs.shape),input_lengths.tolist(),round(loss.item(),6))
```

实际输入需要同高、合适宽高比与按每项宽度计算有效T；padding值/归一化也要和训练一致。CTC长度正确与梯度通过，只证明接口可训练，不证明内容有信息、数据标签正确或模型已经学会OCR。

`input_lengths`只屏蔽CTC loss的发射步，不能阻止普通BiLSTM反向方向读取padding；上例使用pack后再运行BiLSTM，逐项CNN也避免卷积边界借到无效尾部。更高效批处理可明确逐层有效区mask/裁剪策略，但不能只给CTC长度就声称整个识别器不受padding影响。

## 3. CER、WER与结构字段评估

CER=$ (S+D+I)/N_{reference\ chars}$，WER换成预定词单位。替换/删除/插入用编辑距离，插入多时可大于1；参考空时需另定策略，不除0或默默当0。字符按Unicode/codepoint还是字素簇、NFC、标点/空格/大小写是否保留都要固定。中文WER需指定分词，不照搬空格切分。

多文档micro CER用总编辑数/总参考字符；mean per-page CER是另一种每页等权目标。字段F1需要键与值的匹配规则（币种、单位、日期规范、大小写、多条重复行），合法JSON率只是结构指标。树编辑距离关注结构，和纯字符串编辑距离/数值正确性不是一回事。金额/证件号/表格列偏移可CER很低却任务失败，应另报关键字段exact match、数值误差及证据覆盖。

### 3.1 完整文字fixture与字段一致性检查

```python
from decimal import Decimal
import re

def edit_distance(a,b):
    previous=list(range(len(b)+1))
    for i,x in enumerate(a,1):
        current=[i]
        for j,y in enumerate(b,1):
            current.append(min(current[-1]+1,previous[j]+1,previous[j-1]+(x!=y)))
        previous=current
    return previous[-1]
reference="商品A 12.50\n商品B 7.30\n合计 19.80"
predicted=reference.replace("19.80","79.80")
print("CER",edit_distance(reference,predicted)/len(reference))
# 已知识别文字fixture，仅验证解析与算术，不声称从图像读到了金额。
def parse_receipt(text):
    entries=[]; totals=[]
    for index,line in enumerate(text.splitlines()):
        match=re.fullmatch(r"(商品\S+|合计)\s+(\d+\.\d{2})",line)
        if not match: raise ValueError("行结构不支持，需保留原文人工/其他路径处理")
        name,amount=match.groups(); item={"名称":name,"金额":Decimal(amount),"来源行":index}
        (totals if name=="合计" else entries).append(item)
    if len(totals)!=1: raise ValueError("合计缺失或冲突，不能挑一个高分猜测")
    ok=sum((e["金额"] for e in entries),Decimal("0"))==totals[0]["金额"]
    return {"币种":"CNY","单位":"元","总额":str(totals[0]["金额"]),
            "证据行":totals[0]["来源行"],"行项目和一致":ok}
print("正确字段",parse_receipt(reference))
wrong=parse_receipt(predicted)
assert not wrong["行项目和一致"] and wrong["总额"]=="79.80"
print("低CER仍关键字段错",wrong)
```

算术不一致是复查信号，算术一致也不是图像读对的证明；真实收据可能有折扣/税/舍入与不同价目，规则需按文档定义。保存页ID、文字区域坐标、原识别字符串与字段对应证据；VLM生成值不能取代这些来源。阅读顺序和页面变换错误会使“字都认对”却合计属于另一栏。

## 4. VLM：连接器的结构与事实证据

常见VLM把视觉特征 `[N,Lv,Dv]`经线性/MLP、Q-Former、重采样器或cross-attention连接到语言模型。视觉特征不必来自CLIP，也不必只取最终ViT层；投影到LLM hidden dimension不等于已经语义对齐。CLIP类空间与LLM token空间是不同对象，训练仍需真实图文/问答或跨模态监督。

一种路线把视觉tokens和文本tokens交错送入decoder；另一种让decoder通过cross-attention读取视觉；输出可以是描述、问答、结构、坐标/动作，不能称所有2026 VLM都是单一ViT-MLP-LLM结构。对齐、联合预训练、指令微调是可解释阶段，冻结/解冻/LoRA策略按具体架构选择，没有统一“主要只训projector”的全过程。

更高图像分辨率、切tile、多帧会改变视觉token数与成本。融合时需同步embedding槽位、attention mask、position/time信息和训练labels；视觉槽位常不作文本预测目标，以-100忽略。源固定等量placeholder的merge可演示形状，但不同高分辨率/多图样本不能仅复制同一patch数；真实processor定义插入/扩展策略。

### 4.1 完整token桥接和梯度例

```python
import torch
from torch import nn
torch.set_num_threads(1);torch.manual_seed(42)
projector=nn.Sequential(nn.Linear(4,8),nn.GELU(),nn.Linear(8,6))
text_embedding=nn.Embedding(100,6)
# 明确已展开3个image槽位；这里只验证接口，不包含生成语言模型。
ids=torch.tensor([[1,99,99,99,2,3],[1,99,99,99,4,5]])
visual=projector(torch.randn(2,3,4)); text=text_embedding(ids)
merged=text.clone(); labels=ids.clone();attention=torch.ones_like(ids)
for b in range(len(ids)):
    positions=(ids[b]==99).nonzero(as_tuple=True)[0]
    if len(positions)!=visual.shape[1]: raise ValueError("视觉槽位数量和patch数不匹配")
    merged[b,positions]=visual[b];labels[b,positions]=-100
assert merged.shape==(2,6,6) and attention.shape==labels.shape==(2,6)
merged.square().mean().backward()
assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in projector.parameters())
print("桥接shape/忽略槽位",tuple(merged.shape),(labels==-100).sum().item())
```

这不是“toy VLM已会描述图片”，只有桥接形状/梯度证据；均值池化视觉特征+分类头也不是自回归VLM。源toy数据按类别连续排列切85/15，验证集中只剩最后一类，不能把该分数当全类泛化，实际需分层/任务匹配切分。

多层视觉特征可结合细节与语义，但Qwen3-VL官方DeepStack包含把不同视觉深度的信息注入不同LLM层的设计，不仅`torch.cat`通道就复现了它。视觉Agent还需要截图坐标→动作合同、工具反馈和实际成功评价；OSWorld等任务基准有环境/任务定义，某模型榜单或一般VQA分数不保证任意桌面任务可用。

视频还需保帧的真实采样时间和时空位置：时间戳文本token或时间/宽/高位置编码是可选设计，frame序号不能无条件代替秒数。Qwen3-VL技术报告的例子是Interleaved MRoPE与显式时间戳文本；这是有日期的具体架构，非所有VLM统一规范。换帧序、删关键帧或改变采样间隔后问答是否随证据合理变化，是评价时间理解的一个对照。

源材料的模型比较表、12%错配、CMER治理35%收益、固定50～60%空间准确率、70B单卡2～10小时微调费用均不作为长期已核验结论。模型容量、上下文、vision processor、模板与接口应按所用revision记录，真实LoRA/量化预算还受激活/KV、分辨率、token、序列与设备影响。

## 5. 图文相似度告警不等于幻觉评价

生成token概率是语言分布下的信心，既不校准整段答案正确性，也不保证数字/位置真实；`exp(mean(log p))`是几何平均，不是算术平均。使用独立图文双塔作相似度筛查可以是辅助信号，但文字/图像必须用配套共享空间，不把纯图像DINO特征接任意文本embedding。

source所称CMER实现统计“高文本信心且低图文相似”的占**全部输出**比例，和“在高信心输出中的占比”分母不同；未在本批核验的原始VLM技术报告中找到统一标准定义，因此本库称为**自定义对齐告警率**，不当强制行业KPI或真实幻觉率。低相似可由域差异、短答案或数字任务造成，高相似仍可能错数量、金额、否定与空间关系。

```python
import numpy as np
image=np.array([[1.,0.],[1.,0.],[0.,1.],[0.,1.]])
text =np.array([[1.,0.],[0.,1.],[1.,0.],[0.,1.]])
confidence=np.array([.95,.9,.85,.4])
image=image/np.linalg.norm(image,axis=1,keepdims=True)
text=text/np.linalg.norm(text,axis=1,keepdims=True)
similarity=np.sum(image*text,axis=1)
high=confidence>.8; flags=high & (similarity<.25)
print("相似度",similarity.tolist(),"告警",flags.tolist())
print("全部输出占比",flags.mean(),"高信心输出内占比",flags.sum()/high.sum())
assert np.isclose(flags.mean(),.5) and np.isclose(flags.sum()/high.sum(),2/3)
```

阈值需用任务人工标注的正确/错误集测告警Precision/Recall和漏报，不设统一0.25/0.8或提高阈值就得到可靠性保证。监控按模型/提示/输入来源分组、记录原始score与人工复核类别；比例升高还可能是输入或编码器/预处理改版，并不唯一诊断模型漂移。

真实grounding检查可把答案拆为可核查事实：对象有无、数量、数值/文字、坐标/关系，保留区域证据与人工标注。比较原图、遮图、无关图/改图，观察答案与正确率是否随证据合理变化；仅文字先验答对不能证明看图能力。五图十五问只能作初步失败集，不证明一般性能或算出标准CMER。

## 6. 管道的数据合同要含语义与变换

典型链为bytes解码→EXIF方向/色彩→任务预处理→检测/分割→框回原图→crop及分类/OCR→实例/字段聚合→结构输出。各模型可能要求不同resize、RGB/BGR、`[0,1]`/`[-1,1]`或mean/std；给检测器的tensor直接crop交分类器不一定满足分类器权重的官方transforms。

`tuple[float,float,float,float]`只表达四个数，不能自动判断xyxy还是cxcywh。需显式format、units、原图/模型图size、scale/padding、方向、label map、概率/质量score含义、shape/dtype/范围，配合模型适配器与小标注图验算。即使声明与有序关系都合法，调用方把cxcywh错误标成xyxy仍可能通过；已知框正反变换和图上叠加检验才补上语义证据。

每个stage记录revision和trace ID，检测对象用稳定`detection_id`关联crop/classification，不依赖过滤后列表下标。检测数组长度不齐不能用zip静默丢尾；空检测是合法空列表，模型失败是另一状态。越界端点四项都裁剪，完全在图外/裁剪后退化要明确丢弃原因；微小crop可以保检测但分类skip，不能默认“resize224就有了细节”。

### 6.1 完整本地合同与失败fixture

下面只用已解码RGB小数组与预造框，分类函数是颜色规则fixture；**无YOLO/Mask R-CNN/ConvNeXt推理**。预处理范围、metadata、长度、裁剪、错误和关联键都可运行核验。bytes/EXIF解码是外层合同，本例要求已校正方向，未实现上传服务。

```python
import json
import time
import numpy as np

class ContractError(ValueError):
    def __init__(self,code,message): super().__init__(message);self.code=code

def image_tensor(array,meta):
    a=np.asarray(array)
    if meta.get("color")!="RGB" or meta.get("orientation")!="upright":
        raise ContractError("image_metadata","需已校正方向的RGB")
    if a.ndim!=3 or a.shape[2]!=3 or not a.shape[0] or not a.shape[1]:
        raise ContractError("image_shape","需要非空HWC三通道")
    if a.dtype==np.uint8 and meta.get("range")=="0_255": return a.astype(np.float32)/255
    if np.issubdtype(a.dtype,np.floating) and meta.get("range")=="0_1":
        if np.isfinite(a).all() and a.min()>=0 and a.max()<=1:return a.astype(np.float32)
    raise ContractError("image_range","dtype/范围/声明不一致")

def adapt_detections(raw,H,W):
    if any(key not in raw for key in ["boxes","scores","labels"]):
        raise ContractError("detection_fields","缺少检测必需字段")
    fmt,units=raw.get("format"),raw.get("units")
    if fmt not in {"xyxy","cxcywh"} or units not in {"pixels","normalized"}:
        raise ContractError("box_metadata","框格式/单位必须声明")
    b=np.asarray(raw["boxes"],float)
    if b.size==0 and b.shape in ((0,),(0,4)):b=np.empty((0,4))
    s=np.asarray(raw["scores"],float);label=np.asarray(raw["labels"])
    if b.ndim!=2 or b.shape[1]!=4 or s.shape!=(len(b),) or label.shape!=s.shape:
        raise ContractError("detection_lengths","框/分数/标签数量和shape必须相等")
    if (not np.isfinite(b).all() or not np.isfinite(s).all() or np.any((s<0)|(s>1))
            or (len(label) and (not np.issubdtype(label.dtype,np.integer) or np.any(label<0)))):
        raise ContractError("detection_values","非法框/分数/非整型标签")
    if fmt=="cxcywh":b=np.c_[b[:,:2]-b[:,2:]/2,b[:,:2]+b[:,2:]/2]
    if units=="normalized":b=b*np.array([W,H,W,H])
    records=[];rejected=[]
    for index,(box,score,cls) in enumerate(zip(b,s,label)):
        if np.any(box[2:]<=box[:2]):
            rejected.append({"source_index":index,"reason":"invalid_box_order"});continue
        clipped=np.clip(box,[0,0,0,0],[W,H,W,H])
        if np.any(clipped[2:]<=clipped[:2]):
            rejected.append({"source_index":index,"reason":"empty_after_clip"});continue
        records.append({"detection_id":f"fixture:{index}","box":clipped.tolist(),
                        "score":float(score),"class_id":int(cls)})
    return records,rejected

def pipeline(image,meta,raw,min_crop=3):
    start=time.perf_counter();normalized=image_tensor(image,meta);t1=time.perf_counter()
    H,W=normalized.shape[:2];detections,rejected=adapt_detections(raw,H,W);t2=time.perf_counter()
    for detection in detections:
        x1,y1,x2,y2=detection["box"]
        crop=normalized[int(np.floor(y1)):int(np.ceil(y2)),int(np.floor(x1)):int(np.ceil(x2))]
        if min(crop.shape[:2])<min_crop:
            detection["classification_status"]="skipped_tiny";continue
        # 教学fixture：颜色规则，不是学习模型置信概率。
        color="红" if crop[...,0].mean()>.8 else "其他"
        detection["classification_status"]="fixture_only"
        detection["classification"]={"detection_id":detection["detection_id"],"color_rule":color}
    t3=time.perf_counter()
    result={"image_id":"fixture","model_revision":"fixture-v1","geometry":"原图xyxy像素",
            "detections":detections,"rejected":rejected,
            "timing_ms":{"validate_range":(t1-start)*1000,"adapt_clip":(t2-t1)*1000,
                         "fixture_classify":(t3-t2)*1000,"local_total":(t3-start)*1000}}
    json.dumps(result,ensure_ascii=False,allow_nan=False)
    return result

image=np.zeros((20,30,3),np.uint8);image[4:16,8:22,0]=255
meta={"color":"RGB","orientation":"upright","range":"0_255"}
raw={"format":"cxcywh","units":"pixels","boxes":[[15,10,14,12],[.5,.5,1,1],[50,50,5,5]],
     "scores":[.9,.7,.6],"labels":[0,0,0]}
result=pipeline(image,meta,raw)
assert result["detections"][0]["box"]==[8.,4.,22.,16.]
assert result["detections"][0]["classification"]["color_rule"]=="红"
assert result["detections"][1]["classification_status"]=="skipped_tiny"
assert result["rejected"][0]["reason"]=="empty_after_clip"
print("检测合同",result["detections"],"拒绝",result["rejected"])
empty={"format":"xyxy","units":"pixels","boxes":[],"scores":[],"labels":[]}
assert pipeline(image,meta,empty)["detections"]==[]
failures=[("float_range",image.astype(float),meta,raw),
          ("bad_color",image,{**meta,"color":"BGR"},raw),
          ("wrong_length",image,meta,{**raw,"scores":[.9]}),
          ("unknown_format",image,meta,{**raw,"format":"unknown"}),
          ("float_labels",image,meta,{**raw,"labels":[.5,0.,0.]})]
for name,img,m,r in failures:
    try:pipeline(img,m,r)
    except ContractError as e:print(name,e.code)
    else:raise AssertionError("坏fixture必须被识别")
# 证明有序四元组仍可能错误声明语义：两个格式都合法但结果不同。
wrong={**raw,"boxes":[[15,10,14,12]],"scores":[.9],"labels":[0],"format":"xyxy"}
assert pipeline(image,meta,wrong)["rejected"][0]["reason"]=="invalid_box_order"
ambiguous={**wrong,"boxes":[[10,10,15,15]]}
box_as_xyxy=pipeline(image,meta,ambiguous)["detections"][0]["box"]
box_as_center=pipeline(image,meta,{**ambiguous,"format":"cxcywh"})["detections"][0]["box"]
assert box_as_xyxy!=box_as_center  # 类型和有序检查无法替代格式来源与golden验算。
print("同一合法tuple两种语义",box_as_xyxy,box_as_center)
```

错误和空结果分别表达，range/dtype错误不被除255“自动纠正”。实际classifier还要独立执行它自己的crop/resize/normalize，模型输入形状、label map和输出分数不能靠这个颜色fixture证明。处理独立stage异常时保留已有效检测并标明哪一步失败，意外内部错误不能用泛泛except吞掉并返回“成功空结果”。

上传/HTTP层需在**当前库版本**按lifespan加载模型、验证readiness，并对格式、实际解码失败、尺寸/内容类型、超时/资源界限和请求取消给出清楚的错误状态；FastAPI旧`on_event`样例不是新项目首选。CPU重推理不能直接在async事件循环里阻塞；需要合适工作队列/执行池，模型共享与并发状态要检查。本批没有启动服务、监听端口或测试远端请求。

## 7. 掩码RLE、概念查询与响应规模

mask序列化需含shape、行/列顺序、编码类型；源自写`0x数量;1x数量`与COCO RLE不是同一个协议。COCO工具常用列主序/特定压缩counts，自写row-major串不能直接喂COCOeval。RLE对大片连续区域高效，对棋盘格/噪声可比原始mask还大，不能保证10对象JSON始终小于1MB。

### 7.1 完整自定义RLE及非法counts检查

```python
import json
import numpy as np

def encode_mask(mask):
    a=np.asarray(mask)
    if a.ndim!=2 or not np.isin(a,[0,1]).all():raise ValueError("二维二值mask")
    counts=[];previous=0;count=0
    for value in a.ravel(order="C"):
        if int(value)==previous:count+=1
        else:counts.append(count);previous=int(value);count=1
    counts.append(count)
    return {"type":"alternating_rle_v1","shape":list(a.shape),"order":"C","counts":counts}

def decode_mask(payload):
    if payload.get("type")!="alternating_rle_v1" or payload.get("order")!="C":raise ValueError("编码不匹配")
    shape=payload["shape"];counts=payload["counts"]
    if (len(shape)!=2 or any(type(v) is not int or v<0 for v in shape)
            or any(type(v) is not int or v<0 for v in counts) or sum(counts)!=int(np.prod(shape))):
        raise ValueError("shape或counts总数非法")
    flat=np.concatenate([np.full(c,i%2,dtype=np.uint8) for i,c in enumerate(counts)]) if counts else np.array([],np.uint8)
    return flat.reshape(shape,order="C")

mask=np.zeros((6,8),np.uint8);mask[1:5,2:6]=1
payload=encode_mask(mask);assert np.array_equal(decode_mask(payload),mask)
assert np.array_equal(decode_mask(encode_mask(np.ones((2,2),np.uint8))),np.ones((2,2),np.uint8))
print("RLE",payload,"JSON字节",len(json.dumps(payload).encode()))
try:decode_mask({**payload,"counts":[1,2]})
except ValueError:print("坏counts被拒绝",True)
else:raise AssertionError("不能默默补0/截断")
checker=np.indices((16,16)).sum(0)%2
print("棋盘格raw字节/JSON字节",checker.astype(np.uint8).nbytes,len(json.dumps(encode_mask(checker)).encode()))
```

响应把mask映射到原图/约定ROI后，尺寸、bbox与概率阈值才可解释。模型输出局部mask、全图mask、polygon或原生压缩字段需分别适配；SAM系列/开放检测器并非同样原生字段，也并非全部有视频稳定ID。

多概念图像编码可缓存后重复运行提示/解码，稀疏视觉提示和复用已有mask特征也是值得验证的效率思路；缓存必须绑定图像、模型/processor revision、尺度与方向，不复用到不同输入。HF SAM3当前文档有分开预计算视觉/文本特征的示例，本批只核对接口，不承诺源SAM-MI固定减少96%调用或加速1.6倍。

概念输入优先显式短语列表，保留原话与解释，不按每个`and/or`拆语义或丢掉关系后悄悄改任务。`["black and white cat","red car"]`是两个概念，而不是black、white cat、red car三类。多概念结果需要`query_id + local_instance_id`或明确全局ID，跨概念同一个对象再按业务规则合并；源stub每概念重复0/1不能称唯一全局实例。

“文字返回候选→用户include/exclude→输出选择集”的交互应保存候选ID、图像/模型revision、原始概念与选取记录，防止刷新后ID换了却沿用旧选择。图像中概念缺席应允许空列表，不用固定两矩形stub作为所有概念的真实命中。

2026-10-04核对：Meta官方SAM3 processor与HF `Sam3Processor`是不同接口。HF当前文档用processor的images/text输入及`post_process_instance_segmentation`等模型对应后处理；源把官方`set_text_prompt`模式塞进HF processor并通用`post_process_masks`的调用不保留为已验证实现。重跑真实模型时固定revision/访问条件/processor，再验证坐标、presence、mask与video ID，本批没有下载或调用模型。

## 8. 性能预算、排队与真实端到端测量

计时范围明确包括或排除：读请求、图像解码、传输、预处理、模型前向、后处理、crop、分类/OCR、验证与序列化。上例`local_total`只含本地fixture，不含HTTP排队/JPEG解码，更无真实神经模型；不能把它当服务p95或用来推荐硬件。

实际目标设备先warmup，再重复测多个尺寸/对象数/空图/异常图和真实并发。GPU前向异步时要用正确同步或设备event，不以Python调用耗时当全部执行；异步overlap计时也不宜盲目每阶段同步改变系统行为。报告batch、precision、模型revision、硬件、样本数、p50/p95及吞吐、队列等待与失败比例。

不固定预处理最大、检测占70～90%或阶段55%/15%预算。各阶段p95**不能直接相加**得到总p95，因为尾部发生在不同请求且有相关/并行；总时延应对同一请求端到端测量。`1000/单请求ms`只是在特定串行条件下的粗估，不是任意并发/batch系统吞吐上限。

microbatch等待窗口可能增加延迟并提高利用率，但吞吐收益依负载、形状、kernel和资源而变；记录组batch等待、请求回填与超时/取消，等待时间也可能受队列堵塞影响而超过名义10/20ms。不能把固定20ms窗口或SLA<50ms绝不batch写成通用规律。

若性能不足，先按测量判断是解码、模型、后处理、数据传输还是队列；可以改变输入尺寸、候选上限、批处理、缓存、模型/precision或后处理实现，每次核查质量损失。源“总先Pillow/NVJPEG”“超预算30%必换模型”缺任务依据，不照搬。服务框架的功能/维护状态随版本变化；TorchServe官方目前标注有限维护，不能无日期作为新项目普遍默认推荐。

## 9. 练习与参考验收

1. CTC的`a blank a`与`a a`分别是什么？**答案：**aa与a；目标aa至少三步。`zero_infinity=True`遮掉inf不是对齐问题已修好。
2. greedy与beam怎么公平比较？**参考：**同log概率、有效长度、blank/字表、候选目标与语言模型设置，报告CER/WER与延迟。小穷举可验证path合并，真实500步识别训练本批未执行。
3. 低CER能保证发票字段正确吗？**答案：**不能；本例一个字符让19.80变79.80，JSON仍合法。需要字段/单位/页区域证据和真实GT匹配。
4. 20张收据提取item/price F1怎样定义？**参考：**规范名字、decimal币种/单位和行项一对一匹配，报重复/缺失/错价；预定义容差与阅读顺序，不把OCR文本存在就算字段TP。
5. projector输出维度等于LLM即可回答图片吗？**答案：**形状只保证接口，语义对齐、attention/positions、训练目标与数据还要建立。source toy分类器不是生成VLM。
6. CLIP相似度高能保证数字读对吗？**答案：**不能；对齐告警只辅助筛查，需区域、数字和人工证据，custom rate不要命名成通用幻觉标准。
7. tuple四数字能辨所有坐标错吗？**答案：**不能；必须metadata+adapter+golden正反变换+叠图。错误格式有时仍满足有序关系。
8. 某检测是1×1，怎么返回？**答案：**按输入和业务规则保合法检测，分类标`skipped_tiny`；完全图外/退化框标拒绝原因，不能假装成功分类或吞掉整请求。
9. 加RLE是否保证响应<1MB？**答案：**不；按真实mask形状/复杂度测payload，counts总量和order须一致，必要时换协议/压缩/限制输出，而非默默删对象。
10. 一页请求p95怎么算？**答案：**同请求全链测量含队列，分阶段帮助归因，不能加各阶段p95。microbatch用真实并发对照，源5QPS/10ms/GPU实验本批未执行。
11. 视觉问答/LoRA/换encoder开放练习怎样记录？**参考：**按图像/任务/独立验证记录正确、部分正确、无证据幻觉和拒识，冻结配方后测试；换视觉编码器需匹配预处理与视觉token/LLM连接训练，不称机械可换。没有模型调用则只标设计/接口核对，不编性能结果。

## 来源与核验备注

- 2026-10-04：AI Engineering from Scratch Phase04/16、19、25及24的管道/概念处理增补，提交 `3be078b37ffd8f0c04953c0678e48f5c6d0c7775`，正文、代码、测验、输出与图意完整读取；[来源记录](../../来源保全/AI-Engineering-From-Scratch.md)。CLIP/SigLIP图文对齐与zero-shot在03维护，图像SSL、检索评价与索引选型接06，几何与掩码指标在07。
- 原机制：[CTC](https://www.cs.toronto.edu/~graves/icml_2006.pdf)、[CRNN](https://arxiv.org/abs/1507.05717)、[Donut](https://arxiv.org/abs/2111.15664)。当前核对：[PyTorch CTCLoss](https://docs.pytorch.org/docs/stable/generated/torch.nn.CTCLoss.html)、[PaddleOCR快速开始](https://www.paddleocr.ai/latest/en/quick_start.html)、[Qwen3-VL官方](https://github.com/QwenLM/Qwen3-VL)、[HF SAM3](https://huggingface.co/docs/transformers/model_doc/sam3)、[FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/)、[TorchServe维护说明](https://github.com/pytorch/serve)。
- 未安装PaddleOCR/EasyOCR、未调用VLM/SAM/托管API、未开启HTTP服务或做GPU吞吐；程序验证只覆盖CTC/字段/桥接/自定义告警/合同/RLE的小fixture。旧`.ocr(image_path)`等高时效调用不复制为当前通用API，具体版本用官方入口复查。

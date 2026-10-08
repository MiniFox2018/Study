# MCP通信与状态工程

> 本专题补充[核心第10章：MCP](../01-核心章节/10-模型上下文协议-MCP.md)。核心协议固定`2026-07-28`，Apps桥接固定`2026-01-26`，Tasks固定扩展`2026-07-28`。2026-10-08读取/核验与新CPU程序执行；不把教学fixture当真实SDK、HTTP、浏览器或生产发布验收。

## 1. 学习目标、先修与证明边界

先能读JSON对象、列表与字符串，理解函数参数验证、错误返回和事务的提交/回滚。这里研究的具体问题是：一个host连接多个外部能力，怎样确保它发现的函数、发送的参数、网关路由、执行的动作、消费的结果，以及失败后的恢复都指向同一合同。

读完应能解释完整消息、自己改一个拒绝边界、运行本地负例，并指出哪些性质尚未实证。MCP标准化传递能力；授权、业务状态、有效证据、实际操作是否被用户允许，仍需实现。自报身份、tool annotations、可猜handle、模型文字与“程序返回成功”都不能自己产生授权。

下文8个Python块各自完整、只用标准库。可把一个块保存为临时`.py`运行；SQLite例只在`/tmp`临时目录建库并清理，时间是虚拟毫秒或秒。没有安装包、调用模型、启动子进程MCP或HTTP服务。JSON片段、表和流程是协议示意；程序的明确子集不是完整JSON Schema、MCP SDK或官方conformance套件。

## 2. 四种状态寿命不能混用

| 状态 | 由什么命名 | 保存多久 | 失败后需要什么 |
|---|---|---|---|
| 协议元数据 | 本次`params._meta` | 一次请求 | 下一请求重新声明并验证 |
| 在途运输工作 | JSON-RPC请求ID/响应流 | 一次在途RPC | 取消、终态竞争、未知副作用核对 |
| MRTR输入交互 | 原方法/参数、input键、opaque state | 一个有界输入流程 | 新ID重试、原封state、当前输入与完整性校验 |
| 持久业务任务/草稿 | 明确`taskId`或业务handle | 跨请求/重启 | 存储、每次授权、租约/版本、到期与回执 |

现代无protocol session不等应用无状态。一号replica内存创建草稿，下一POST到二号replica就看不到，是应用存储失误；sticky routing只遮住症状。应返回明确handle，按可信principal定位共享记录，或将短暂MRTR状态完整性保护后随重试携带。业务handle本身也不授权：认证服务逐次校验所有权；无认证服务若将handle当bearer capability，应有足够熵、明确寿命与相应风险。

任务一旦已返回，原RPC已结束。关闭原响应不能命名该task；要新发`tasks/cancel`。同样，一个订阅是长请求，其filter与通知状态归该请求，并非让其他RPC依赖连接历史。

## 3. stdio、Streamable HTTP与版本适配

### 3.1 字节帧、进程与peer

stdio的规范帧是UTF-8 JSON-RPC一行一条，`stdout`只写合法协议消息，诊断去`stderr`。JSON字符串中的换行要转义，不能把漂亮打印的多行JSON当一帧。一次read可能切在中文UTF-8字符中间，也可能带两条消息；先按换行累积字节，再解码完整帧。设单帧字节上限，EOF有残帧时报告未完整接收。stderr有信息不等错误；EOF是跨平台优雅退出信号，超时才按宿主系统策略结束进程。

客户端记录pending IDs和运输健康，响应ID要在JSON类型和值上都对应原请求，bool不等整数ID。有效请求只发一个结果或错误，不能两个都有；通知没有关联响应。服务器现代不会独立反向发请求，elicitation/sampling/roots在MRTR结果内交付。丢失在途RPC后恢复peer、重新发现/列目录/订阅，再按动作安全性决定重试。

### 3.2 HTTP语义与错误顺序

单MCP endpoint每条客户端消息用新POST；客户端Accept包含JSON和SSE，请求是JSON正文，不能POST JSON-RPC response。普通请求回应一个JSON对象，或先有该请求相关通知再有最终响应的SSE；订阅由`subscriptions/listen`的POST响应保持打开。没有现代独立GET流、session DELETE或Last-Event-ID恢复。现代-only端点对旧GET/DELETE返回405是规范推荐响应；收到session/replay headers忽略且不mint/echo。

每次验证顺序是envelope与元数据类型→头/正文镜像一致→匹配版本是否支持→所需能力→具体参数和可信主体授权→handler。header表示被网关允许的read，但正文执行delete，必须拒绝；正文版本不支持、header又不同，也应先报`-32020`，不能把语义冲突掩盖成版本协商。字段名大小写不敏感，值大小写敏感。

| HTTP情况 | 实际合同 |
|---|---|
| request元数据缺失/错类型 | 400，JSON-RPC `-32602` |
| 必需头缺失/冲突 | 400，`-32020` |
| 头与正文一致但版本未支持 | 400，`-32022`，data含requested/supported |
| 所需可选能力缺失 | 400，`-32021`及requiredCapabilities |
| 服务器未实现RPC method | 404，JSON-RPC `-32601` |
| 接受通知 | 202、无body |
| 拒收通知 | HTTP错误；可附**无id**的JSON-RPC错误诊断body |

最后两行是运输规则，当前core没有HTTP客户端通知；下例用明确课程扩展通知检serializer，不创造新core方法。不要把`tools/list`简单去ID当合法核心通知。普通JSON-RPC通知没有关联success/error响应，HTTP拒收诊断的例外需要独立解释。

Origin防DNS rebinding，应精确匹配允许源；没有Origin的非浏览器客户端可以被接受。Origin不等认证，localhost通常只绑定127.0.0.1；本地服务依然需自己的授权。prefix `https://trusted.example`会误放行`https://trusted.example.evil`，不适合作为Origin policy。

### 3.3 完整CPU例：逐请求校验和字节分帧

输入是JSON消息对象与可选镜像头；输出为状态/响应或通知无响应。成功列表有cache字段，recognized错误保持分层。最后按2字节切割中文JSON帧，证明本地buffer正确；它没有启动真pipe或HTTP，不证明反压、子进程退出和网络协商。这里只检查已说明的能力结构和几个方法，方法专用全schema仍须SDK/完整验证器。

```python
import copy,json
V='2026-07-28';PV='io.modelcontextprotocol/protocolVersion';CAP='io.modelcontextprotocol/clientCapabilities'
CACHE={'server/discover','tools/list','resources/list','resources/templates/list','resources/read','prompts/list'}
MRTR={'tools/call','resources/read','prompts/get'}
class Fault(Exception):
    def __init__(self,code,message,data=None):self.code=code;self.message=message;self.data=data

def request(rid,method,p=None,caps=None,version=V):
    return {'jsonrpc':'2.0','id':rid,'method':method,'params':{**(p or {}),'_meta':{PV:version,CAP:{} if caps is None else caps}}}
def validate(message,headers=None):
    if type(message) is not dict or message.get('jsonrpc')!='2.0' or type(message.get('method')) is not str:raise Fault(-32600,'envelope')
    if 'id' in message and type(message['id']) not in (int,str):raise Fault(-32600,'id')
    p=message.get('params');meta=p.get('_meta') if type(p) is dict else None
    if type(meta) is not dict or type(meta.get(PV)) is not str or type(meta.get(CAP)) is not dict:raise Fault(-32602,'metadata')
    caps=meta[CAP]
    for k in ('sampling','roots','elicitation','extensions'):
        if k in caps and type(caps[k]) is not dict:raise Fault(-32602,'capability shape')
    if 'extensions' in caps and any(type(x) is not dict for x in caps['extensions'].values()):raise Fault(-32602,'extension shape')
    if 'elicitation' in caps and any(type(x) is not dict for x in caps['elicitation'].values()):raise Fault(-32602,'elicitation shape')
    # fixture只支持三种routing name；HTTP拒收诊断没有相关RPC id。
    if headers is not None:
        h={}
        for k,v in headers.items():
            key=k.casefold()
            if key in h:raise Fault(-32020,'duplicate header')
            h[key]=v
        expected={'mcp-protocol-version':meta[PV],'mcp-method':message['method']}
        name_field={'tools/call':'name','resources/read':'uri','prompts/get':'name'}.get(message['method'])
        if name_field:expected['mcp-name']=p.get(name_field)
        if any(type(v) is not str or h.get(k)!=v for k,v in expected.items()):raise Fault(-32020,'header mismatch')
    if meta[PV]!=V:raise Fault(-32022,'version',{'requested':meta[PV],'supported':[V]})
    return caps

def serve(message,headers=None):
    is_note=type(message) is dict and 'id' not in message
    try:
        caps=validate(message,headers);m=message['method']
        if m=='tools/call':
            if message['params'].get('name')!='approve':raise Fault(-32602,'unknown tool')
            eli=caps.get('elicitation')
            if type(eli) is not dict or eli and type(eli.get('form')) is not dict:raise Fault(-32021,'form needed',{'requiredCapabilities':{'elicitation':{'form':{}}}})
        if m not in ('tools/list','server/discover','tools/call','notifications/com.example/demo'):raise Fault(-32601,'method')
        payload={'tools':[]} if m=='tools/list' else {'supportedVersions':[V],'capabilities':{'tools':{}}} if m=='server/discover' else {'content':[{'type':'text','text':'fixture complete'}]}
        result={'resultType':'complete',**payload,'_meta':{
            'io.modelcontextprotocol/serverInfo':{'name':'wire-fixture','version':'1'}}}
        if m in CACHE:result.update(ttlMs=0,cacheScope='private')
        if is_note:return (202,None) if headers is not None else None
        return (200,{'jsonrpc':'2.0','id':message['id'],'result':result})
    except Fault as e:
        error={'code':e.code,'message':e.message}
        if e.data is not None:error['data']=e.data
        if is_note:
            return (400,{'jsonrpc':'2.0','error':error}) if headers is not None else None
        diagnostic={'jsonrpc':'2.0','error':error}
        if type(message) is dict and type(message.get('id')) in (int,str):diagnostic['id']=message['id']
        return (404 if e.code==-32601 else 400,diagnostic)

def consume(message,response):
    if type(response) is not dict or response.get('jsonrpc')!='2.0' or type(response.get('id')) is not type(message['id']) or response.get('id')!=message['id']:raise ValueError('response correlation')
    if ('result' in response)==('error' in response):raise ValueError('exclusive result/error')
    if 'error' in response:return response['error']
    r=response['result'];kind=r.get('resultType');m=message['method']
    if kind=='input_required':
        if m not in MRTR or not ('inputRequests' in r or 'requestState' in r) or 'inputRequests' in r and type(r['inputRequests']) is not dict or 'requestState' in r and type(r['requestState']) is not str:raise ValueError('MRTR shape')
    elif kind=='complete':
        meta=r.get('_meta');info=meta.get('io.modelcontextprotocol/serverInfo') if type(meta) is dict else None
        if type(info) is not dict or any(type(info.get(k)) is not str for k in ('name','version')):raise ValueError('server identity metadata')
        if m in CACHE and (type(r.get('ttlMs')) is not int or r['ttlMs']<0 or r.get('cacheScope') not in ('public','private')):raise ValueError('cache hints')
    else:raise ValueError('unknown/unnegotiated result type')
    return copy.deepcopy(r)

def rejects(fn):
    try:fn()
    except ValueError:return
    raise AssertionError('expected rejection')
invalid=request(99,'tools/list');invalid['id']=True
assert 'id' not in serve(invalid)[1] and serve([1])[1]['error']['code']==-32600
a=request(1,'tools/list');ok=serve(a)[1];assert consume(a,ok)['tools']==[]
assert serve(request(100,'fixture/unsupported'))[0]==404
no_identity=copy.deepcopy(ok);no_identity['result'].pop('_meta');rejects(lambda:consume(a,no_identity))
b=request(2,'tools/list');b['params']['_meta'].pop(CAP);assert serve(b)[1]['error']['code']==-32602
bad=request(3,'tools/list',version='2027-01-01');h={'MCP-Protocol-Version':V,'Mcp-Method':'tools/list'}
assert serve(bad,h)[1]['error']['code']==-32020
h['MCP-Protocol-Version']='2027-01-01';assert serve(bad,h)[1]['error']['data']=={'requested':'2027-01-01','supported':[V]}
c=request(4,'tools/call',{'name':'approve'});assert serve(c)[1]['error']['code']==-32021
assert serve(request(6,'tools/call',{'name':'approve'},caps={'elicitation':{'url':{}}}))[1]['error']['code']==-32021
assert 'result' in serve(request(7,'tools/call',{'name':'approve'},caps={'elicitation':{}}))[1]
rejects(lambda:consume(a,{**ok,'id':True}));rejects(lambda:consume(a,{**ok,'error':{}}))
rejects(lambda:consume(a,{'jsonrpc':'2.0','id':1,'result':{'resultType':'complete','tools':[]}}))
rejects(lambda:consume(a,{'jsonrpc':'2.0','id':1,'result':{'resultType':'input_required','requestState':'x'}}))
rejects(lambda:consume(a,{'jsonrpc':'2.0','id':1,'result':{'resultType':'future_mode'}}))
ok['result']['futureHint']=7;assert consume(a,ok)['futureHint']==7
note=request(5,'notifications/com.example/demo');note.pop('id');headers={'MCP-Protocol-Version':V,'Mcp-Method':note['method']}
assert serve(note,headers)==(202,None)
note['params']['_meta'].pop(CAP);status,diagnostic=serve(note,headers);assert status==400 and 'id' not in diagnostic and diagnostic['error']['code']==-32602
assert serve(note) is None
class Frames:
    def __init__(self):self.buffer=b''
    def feed(self,chunk):
        self.buffer+=chunk;out=[]
        while b'\n' in self.buffer:
            line,self.buffer=self.buffer.split(b'\n',1)
            if len(line)>1024:raise ValueError('frame byte budget')
            out.append(json.loads(line.decode('utf-8')))
        if len(self.buffer)>1024:raise ValueError('incomplete frame budget')
        return out
    def eof(self):
        if self.buffer:raise ValueError('EOF with unfinished frame')
framed=json.dumps(request(11,'tools/list',{'label':'中文\n行'}),ensure_ascii=False,separators=(',',':')).encode()+b'\n'
f=Frames();pieces=[]
for start in range(0,len(framed),2):pieces+=f.feed(framed[start:start+2])
f.eof();assert pieces[0]['params']['label']=='中文\n行'
rejects(lambda:Frames().feed(b'DEBUG tools loaded\n'))
f=Frames();f.feed(b'{');rejects(f.eof)
print('wire: metadata/header/version/capability分层、响应关联、cache/MRTR负例、通知接受与拒收诊断通过；仅内存子集')
```

### 3.4 双时代适配与目录合并

modern request不需要先initialize。stdio双时代客户端宜先`server/discover`：有效现代发现或recognized现代错误都保持modern；`-32022`选共同版本重试，新ID。未知错误/超时按官方兼容流程可探旧initialize。精确配置peer的legacy白名单、有界探测、有效initialize正证是应用加严：核jsonrpc、ID、result/error互斥、所支持legacy revision、capabilities与serverInfo结构后才发initialized。不能把超时当用户批准，也不能把应用加严误称协议MUST。

canonical/local名称各存一份。固定排序再合并，前缀来自稳定peer配置，不来自可能重复/自报的serverInfo。两peer都叫search时，选择显式prefix或报告两个owner的冲突；禁止silent overwrite/静默忽略。路由只能查已准入的owner，owner离线不能悄悄把参数发给别的server。旧适配器和modern parser分别验；运输重启后重新建peer资料。

## 4. 镜像头与参数路由

`MCP-Protocol-Version`镜像正文版本；`Mcp-Method`镜像method；call/get镜像name，resource read镜像uri。Tasks的方法另外镜像taskId。可选`x-mcp-header: "Region"`使某个参数值成为`Mcp-Param-Region`，让网关不用解析整正文也能路由；服务器仍要比较正文的真值。

有效annotation位置是仅经`properties`链从根静态可达的属性，例如`properties.route.properties.region`。嵌套对象允许；穿过items、oneOf/anyOf/allOf/not、if/then/else或$ref都不允许。检查完整schema树以发现非法位置，而非只看这次执行走的分支。annotation名字是非空HTTP token、忽略大小写唯一，值类型限string/integer/boolean；number不合法，integer限`[-(2^53-1), 2^53-1]`。stdio可以忽略此HTTP注解；HTTP client应按规范镜像或排除非法tool。

字符串原值UTF-8编码后用标准Base64 sentinel `=?base64?…?=`；不能先trim/normalize。Unicode、控制字符、首尾空白和完整sentinel-looking值需编码；内部ASCII空格/HTAB可按HTTP合法值传递，本例保留。bool写lowercase，整数写十进制。值不存在或null省头；recognized header缺失、重复、错值、malformed编码应在分派前拒绝。未知镜像头的透明intermediary应转发并不解释它。整数推荐按数值比较，因此header `42.0`可等于正文42，不能用浮点舍入接收超safe范围整数。

敏感字段不进header是规范建议；host可把固定credential/PII准入策略加严成拒绝。日志只保header名字/拒绝类别，Base64仍可逆，不能把编码值当脱敏。以下完整例不跟随外部$ref、不做完整schema验证，专门证明annotation位置和镜像合同；本地schema预算和敏感名字denylist是应用策略。

```python
import base64,re,copy
from decimal import Decimal,InvalidOperation
TOKEN=re.compile(r"[!#$%&'*+\-.^_`|~0-9A-Za-z]+")
SAFE=2**53-1;SENSITIVE={'password','token','secret','authorization','apikey'}
def canon_name(s):return ''.join(c for c in s.casefold() if c.isalnum())
def bindings(schema):
    if type(schema) is not dict or schema.get('type')!='object':raise ValueError('object-root inputSchema')
    found=[];names=set();nodes=[0]
    def walk(node,path=()):
        nodes[0]+=1
        if len(path)>24 or nodes[0]>500:raise ValueError('schema budget')
        if type(node) is dict:
            if 'x-mcp-header' in node:
                # 有效路径：properties,A,properties,B,...；不跟随任何$ref。
                if not path or len(path)%2 or any(k!='properties' for k in path[0::2]) or any(type(k) is not str for k in path[1::2]):raise ValueError('not properties-only reachable')
                suffix=node['x-mcp-header'];typ=node.get('type')
                if type(suffix) is not str or not TOKEN.fullmatch(suffix) or suffix.casefold() in names or typ not in ('string','integer','boolean'):raise ValueError('header definition')
                if any(canon_name(x) in SENSITIVE for x in (*path[1::2],suffix)):raise ValueError('local sensitive-field policy')
                names.add(suffix.casefold());found.append((path[1::2],'Mcp-Param-'+suffix,typ))
            for k,v in node.items():
                if type(v) in (dict,list):walk(v,(*path,k))
        elif type(node) is list:
            for i,v in enumerate(node):
                if type(v) in (dict,list):walk(v,(*path,i))
    walk(schema);return found

def at(obj,path):
    for k in path:
        if type(obj) is not dict or k not in obj:return None
        obj=obj[k]
    return obj

def text(value,typ):
    if typ=='string' and type(value) is str:return value
    if typ=='boolean' and type(value) is bool:return 'true' if value else 'false'
    if typ=='integer' and type(value) is int and -SAFE<=value<=SAFE:return str(value)
    raise ValueError('primitive type/safe integer')

def encode(s):
    # 本例允许内部ASCII空格/HTAB；首尾空白、控制符、Unicode和完整sentinel必须编码。
    ascii_safe=all(c=='\t' or 0x20<=ord(c)<=0x7e for c in s)
    sentinel=s.startswith('=?base64?') and s.endswith('?=')
    if s and ascii_safe and s==s.strip() and not sentinel:return s
    return '=?base64?'+base64.b64encode(s.encode('utf-8')).decode('ascii')+'?='

def decode(s):
    if type(s) is not str:raise ValueError('header type')
    if s.startswith('=?base64?') and s.endswith('?='):
        try:return base64.b64decode(s[9:-2],validate=True).decode('utf-8')
        except (ValueError,UnicodeDecodeError) as e:raise ValueError('encoded header') from e
    if not s or s!=s.strip() or any(c!='\t' and not 0x20<=ord(c)<=0x7e for c in s):raise ValueError('unsafe plain header')
    return s

def build(schema,args):
    return {h:encode(text(v,t)) for p,h,t in bindings(schema) if (v:=at(args,p)) is not None}

def parity(schema,args,headers):
    normalized={}
    for k,v in headers.items():
        if k.casefold() in normalized:raise ValueError('duplicate header')
        normalized[k.casefold()]=v
    checked=[]
    for p,h,t in bindings(schema):
        value=at(args,p);got=normalized.get(h.casefold())
        if value is None:
            if got is not None:raise ValueError('header without non-null argument')
            continue
        if got is None:raise ValueError('missing recognized header: -32020')
        decoded=decode(got);expected=text(value,t)
        if t=='integer':
            try:same=Decimal(decoded).is_finite() and Decimal(decoded)==Decimal(expected)
            except InvalidOperation:same=False
        else:same=decoded==expected
        if not same:raise ValueError('header/body mismatch: -32020')
        checked.append(h)
    return {'headerNames':sorted(checked)} # audit只记名字；未知headers不解释。

def reject(fn):
    try:fn()
    except ValueError:return
    raise AssertionError('expected rejection')
schema={'type':'object','properties':{'route':{'type':'object','properties':{'region':{'type':'string','x-mcp-header':'Region'}}},'shard':{'type':'integer','x-mcp-header':'Shard'},'dry':{'type':'boolean','x-mcp-header':'Dry'}}}
for value in ['eu west','eu\twest','世界',' line ','a\nb','','=?base64?SGVsbG8=?=']:
    args={'route':{'region':value},'dry':False};h=build(schema,args);assert decode(h['Mcp-Param-Region'])==value;assert parity(schema,args,h)['headerNames']==['Mcp-Param-Dry','Mcp-Param-Region']
assert build(schema,{'route':{'region':None}})=={}
for n in [-SAFE,SAFE]:assert build(schema,{'shard':n})['Mcp-Param-Shard']==str(n)
assert parity(schema,{'shard':42},{'mCp-PaRaM-sHaRd':'42.0'})['headerNames']==['Mcp-Param-Shard']
reject(lambda:build(schema,{'shard':True}));reject(lambda:build(schema,{'shard':SAFE+1}))
reject(lambda:parity(schema,{'shard':42},{}));reject(lambda:parity(schema,{'shard':42},{'Mcp-Param-Shard':'41'}))
for bad in [{'type':'object','properties':{'x':{'oneOf':[{'type':'string','x-mcp-header':'X'}]}}},{'type':'object','properties':{'x':{'type':'array','items':{'type':'string','x-mcp-header':'X'}}}},{'type':'object','$defs':{'x':{'type':'string','x-mcp-header':'X'}},'properties':{'x':{'$ref':'#/$defs/x'}}},{'type':'object','properties':{'token':{'type':'string','x-mcp-header':'Token'}}}]:reject(lambda b=bad:bindings(b))
assert '世界' not in str(parity(schema,{'route':{'region':'世界'}},build(schema,{'route':{'region':'世界'}})))
print('headers: nested properties链合法、组合/items/ref拒绝、UTF8原值往返、null省略、整数边界/数值比较与无值audit通过')
```

## 5. 工具、资源、提示与消费合同

### 5.1 从消费者意图选择primitive

模型/应用要执行搜索或修改，用tool；host读URI标识的文档，用resource；用户主动选一套消息工作流，用prompt。相同note可被tool引用、被resource读取、被prompt审阅，但不能为了“完整”把同一动作暴露三份。每多一面都要维护目录、权限、错误、cache和测试。

resource URI应稳定、带领域命名空间、逐次解析和授权。模板`notes://projects/{project}/notes/{id}`描述地址族，不免除变量类型、长度、字符和权限校验；拼接任意URI尾巴到文件/SQL是错误实现。read可返回多个contents，例如目录内文件；不存在/非法URI返回-32602，不能用空数组伪装成功。file URI可以是虚拟文件概念，不能因它写成file://就假定同机真实路径。

prompt由用户选择、服务器定义。list说明必需/可选arguments，get返回user/assistant消息；不是新system授权。prompt引用resource时应经过同一访问检查，不能成旁路。resource正文、prompt、工具描述都应保provenance和作为外部内容处理。

### 5.2 Schema、内容与错误层次

JSON Schema默认2020-12；声明别的dialect应按该dialect验证，不支持则明确错误。不自动联网解外部$ref，无法解析时不要偷偷变宽松。复杂composition可造成验证资源爆炸，需要深度/子schema/时间上限。下面验证器只接受明示子集并拒绝未知关键词；没有“支持oneOf”的假象。JSON bool与number不同，有限1和1.0在数值enum相等。输出可array/scalar/null；发布outputSchema后isError仍要给符合的structuredContent。

| content类型 | 当前与后续边界 |
|---|---|
| text | 限字节并作为外部文字消费 |
| image/audio | Base64、真实MIME、字节/像素/时长；有效编码不证明媒体有效 |
| resource_link | 当前只给URI；之后读取重新授权，未必出现在resources/list |
| embedded resource | 当前就携带text/blob，要立即计payload与权限预算 |

兼容text最好序列化structuredContent，二者要表达相同业务值；验证真源是structuredContent。普通domain失败让模型得到可纠错的isError结果，未知tool/非法CallToolRequest则是协议错误。明确参数schema失败与已进入handler的业务范围失败；不要把所有异常都转-32603，也不要在输出schema存在时漏掉错误的结构化数据。annotations、priority/audience等只供展示/选择，不替代执行权。

## 6. 缓存、分页、补全与订阅

### 6.1 缓存正确性先于命中率

discover、tools/prompts/resources list、templates list及resource read的complete结果要有`ttlMs`与`cacheScope`。ttl以接收时刻起算：`now < received + ttlMs`才fresh；0立即陈旧。它是新鲜度建议，不是data永不变化或后台poll计划。public内容不随用户变化，可跨授权上下文复用；private只能相同凭证/授权上下文。每个primitive的执行/读取仍有当前访问控制。

key含method和所有影响结果的参数（URI、cursor、locale、variant等）；private再含credential context。不能因同用户就跨不同token共享。相关change通知使fresh缓存立即stale。MRTR的input_required以及携带inputResponses/requestState的重试结果不可缓存。UI资源还可能执行代码，要把资源hash、绑定、admission pin、版本与policy纳入自己的复审/失效策略。

每页独立TTL，所有页cacheScope应一致；规范不保证跨页快照一致。目录变动会重复/漏项；需要一致快照时从头重取，cursor失效时丢旧pages重来。cursor是opaque string，空字符串有效；不能decode/递增/猜页号。结束按缺失/非null判断，另设本地最大页数避免坏server无限循环，不从token内容推断语义。

### 6.2 补全和通知没有额外权限

completion针对ref/prompt或ref/resource模板的argument，可带先前argument上下文；每次最多100字符串，total/hasMore描述其余候选。用户输入“p”不该看到未授权production，补全是敏感名称暴露面。client debounce、server rate limit、逐reference授权与输出数量都需独立。限流不是随意自造MCP保留码的理由。

subscriptions/listen声明通知filter。服务器先ack接受的子集，再发该订阅的事件；所有通知与graceful final result带subscriptionId=原listen ID。stdio的多订阅可交错，顺序定义在各ID内部。resource updated只说明变化，之后read仍重新授权；不要把事件当新正文。断流新ID listen并refetch，既不Last-Event-ID恢复也不自动重放危险写。related progress只在原请求SSE，不能放订阅stream；keepalive comment不算业务进度。

### 6.3 完整CPU例：声明子集、内容、分页和缓存

本例生成真实微小PNG/WAV字节，但只核PNG签名/尺寸和WAV时长，不冒充完整媒体解码器。它接受合法空content，要求outputSchema结果包含structuredContent；两个cache凭证不能混用，TTL边界和MRTR禁cache均有反例。订阅对象仅显示按ID过滤的消息模型，没有真实推送服务。

```python
import json,math,copy,base64,struct,zlib,io,wave
KEYS={'type','properties','required','additionalProperties','items','enum','minimum','maximum','minLength','maxLength'}
TYPES={'object','array','string','integer','number','boolean','null'}
def json_scalar(v):return v is None or type(v) in (str,bool,int) or type(v) is float and math.isfinite(v)
def equal(a,b):
    if type(a) in (int,float) and type(b) in (int,float):return a==b
    return type(a) is type(b) and a==b

def check_schema(s,depth=0):
    if type(s) is not dict or set(s)-KEYS or depth>12 or s.get('type') not in TYPES:raise ValueError('unsupported schema subset')
    if 'enum' in s and (type(s['enum']) is not list or not s['enum'] or not all(json_scalar(x) for x in s['enum'])):raise ValueError('scalar finite enum')
    if s['type']=='object':
        props=s.get('properties',{});req=s.get('required',[])
        if type(props) is not dict or type(req) is not list or any(type(x) is not str or x not in props for x in req) or type(s.get('additionalProperties',True)) is not bool:raise ValueError('object schema')
        for child in props.values():check_schema(child,depth+1)
    if s['type']=='array' and 'items' in s:check_schema(s['items'],depth+1)
    for key in ('minLength','maxLength'):
        if key in s and (type(s[key]) is not int or s[key]<0):raise ValueError('length bound')
    for key in ('minimum','maximum'):
        if key in s and (type(s[key]) not in (int,float) or not math.isfinite(s[key])):raise ValueError('finite numeric bound')

def validate(v,s):
    check_schema(s);t=s['type'];numeric=type(v) is int or type(v) is float and math.isfinite(v)
    match={'object':type(v) is dict,'array':type(v) is list,'string':type(v) is str,'integer':numeric and v==int(v),'number':numeric,'boolean':type(v) is bool,'null':v is None}[t]
    if not match or 'enum' in s and not any(equal(v,x) for x in s['enum']):raise ValueError('type/enum')
    if t=='object':
        p=s.get('properties',{})
        if any(k not in v for k in s.get('required',[])) or s.get('additionalProperties') is False and set(v)-set(p):raise ValueError('object keys')
        for k,x in v.items():
            if k in p:validate(x,p[k])
    if t=='array' and 'items' in s:
        for x in v:validate(x,s['items'])
    if t=='string' and not s.get('minLength',0)<=len(v)<=s.get('maxLength',10**9):raise ValueError('length')
    if numeric and not s.get('minimum',-math.inf)<=v<=s.get('maximum',math.inf):raise ValueError('range')

def png():
    def chunk(k,b):return struct.pack('>I',len(b))+k+b+struct.pack('>I',zlib.crc32(k+b)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(b'\x00\x00\x00\x00\xff'))+chunk(b'IEND',b'')
def wav():
    b=io.BytesIO()
    with wave.open(b,'wb') as w:w.setparams((1,2,8000,0,'NONE','not compressed'));w.writeframes(b'\x00\x00'*8)
    return b.getvalue()
def content(block):
    if type(block) is not dict:raise ValueError('block')
    t=block.get('type')
    if t=='text':
        if type(block.get('text')) is not str or len(block['text'].encode())>4096:raise ValueError('text budget')
    elif t in ('image','audio'):
        b=base64.b64decode(block['data'],validate=True)
        if len(b)>4096:raise ValueError('media bytes')
        if t=='image':
            if block['mimeType']!='image/png' or not b.startswith(b'\x89PNG\r\n\x1a\n') or len(b)<24 or max(struct.unpack('>II',b[16:24]))>16:raise ValueError('PNG policy')
        else:
            with wave.open(io.BytesIO(b)) as w:
                if block['mimeType']!='audio/wav' or w.getnframes()/w.getframerate()>.1:raise ValueError('audio policy')
    elif t=='resource_link':
        if any(type(block.get(k)) is not str for k in ('uri','name')):raise ValueError('link')
    elif t=='resource':
        r=block.get('resource',{})
        if type(r.get('uri')) is not str or ('text' in r)==('blob' in r):raise ValueError('embedded contents')
        if 'text' in r:content({'type':'text','text':r['text']})
        elif len(base64.b64decode(r['blob'],validate=True))>4096:raise ValueError('embedded bytes')
    else:raise ValueError('unknown block')
def result(r,output=None):
    if r.get('resultType')!='complete' or type(r.get('content')) is not list or type(r.get('isError',False)) is not bool:raise ValueError('result')
    for b in r['content']:content(b)
    if output is not None:
        if 'structuredContent' not in r:raise ValueError('output missing')
        validate(r['structuredContent'],output)
class Cache:
    def __init__(self):self.entries={}
    def key(self,method,params,scope,credential):return method,json.dumps(params,sort_keys=True),credential if scope=='private' else 'shared'
    def put(self,method,params,r,credential,now):
        if any(k in params for k in ('requestState','inputResponses')) or r['resultType']!='complete':return
        self.entries[self.key(method,params,r['cacheScope'],credential)]=(now,r['ttlMs'],copy.deepcopy(r))
    def get(self,method,params,scope,credential,now,authorized):
        if not authorized:return None
        row=self.entries.get(self.key(method,params,scope,credential))
        return copy.deepcopy(row[2]) if row and now<row[0]+row[1] else None
    def invalidate(self):self.entries.clear()
def paginate(fetch,max_pages=4):
    cursor=None;out=[]
    for _ in range(max_pages):
        r=fetch({} if cursor is None else {'cursor':cursor});out+=r['items'];cursor=r.get('nextCursor')
        if cursor is None:return out
        if type(cursor) is not str:raise ValueError('cursor type')
    raise ValueError('local page budget')
def reject(fn):
    try:fn()
    except ValueError:return
    raise AssertionError('expected rejection')
validate(1.0,{'type':'integer','enum':[1]});reject(lambda:validate(True,{'type':'integer','enum':[1]}));reject(lambda:validate(float('nan'),{'type':'number'}));reject(lambda:validate(2,{'type':'integer','oneOf':[]}))
blocks=[{'type':'text','text':'示例证据'}, {'type':'image','mimeType':'image/png','data':base64.b64encode(png()).decode()}, {'type':'audio','mimeType':'audio/wav','data':base64.b64encode(wav()).decode()}, {'type':'resource_link','uri':'evidence://1','name':'e1'}, {'type':'resource','resource':{'uri':'evidence://1/text','text':'small'}}]
for b in blocks:content(b)
output={'type':'array','items':{'type':'string'}};r={'resultType':'complete','content':[{'type':'text','text':'[]'}],'structuredContent':[],'isError':True};result(r,output)
reject(lambda:result({**r,'structuredContent':{}},output));reject(lambda:result({'resultType':'complete','content':[],'isError':True},output))
trace=[]
def fetch(p):
    trace.append(p.copy());return {'items':['a'],'nextCursor':''} if 'cursor' not in p else {'items':['b']}
assert paginate(fetch)==['a','b'] and trace==[{}, {'cursor':''}]
reject(lambda:paginate(lambda p:{'items':[],'nextCursor':'opaque'},2))
c=Cache();cached={'resultType':'complete','ttlMs':10,'cacheScope':'private','contents':[]};c.put('resources/read',{'uri':'notes://a'},cached,'token-A',0)
assert c.get('resources/read',{'uri':'notes://a'},'private','token-A',9,True)
assert c.get('resources/read',{'uri':'notes://a'},'private','token-B',9,True) is None
assert c.get('resources/read',{'uri':'notes://a'},'private','token-A',9,False) is None
assert c.get('resources/read',{'uri':'notes://a'},'private','token-A',10,True) is None
c.put('resources/read',{'uri':'notes://a','requestState':'x'},cached,'token-A',0);assert len(c.entries)==1
c.invalidate();assert not c.entries
# 两条订阅先各自ack，再按各自filter发event；它们共享的只是运输通道。
streams={7:{'resources':['notes://a']},8:{'resources':['notes://b']}}
wire=[{'method':'notifications/subscriptions/acknowledged','subscriptionId':i} for i in streams]
wire += [{'method':'notifications/resources/updated','subscriptionId':i,'uri':u} for i,s in streams.items() for u in s['resources']]
assert [x['subscriptionId'] for x in wire]==[7,8,7,8]
print('surfaces:声明schema子集/五内容型/输出错误合同、空cursor、private授权TTL/MRTR禁cache、双订阅过滤通过；未HTTP/媒体完整解码')
```

## 7. 授权MRTR与交互状态

### 7.1 一次输入流程如何独立重试

MRTR只可由tools/call、resources/read、prompts/get返回input_required。至少有inputRequests或requestState；inputRequests以server分配的key匹配inputResponses。原请求已结束，host按当前能力、用户/模型策略收集输入，再用新RPC ID重发原方法/参数。只回当轮输入，不混入并行请求；state按原封字符串回传，client不可解析/修改。缺必要输入可再次请求，服务器不能假定host一定回答。

“两轮Sampling”可先pick_files再summary：第一返回pick输入需求；第二请求带选择结果，服务器验证文件白名单并把选项写入下一个signed state；第三请求带summary完成。这是2次输入、3次RPC。host必须限轮次、bytes/tokens/时间/费用，错误JSON、unknown filename、空输出不成为工具参数或身份。模型preferences的cost/speed/intelligence都是0–1独立偏好，不必和为1，也不是客户端必须选的型号。maxTokens必须尊重，其余温度/提示/偏好可按host策略改或忽略。

Sampling、Roots、Logging自2026-07-28弃用，窗口不等立即失效。新server需要推理优先直接provider；费用、凭证、重试、数据出站与观测随此架构移到server。兼容Sampling只能在MRTR内请求，不能独立反向RPC；工具Sampling还需sampling.tools，toolUse全部以匹配ID的toolResult紧随，toolResult用户消息不混普通文字。Roots只给工作范围信息，不提供授权、路径containment或OS sandbox。新设计用显式workspace参数/URI/配置，迁移适配隔离。

### 7.2 Form、URL与实际授权

form支持`elicitation: {}`（隐式form）或form:{}；url-only不能满足form。schema是flat对象primitive及规定enum数组，不能照搬深层业务JSON Schema。accept是明确提交，decline明确拒绝，cancel未作明确选择；缺content/confirm=1不能当true。不要把decline改成循环强问。非敏感偏好可以form，凭证/支付secret必须出站到URL mode的安全外部流程。

URL显示完整目的地并获同意后打开，不能预取URL或metadata，不能含secret/已认证bearer；accept只表示同意打开，不证明第三方OAuth完成。MCP server检查自己的外部流程状态；MCP client到server授权与server到第三方授权不同。浏览器完成者必须是发起elicitation的可信主体，避免恶意用户把自己的链接交给受害者，绑定受害者凭证。

scope需要三层：可信principal有workspace权限→解码/规范化后组件级containment→真实OS/文件系统隔离。`notes-evil`与编码`../`反例能证明词法containment，不能证明symlink/TOCTOU安全；真实文件服务还需打开时约束和平台策略。principal来自可信认证边界，不能来自clientInfo或桥接参数自称身份。

### 7.3 状态完整性与回执不是同一件事

requestState影响业务时必须防篡改，HMAC提供完整性，AEAD还可保密。绑定主体、method/tool、原参数digest、候选集、目标revision/hash、nonce和短expiry。仅签phase或Base64不够。主体/TTL/参数绑定约束replay范围，却不保证single-use；不可重复动作要共享事务nonce store。

本例策略：cancel不消耗nonce，expiry前可重新提交；decline终止该nonce但不删除；accept把选择指纹、nonce、删除与receipt一起提交。同nonce同回答可在有效期内取原receipt，防丢响应后重复删除；同nonce不同回答拒绝；expiry先拒再查receipt。新独立意图用新nonce。服务器重核可信权限和live revision，旧展示的批准不能删除后来改过的记录。

### 7.4 完整CPU例：批准、两轮假host与SQLite竞争

输入为可信principal、明确args、signed state、假host回答和虚拟秒。两个独立SQLite连接在barrier后竞争同nonce的不同目标，只有一次删除；重开连接仍能读原receipt，修改返回字典不改库记录。业务删除只是notes表中的记录，未删真实文件。代码末尾演示两轮假Sampling，文件和模型输出均预设；没有真实人机批准或模型质量证据。事务保护本地nonce/记录，不能顺带让外部邮件/支付exactly-once。

```python
import json,hashlib,hmac,uuid,sqlite3,tempfile,copy,threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse,unquote
import posixpath
SECRET=b'fixture-only-not-production';ROOT='file:///work/notes';POLICY={'alice':{ROOT},'bob':{'file:///work/bob'}}
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(x):return hashlib.sha256(canonical(x).encode()).hexdigest()
def within(root,target):
    a,b=urlparse(root),urlparse(target)
    if a.scheme!='file' or b.scheme!='file' or a.netloc!=b.netloc or a.query or b.query or a.fragment or b.fragment:return False
    ap,bp=posixpath.normpath(unquote(a.path)),posixpath.normpath(unquote(b.path))
    return ap.startswith('/') and bp.startswith('/') and posixpath.commonpath([ap,bp])==ap

def seal(x):
    body=canonical(x);return body+'.'+hmac.new(SECRET,body.encode(),'sha256').hexdigest()
def unseal(token):
    if type(token) is not str:raise ValueError('state type')
    try:body,sig=token.rsplit('.',1)
    except ValueError:raise ValueError('state encoding')
    if not hmac.compare_digest(sig,hmac.new(SECRET,body.encode(),'sha256').hexdigest()):raise ValueError('state signature')
    x=json.loads(body)
    if type(x) is not dict:return None
    return x

def db(path):return sqlite3.connect(path,isolation_level=None,timeout=5)
def init(path):
    c=db(path);c.executescript('CREATE TABLE notes(id TEXT PRIMARY KEY,owner TEXT,uri TEXT,revision INTEGER,text TEXT);CREATE TABLE claims(nonce TEXT PRIMARY KEY,expires INTEGER,response_hash TEXT,result TEXT);CREATE TABLE effects(nonce TEXT PRIMARY KEY);')
    c.executemany('INSERT INTO notes VALUES(?,?,?,?,?)',[('a','alice',ROOT+'/a.md',0,'A'),('b','alice',ROOT+'/b.md',0,'B')]);c.close()
def authorize(principal,args):
    if type(args) is not dict or set(args)!={'workspaceUri','action'} or args['action']!='delete' or args['workspaceUri'] not in POLICY.get(principal,set()):raise ValueError('trusted-principal authorization')
def begin(path,principal,args,now,caps):
    authorize(principal,args)
    el=caps.get('elicitation')
    if type(el) is not dict or el and type(el.get('form')) is not dict:raise ValueError('form capability: -32021')
    c=db(path);rows=c.execute('SELECT id,uri,revision,text FROM notes WHERE owner=? ORDER BY id',(principal,)).fetchall();c.close()
    candidates={i:{'revision':rev,'sha':digest(text)} for i,uri,rev,text in rows if within(args['workspaceUri'],uri)}
    if not candidates:return {'resultType':'complete','content':[{'type':'text','text':'no matching authorized note'}],'isError':True}
    state={'principal':principal,'method':'tools/call','tool':'delete_notes','argsHash':digest(args),'candidates':candidates,'nonce':uuid.uuid4().hex,'expires':now+30}
    return {'resultType':'input_required','requestState':seal(state),'inputRequests':{'choice':{'method':'elicitation/create','params':{'mode':'form','message':'选择本次看到的版本，并确认删除','requestedSchema':{'type':'object','properties':{'noteId':{'type':'string','enum':list(candidates)},'confirm':{'type':'boolean'}},'required':['noteId','confirm']}}}}}

def finish(path,principal,args,token,answer,now):
    authorize(principal,args);s=unseal(token)
    if not s or s.get('principal')!=principal or s.get('method')!='tools/call' or s.get('tool')!='delete_notes' or s.get('argsHash')!=digest(args) or type(s.get('expires')) is not int or now>=s['expires']:raise ValueError('state binding/expiry')
    if type(answer) is not dict or answer.get('action') not in ('accept','decline','cancel'):raise ValueError('elicitation action')
    action=answer['action'];a=answer.get('content',{})
    if action=='accept' and (type(a) is not dict or set(a)!={'noteId','confirm'} or a.get('confirm') is not True or a.get('noteId') not in s['candidates']):raise ValueError('accept schema/candidate')
    if action=='cancel':return {'resultType':'complete','content':[{'type':'text','text':'cancelled'}],'structuredContent':{'deleted':False},'isError':False}
    fingerprint=digest(answer);c=db(path)
    try:
        c.execute('BEGIN IMMEDIATE')
        c.execute('DELETE FROM claims WHERE expires<=?',(now,))
        old=c.execute('SELECT response_hash,result FROM claims WHERE nonce=?',(s['nonce'],)).fetchone()
        if old:
            if old[0]!=fingerprint:raise ValueError('nonce already bound to another answer')
            c.execute('COMMIT');return json.loads(old[1])
        # receipt命中仅在仍有效且同回答时返回；新执行必须核当前授权和实际记录。
        authorize(principal,args)
        deleted=False
        if action=='accept':
            i=a['noteId'];row=c.execute('SELECT owner,uri,revision,text FROM notes WHERE id=?',(i,)).fetchone()
            snapshot=s['candidates'][i]
            if not row or row[0]!=principal or not within(args['workspaceUri'],row[1]) or row[2]!=snapshot['revision'] or digest(row[3])!=snapshot['sha']:raise ValueError('live target changed')
            c.execute('DELETE FROM notes WHERE id=? AND revision=?',(i,snapshot['revision']))
            c.execute('INSERT INTO effects VALUES(?)',(s['nonce'],));deleted=True
        result={'resultType':'complete','content':[{'type':'text','text':'deleted' if deleted else 'declined'}],'structuredContent':{'deleted':deleted,'noteId':a.get('noteId') if deleted else None},'isError':False}
        c.execute('INSERT INTO claims VALUES(?,?,?,?)',(s['nonce'],s['expires'],fingerprint,canonical(result)))
        c.execute('COMMIT');return json.loads(canonical(result))
    except BaseException:
        if c.in_transaction:c.execute('ROLLBACK')
        raise
    finally:c.close()

def reject(fn):
    try:fn()
    except ValueError:return
    raise AssertionError('expected rejection')
with tempfile.TemporaryDirectory(dir='/tmp',prefix='study-mrtr-') as folder:
    path=str(Path(folder)/'notes.db');init(path);args={'workspaceUri':ROOT,'action':'delete'};caps={'elicitation':{}}
    reject(lambda:begin(path,'bob',args,100,caps));assert not within(ROOT,ROOT+'-evil/a') and not within(ROOT,ROOT+'/%2e%2e/private')
    first=begin(path,'alice',args,100,caps);token=first['requestState'];accept={'action':'accept','content':{'noteId':'a','confirm':True}}
    reject(lambda:finish(path,'bob',args,token,accept,101));reject(lambda:finish(path,'alice',args,token+'x',accept,101))
    reject(lambda:finish(path,'alice',args,token,{'action':'accept','content':{'noteId':'a','confirm':1}},101))
    assert not finish(path,'alice',args,token,{'action':'cancel'},101)['structuredContent']['deleted']
    # 相同token、不同选择竞争：两条实际连接中，仅一个nonce能与删除共同提交。
    barrier=threading.Barrier(2)
    def compete(note_id):
        barrier.wait();ans={'action':'accept','content':{'noteId':note_id,'confirm':True}}
        try:return finish(path,'alice',args,token,ans,102)
        except ValueError:return 'rejected'
    with ThreadPoolExecutor(2) as pool:answers=list(pool.map(compete,['a','b']))
    assert sum(type(x) is dict for x in answers)==1
    committed=next(x for x in answers if type(x) is dict);winner=committed['structuredContent']['noteId'];same={'action':'accept','content':{'noteId':winner,'confirm':True}}
    committed['structuredContent']['deleted']='tampered'
    replay=finish(path,'alice',args,token,same,103);assert replay['structuredContent']['deleted'] is True
    c=db(path);assert c.execute('SELECT count(*) FROM effects').fetchone()[0]==1;c.close()
    reject(lambda:finish(path,'alice',args,token,same,130))
    # 新nonce绑定仍在库中的目标；审批展示后改revision，不能沿用旧批准。
    other='b' if winner=='a' else 'a';next_token=begin(path,'alice',args,104,caps)['requestState'];c=db(path);c.execute('UPDATE notes SET revision=revision+1 WHERE id=?',(other,));c.close()
    reject(lambda:finish(path,'alice',args,next_token,{'action':'accept','content':{'noteId':other,'confirm':True}},105))
    decline_token=begin(path,'alice',args,106,caps)['requestState'];assert not finish(path,'alice',args,decline_token,{'action':'decline'},107)['structuredContent']['deleted']
    reject(lambda:finish(path,'alice',args,decline_token,{'action':'accept','content':{'noteId':other,'confirm':True}},108))
# 另一个只读工作流：两次假host模型输入，三次独立RPC；状态不驻连接。
FILES={'README.md':'fixture overview','server.py':'fixture dispatcher','docs/intro.md':'fixture protocol'}
def sample_round(params,principal,caps,now):
    if type(caps.get('sampling')) is not dict:raise ValueError('sampling capability: -32021')
    args=params['arguments'];token=params.get('requestState')
    state={'principal':principal,'method':'tools/call','tool':'summarize','argsHash':digest(args),'phase':'pick','expires':now+30}
    if token is not None:
        state=unseal(token)
        if type(state) is not dict or state.get('principal')!=principal or state.get('method')!='tools/call' or state.get('tool')!='summarize' or state.get('phase') not in ('pick','summary') or state.get('argsHash')!=digest(args) or type(state.get('expires')) is not int or now>=state['expires']:raise ValueError('sampling state')
        response=params.get('inputResponses',{}).get(state['phase'])
        if type(response) is not dict or response.get('role')!='assistant' or type(response.get('model')) is not str or type(response.get('content')) is not dict or response['content'].get('type')!='text':raise ValueError('sampling response')
        text=response['content'].get('text')
        if type(text) is not str or not text.strip() or len(text.encode())>500:raise ValueError('response budget')
        if state['phase']=='pick':
            picked=json.loads(text)
            if type(picked) is not list or not 1<=len(picked)<=3 or any(type(x) is not str for x in picked) or len(set(picked))!=len(picked) or any(x not in FILES for x in picked):raise ValueError('filename allowlist')
            state={**state,'phase':'summary','picked':picked}
        else:return {'resultType':'complete','content':[{'type':'text','text':text}],'structuredContent':{'files':state['picked'],'summary':text}}
    key=state['phase'];prompt='选择文件，返回JSON数组' if key=='pick' else '总结：'+canonical({x:FILES[x] for x in state['picked']})
    return {'resultType':'input_required','requestState':seal(state),'inputRequests':{key:{'method':'sampling/createMessage','params':{'messages':[{'role':'user','content':{'type':'text','text':prompt}}],'maxTokens':100}}}}
params={'arguments':{'audience':'learner'}};caps={'sampling':{}};ids=[201];pending=sample_round(params,'alice',caps,100)
for rid in (202,203):
    key=next(iter(pending['inputRequests']));text='["README.md","server.py"]' if key=='pick' else '这是显式逐请求的教学目录。'
    params={**params,'requestState':pending['requestState'],'inputResponses':{key:{'role':'assistant','model':'fake-host','content':{'type':'text','text':text}}}}
    ids.append(rid);pending=sample_round(params,'alice',caps,101)
assert ids==[201,202,203] and pending['resultType']=='complete'
reject(lambda:sample_round({**params,'arguments':{'audience':'changed'}},'alice',caps,102))
print('MRTR:principal/候选版本/nonce/TTL绑定、两SQLite连接竞争仅一删除、重开receipt防alias、cancel可重试与decline终态通过；假host未真人批准')
```

## 8. Tasks：持久工作、输入与租约

### 8.1 创建、快照与方法

Tasks是`io.modelcontextprotocol/tasks`扩展，双方声明；当前eligible方法是tools/call。client支持并不强制task模式，server逐调用决定同步result或CreateTaskResult；未声明能力不能返回task。handle发送前必须已持久且tasks/get可读，不能让client猜“刚建的任务也许尚不存在”。初始可做同步MRTR，建task后输入改用tasks/get的inputRequests→tasks/update，不重试原tools/call。

外层tasks/get `resultType: complete`表示poll完成，内层status才是job。working/input_required可到working或终态；completed/failed/cancelled一旦终态不能再迁移。completed带原工具result，即使isError:true也仍completed；deferred JSON-RPC错误才failed并带error。当前方法是get/update/cancel，没有tasks/list/result/status；历史适配别当新默认。

Task包含id、ISO创建/更新时间、status、TTL（创建起算，null可不设限）、可变建议poll interval和可选statusMessage。TTL不是“完成后保留多久”；过期可失效/清除。每次get/update/cancel及订阅都核owner，未知、他人、过期的存在信息按应用策略统一不可用。三task方法的Mcp-Name=taskId，不是method。

### 8.2 输入与取消

inputRequests键在整个task寿命唯一。重复poll出现同key，host去重UI；未知、已回答、被替换key的response应忽略。partial update可能ack后仍input_required，全部必要keys齐全才继续。ack只确认接收，observable status可最终一致；client按需求poll或listen。任务通知是完整快照、subscriptionId相关，需task能力；task流不发ordinary progress/message。

tasks/cancel是普通新请求，ack不保证worker已停，也不保证最终cancelled；完成可赢竞态。client若不再需要该任务，可按规范取消后删除自己的跟踪状态，不必须等cancelled；若UI要宣称“停止完成”，就必须继续观察实际terminal。业务任务不跟原运输连接一起消失。

### 8.3 原子存储与worker提交权

临时文件replace证明单机原子替换，不证明断电落盘、多worker互斥、跨replica即时读取或事务。实际持久任务需要共享store和可靠worker机制。SQLite例每次读共享文件，BEGIN IMMEDIATE串行化改状态；租约是提交权，过期后新worker拿新token，旧worker即使完成计算也不能写回。副作用与结果若在外系统，仍需外部幂等/outbox，单机SQLite不能宣称全球exactly-once。

### 8.4 完整CPU例：持久任务与两个连接

程序支持固定整数TTL、两项form输入与有限状态子集；未实现真实queue、HTTP订阅和全集schema。数据库重开get证明恢复，barrier竞争证明两个连接只能有一份有效lease，过期恢复token拒旧worker，部分输入与重复key都有反例。cancel ack后仍working，以及worker可选择已完成结果，是不同路径。

```python
import sqlite3,json,tempfile,uuid,threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone,timedelta
EXT='io.modelcontextprotocol/tasks';CAPS={'extensions':{EXT:{}},'elicitation':{}};TERMINAL={'completed','failed','cancelled'}
def stamp(t):return (datetime(2026,10,8,tzinfo=timezone.utc)+timedelta(milliseconds=t)).isoformat()
def require(caps):
    if type(caps) is not dict or type(caps.get('extensions')) is not dict or type(caps['extensions'].get(EXT)) is not dict:raise ValueError('tasks capability: -32021')
def form(caps):
    e=caps.get('elicitation');return type(e) is dict and (not e or type(e.get('form')) is dict)
class Store:
    def __init__(self,path):
        self.path=path
        c=self.db()
        try:c.executescript('CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY,owner TEXT,status TEXT,created INTEGER,updated INTEGER,ttl INTEGER,revision INTEGER,cancel INTEGER,lease TEXT,lease_until INTEGER,result TEXT,error TEXT);CREATE TABLE IF NOT EXISTS inputs(task TEXT,key TEXT,answer TEXT,PRIMARY KEY(task,key));CREATE TABLE IF NOT EXISTS effects(task TEXT PRIMARY KEY);')
        finally:c.close()
    def db(self):return sqlite3.connect(self.path,isolation_level=None,timeout=5)
    def create(self,principal,caps,now,ttl=1000):
        require(caps);i=uuid.uuid4().hex;c=self.db()
        try:
            c.execute('BEGIN IMMEDIATE');c.execute('INSERT INTO tasks VALUES(?,?,?,?,?,?,0,0,NULL,NULL,NULL,NULL)',(i,principal,'working',now,now,ttl));c.execute('COMMIT')
        finally:c.close()
        return {'resultType':'task',**self.get(i,principal,caps,now,outer=False)}
    def owned(self,c,i,principal,now):
        c.row_factory=sqlite3.Row;r=c.execute('SELECT * FROM tasks WHERE id=?',(i,)).fetchone()
        if not r or r['owner']!=principal or now>=r['created']+r['ttl']:raise ValueError('task unavailable: -32602')
        return r
    def get(self,i,principal,caps,now,outer=True):
        require(caps);c=self.db()
        try:
            r=self.owned(c,i,principal,now);out={'taskId':i,'status':r['status'],'createdAt':stamp(r['created']),'lastUpdatedAt':stamp(r['updated']),'ttlMs':r['ttl'],'pollIntervalMs':20}
            if r['status']=='input_required':
                if not form(caps):raise ValueError('form capability: -32021')
                keys=c.execute('SELECT key FROM inputs WHERE task=? AND answer IS NULL ORDER BY key',(i,)).fetchall()
                out['inputRequests']={k['key']:{'method':'elicitation/create','params':{'mode':'form','message':'批准 '+k['key'],'requestedSchema':{'type':'object','properties':{'yes':{'type':'boolean'}},'required':['yes']}}} for k in keys}
            if r['status']=='completed':out['result']=json.loads(r['result'])
            if r['status']=='failed':out['error']=json.loads(r['error'])
            if outer:out['resultType']='complete'
            return out
        finally:c.close()
    def need_input(self,i,principal,caps,keys,now):
        require(caps)
        if not form(caps):raise ValueError('form capability: -32021')
        c=self.db()
        try:
            c.execute('BEGIN IMMEDIATE');r=self.owned(c,i,principal,now)
            if r['status']!='working':raise ValueError('cannot request input from terminal/waiting')
            for k in keys:c.execute('INSERT INTO inputs VALUES(?,?,NULL)',(i,k)) # PK禁止整个task寿命重用key。
            c.execute('UPDATE tasks SET status=?,updated=?,revision=revision+1,lease=NULL,lease_until=NULL WHERE id=?',('input_required',now,i));c.execute('COMMIT')
        except BaseException:
            if c.in_transaction:c.execute('ROLLBACK')
            raise
        finally:c.close()
    def update(self,i,principal,caps,responses,now):
        require(caps);c=self.db()
        try:
            c.execute('BEGIN IMMEDIATE');r=self.owned(c,i,principal,now)
            if r['status']=='input_required':
                for k,v in responses.items():
                    pending=c.execute('SELECT 1 FROM inputs WHERE task=? AND key=? AND answer IS NULL',(i,k)).fetchone()
                    if not pending:continue
                    if v!={'action':'accept','content':{'yes':True}} or v['content']['yes'] is not True:raise ValueError('input schema')
                    c.execute('UPDATE inputs SET answer=? WHERE task=? AND key=?',(json.dumps(v),i,k))
                left=c.execute('SELECT count(*) FROM inputs WHERE task=? AND answer IS NULL',(i,)).fetchone()[0]
                if not left:c.execute('UPDATE tasks SET status=?,updated=?,revision=revision+1 WHERE id=?',('working',now,i))
            c.execute('COMMIT');return {'resultType':'complete'}
        except BaseException:
            if c.in_transaction:c.execute('ROLLBACK')
            raise
        finally:c.close()
    def cancel(self,i,principal,caps,now):
        require(caps);c=self.db()
        try:
            c.execute('BEGIN IMMEDIATE');r=self.owned(c,i,principal,now)
            if r['status'] not in TERMINAL:c.execute('UPDATE tasks SET cancel=1,updated=? WHERE id=?',(now,i))
            c.execute('COMMIT');return {'resultType':'complete'}
        finally:c.close()
    def claim(self,i,principal,worker,now):
        c=self.db()
        try:
            c.execute('BEGIN IMMEDIATE');r=self.owned(c,i,principal,now)
            if r['status']!='working' or r['lease'] is not None and now<r['lease_until']:c.execute('COMMIT');return None
            token=worker+':'+uuid.uuid4().hex;c.execute('UPDATE tasks SET lease=?,lease_until=?,revision=revision+1 WHERE id=?',(token,now+50,i));c.execute('COMMIT');return token
        finally:c.close()
    def finish(self,i,principal,token,now,honor_cancel=True,tool_error=False,rpc_error=None):
        c=self.db()
        try:
            c.execute('BEGIN IMMEDIATE');r=self.owned(c,i,principal,now)
            if r['status']!='working' or r['lease']!=token or now>=r['lease_until']:raise ValueError('stale lease/terminal')
            status='cancelled' if r['cancel'] and honor_cancel else 'failed' if rpc_error else 'completed'
            result={'resultType':'complete','content':[{'type':'text','text':'domain failure' if tool_error else 'report ready'}],'isError':tool_error}
            if status=='completed':c.execute('INSERT INTO effects VALUES(?)',(i,))
            c.execute('UPDATE tasks SET status=?,updated=?,result=?,error=?,lease=NULL,lease_until=NULL,revision=revision+1 WHERE id=?',(status,now,json.dumps(result) if status=='completed' else None,json.dumps(rpc_error) if status=='failed' else None,i));c.execute('COMMIT');return status
        except BaseException:
            if c.in_transaction:c.execute('ROLLBACK')
            raise
        finally:c.close()

def reject(fn):
    try:fn()
    except (ValueError,sqlite3.IntegrityError):return
    raise AssertionError('expected rejection')
with tempfile.TemporaryDirectory(dir='/tmp',prefix='study-tasks-') as folder:
    path=str(Path(folder)/'tasks.db');s=Store(path);reject(lambda:s.create('alice',{},0));i=s.create('alice',CAPS,0)['taskId']
    s=Store(path);assert s.get(i,'alice',CAPS,1)['status']=='working';reject(lambda:s.get(i,'bob',CAPS,1))
    s.need_input(i,'alice',CAPS,['outline-1','format-2'],2);reject(lambda:s.get(i,'alice',{'extensions':{EXT:{}}},3))
    s.update(i,'alice',CAPS,{'outline-1':{'action':'accept','content':{'yes':True}},'unknown':{}},3)
    assert list(s.get(i,'alice',CAPS,4)['inputRequests'])==['format-2']
    s.update(i,'alice',CAPS,{'format-2':{'action':'accept','content':{'yes':True}}},5);assert s.get(i,'alice',CAPS,6)['status']=='working'
    reject(lambda:s.need_input(i,'alice',CAPS,['outline-1'],6))
    gate=threading.Barrier(2)
    def race(w):gate.wait();return Store(path).claim(i,'alice',w,10)
    with ThreadPoolExecutor(2) as pool:tickets=list(pool.map(race,['worker-A','worker-B']))
    assert sum(x is not None for x in tickets)==1;old=next(x for x in tickets if x)
    new=s.claim(i,'alice','recovery-worker',61);reject(lambda:s.finish(i,'alice',old,62))
    ack=s.cancel(i,'alice',CAPS,62);assert ack=={'resultType':'complete'} and s.get(i,'alice',CAPS,62)['status']=='working'
    assert s.finish(i,'alice',new,63)=='cancelled';reject(lambda:s.finish(i,'alice',new,64))
    assert s.cancel(i,'alice',CAPS,65)==ack and s.get(i,'alice',CAPS,65)['status']=='cancelled'
    j=s.create('alice',CAPS,70)['taskId'];t=s.claim(j,'alice','worker',71);s.cancel(j,'alice',CAPS,72)
    assert s.finish(j,'alice',t,73,honor_cancel=False,tool_error=True)=='completed'
    done=Store(path).get(j,'alice',CAPS,74);assert done['resultType']=='complete' and done['result']['isError'] is True
    reject(lambda:s.need_input(j,'alice',CAPS,['late'],75));reject(lambda:s.get(j,'alice',CAPS,1070))
    k=s.create('alice',CAPS,80)['taskId'];t=s.claim(k,'alice','worker',81);assert s.finish(k,'alice',t,82,rpc_error={'code':-32603,'message':'renderer'})=='failed'
    assert Store(path).get(k,'alice',CAPS,83)['error']['code']==-32603
print('tasks:持久后返回/重开、owner/能力、部分输入/永久unique key、双连接lease竞争与旧worker拒绝、ack非终态/终态冻结、tool-error与RPC-failed通过')
```

## 9. 取消竞态、幂等、背压与恢复

### 9.1 两个时钟与一个终态

stdio客户端用notifications/cancelled，HTTP关闭该请求SSE响应，不为普通HTTP RPC另POST取消通知。server的stdio取消只用于订阅teardown；无法取消、未知/晚到通知可忽略。接受取消后不再发该请求消息；cancel先到抑制最终响应，complete先到保留结果，client忽略自己已放弃的晚响应。取消不是撤销已经发生的副作用。

idle timeout看距最后**有效业务活动**多久，maximum timeout从起点始终不改。进度可reset idle但不能reset maximum；keepalive不算progress。token在活跃请求中唯一、值严格递增、有限JSON number，结束后不再发；可选progress可能完全不来，因此token不能产生无限timeout。频率还需限流，图里每秒预设一次不证明真实带宽或时延。

### 9.2 业务key跨RPC重试

新RPC ID只作相关。只读可以在弄清失败边界后安全重试；有副作用且有durable key/同参数合同才条件重试；无权威去重的未知写结果先reconcile。key应命名主体/tenant、操作和业务意图；同key不同数量/金额拒绝。工具idempotentHint并不证明实现。

“查key→外部动作→写receipt”中，两个worker可都查到空；动作后崩溃也可丢receipt。下面把key指纹、本地模拟effect与result同事务，两个连接证明一次commit；外部支付不在此事务，就必须依靠upstream同key或outbox等桥接。返回JSON重建副本，避免调用者修改回执污染后续replay。

### 9.3 有限流量而不是无限队列

producer快于consumer会把慢网络变成内存问题。progress可同token合并，拥塞时丢可替换progress并标需要权威refetch；final结果不能丢。若容量全是final，拒绝新增或做admission，不能偷偷删旧final；这也说明队列策略与状态机要一起设计。

SSE可用no-cache、X-Accel-Buffering:no和comment keepalive减少proxy缓冲/idle断连，但配置文案不证明实际proxy已按时转发。断流新listen ID/恢复filter/重取当前资源目录或task，不做现代event replay，不因response lost重放未知写。reconnect用有上限指数退避+jitter，避免恢复瞬间大量client同时冲击；fixture SHA派生jitter只为可重复检查，生产可用运行时随机。

### 9.4 完整CPU例：竞态、回执和有限队列

虚拟毫秒使两个event order无需sleep。真实SQLite连接竞争同主体/操作/key只有一份effect；无key不同RPC两份effect；重开、changed args和mutable alias都被核对。Buffer只保有限对象，不证明真实socket/backpressure；本地counter不是支付。

```python
import sqlite3,json,hashlib,tempfile,uuid,threading,math
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
class Request:
    def __init__(self,rid,transport,token=None):
        if type(rid) not in (int,str) or transport not in ('stdio','http'):raise ValueError('request')
        if token is not None and type(token) not in (int,str):raise ValueError('progress token')
        self.id=rid;self.transport=transport;self.token=token;self.start=0;self.last=0;self.now=0;self.progress_value=None;self.state='active';self.response=None
    def clock(self,t):
        if type(t) is not int or t<self.now:raise ValueError('monotonic virtual clock')
        self.now=t
    def progress(self,v,t):
        self.clock(t)
        if self.state!='active' or self.token is None:return None
        if type(v) not in (int,float) or not math.isfinite(v) or self.progress_value is not None and v<=self.progress_value:raise ValueError('finite increasing progress')
        self.progress_value=v;self.last=t;return {'method':'notifications/progress','progressToken':self.token,'progress':v}
    def due(self,t):
        self.clock(t)
        return self.cancel() if self.state=='active' and (t-self.start>=2000 or t-self.last>=500) else None
    def cancel(self):
        if self.state!='active':return None
        self.state='cancelled'
        return {'jsonrpc':'2.0','method':'notifications/cancelled','params':{'requestId':self.id}} if self.transport=='stdio' else {'action':'close_response_stream','requestId':self.id}
    def finish(self):
        if self.state=='cancelled':return None
        if self.response is None:self.state='complete';self.response={'jsonrpc':'2.0','id':self.id,'result':{'resultType':'complete','content':[]}}
        return self.response
class Ledger:
    def __init__(self,path):
        self.path=path;c=self.db()
        try:c.executescript('CREATE TABLE IF NOT EXISTS receipts(principal TEXT,operation TEXT,key TEXT,fingerprint TEXT,result TEXT,PRIMARY KEY(principal,operation,key));CREATE TABLE IF NOT EXISTS effects(receipt TEXT PRIMARY KEY,principal TEXT,operation TEXT);')
        finally:c.close()
    def db(self):return sqlite3.connect(self.path,isolation_level=None,timeout=5)
    def mutate(self,principal,op,args,key=None):
        if type(args.get('cents')) is not int or args['cents']<=0:raise ValueError('positive integer cents')
        fp=hashlib.sha256(json.dumps(args,sort_keys=True,allow_nan=False).encode()).hexdigest();c=self.db()
        try:
            c.execute('BEGIN IMMEDIATE')
            if key is not None:
                row=c.execute('SELECT fingerprint,result FROM receipts WHERE principal=? AND operation=? AND key=?',(principal,op,key)).fetchone()
                if row:
                    if row[0]!=fp:raise ValueError('key with changed arguments')
                    c.execute('COMMIT');return json.loads(row[1])
            receipt=uuid.uuid4().hex;out={'receipt':receipt,**args};encoded=json.dumps(out,sort_keys=True)
            c.execute('INSERT INTO effects VALUES(?,?,?)',(receipt,principal,op))
            if key is not None:c.execute('INSERT INTO receipts VALUES(?,?,?,?,?)',(principal,op,key,fp,encoded))
            c.execute('COMMIT');return json.loads(encoded)
        except BaseException:
            if c.in_transaction:c.execute('ROLLBACK')
            raise
        finally:c.close()
class Buffer:
    def __init__(self,capacity):self.capacity=capacity;self.rows=[];self.refetch=False
    def push(self,kind,data):
        if kind=='progress' and self.rows and self.rows[-1][0]=='progress' and self.rows[-1][1]['token']==data['token']:self.rows[-1]=(kind,data);return
        if len(self.rows)==self.capacity:
            index=next((i for i,x in enumerate(self.rows) if x[0]=='progress'),None)
            if index is None:
                if kind=='progress':self.refetch=True;return
                raise BufferError('final capacity exhausted')
            self.rows.pop(index);self.refetch=True
        self.rows.append((kind,data))
def delay(client,attempt):
    if type(attempt) is not int or attempt<0:raise ValueError('attempt')
    top=min(8000,250*2**min(attempt,16));bottom=top//2
    return bottom+int.from_bytes(hashlib.sha256(f'{client}:{attempt}'.encode()).digest()[:4],'big')%(top-bottom+1)
def reject(fn,typ=ValueError):
    try:fn()
    except typ:return
    raise AssertionError('expected rejection')
a=Request(1,'stdio','p1');assert a.cancel()['method']=='notifications/cancelled' and a.finish() is None
b=Request(2,'http');answer=b.finish();assert b.cancel() is None and b.finish()==answer
c=Request(3,'http','p3')
for v,t in enumerate([400,800,1200,1600,1999],1):c.progress(v,t)
assert c.due(2000)['action']=='close_response_stream'
d=Request(4,'stdio','p4');d.progress(1,100);reject(lambda:d.progress(float('nan'),110));assert d.due(600)['params']['requestId']==4
# active token uniqueness belongs to the request registry, independently of request-id correlation.
class Registry:
    def __init__(self):self.requests={};self.tokens=set()
    def add(self,r):
        if r.id in self.requests or r.token is not None and r.token in self.tokens:raise ValueError('active id/token collision')
        self.requests[r.id]=r
        if r.token is not None:self.tokens.add(r.token)
registry=Registry();registry.add(Request(5,'stdio','p5'));reject(lambda:registry.add(Request(6,'http','p5')));reject(lambda:registry.add(Request(5,'http','p6')))
with tempfile.TemporaryDirectory(dir='/tmp',prefix='study-ledger-') as folder:
    path=str(Path(folder)/'ledger.db');x=Ledger(path);args={'account':'fixture-account','cents':500}
    assert x.mutate('alice','unsafe',args)['receipt']!=x.mutate('alice','unsafe',args)['receipt']
    barrier=threading.Barrier(2)
    def race(rpc_id):barrier.wait();return Ledger(path).mutate('alice','charge',args,'order-1')
    with ThreadPoolExecutor(2) as pool:rows=list(pool.map(race,[41,42]))
    assert rows[0]==rows[1] and rows[0] is not rows[1]
    rows[0]['cents']=999;assert Ledger(path).mutate('alice','charge',args,'order-1')['cents']==500
    reject(lambda:x.mutate('alice','charge',{**args,'cents':700},'order-1'))
    x.mutate('bob','charge',args,'order-1') # 另一主体的同名业务key是独立意图。
    conn=x.db();assert conn.execute("SELECT count(*) FROM effects WHERE principal='alice' AND operation='charge'").fetchone()[0]==1;assert conn.execute("SELECT count(*) FROM effects WHERE operation='unsafe'").fetchone()[0]==2;conn.close()
q=Buffer(3)
for i in range(10):q.push('progress',{'token':f'p{i}','value':i})
q.push('final',{'id':41});assert len(q.rows)==3 and q.rows[-1][0]=='final' and q.refetch
full=Buffer(2);full.push('final',{'id':1});full.push('final',{'id':2});reject(lambda:full.push('final',{'id':3}),BufferError)
assert len({delay(x,4) for x in ('a','b','c','d')})>1 and all(2000<=delay(x,4)<=4000 for x in ('a','b','c','d'))
print('reliability:取消竞态/双deadline/有限progress、两SQLite连接同key仅一effect/重开防alias、主体隔离、有限队列保final/refetch与jitter通过；无外部支付或网络')
```

## 10. Apps：界面桥接与宿主权力

### 10.1 三层协议与预声明资源

core运送discover/list/call/read；Apps扩展声明UI；浏览器sandbox负责界面隔离。`io.modelcontextprotocol/ui`设置应带`mimeTypes: ["text/html;profile=mcp-app"]`，不是只见ui:{}就认定可呈现。tool在list时用`_meta.ui.resourceUri`绑定ui://资源，host可预取/复审；tool result保持有意义text/structuredContent，不能临时发明content类型重复URI。

HTML5 UI资源用该MIME，以text或Base64 blob交付，_meta.ui声明CSP/permissions。resource能力仍须实现list，但UI-only resource可按扩展不列进list，因为tool binding已发现。无Apps的host保有普通工具与text fallback；不能让“未渲染iframe”成为tool业务失败。旧flat ui/resourceUri是兼容面，不当新写法。

visibility缺省model+app；app-only工具不进模型目录，model-only拒app调用；app-only不可跨server。host仍检查具体tool参数、可信当前身份、目标与操作策略，按钮或桥接消息不能自行同意自己的危险动作。

### 10.2 桥接初始化、隔离与撤权

Apps的ui/initialize使用其**自己的2026-01-26版本**，请求含appInfo/appCapabilities/protocolVersion，结果含version/hostInfo/hostCapabilities/hostContext。View响应后发ui/notifications/initialized；host收到ready才发送其后的请求/通知。它建立的是iframe-local bridge，不恢复已取消的core initialize/session。被桥接的新core请求要新ID和完整当前meta。

web Host使用不同源Sandbox proxy再加载View；规范Sandbox权限包含allow-scripts与allow-same-origin，安全依赖**不同origin与隔离链**，不能不分origin乱拷flags。消息校验应按可信peer/source与origin设计。下面已知origin fixture要求精确origin和source；opaque origin/SDK路由要按官方transport实现，不能把所有wildcard target泛称协议违规。

host按声明域构造CSP、禁止未声明域，connect网络、resource脚本/字体、frame嵌套和base URI分别控制。允许API域仍可外传数据，不能等同“安全”；credentials不进iframe，窄动作由host代理并限制payload。空connect名单不证明OS隔离或所有iframe权力已实现。

hostContext不只是启动主题：主题/对比度/字号变化、尺寸请求、焦点顺序、accessibility、zoom与reduced-motion都需更新和实际测试。account/policy/server admission撤销时检查每次action，拒待发privileged calls、停止不再允许网络、清敏感视图或重挂/回text。UI资源缓存过期、hash/绑定/pin变更和resource change要refetch并重新审policy，不能让旧iframe永久保旧权限。

### 10.3 完整CPU例：headless bridge合同

本例不启动浏览器，只验证结构、版本、ready、visibility、可信source与当前撤权；由host给principal，不从消息字段授权。notes_open是只读fixture，输出并未打开真实文件。实际CSP、sandbox、键盘/读屏/resize仍待浏览器验证；HTML里出现安全字符串和测试assert不能替代这些。

```python
import copy
CORE='2026-07-28';UI='2026-01-26';MIME='text/html;profile=mcp-app';EXT='io.modelcontextprotocol/ui'
PV='io.modelcontextprotocol/protocolVersion';CAP='io.modelcontextprotocol/clientCapabilities'
TOOLS={'notes_open':{'visibility':['app'],'server':'notes'},'admin_export':{'visibility':['model'],'server':'notes'},'timeline':{'visibility':['model','app'],'server':'notes'}}
def supports(caps):
    extensions=caps.get('extensions',{})
    if type(extensions) is not dict:return False
    ui=extensions.get(EXT)
    return type(ui) is dict and type(ui.get('mimeTypes')) is list and all(type(x) is str for x in ui['mimeTypes']) and MIME in ui['mimeTypes']
def descriptor(caps):
    d={'name':'timeline','inputSchema':{'type':'object'}}
    if supports(caps):d['_meta']={'ui':{'resourceUri':'ui://notes/timeline','visibility':['model','app']}}
    return d
class Host:
    def __init__(self,principal='alice'):
        self.principal=principal # 由fixture的可信host边界注入，不取event/clientInfo。
        self.peer=object();self.origin='https://sandbox.example';self.state='new';self.allowed={'tools/call'};self.next_id=100;self.core_sent=[];self.sensitive_view=False
    def receive(self,event):
        if event.get('source') is not self.peer or event.get('origin')!=self.origin:raise ValueError('peer source/origin')
        m=event.get('data')
        if type(m) is not dict or m.get('jsonrpc')!='2.0' or type(m.get('method')) is not str:raise ValueError('bridge envelope')
        method=m['method'];p=m.get('params',{})
        if type(p) is not dict:raise ValueError('bridge params')
        if method=='ui/notifications/initialized':
            if 'id' in m or self.state!='initialized-response':raise ValueError('readiness order')
            self.state='ready';return None
        if type(m.get('id')) not in (int,str):raise ValueError('bridge id')
        if method=='ui/initialize':
            info=p.get('appInfo');caps=p.get('appCapabilities')
            if self.state!='new' or p.get('protocolVersion')!=UI or type(info) is not dict or any(type(info.get(k)) is not str for k in ('name','version')) or type(caps) is not dict:raise ValueError('Apps initialize contract')
            self.state='initialized-response'
            return {'jsonrpc':'2.0','id':m['id'],'result':{'protocolVersion':UI,'hostInfo':{'name':'fixture-host','version':'1'},'hostCapabilities':{'tools':{}},'hostContext':{'theme':'light','locale':'zh-CN'}}}
        if self.state!='ready' or method not in self.allowed:raise ValueError('current bridge capability')
        if method!='tools/call':raise ValueError('fixture only tools/call')
        name=p.get('name');definition=TOOLS.get(name);args=p.get('arguments')
        if not definition or 'app' not in definition['visibility'] or definition['server']!=p.get('server','notes') or type(args) is not dict:raise ValueError('visibility/owner/arguments')
        # principal由host登录边界给出。桥接参数自称principal不能覆盖它；此fixture只允许只读open。
        if self.principal!='alice' or name!='notes_open' or set(args)!={'noteId'} or args['noteId']!='fixture-note':raise ValueError('host action policy')
        self.next_id+=1;wire={'jsonrpc':'2.0','id':self.next_id,'method':'tools/call','params':{'name':name,'arguments':copy.deepcopy(args),'_meta':{PV:CORE,CAP:{'extensions':{EXT:{'mimeTypes':[MIME]}}}}}}
        self.core_sent.append(wire)
        return {'jsonrpc':'2.0','id':m['id'],'result':{'content':[{'type':'text','text':'fixture read only'}],'isError':False}}
    def tool_data(self):
        if self.state!='ready':raise ValueError('no host notification before readiness')
        self.sensitive_view=True;return {'jsonrpc':'2.0','method':'ui/notifications/tool-result','params':{'content':[{'type':'text','text':'fixture'}]}}
    def revoke(self):self.allowed.clear();self.sensitive_view=False
    def event(self,m):return {'origin':self.origin,'source':self.peer,'data':m}
def init_message(version=True):
    p={'appInfo':{'name':'timeline','version':'1'},'appCapabilities':{}}
    if version:p['protocolVersion']=UI
    return {'jsonrpc':'2.0','id':0,'method':'ui/initialize','params':p}
def reject(fn):
    try:fn()
    except ValueError:return
    raise AssertionError('expected rejection')
caps={'extensions':{EXT:{'mimeTypes':[MIME]}}};assert '_meta' in descriptor(caps) and '_meta' not in descriptor({'extensions':{EXT:{}}})
# UI-only resource可不列进resources/list，绑定仍可由resources/read解析；此处只检合同，不服务HTML。
resources=[];binding=descriptor(caps)['_meta']['ui']['resourceUri'];assert resources==[] and binding=='ui://notes/timeline'
h=Host();reject(lambda:h.receive(h.event(init_message(False))));r=h.receive(h.event(init_message()));assert set(r['result'])=={'protocolVersion','hostInfo','hostCapabilities','hostContext'}
reject(h.tool_data);assert h.receive(h.event({'jsonrpc':'2.0','method':'ui/notifications/initialized'})) is None
assert h.tool_data()['method']=='ui/notifications/tool-result'
call={'jsonrpc':'2.0','id':1,'method':'tools/call','params':{'name':'notes_open','arguments':{'noteId':'fixture-note'}}}
h.receive(h.event(call));assert h.core_sent[-1]['id']!=call['id'] and h.core_sent[-1]['params']['_meta'][PV]==CORE
reject(lambda:h.receive({**h.event(call),'source':object()}));reject(lambda:h.receive({**h.event(call),'origin':'https://evil.example'}))
reject(lambda:h.receive(h.event({**call,'params':{**call['params'],'server':'other'}})))
reject(lambda:h.receive(h.event({**call,'params':{'name':'admin_export','arguments':{}}})))
assert [n for n,t in TOOLS.items() if 'model' in t['visibility']]==['admin_export','timeline']
h.revoke();reject(lambda:h.receive(h.event(call)));assert not h.sensitive_view
print('Apps: MIME capability/预声明binding、独立UI版本/完整初始化/ready顺序、可信peer与visibility/同server/action实时撤权、完整新core元数据通过；未iframe/CSP/浏览器')
```

## 11. 证据符合性与操作判断

### 11.1 验原始合同，也验实现的转换

golden transcript含实际要检查的status/header/body，negative证明**哪个边界**拒绝。header mismatch不因本地validator抛异常就算server正确，必须检查fixture中捕获的400、-32020和相同请求ID；真实集成下一层再捕获实际进/出字节。normalized SDK对象可隐藏resultType、cache hints或未知字段，wire证据要独立保存。known discriminator合法也要验证method payload、cache、MRTR eligible方法和本次wire能力。

forward compatibility区分未知附加字段与未知生命周期判别值：前者可按组件职责保留/有意忽略，透明proxy通常应保真；后者不能当complete。比较SDK时按method-specific语义投影，工具目录的cache TTL可由SDK另管，Tasks的ttlMs却是job寿命，不能统一删掉。未知futureHint损失应可见，不能拿最便利的projection掩盖回归。

proxy至少比ingress原请求、origin转发与响应、egress客户端可见状态/正文。origin400变proxy500、header/body语义改变、SSE被buffer到最后都是不同证据；路由认证、Content-Type/Accept、TLS终结、压缩/trace也需真实部署测试。此处仅预设对象，不称完成网络集成。

### 11.2 脱敏、健康与可恢复发布

先递归脱敏，再序列化/hash/写日志；camelCase与分隔符变体使用相同canonical key。denylist只能去明显credentials，query等普通键也可含PII，需要method-specific采集政策。Hash表明哪份**脱敏**证据驱动判断，不证明证据真实或保留raw有授权。

健康门槛预先定样本数、错误分母/上限、latency分位、资源饱和和观察窗口。0 samples、bool count、NaN rate不算healthy；教学preset数不称真实压测。回滚目标绑定exact版本、artifact/descriptor/admission digest、当前Registry状态、健康与观测时间，并由可信controller验证attestation。格式像SHA只是结构检查，签名只是确认哪主体认可该payload，不能让陈旧health永久有效。

候选未投流就失败应hold；已投流失败且有验证过目标才rollback，否则hold traffic并处理。promotion前验证恢复路径是应用发布策略，不是MCP core操作授权。下面HMAC key/health/registry/proxy/SDK都明确假数据，没有真实部署动作。

### 11.3 完整CPU例：错误证据、语义投影与门禁

程序有合法列表与缺cache反例，task能力从request._meta读取，Task TTL投影保留；SDK future字段丢失、proxy状态collapse、递归脱敏后hash、typed有限health与过期/篡改attestation各自能失败。它是所列规则的可运行子集，不是官方conformance全套；构造transcript不等实际采集线上wire。

```python
import json,hashlib,hmac,math,copy,re
PV='io.modelcontextprotocol/protocolVersion';CAP='io.modelcontextprotocol/clientCapabilities';EXT='io.modelcontextprotocol/tasks';V='2026-07-28'
CACHE={'server/discover','tools/list','prompts/list','resources/list','resources/templates/list','resources/read'}
SECRET={'authorization','cookie','setcookie','accesstoken','refreshtoken','apikey','clientsecret','registrationaccesstoken','password','token','secret'}
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False)
def redact(x):
    if type(x) is dict:return {k:'[REDACTED]' if ''.join(c for c in k.casefold() if c.isalnum()) in SECRET else redact(v) for k,v in x.items()}
    if type(x) is list:return [redact(v) for v in x]
    return x
def digest(x):return hashlib.sha256(canonical(redact(x)).encode()).hexdigest()
def projection(method,r):
    # tasks/get或tools/call返回task时，ttlMs是业务job寿命，必须保留。
    omitted={'resultType','_meta'} | ({'ttlMs','cacheScope'} if method in CACHE else set())
    return {k:v for k,v in r.items() if k not in omitted}
def response(req,status,r):
    if type(r) is not dict or r.get('jsonrpc')!='2.0' or type(r.get('id')) is not type(req['id']) or r.get('id')!=req['id'] or ('result' in r)==('error' in r):raise ValueError('response envelope')
    if 'error' in r:
        e=r['error']
        if type(e) is not dict or type(e.get('code')) is not int or type(e.get('message')) is not str:raise ValueError('error shape')
        if e['code'] in (-32020,-32021,-32022,-32602) and status!=400 or e['code']==-32601 and status!=404:raise ValueError('status mapping')
        return
    if status!=200:raise ValueError('success status')
    result=r['result']
    if type(result) is not dict:raise ValueError('result object')
    meta=result.get('_meta');info=meta.get('io.modelcontextprotocol/serverInfo') if type(meta) is dict else None
    if type(info) is not dict or any(type(info.get(k)) is not str for k in ('name','version')):raise ValueError('server identity metadata')
    kind=result.get('resultType');m=req['method']
    if kind=='complete':
        if m in CACHE and (type(result.get('ttlMs')) is not int or result['ttlMs']<0 or result.get('cacheScope') not in ('private','public')):raise ValueError('cache contract')
        if m=='tools/list' and type(result.get('tools')) is not list:raise ValueError('tool list')
    elif kind=='input_required':
        if m not in ('tools/call','resources/read','prompts/get') or not any(k in result for k in ('inputRequests','requestState')) or 'requestState' in result and type(result['requestState']) is not str or 'inputRequests' in result and type(result['inputRequests']) is not dict:raise ValueError('MRTR contract')
    elif kind=='task':
        caps=req['params']['_meta'][CAP];extensions=caps.get('extensions',{})
        if m!='tools/call' or type(extensions) is not dict or type(extensions.get(EXT)) is not dict:raise ValueError('wire task capability')
        if any(type(result.get(k)) is not str for k in ('taskId','status','createdAt','lastUpdatedAt')) or 'ttlMs' not in result or result['ttlMs'] is not None and (type(result['ttlMs']) is not int or result['ttlMs']<0):raise ValueError('task fields')
        if result['status'] not in ('working','input_required','completed','failed','cancelled'):raise ValueError('task status')
    else:raise ValueError('unknown discriminator')
def transcript(req,headers,status,r):
    p=req.get('params');meta=p.get('_meta') if type(p) is dict else None;issue=None
    if type(meta) is not dict or type(meta.get(PV)) is not str or type(meta.get(CAP)) is not dict:issue=-32602
    elif headers.get('MCP-Protocol-Version')!=meta[PV] or headers.get('Mcp-Method')!=req['method']:issue=-32020
    elif meta[PV]!=V:issue=-32022
    response(req,status,r)
    if issue is not None and r.get('error',{}).get('code')!=issue:raise ValueError('missing actual rejection evidence')
    return digest({'request':req,'headers':headers,'status':status,'response':r})
def differential(method,raw,sdk):
    semantic=projection(method,raw)
    missing=sorted(k for k in semantic if k not in sdk);changed=sorted(k for k in semantic if k in sdk and semantic[k]!=sdk[k])
    return {'passed':not missing and not changed,'missing':missing,'changed':changed,'rawDigest':digest(raw),'sdkDigest':digest(sdk)}
def proxy(exchange):
    origin,egress=exchange['origin'],exchange['egress']
    return {'passed':origin['status']==egress['status'] and origin['body']==egress['body'],'digests':{k:digest(v) for k,v in exchange.items()}}
def healthy(h):
    numbers=('errorRate','p95Ms')
    return type(h.get('sampleCount')) is int and h['sampleCount']>=2 and all(type(h.get(k)) in (int,float) and math.isfinite(h[k]) for k in numbers) and 0<=h['errorRate']<=.01 and 0<=h['p95Ms']<=500
KEY=b'non-secret-fixture-key';TRUSTED={'release-controller':KEY}
def attest(payload):return {**payload,'signer':'release-controller','signature':hmac.new(KEY,canonical(payload).encode(),'sha256').hexdigest()}
def rollback_ok(e,now):
    if type(e) is not dict:return False
    payload={k:v for k,v in e.items() if k not in ('signer','signature')};key=TRUSTED.get(e.get('signer'))
    if not key or type(e.get('signature')) is not str:return False
    try:expected=hmac.new(key,canonical(payload).encode(),'sha256').hexdigest()
    except (ValueError,TypeError):return False
    pins=('artifactDigest','descriptorDigest','admissionDigest')
    return hmac.compare_digest(e['signature'],expected) and type(e.get('version')) is str and bool(e['version']) and e.get('registryStatus')=='active' and all(type(e.get(k)) is str and re.fullmatch('[0-9a-f]{64}',e[k]) for k in pins) and type(e.get('observedAt')) is int and 0<=now-e['observedAt']<20 and healthy(e.get('health',{}))
def gate(candidate_ok,health,evidence_digests,target,now,in_traffic):
    complete=bool(evidence_digests) and all(type(d) is str and re.fullmatch('[0-9a-f]{64}',d) for d in evidence_digests)
    ready=rollback_ok(target,now)
    if candidate_ok is True and healthy(health) and complete and ready:return 'promote'
    return 'rollback' if in_traffic and ready else 'hold'
def reject(fn):
    try:fn()
    except ValueError:return
    raise AssertionError('expected rejection')
req={'jsonrpc':'2.0','id':1,'method':'tools/list','params':{'_meta':{PV:V,CAP:{}}}}
headers={'MCP-Protocol-Version':V,'Mcp-Method':'tools/list'};info_meta={'io.modelcontextprotocol/serverInfo':{'name':'evidence-fixture','version':'1'}}
r={'jsonrpc':'2.0','id':1,'result':{'resultType':'complete','tools':[],'ttlMs':0,'cacheScope':'private','futureHint':7,'_meta':info_meta}}
evidence=transcript(req,headers,200,r)
reject(lambda:response(req,200,{**r,'result':{'resultType':'complete','tools':[],'_meta':info_meta}})) # 专测cache缺失。
no_identity=copy.deepcopy(r);no_identity['result'].pop('_meta');reject(lambda:response(req,200,no_identity))
reject(lambda:response(req,200,{**r,'id':True}))
bad_headers={**headers,'MCP-Protocol-Version':'2027-01-01'};reject(lambda:transcript(req,bad_headers,500,{'jsonrpc':'2.0','id':1,'error':{'code':-32603,'message':'proxy'}}))
assert transcript(req,bad_headers,400,{'jsonrpc':'2.0','id':1,'error':{'code':-32020,'message':'mismatch'}})
raw_task={'resultType':'task','taskId':'t1','status':'working','createdAt':'2026-10-08T00:00:00Z','lastUpdatedAt':'2026-10-08T00:00:00Z','ttlMs':1000,'_meta':info_meta}
tr={**req,'method':'tools/call'};reject(lambda:response(tr,200,{**r,'result':raw_task}))
tr=copy.deepcopy(tr);tr['params']['_meta'][CAP]={'extensions':{EXT:{}}};response(tr,200,{**r,'result':raw_task})
assert projection('tools/call',raw_task)['ttlMs']==1000 and projection('tasks/get',{**raw_task,'resultType':'complete'})['ttlMs']==1000
assert 'ttlMs' not in projection('tools/list',r['result']) and projection('tools/list',r['result'])['futureHint']==7
safe=redact({'accessToken':'A','headers':{'Authorization':'B'},'client.secret':'C'});assert all(v=='[REDACTED]' for v in (safe['accessToken'],safe['headers']['Authorization'],safe['client.secret']))
assert digest({'Authorization':'A'})==digest({'Authorization':'B'})
assert not differential('tools/list',r['result'],{'tools':[]})['passed']
assert differential('tools/list',r['result'],{'tools':[],'futureHint':7})['passed']
assert not differential('tools/call',raw_task,{k:v for k,v in projection('tools/call',raw_task).items() if k!='ttlMs'})['passed']
exchange={'ingress':{'headers':headers,'body':req},'origin':{'status':400,'body':{'error':{'code':-32020}}},'egress':{'status':500,'body':{'message':'upstream'}}};assert not proxy(exchange)['passed']
exchange['egress']=copy.deepcopy(exchange['origin']);assert proxy(exchange)['passed']
h={'sampleCount':100,'errorRate':.002,'p95Ms':180};assert healthy(h) and not healthy({**h,'sampleCount':True}) and not healthy({**h,'errorRate':float('nan')})
target=attest({'version':'fixture-v1','registryStatus':'active','artifactDigest':'a'*64,'descriptorDigest':'b'*64,'admissionDigest':'c'*64,'observedAt':90,'health':h})
assert gate(True,h,[evidence],target,100,False)=='promote'
assert gate(False,h,[evidence],target,100,False)=='hold' and gate(False,h,[evidence],target,100,True)=='rollback'
assert gate(True,h,[],target,100,False)=='hold'
assert not rollback_ok({**target,'version':'tampered'},100) and not rollback_ok(target,110)
print('evidence:fixture拒绝响应证据、cache/task CAP负例、method-specific TTL投影、脱敏后hash、有限typed health与签名/新鲜rollback、未投流失败hold通过；假SDK/proxy/health')
```

## 12. 原练习与开放实验怎样验收

以下是完整练习的判据索引，原课程编号只用于追溯，知识主结构仍是上面的通信、输入、状态和可靠性。程序覆盖的是表中明确的本地性质；要求SDK、真实HTTP、URL登录、symlink文件系统、跨进程/多机或浏览器的题目仍以方法/判据保留，未称已运行。

| 原题 | 验收判据 |
|---|---|
| 06-1 版本2027 | -32022，requested原值与supported集合；新ID选共同版本 |
| 06-2 第二请求缺CAP | -32602，不继承第一请求；与缺可选能力区分 |
| 06-3 反转registry | list稳定排序，目录成员不依赖连接历史 |
| 06-4 public/private | public内容无用户差异；private同凭证context，primitive当前授权另核 |
| 06-5 无clientInfo | 可合法处理；该信息SHOULD但不做auth |
| 07-1 缺CAP | 每请求元数据检查；无连接默认值 |
| 07-2 反转三registry | tools/prompts/resources固定sort key，各完整结果有cache hints |
| 07-3 destructive delete | annotations仅UX；executor可信主体、目标版本/范围和批准校验 |
| 07-4 templates list | 有URI模板、固定排序/TTL/scope，变量解析与授权不省略 |
| 07-5 legacy adapter | 两parser明确入口；modern不会initialize或复用旧CAP |
| 08-1 无共同版本 | recognized现代错误仍不降级；surface error |
| 08-2 旧探测timeout | 应用allowlist只准probe；没有有效initialize正证不activate |
| 08-3 两private contexts | cache跨token/主体不能复用，TTL/通知/权限变化可使失效 |
| 08-4 reject冲突 | 两owner与local name报错；不能源码continue静默略过 |
| 08-5 listen断流 | 新ID/filter+refetch，无Last-Event-ID；unsafe write先核回执 |
| 09-1 缺Mcp-Method | 400/-32020、before dispatch |
| 09-2 一致未知version | 400/-32022且data准确；不混header mismatch |
| 09-3 Unicode URI | UTF8 Base64 sentinel解码后与正文uri同值 |
| 09-4 break listen | 新listen ID与受影响目录refetch；真实断流尚未运行 |
| 09-5 workflow handle | 可信主体每次授权、共享存储/寿命/并发；无connection affinity依赖 |
| 10-1 resource template | 两变量解析/长度/字符/权限，不任意拼路径 |
| 10-2 pagination | 全局稳定次序、empty cursor继续、page cap与变更快照边界 |
| 10-3 private TTL0 | MCP scope不接受no-store；host可另设no-store policy |
| 10-4 prompt通知filter | 未声明promptsListChanged不发事件，ack接受子集先到 |
| 10-5 两subscriptions | 各ID先ack并独立filter，可共用stdio通道 |
| 10-6 owner+cache | prompt/read同权限，主体/凭证变化不泄内容 |
| 11-1 invalid pick JSON | 输入拒绝，不把文本当文件路径；known files白名单 |
| 11-2 audience变更 | signed参数digest拒跨请求state重用 |
| 11-3 critique第三轮 | phase/已验证中间值签入state；至多三次输入，RPC IDs独立 |
| 11-4 direct provider | 写清server接管凭证/费用/重试/出站/观测；真实provider未跑 |
| 11-5 expiry | exact边界过期拒绝；TTL不能替single-use nonce |
| 12-1 SQLite nonce | claim+删除+回执同事务；两个连接competition/重开；两真实进程待验 |
| 12-2 URL mode | 当前CAP支持url，完整URL同意后打开，不prefetch；外部credentials不回client |
| 12-3 notes SQLite | 事务内核owner、containment、版本；不只之前检查 |
| 12-4 symlink policy | 词法containment非真实sandbox/TOCTOU证明，需真实安全open验证 |
| 12-5 legacy elicitation | 单独旧适配；modern MRTR/新ID不变成reverse request |
| 13-1 两input keys | partial update后仍input_required，齐全后working；lifetime不重用 |
| 13-2 tenant ownership | task ID不授权，get/update/cancel/listen每次检查 |
| 13-3 worker lease | 真两个SQLite连接一个claim，过期recovery使旧token失效 |
| 13-4 POST SSE adapter | ack/filter/subscriptionId/fullsnapshots与任务CAP；真实HTTP未跑 |
| 13-5 expiry cleanup | 创建起算TTL、task unavailable与所有权不泄漏；可删过期记录 |
| 14-1 text fallback | 无所需mimeTypes即不绑定UI，普通工具仍有有意义结果 |
| 14-2 wrong resource header | 400/-32020，不择header/body其中一项执行 |
| 14-3 private UI | HTML/权限或数据随credential变才private；缓存hash/pin/policy一并核 |
| 14-4 external script | resourceDomains只放必要origin；供应链可执行代码需admission，非connect许可 |
| 14-5 host mediated open | predeclared/app visibility、当前cap/身份/目标，不能按钮自授权；未真实打开文件 |

第28课的交互实验应逐项改output array→object观察拒绝，恢复后比较empty与null结束cursor策略；敏感annotation在准入前拒，嵌套properties正确允许、组合/items/ref拒；Unicode/控制符/首尾空白/sentinel往返，缺recognized header为400/-32020。其search_evidence开放lab要求query/limit/region、array(uri/title/score)输出、兼容text和每item resource link、未知参数拒绝、limit范围、低权限不见URI、错误score/注解/双页/安全整数和header大小写反例；必须对照actual args/results，不能只看有schema文案。

第29课的交互实验比较cancel先、complete先、持续progress碰maximum和HTTP close四种event ordering，换stdio只换signal。reserve_inventory开放lab把SKU/quantity/tenant/operation纳入业务意图，samekey同参数原回执、changedquantity拒绝、commit丢响应可reconcile；无key禁自动retry，两连接竞争、returned alias、重开与断订阅refetch都要验。inventory外服务若不参加事务，说明upstream key/outbox边界。

第31课的四实验分别比较modern/legacy discriminator、加严fallback与recognized错误、additive字段对unknown resultType、SDK projection损失与proxy修复。只给本地异常不构成server拒绝证据。SSE开放lab还要实际status/contentType/ordered events/终止、错误ID与buffering反例、redact前不落盘raw、首event latency/时长/count进入真实health。当前只有对象fixture与CPU模型；这些真实边界尚未执行。

72道原quiz的答案与逐题判断在本批覆盖清单保留。学习者可用本章自检核对：是否区分角色/primitive、逐请求/legacy、error层、cache scope、opaque cursor、MRTR输入与业务task、RPC完成与job完成、取消ack与实际停止、Apps桥接与core版本、附加字段与discriminator、fixture与集成证明。正确答案不代表实际掌握；开放题用上述可观察判据，不编造唯一生产配置。

## 13. 图示、作者产物与实际未覆盖

九SVG的角色/原生primitive、请求验证、传输时代、Sampling/MRTR、显式scope、Apps隔离意图有学习价值；task-lifecycle.svg错误地画completed→failed/cancelled，本专题只保非终态至terminal且不可回流的规则。十二正文动态图最终provider是figures-mcp.js，晚注册覆盖旧SMIL/provider；它的scenario/choice→evaluate→展示wire与verdict是有限预设模型。HMAC字符串、effectCount、blocked sandbox、Python/TypeScript runner名称不是运行相应机制的证据；旧fallback图缺现代meta/绑定等细节也不能照教。

作者outputs被转成设计/验收判据，未安装Skill或执行其拒绝/部署门禁。目录、章节、测验、练习、图示、代码和tests完整阅读不等所有API全文审验。源222个test_方法仅阅读；新8个本地块与旧核心强例的证据分别记录，历史日期不改成今天。

真实stdio子进程/HTTP/SSE/OAuth/SDK、完整JSON Schema dialect/外部ref、网络取消、队列worker/多机store、真实人机/URL登录、symlink/OSsandbox、iframe/CSP/可访问性、实际proxy/SDK differential、生产canary/回滚与模型推理均未执行。需要时从对应局部fixture进入真实集成，并保raw与normalized、预期与观测、失败与未知的独立证据。

## 14. 固定来源与后续维护

主要来源：AI Engineering from Scratch，固定[3be078b37ffd8f0c04953c0678e48f5c6d0c7775的Phase13](https://github.com/rohitg00/ai-engineering-from-scratch/tree/3be078b37ffd8f0c04953c0678e48f5c6d0c7775/phases/13-tools-and-protocols)，本专题吸收06–14/28/29/31有效知识，与旧核心MCP例融合；不镜像整来源，不读取后四站。

官方细节2026-10-08按明确范围核验：[Base/元数据/错误](https://modelcontextprotocol.io/specification/2026-07-28/basic)、[发现](https://modelcontextprotocol.io/specification/2026-07-28/server/discover)、[MRTR](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/mrtr)、[stdio](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/stdio)、[Streamable HTTP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)、[缓存](https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/caching)、[分页](https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/pagination)、[资源](https://modelcontextprotocol.io/specification/2026-07-28/server/resources)、[提示](https://modelcontextprotocol.io/specification/2026-07-28/server/prompts)、[工具](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)、[补全](https://modelcontextprotocol.io/specification/2026-07-28/server/utilities/completion)、[Elicitation](https://modelcontextprotocol.io/specification/2026-07-28/client/elicitation)、[Sampling](https://modelcontextprotocol.io/specification/2026-07-28/client/sampling)、[Roots](https://modelcontextprotocol.io/specification/2026-07-28/client/roots)、[取消](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/cancellation)、[进度](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/progress)、[订阅](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/subscriptions)、[版本兼容](https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning)。固定schema/spec提交为`0a11bf68c7ec4473526ec15589f592afcd12d1e8`，读取范围在覆盖清单，不声称全库全文。

[Tasks详细2026-07-28规范](https://github.com/modelcontextprotocol/ext-tasks/blob/93a4915aadf714f87ece5cd40c317bce24779cf5/specification/2026-07-28/tasks.md)固定`93a4915aadf714f87ece5cd40c317bce24779cf5`；[Apps详细2026-01-26规范](https://github.com/modelcontextprotocol/ext-apps/blob/82221c0c8ce7661efa6771c9d461511b1650495f/specification/2026-01-26/apps.mdx)与[初始化类型](https://github.com/modelcontextprotocol/ext-apps/blob/82221c0c8ce7661efa6771c9d461511b1650495f/src/spec.types.ts)固定`82221c0c8ce7661efa6771c9d461511b1650495f`。扩展旧示意中initialize不能直接套进modern core，适用层与版本先核对。

延伸：[工具使用](../01-核心章节/05-工具使用.md)、[异常处理与恢复](../01-核心章节/12-异常处理和恢复.md)、[人机协同](../01-核心章节/13-人机协同.md)、[安全模式](../01-核心章节/18-安全模式.md)、[评估和监控](../01-核心章节/19-评估和监控.md)、[交互与动作空间](03-交互与动作空间.md)。这些章节由其维护者统一融合，本专题不重复另写其完整骨架。

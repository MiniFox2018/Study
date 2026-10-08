# 第 10 章：模型上下文协议（MCP）

> 来源：<https://adp.xindoo.xyz/chapters/>  
> 整理语言：中文  
> 整理更新：2026-10-02；含原理、教学例子与自检。示例不是生产部署验收。

## 本章定位

通过标准化协议连接模型与外部数据、工具和服务，降低集成成本。

## 三个角色与三类能力

MCP（Model Context Protocol）连接的是 **LLM 应用与外部能力**，不是修改模型权重的协议。Host 是承载用户交互和权限管理的应用；Client 是 Host 中连接服务的组件；Server 暴露数据或可调用能力，可运行在本机或远端。

服务端的常见能力包括：Tools（执行函数）、Resources（读取上下文数据）、Prompts（可复用交互模板）。具体支持什么由双方能力和协议版本决定，不能假定每个 MCP 服务都提供全部功能。协议使用 JSON-RPC 2.0；本地常用 stdio，远程常用 Streamable HTTP。

## 具体例子：只读文件检索

应用连接一个限定目录的服务 → 发现可用工具和 schema → 请求在指定目录搜索关键词 → 服务验证路径与权限 → 返回匹配片段及来源 → 应用引用结果。MCP 让发现/调用格式可复用，搜索是否准确、路径是否越界、数据是否可信仍由实现负责。

“连上 MCP”不等于用户批准了所有动作。新增服务器、工具权限和敏感数据流向应明确；工具描述及返回文本也可能不可信。

## 版本边界与自检

核验日期：2026-10-02。官方架构文档当前指向 `2026-07-28` 规范；其发现、逐请求元数据和部分功能状态与早期教程不同。执行时固定客户端/服务端支持的协议版本，按该版规范与 SDK 进行集成，不复制混合版本的握手代码。本章示例是交互流程，没有声称部署过服务。

**问题**：MCP 与工具函数 schema 是不是同一层？

**核对**：不是。函数 schema 描述一次调用的输入结构；MCP 还定义连接双方的协议语义、能力发现和传输相关行为，但不替代业务验证。

官方依据：[架构说明](https://modelcontextprotocol.io/docs/learn/architecture)、[2026-07-28 规范](https://modelcontextprotocol.io/specification/2026-07-28)。

## 来自《深入理解 AI Agent》的增量吸收

- MCP 应放在更大的“工具生态”中理解：它解决标准化连接问题，但不能替代工具本身的能力设计、权限边界和上下文管理。
- 当工具规模扩大时，还需要配合层次化组织、按需加载、主动工具发现和 Skill 机制。
- 设计 MCP 服务时应关注工具描述质量、参数传递保真、失败反馈和安全边界。

完整来源：[第 4 章 工具](../05-来源保全/深入理解%20AI%20Agent/source/book/chapter4.md)


## 2026-07-28详细契约：连接、协议与应用状态

2026-10-07重新核对[详细Base规范](https://modelcontextprotocol.io/specification/2026-07-28/basic)、[发现](https://modelcontextprotocol.io/specification/2026-07-28/server/discover)、[MRTR](https://modelcontextprotocol.io/specification/2026-07-28/basic/patterns/mrtr)和固定schema。现代请求每次在`params._meta`带`io.modelcontextprotocol/protocolVersion`及`io.modelcontextprotocol/clientCapabilities`，clientInfo建议提供但自报身份不能用于授权。缺失/错类型为−32602；有效但不支持的版本为−32022，data带supported/requested。一次discover成功不能免除后续检查。本例只校验meta顶层必需字段及闭合工具参数，未完整验证已知CAP嵌套字段、扩展或全部协议schema；`elicitation={}`官方允许隐式form支持，不能因没有显式`form`键就误报缺能力。Server必须实现server/discover，client可选提前发现或直接调用并处理版本错误。

现代核心result显式complete或input_required；未认识的resultType应拒绝，旧版没有resultType按兼容规则视complete，但不能由此把legacy handshake混入现代连接。List/read/discover等可缓存结果带ttlMs/cacheScope，private只在相同授权上下文复用，public也仍受当前访问条件约束。serverInfo、destructiveHint只作描述，不能替代身份/实际执行策略。JSON Schema默认2020-12，input/outputSchema可用该dialect任意keywords，structuredContent可为任何JSON值并须符合所给outputSchema；本例只实现closed-object子集，不将其限制冒充标准。不自动获取外部$ref。

协议无connection-session不等应用无状态。服务可存draft，返回handle，每次携带并授权；生产handle宜采用随机不可猜ID，但仍不能自动拥有权限。下例draft-计数刻意可猜，仅演示主体授权，不能称防枚举实现。原source `tools/call`只执行handler，未运行完整schema验证或权限门禁，annotations仅标危险。它把所有handler异常变协议−32603，忽略了tool-domain错误通常应在complete结果中`isError:true`供模型纠错。其20个test_方法在前组只读，不包装成已执行或协议conformance。

### 完整内存往返：逐请求校验、handle与MRTR

下例仅实现明确的小协议子集：算术、草稿handle、配置resource与review prompt；不冒充完整MCP SDK、schema validator或HTTP。身份`principal`由fixture调用边界给定，不取clientInfo。编辑草稿先返回elicitation要求，再以新JSON-RPC ID重发原方法/参数、inputResponses及原封requestState。HMAC绑定主体/动作/参数、当前草稿revision/hash、唯一nonce与有效期；批准旧版本不改草稿，独立新轮次nonce不同。receipt让同一已完成确认在有效期内重试返回原结果，不因其自身更新了revision而失败；过期先拒绝，再考虑receipt，保持当前代码的安全顺序。审批输入由假host构造，不证明真人交互已实现。

```python
import json,hashlib,hmac,copy,uuid

VERSION='2026-07-28';PV='io.modelcontextprotocol/protocolVersion';CAP='io.modelcontextprotocol/clientCapabilities'
def canonical(obj):return json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
def digest(obj):return hashlib.sha256(canonical(obj).encode()).hexdigest()
class ProtocolError(Exception):
    def __init__(self,code,message,data=None):self.code=code;self.message=message;self.data=data
class DemoServer:
    def __init__(self):self.drafts={};self.receipts={};self.secret=b'fixture-secret-only';self.now=0;self.updates=0
    def complete(self,payload,cache=False):
        result={'resultType':'complete','_meta':{'io.modelcontextprotocol/serverInfo':{'name':'memory-demo','version':'1'}},**payload}
        if cache:result.update(ttlMs=1000,cacheScope='private')
        return result
    def seal(self,payload):
        body=canonical(payload);return body+'.'+hmac.new(self.secret,body.encode(),'sha256').hexdigest()
    def unseal(self,token):
        if type(token) is not str:raise ProtocolError(-32602,'state字符串')
        try:body,signature=token.rsplit('.',1)
        except ValueError:raise ProtocolError(-32602,'state格式')
        if not hmac.compare_digest(signature,hmac.new(self.secret,body.encode(),'sha256').hexdigest()):raise ProtocolError(-32602,'state完整性')
        return json.loads(body)
    def handle(self,message,principal):
        rid=message.get('id') if type(message) is dict else None
        try:
            if type(message) is not dict or message.get('jsonrpc')!='2.0' or type(message.get('method')) is not str:raise ProtocolError(-32600,'请求')
            if 'id' not in message:return None
            if type(rid) not in (str,int):raise ProtocolError(-32600,'ID')
            params=message.get('params');meta=params.get('_meta') if type(params) is dict else None
            if type(meta) is not dict or type(meta.get(PV)) is not str or type(meta.get(CAP)) is not dict:raise ProtocolError(-32602,'每次meta')
            if meta[PV]!=VERSION:raise ProtocolError(-32022,'不支持版本',{'supported':[VERSION],'requested':meta[PV]})
            method=message['method']
            if method=='server/discover':result=self.complete({'supportedVersions':[VERSION],'capabilities':{'tools':{},'resources':{},'prompts':{}}},True)
            elif method=='tools/list':
                schemas={'add':{'a':{'type':'integer'},'b':{'type':'integer'}},'subtract':{'a':{'type':'integer'},'b':{'type':'integer'}},'create_draft':{'text':{'type':'string'}},'update_draft':{'draftId':{'type':'string'},'text':{'type':'string'}}}
                result=self.complete({'tools':[{'name':n,'inputSchema':{'type':'object','properties':v,'required':list(v),'additionalProperties':False}} for n,v in sorted(schemas.items())]},True)
            elif method=='resources/list':result=self.complete({'resources':[{'uri':'config://app','name':'app'}]},True)
            elif method=='resources/read':
                if params.get('uri')!='config://app':raise ProtocolError(-32602,'resource')
                result=self.complete({'contents':[{'uri':'config://app','mimeType':'text/plain','text':'{"mode":"fixture"}'}]},True)
            elif method=='prompts/list':result=self.complete({'prompts':[{'name':'review','arguments':[{'name':'code','required':True}]}]},True)
            elif method=='prompts/get':
                a=params.get('arguments')
                if params.get('name')!='review' or type(a) is not dict or set(a)!={'code'} or type(a['code']) is not str:raise ProtocolError(-32602,'prompt参数')
                result=self.complete({'messages':[{'role':'user','content':{'type':'text','text':'审阅资料：'+a['code']}}]})
            elif method=='tools/call':result=self.call(params,principal,meta[CAP])
            else:raise ProtocolError(-32601,'方法不存在')
            return {'jsonrpc':'2.0','id':rid,'result':result}
        except ProtocolError as e:
            error={'code':e.code,'message':e.message}
            if e.data is not None:error['data']=e.data
            return {'jsonrpc':'2.0','id':rid if type(rid) in (str,int) else None,'error':error}
    def call(self,p,principal,capabilities):
        name=p.get('name');a=p.get('arguments',{})
        if type(a) is not dict:raise ProtocolError(-32602,'arguments')
        if name in ('add','subtract'):
            if set(a)!={'a','b'} or any(type(v) is not int for v in a.values()):raise ProtocolError(-32602,'闭合整数参数')
            out={'value':a['a']+a['b'] if name=='add' else a['a']-a['b']}
        elif name=='create_draft':
            if set(a)!={'text'} or type(a['text']) is not str:raise ProtocolError(-32602,'create参数')
            did='draft-'+str(len(self.drafts)+1);self.drafts[did]={'owner':principal,'text':a['text'],'revision':0};out={'draftId':did}
        elif name=='update_draft':
            if set(a)!={'draftId','text'} or any(type(v) is not str for v in a.values()):raise ProtocolError(-32602,'update参数')
            draft=self.drafts.get(a['draftId'])
            if not draft or draft['owner']!=principal:return self.complete({'content':[{'type':'text','text':'无访问权限'}],'isError':True})
            bound={'principal':principal,'operation':digest({'method':'tools/call','name':name,'arguments':a})}
            if 'requestState' not in p:
                if type(capabilities.get('elicitation')) is not dict or (capabilities['elicitation'] and type(capabilities['elicitation'].get('form')) is not dict):raise ProtocolError(-32021,'缺elicitation',{'requiredCapabilities':{'elicitation':{'form':{}}}})
                token=self.seal({**bound,'expires':self.now+30,'nonce':uuid.uuid4().hex,'draft_revision':draft['revision'],'draft_sha':digest({'text':draft['text']})})
                return {'resultType':'input_required','requestState':token,'inputRequests':{'approval':{'method':'elicitation/create','params':{'mode':'form','message':'批准该版本草稿？','requestedSchema':{'type':'object','properties':{'confirm':{'type':'boolean'}},'required':['confirm']}}}}}
            token=p['requestState'];state=self.unseal(token)
            if any(state.get(k)!=v for k,v in bound.items()) or self.now>=state.get('expires',-1):raise ProtocolError(-32602,'state主体/参数/过期')
            nonce=state.get('nonce')
            if type(nonce) is not str or not nonce:raise ProtocolError(-32602,'state nonce')
            if token in self.receipts:return copy.deepcopy(self.receipts[token]['result'])
            if state.get('draft_revision')!=draft['revision'] or state.get('draft_sha')!=digest({'text':draft['text']}):raise ProtocolError(-32602,'批准的draft版本已过期')
            responses=p.get('inputResponses',{})
            if type(responses) is not dict:raise ProtocolError(-32602,'inputResponses对象')
            reply=responses.get('approval',{})
            if type(reply) is not dict:raise ProtocolError(-32602,'approval对象')
            content=reply.get('content')
            if reply.get('action')!='accept' or type(content) is not dict or set(content)!={'confirm'} or type(content['confirm']) is not bool or not content['confirm']:
                return self.complete({'content':[{'type':'text','text':'未批准，不更新'}],'isError':True})
            draft['text']=a['text'];draft['revision']+=1;self.updates+=1;out={'draftId':a['draftId'],'updated':True,'revision':draft['revision']}
            result=self.complete({'content':[{'type':'text','text':canonical(out)}],'structuredContent':out,'isError':False});self.receipts[token]={'nonce':nonce,'applied_revision':draft['revision'],'result':copy.deepcopy(result)};return result
        else:raise ProtocolError(-32602,'未知工具')
        return self.complete({'content':[{'type':'text','text':canonical(out)}],'structuredContent':out,'isError':False})
server=DemoServer();counter=[0]
def request(method,params=None,principal='alice'):
    counter[0]+=1;p={'_meta':{PV:VERSION,CAP:{'elicitation':{'form':{}}}},**(params or {})}
    message={'jsonrpc':'2.0','id':counter[0],'method':method,'params':p}
    return server.handle(json.loads(json.dumps(message)),principal)
assert request('server/discover')['result']['supportedVersions']==[VERSION]
assert [t['name'] for t in request('tools/list')['result']['tools']]==['add','create_draft','subtract','update_draft']
assert request('tools/call',{'name':'subtract','arguments':{'a':5,'b':3}})['result']['structuredContent']['value']==2
assert request('tools/call',{'name':'add','arguments':{'a':True,'b':1}})['error']['code']==-32602
assert request('resources/read',{'uri':'config://app'})['result']['contents'][0]['text']
assert request('prompts/get',{'name':'review','arguments':{'code':'x=1'}})['result']['messages']
did=request('tools/call',{'name':'create_draft','arguments':{'text':'A'}})['result']['structuredContent']['draftId']
args={'name':'update_draft','arguments':{'draftId':did,'text':'B'}};paused=request('tools/call',args)
second_round=request('tools/call',args);stale_token=second_round['result']['requestState']
token=paused['result']['requestState'];assert token!=stale_token
reply={'approval':{'action':'accept','content':{'confirm':True}}}
assert request('tools/call',{**args,'_meta':{PV:VERSION,CAP:{}}})['error']['code']==-32021
bool_trap={'approval':{'action':'accept','content':{'confirm':1}}}
assert request('tools/call',{**args,'requestState':token,'inputResponses':bool_trap})['result']['isError'] and server.updates==0
assert request('tools/call',{**args,'requestState':token+'x','inputResponses':reply})['error']['code']==-32602
changed={'name':'update_draft','arguments':{'draftId':did,'text':'C'},'requestState':token,'inputResponses':reply}
assert request('tools/call',changed)['error']['code']==-32602
accepted=request('tools/call',{**args,'requestState':token,'inputResponses':reply});assert accepted['id']!=paused['id']
assert accepted['result']['structuredContent']['updated'] and server.drafts[did]['text']=='B'
retried=request('tools/call',{**args,'requestState':token,'inputResponses':reply});assert server.updates==1 and retried['result']==accepted['result']
assert request('tools/call',{**args,'requestState':stale_token,'inputResponses':reply})['error']['code']==-32602
new_round=request('tools/call',args);new_token=new_round['result']['requestState'];assert new_token not in (token,stale_token)
new_accepted=request('tools/call',{**args,'requestState':new_token,'inputResponses':reply});assert new_accepted['result']['structuredContent']['revision']==2 and server.updates==2
assert server.receipts[token]['nonce']!=server.receipts[new_token]['nonce']
assert request('tools/call',args,principal='bob')['result']['isError']
assert request('tools/list',{'_meta':{}})['error']['code']==-32602
bad=request('tools/list',{'_meta':{PV:'2025-11-25',CAP:{}}});assert bad['error']['code']==-32022 and bad['error']['data']['requested']=='2025-11-25'
print('内存wire：逐请求meta/三能力/版本/严格整数/handle授权/MRTR参数/nonce/draft版本绑定与新ID/真实重试receipt通过；未部署SDK或HTTP')
```

此例receipt/HMAC密钥仅驻内存、授权输入是fixture，未实现持久事务、并发、真实身份、OAuth、完整schema/dialect、通知/分页/订阅、取消/流式。重复create_draft仍需业务幂等ID，不能因update receipt存在就说所有操作exactly-once。不同server replica须共享必要业务状态或携带可验证handle，协议不会替应用保存它。

### 传输与兼容：详细规则先于总览

[当前Streamable HTTP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)每message POST单endpoint，请求响应为JSON或request-scoped SSE，通知接受202空body；协议正文_meta为真源，镜像header必须一致。不继续沿用Mcp-Session-Id、DELETE session或旧GET stream；订阅是subscriptions/listen POST。stdio是逐行JSON，stdout不能夹日志；源in-process函数调用没有真正启动stdio子进程或HTTP。

现代server不发独立server-to-client JSON-RPC request；MRTR只在tools/call/resources/read/prompts/get返回input_required，至少有inputRequests或requestState。客户端不能解析/改opaque state，按键对应inputResponses并用新ID重试；未声明elicitation/sampling/roots能力不能请求对应输入。requestState若影响业务，服务必须验证完整性、主体、TTL和动作绑定，绝不能当“服务器发过就可信”。旧总览仍出现初始化/双向请求措辞时，以详细版/schema为准。双时代stdio可discover探测；已识别现代错误不触发legacy回退，未知错误/超时才按[兼容规则](https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning)处理，传输失败不视用户批准。

## MCP原练习与版本维护

①subtract/list排序已在新内存例核对。②缺meta与不支持2025-11-25分别−32602/−32022并echo requested。③draftId是应用handle且每次核主体，不是protocol session。④新例完成MRTR fake-host确认与新ID/state原封回传，未调用真实人机UI或SDK；拒绝/篡改不改变稿。⑤兼容只写明确检测/回退条件，未连接旧版server。静态图`mcp-architecture`与动态`mcp-nxm-collapse`展示三host/三server逻辑关系与2.4秒预设packet动画；标准化降低适配种类，不等所有消息必须过可信中央hub，更不验证OAuth、安全、metadata或网络互通。

依据schema固定Git commit `0a11bf68c7ec4473526ec15589f592afcd12d1e8`的`schema/2026-07-28/schema.ts`，2026-10-07核请求meta、error、Discover、CallTool、MRTR/elicitation与cache字段；未声称通读所有未来扩展。原source固定3be078b Phase11第14课全文件/tests读取2026-10-06，新程序执行与详细官方核对2026-10-07；旧10-02阅读日期保留，未安装source输出Skill。

迁移提示：2026-07-28的Roots、Sampling、Logging和OAuth DCR已标Deprecated但窗口期不等立即失效；需要其旧功能时按详细页/SDK支持选择，不能教作现代新默认。Streamable HTTP取消通过关闭请求响应流，取消不自动撤销已发生副作用；OAuth/token audience与资源scope仍在执行边界检查。[变更表](https://modelcontextprotocol.io/specification/2026-07-28/changelog)、[授权规范](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)

SDK落实：另外只读核对MCP Python SDK固定commit `91941ed4d3985d59def99e090baa3f880c626cc8`的README和protocol-versions文档（v2文档接口）。其`Client`文档提供auto/legacy/现代version pin，pin可省discover但不自动取得server信息；旧`ClientSession/FastMCP`教程不能与这份接口混写。文档中的概述不能取代详细规范对recognized modern error的判断。此处没有安装/运行该SDK，实际项目须锁包版本并对metadata、MRTR、错误和两种传输做独立测试；本例手写内存server类不是`mcp.server.MCPServer`实现。[该固定SDK版本文档](https://github.com/modelcontextprotocol/python-sdk/blob/91941ed4d3985d59def99e090baa3f880c626cc8/docs/protocol-versions.md)

## 输入、结果与发现：先看完整合同

2026-10-08增量核验保留上面的2026-10-07内存强例及其原执行证据。完整通信、持久状态和新的CPU反例进入[专题06：MCP通信与状态工程](../06-专题扩展/06-MCP通信与状态工程.md)。学习顺序是本章的角色/逐请求合同→专题中的传输与消费→输入交互→任务和取消→Apps与证据；原理、手写子集与真实集成分别验收。

一次工具调用至少跨过五道门：发现目录→客户端准入描述→验证本次参数/权限并构造传输元数据→服务器执行→客户端检查结果再交模型。工具参数写得像JSON、服务器返回一个字典、SDK调用成功，各自只说明一道边界的一部分。工具描述、资源文字、提示模板和结果仍是外部数据，不能升级为host的可信系统指令。

`inputSchema`是JSON Schema对象，工具参数总是JSON对象，因此根的`type: "object"`是必需的；根旁边仍可使用`oneOf`、`allOf`、`if`、`$defs`等2020-12关键词。`outputSchema`若出现，完整结果的`structuredContent`必须符合它，包括`isError: true`的结果。`structuredContent`可为数组、标量或null；它是服务器产出的业务数据，与LLM“受约束生成”是不同层。描述可选，要求每个工具有足够有用的描述是有价值的应用准入策略，不是字段必需性的协议规则。

例如标签目录的请求与结果可以是下面的**消息示意**，不是可运行网络服务：

```json
{"jsonrpc":"2.0","id":41,"method":"tools/call","params":{"name":"tag_catalog","arguments":{},"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28","io.modelcontextprotocol/clientCapabilities":{}}}}
```

```json
{"jsonrpc":"2.0","id":41,"result":{"resultType":"complete","content":[{"type":"text","text":"[\"mcp\",\"contracts\"]"}],"structuredContent":["mcp","contracts"],"isError":false,"_meta":{"io.modelcontextprotocol/serverInfo":{"name":"catalog-fixture","version":"1"}}}}
```

描述中的输出schema应为`{"type":"array","items":{"type":"string"}}`。客户端若强行要求字典，会拒绝合法数组；若只解析兼容text却不验证`structuredContent`，会绕过真正合同。序列化JSON到text是兼容建议，不能改说标准强制每个结果都有非空text。`content`本身是列表；没有输出schema的合法空列表和“资源不存在却返回空contents”也要区分。

| 决策 | 正确判断 |
|---|---|
| 缺必需元数据、元数据错类型 | `-32602`，不能从过去请求补齐 |
| 本次缺处理所需可选能力 | `-32021`，data列`requiredCapabilities` |
| 支持的字符串版本未实现 | `-32022`，data列`requested`与`supported` |
| HTTP镜像字段与正文不一致 | 先返回`-32020`，不由header替代正文 |
| 未找到工具、无法按请求schema分派 | JSON-RPC错误；未知工具示例用`-32602` |
| 已进入工具的业务/输入范围失败 | 完整结果`isError: true`，仍守输出schema |
| 新字段与未知`resultType` | 新字段可保留/有意忽略；未知生命周期判别值必须拒绝 |

不能为业务限流/容量错误随意占用`-32020`至`-32099`：这段归MCP规范，目前这里定义的是三种现代错误。业务错误可在工具结果表达；确需自定义RPC码时，应选择JSON-RPC保留区之外并明确自己的合同。`clientInfo/serverInfo`是自报软件信息，不能代替可信认证主体或稳定peer配置身份。[Base与错误分配](https://modelcontextprotocol.io/specification/2026-07-28/basic)、[Tools与输出schema](https://modelcontextprotocol.io/specification/2026-07-28/server/tools)

### 多服务器发现不等于授予执行权

`server/discover`是服务器必需实现的方法，返回版本、能力、可选使用说明与cache hints；客户端可选先调用，也可直接调用其他方法再处理版本错误。它不是握手、授权票据或后续元数据检查的替代品。声明tools/resources/prompts能力后，应提供对应list方法，目录可以为空；成员可因本次授权变化，不能因先前连接历史偷偷变化。

多服务器聚合记录**配置peer→canonical name→local name**。例如`notes/search`展示给模型，实际发给notes peer的参数仍是`name: "search"`。同名冲突应按固定规则加前缀或明确报错；不能静默覆盖或悄悄丢掉。self-reported serverInfo.name未保证唯一，不适合作为安全路由标识。peer的运输句柄、所选era、目录和健康记录是客户端管理状态，不能变成服务器省略逐请求元数据的理由。

旧版`2025-11-25`及以前的初始化分支仍可用于明确兼容。recognized现代错误证明对端懂现代语义，应修复请求或选共同版本，不降级。官方允许不识别错误/超时后的旧版探测；课程采用精确peer白名单、有界探测和有效initialize正证，是**应用加严策略**，不能冒称所有这些都是协议MUST。两套parser应隔离，旧能力不能漏进现代请求。[发现](https://modelcontextprotocol.io/specification/2026-07-28/server/discover)、[版本兼容](https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning)

### 自检与下一步

**题**：目录是public、tool标idempotent、用户点击Apps按钮，是否足以重试写动作？**判据**：不足。public只描述缓存共享，annotation只是提示，按钮表达意图；仍需当前授权、动作合同和业务幂等/回执。RPC新ID也不去重副作用。

**题**：task轮询返回`resultType: complete`，但`status: working`，能显示完成吗？**判据**：只表示轮询RPC完成。任务寿命、取消和最终结果独立，继续按应用需要观察；task取消确认也不保证worker停止。

**题**：缓存resource的MRTR重试结果或用旧草稿批准编辑新revision，为什么不安全？**判据**：前者依赖额外input/state，规范禁止缓存；后者批准对象已变，必须重新确认。专题的事务例进一步验证nonce、版本和回执。

本次固定来源仍为AI Engineering from Scratch `3be078b37ffd8f0c04953c0678e48f5c6d0c7775`，Phase13第06–14/28/29/31课于2026-10-08完整读取。官方Base固定`0a11bf68c7ec4473526ec15589f592afcd12d1e8`；Tasks与Apps扩展各自版本和范围见专题来源段。源测试仅阅读，作者输出Skill未安装；专题新CPU例的成功不意味着真实MCP部署或用户掌握。

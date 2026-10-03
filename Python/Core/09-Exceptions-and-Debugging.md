# 09 · 异常、断言与调试

## 1. 异常是程序契约的一部分

异常表示当前操作无法按正常路径完成。设计异常时要回答：

- 哪些错误调用者可以恢复？
- 哪些应立即暴露为程序错误？
- 哪些需要增加上下文后继续抛出？

## 2. try / except

~~~python
def parse_age(raw: str) -> int:
    try:
        age = int(raw)
    except ValueError:
        raise ValueError("age must be an integer") from None

    if age < 0:
        raise ValueError("age cannot be negative")
    return age
~~~

优先捕获具体异常，不要无差别 except。

多个异常可以分开处理：

~~~python
try:
    value = int(text)
    result = 100 / value
except ValueError:
    print("not a number")
except ZeroDivisionError:
    print("cannot divide by zero")
~~~

确实采用同一恢复策略时：

~~~python
except (ValueError, TypeError) as exc:
    ...
~~~

## 3. 异常层次与顺序

先捕获具体异常，再捕获其父类。否则具体分支永远不会执行。

BaseException 还包含 KeyboardInterrupt、SystemExit 等，普通应用不要随意捕获它。

## 4. else 与 finally

~~~python
try:
    file = open(path, encoding="utf-8")
except OSError as exc:
    handle_open_error(exc)
else:
    with file:
        process(file)
finally:
    metrics.record_attempt()
~~~

else 只在 try 块没有异常时运行，可以让“真正可能失败的语句”范围更清晰。

finally 无论正常、异常、return 都会执行，常用于必须清理的资源。若已有上下文管理器，优先 with。

## 5. raise 与异常链

~~~python
class ConfigError(Exception):
    pass

def load_config(path):
    try:
        return read_json(path)
    except OSError as exc:
        raise ConfigError(f"cannot read config: {path}") from exc
~~~

from exc 保留原始因果链；from None 可以有意隐藏实现层异常，但应确认这样不会丢失重要诊断信息。

裸 raise 用于在 except 中重新抛出当前异常。

## 6. 自定义异常

为一个领域建立少量、语义明确的异常层次：

~~~python
class PaymentError(Exception):
    pass

class InsufficientFunds(PaymentError):
    pass

class PaymentGatewayUnavailable(PaymentError):
    pass
~~~

不要为每个错误字符串都创建一个类。调用者需要不同恢复行为时，自定义类型才真正有价值。

## 7. 断言 assert

assert 用于内部不变量和开发期自检：

~~~python
def midpoint(low, high):
    assert low <= high, "invalid interval"
    return (low + high) / 2
~~~

不能用 assert 验证用户输入、权限、支付条件等业务规则，因为 Python 优化模式可以移除断言。外部输入必须使用正常条件与异常。

也不要把有副作用的代码放在 assert 表达式里。

## 8. 错误类型

### SyntaxError

代码无法解析，程序还没开始正常执行。

### 运行时异常

例如 KeyError、TypeError、ValueError、FileNotFoundError。

### 逻辑错误

程序不抛异常，但结果错误。这类问题需要测试、断点和不变量才能发现。

## 9. print 调试

小问题可临时打印变量，但正式调试后要清理。print 不能替代结构化日志。

## 10. logging

~~~python
import logging

logger = logging.getLogger(__name__)

def process(user_id):
    logger.info("processing user_id=%s", user_id)
    try:
        ...
    except OSError:
        logger.exception("processing failed user_id=%s", user_id)
        raise
~~~

logger.exception 会在异常上下文中记录堆栈。日志中不要输出密码、token、完整身份证件、敏感请求体等。

## 11. breakpoint 与 pdb

Python 3 可直接：

~~~python
def calculate(values):
    breakpoint()
    return sum(values)
~~~

常用 pdb 操作包括查看变量、单步、进入函数、继续、查看调用栈。IDE 的图形调试器本质上提供同样的断点和执行控制能力。

## 12. traceback 与事后调试

需要记录异常时可以使用 traceback；生产系统更常让 logging 或错误监控平台捕获结构化堆栈。

调试时保留“原始异常 + 输入条件 + 环境版本 + 最小复现”，不要只保存一句“报错了”。

## 13. 资源异常优先用上下文管理器

错误：

~~~python
file = open(path)
data = file.read()
file.close()
~~~

中间 read 抛异常时 close 可能不执行。

正确：

~~~python
with open(path, encoding="utf-8") as file:
    data = file.read()
~~~

## 14. 一个可诊断例子

~~~python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def average_text(values):
    parsed = []
    for index, raw in enumerate(values):
        try:
            parsed.append(float(raw))
        except (TypeError, ValueError) as exc:
            logger.warning(
                "skip invalid value index=%s value=%r error=%s",
                index,
                raw,
                exc,
            )

    if not parsed:
        raise ValueError("no valid values")
    return sum(parsed) / len(parsed)
~~~

这段代码没有把坏数据悄悄吞掉，同时允许业务明确选择“跳过无效单项”。

## 15. 常见错误

- except Exception: pass；
- 捕获太大范围导致真正 bug 被误当业务异常；
- 在 except 中重新抛出新异常却丢失 cause；
- 用 assert 做安全或输入验证；
- 日志记录密钥；
- 大量 print 留在生产代码；
- 把异常当普通分支反复使用导致代码难读；
- 只修症状，不建立最小复现和测试。

## 16. 练习与答案

**练习 1**：什么时候用 finally，什么时候用 with？  
**答案**：有上下文管理协议的资源优先 with；跨多个资源/动作的通用清理逻辑可用 finally。

**练习 2**：为什么捕获 Exception 后静默继续危险？  
**答案**：它会掩盖程序错误，使状态可能已损坏却继续运行，并丢失诊断信息。

**练习 3**：raise X from exc 的价值？  
**答案**：把底层异常转换为领域异常，同时保留因果链供调试。

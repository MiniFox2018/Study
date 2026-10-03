# 12 · 线程、进程与异步并发

## 1. 并发不是一个技术

先区分任务性质：

- I/O-bound：等待网络、磁盘、数据库；
- CPU-bound：大量计算；
- async-friendly：大量可等待的异步 I/O；
- shared-state：多个执行单元访问共同状态。

Python 提供 threading、multiprocessing、concurrent.futures、asyncio。选择由工作负载决定。

## 2. Thread

~~~python
from threading import Thread

def worker(name):
    print(f"hello {name}")

thread = Thread(target=worker, args=("A",))
thread.start()
thread.join()
~~~

线程共享同一进程内存，因此传数据方便，但也会出现竞态条件。

I/O-bound 工作常适合线程；不要为每个小任务无限创建线程，通常使用线程池。

## 3. GIL 与 free-threaded Python

传统默认 CPython 构建有 Global Interpreter Lock。同一进程中的多个 Python 线程通常不能同时执行普通 Python 字节码，因此 CPU-bound 纯 Python 任务很少因为增加线程而线性提速。

但这个结论现在必须加版本边界：

- CPython 3.13 起提供 free-threaded 构建；
- Python 3.14 中 free-threaded 支持进入正式支持阶段；
- free-threaded 构建可以禁用 GIL，但第三方扩展、线程安全、性能和实际部署仍需单独验证；
- 默认安装是否启用 free-threading取决于具体发行构建。

因此，不再使用“Python 线程永远无法 CPU 并行”的绝对说法。

## 4. 竞态条件与 Lock

共享状态的复合操作可能交错：

~~~python
from threading import Lock

lock = Lock()
balance = 0

def deposit(amount):
    global balance
    with lock:
        balance += amount
~~~

不要依赖“某个操作在当前 CPython 看起来原子”作为长期线程安全设计。

临界区要尽量小，避免持锁进行慢网络 I/O。

## 5. RLock、Semaphore、Event、Condition

- Lock：互斥。
- RLock：同一线程可重复获取，适合嵌套锁定 API。
- Semaphore：限制同时进入资源区的任务数量。
- BoundedSemaphore：额外检查释放次数。
- Event：一方向多个线程广播状态。
- Condition：等待某个受锁保护的条件变化。

生产者-消费者通常优先 queue.Queue，而不是自己组合多个锁和信号量。

## 6. 死锁、饥饿与锁顺序

两个线程按不同顺序获取两把锁可死锁。规避策略：

- 全局统一锁顺序；
- 缩短锁持有时间；
- 使用更高层队列/执行器；
- 必要时使用超时；
- 尽量减少共享可变状态。

## 7. multiprocessing

CPU-bound 任务可以用独立进程：

~~~python
from multiprocessing import Pool

def square(x):
    return x * x

if __name__ == "__main__":
    with Pool() as pool:
        print(pool.map(square, range(5)))
~~~

Windows、macOS 某些启动模式下 __main__ guard 很重要，避免子进程重复创建进程。

进程之间不共享普通 Python 对象，需要序列化、Queue、Pipe、shared memory、Manager 等 IPC。

进程有启动、序列化和内存成本，不适合特别细小的任务。

## 8. concurrent.futures

### ThreadPoolExecutor

~~~python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=8) as pool:
    results = list(pool.map(fetch, urls))
~~~

### ProcessPoolExecutor

~~~python
from concurrent.futures import ProcessPoolExecutor

with ProcessPoolExecutor() as pool:
    results = list(pool.map(cpu_work, items))
~~~

Future 表示尚未完成的结果，可取得 result、exception、cancel 状态，也可使用 as_completed 按完成顺序处理。

## 9. asyncio

asyncio 使用事件循环协作调度 coroutine：

~~~python
import asyncio

async def job(name, delay):
    await asyncio.sleep(delay)
    return name

async def main():
    results = await asyncio.gather(
        job("A", 0.1),
        job("B", 0.2),
    )
    print(results)

asyncio.run(main())
~~~

await 只能在可等待点让出控制。普通阻塞函数放在 async 函数里仍会阻塞整个事件循环。

## 10. Task 与 TaskGroup

create_task 把协程排入并发执行，但任务生命周期必须被管理。

Python 3.11+ 的 TaskGroup 提供结构化并发：

~~~python
import asyncio

async def main():
    async with asyncio.TaskGroup() as group:
        first = group.create_task(fetch("a"))
        second = group.create_task(fetch("b"))

    return first.result(), second.result()
~~~

退出 TaskGroup 时会等待组内任务；任务失败时提供比“创建后台任务后忘记它”更可靠的取消和异常传播结构。

## 11. 超时与取消

异步任务必须把取消当正常控制路径：

~~~python
async with asyncio.timeout(2):
    result = await fetch_data()
~~~

取消时通常应清理资源后重新传播 CancelledError，不要广泛吞掉。

同步 Future 也可对 result 设置 timeout。

## 12. gather 与 TaskGroup

gather 适合收集一批并发结果；TaskGroup 更强调一组相关任务的生命周期和失败传播。新写结构化并发流程优先理解 TaskGroup。

## 13. 协程与生成器协程历史

早期 Python 曾用 yield/send 构造协程；现代异步应用应以 async def / await 为主。理解生成器协程有助于认识演进，但不要把旧式 generator-based coroutine 当新项目主线。

## 14. 调度任务

进程内部：

- time.sleep / threading.Timer：简单延时；
- asyncio：事件循环内调度；
- APScheduler 等：应用内调度。

系统级：

- cron / systemd timer；
- Windows Task Scheduler；
- 容器平台或云调度服务。

“每天必须执行一次”的关键生产任务不应只依赖一个永远运行的 while True + sleep 进程，而要考虑重启、重复执行、时区、错过触发、锁和可观测性。

## 15. 选择表

| 场景 | 常见首选 |
|---|---|
| 少量阻塞 I/O | ThreadPoolExecutor |
| 大量 async 原生 I/O | asyncio / TaskGroup |
| CPU 密集且可分块 | ProcessPoolExecutor |
| 简单共享工作队列 | queue.Queue + threads |
| 需要独立故障隔离 | process / 外部任务系统 |
| free-threaded CPython CPU 线程 | 可评估，但需验证依赖线程安全与实测性能 |

## 16. 常见错误

- CPU 密集任务盲目开大量普通线程；
- async 函数中调用阻塞 requests/time.sleep；
- create_task 后没有保存、等待或管理任务；
- 持锁做网络请求；
- 忘记进程 main guard；
- 把共享 mutable state 当免费资源；
- 忽略 Future/Task 中的异常；
- 把 free-threaded 支持理解成所有 Python 环境默认无 GIL。

## 17. 练习与答案

**练习 1**：100 个 HTTP 请求，库是阻塞 API，通常先考虑什么？  
**答案**：受限 ThreadPoolExecutor；若库有成熟 async API 且规模大，可改 asyncio。

**练习 2**：纯 Python CPU 计算在默认有 GIL 的 CPython 怎么并行？  
**答案**：通常进程池；或验证 free-threaded 构建/释放 GIL 的 C 扩展是否适合当前环境。

**练习 3**：TaskGroup 相比孤立 create_task 的核心收益？  
**答案**：把子任务生命周期、等待、失败和取消结构化地绑定到一个作用域。

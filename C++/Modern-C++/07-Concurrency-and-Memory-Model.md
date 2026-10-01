# 07 · Parallelism, Concurrency and Memory Model

## 1. C++11 标准化并发

C++11 之前，并发通常依赖 pthread、Win32 Thread 等平台 API。  
C++11 将线程、mutex、future、condition variable 和 memory model 纳入语言/标准库体系，使跨平台并发程序有统一语义。

## 2. std::thread

```cpp
std::thread worker([] {
    do_work();
});

worker.join();
```

线程对象必须被正确管理。仍处于 joinable 状态的 `std::thread` 在析构时会触发 `std::terminate`。

常用操作：

- `join()`
- `detach()`
- `joinable()`
- `get_id()`

一般优先确保明确 join，而不是随意 detach。

## 3. Mutex 与临界区

`std::mutex` 提供互斥访问。

不推荐：

```cpp
m.lock();
// ...
m.unlock();
```

更推荐 RAII：

```cpp
std::lock_guard<std::mutex> lock(m);
```

这样 return、异常等退出路径都能自动释放锁。

## 4. lock_guard 与 unique_lock

### lock_guard
简单、轻量，构造即上锁、析构即解锁。

### unique_lock
更灵活：

- 可延迟上锁；
- 可手工 unlock/lock；
- 可移动；
- 可与 condition_variable 配合。

如果只是单作用域互斥，优先简单的 scoped RAII 锁；只有需要灵活控制时才使用 unique_lock。

## 5. Future

`std::future<T>` 表达一个未来可获得的结果。

来源包括：

- `std::async`
- `std::promise`
- `std::packaged_task`

示意：

```cpp
std::packaged_task<int()> task([] {
    return 42;
});

auto result = task.get_future();
std::thread(std::move(task)).detach();

int value = result.get();
```

future 不只是“结果容器”，也承担同步：get/wait 会等待结果 ready。

## 6. Condition Variable

condition_variable 用于“等待某个条件成立”，避免 busy-wait。

典型模式：

```cpp
std::unique_lock<std::mutex> lock(m);

cv.wait(lock, [&] {
    return ready;
});
```

关键点：

- wait 会原子地释放锁并进入等待；
- 被唤醒后重新获得锁；
- 必须用 predicate 防止 spurious wakeup；
- `notify_one()` 唤醒一个等待者；
- `notify_all()` 唤醒全部等待者。

## 7. 为什么 volatile 不能做线程同步

`volatile` 主要约束编译器对特定内存访问的优化，**不提供原子性，也不建立跨线程 happens-before**。

因此：

```cpp
volatile bool ready;
```

不能替代 atomic 或 mutex。

## 8. Data Race

两个线程访问同一内存位置：

- 至少一个为写；
- 没有建立正确同步；

则形成 data race，程序行为未定义。

并发程序的正确性首先要消灭 data race。

## 9. std::atomic

`std::atomic<T>` 为支持的类型提供原子读写/RMW 操作。

```cpp
std::atomic<int> counter{0};

counter.fetch_add(1);
counter++;
```

典型操作：

- load / store
- exchange
- fetch_add / fetch_sub
- compare_exchange_weak
- compare_exchange_strong

## 10. lock-free 不等于 wait-free

`is_lock_free()` 只能说明某 atomic 类型的实现是否不依赖内部锁。

更严格的并发进度保证包括：

- blocking
- lock-free
- wait-free

这三者不是同一个概念。

## 11. Compare-and-Swap

CAS 的基本逻辑：

> 如果当前值仍等于 expected，则替换为 desired；否则更新 expected 并报告失败。

```cpp
value.compare_exchange_strong(expected, desired);
```

weak 版本允许 spurious failure，因此通常用于循环：

```cpp
while (!value.compare_exchange_weak(expected, desired)) {
    // retry
}
```

## 12. C++ Memory Model

现代 CPU 与编译器都可能重新排序内存操作。  
C++11 memory model 定义：

- 哪些读写构成 data race；
- atomic 的同步语义；
- happens-before；
- memory order；
- 多线程程序可以依赖的可见性保证。

这让高性能并发代码第一次有标准化的跨平台语言语义。

## 13. memory_order_relaxed

只保证该 atomic 操作本身具有原子性，不额外建立跨变量同步关系。

适合：

- 独立统计计数器；
- 不依赖其它内存可见性的场景。

```cpp
counter.fetch_add(1, std::memory_order_relaxed);
```

## 14. Release / Acquire

典型发布-订阅关系：

Producer：

```cpp
data = 42;
ready.store(true, std::memory_order_release);
```

Consumer：

```cpp
while (!ready.load(std::memory_order_acquire)) {}

assert(data == 42);
```

如果 acquire 读到了对应 release 的结果，那么 release 之前的写对 acquire 之后可见。

## 15. memory_order_acq_rel

用于同时具有 acquire 与 release 性质的 read-modify-write 操作，例如某些 CAS 或 fetch 操作。

## 16. memory_order_seq_cst

Sequentially Consistent 是默认 memory order。

它提供最强、最容易理解的全局顺序模型，但某些架构上可能带来更高同步成本。

优化 memory order 前应先证明正确性，并通过基准确认收益。

## 17. memory_order_consume

标准中定义过 dependency-based ordering，但长期以来编译器实现和语义都存在现实问题。工程代码通常使用 acquire，而不是依赖 consume 的特殊语义。

## 18. 一致性概念

原书用分布式系统类比介绍多种一致性强度，包括：

- linear consistency；
- sequential consistency；
- causal consistency；
- eventual consistency。

在标准 C++ 原子语义中，最直接相关的是：

- happens-before；
- modification order；
- sequential consistency；
- acquire/release ordering。

这些语言级定义比宏观分布式一致性类比更适合实际判断 C++ 程序是否正确。

## 19. 并发设计原则

1. 优先减少共享可变状态；
2. 优先 mutex + RAII 获得正确程序；
3. atomic 不等于“更高级的 mutex”；
4. 无锁算法只有在 profile 证明必要时才值得引入；
5. 并发对象生命周期与同步同等重要；
6. 用 ThreadSanitizer 检查 data race。

## 来源
Modern C++ Tutorial — Chapter 07

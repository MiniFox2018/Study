# 14 · Multithreading

## 创建线程
C++11 提供 `std::thread`。线程创建后必须最终 `join()` 或 `detach()`，否则 thread 对象析构时可能导致程序终止。

```cpp
#include <thread>

void work() {}

int main() {
    std::thread t(work);
    t.join();
}
```

## 数据竞争
多个线程并发访问同一内存位置，且至少一个线程执行写操作，如果缺少正确同步，就可能形成 data race，属于未定义行为。

## mutex
`std::mutex` 用于互斥访问共享资源。正常业务代码不应依赖手工 `lock()/unlock()`，更推荐使用 RAII：
- `std::lock_guard`
- `std::unique_lock`
- C++17 `std::scoped_lock`

## 死锁
常见原因是多个线程以不同顺序获取多把锁。

常见避免方式：
- 固定加锁顺序
- 使用 `std::scoped_lock`
- 缩短锁持有时间
- 避免持锁调用未知或外部代码

## 条件变量
`std::condition_variable` 用于等待某个共享条件成立，需要与 mutex 配合。应使用带谓词的 wait 处理虚假唤醒。

```cpp
cv.wait(lock, [] { return ready; });
```

## 原子操作
`std::atomic<T>` 为特定读写操作提供原子性，常用于计数器、状态标记和无锁算法基础。复杂无锁代码还涉及 memory ordering，不能仅因为“使用了 atomic”就认为线程安全。

## future 与 promise
- `std::promise<T>`：生产结果
- `std::future<T>`：接收结果
- `std::async`：将任务与 future 结合

future/promise 还可以在线程之间传播异常。

## 生命周期
线程函数中捕获引用、裸指针或 `this` 时，必须保证相关对象在线程完成前仍然有效。许多并发错误本质上是生命周期错误。

## 减少共享状态
更稳健的并发设计通常倾向于：
- 不可变数据
- 消息传递
- 任务队列
- 明确所有权
- 更小的临界区

而不是大量共享可变状态。

## 参考
https://www.compilenrun.com/docs/language/cpp/cpp-multithreading/

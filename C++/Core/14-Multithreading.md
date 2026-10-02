# 14 · 多线程与同步

## 创建线程
C++11 提供 `std::thread`。线程对象在析构前必须不再处于 `joinable()` 状态，通常通过 `join()` 达成；仍可连接的 `std::thread` 析构时一定调用 `std::terminate`，即使线程函数早已返回。`detach()` 不是生命周期问题的通用修复。

```cpp
#include <thread>

void work() {}

int main() {
    std::thread t(work);
    t.join();
}
```

## 数据竞争
不同线程对同一内存位置进行冲突访问（如至少一方写入），至少一个访问非原子，且两者之间没有 happens-before 关系，就构成数据竞争（data race），属于未定义行为。全原子读写可以没有数据竞争，但多步骤业务逻辑仍可能产生竞态。

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

## 小实验：用一把锁保护完整更新

```cpp
#include <iostream>
#include <mutex>
#include <thread>
int main() {
    int count = 0;
    std::mutex mutex;
    auto work = [&] {
        for (int i = 0; i < 1000; ++i) {
            std::lock_guard<std::mutex> guard(mutex);
            ++count;
        }
    };
    std::thread first(work);
    work();
    first.join();
    std::cout << count << '\n';
}
```

以 `clang++ -std=c++17 -Wall -Wextra -Wpedantic -pthread main.cpp -o app` 编译，输出应始终是 `2000`。锁保护整个读改写；`join` 让输出发生在线程完成之后。去掉锁后的程序含未定义行为，不能用某次仍输出 2000 来证明正确。

C++20 的 `std::jthread` 在析构时请求停止并连接线程，更适合局部拥有线程；停止仍需线程函数配合检查，不能强制中断阻塞 I/O。普通线程函数若让异常逃到线程入口外会终止进程，需捕获并通过 future 等通道传递。

## 参考
https://www.compilenrun.com/docs/language/cpp/cpp-multithreading/

# 16 · Best Practices

## 命名规范
命名应一致、可搜索且能够表达语义。常见风格包括：
- 类型：PascalCase
- 函数/变量：camelCase 或 snake_case
- 常量：按照项目统一规则

具体采用哪种风格不是核心，整个代码库保持一致更加重要。

## 代码组织
- 头文件主要放接口，源文件放实现
- 头文件保持自包含
- 减少不必要的 include
- 使用命名空间组织模块
- 大型项目通过库或模块划分依赖边界
- 构建流程应可重复

## 调试
常见手段：
- 编译器警告
- 断点、单步、watch
- 日志
- assertions
- 单元测试
- AddressSanitizer
- UndefinedBehaviorSanitizer
- ThreadSanitizer

调试时应先构造最小可复现问题，再验证具体假设，避免无目的地随机改代码。

## 性能优化
合理顺序：
1. 先保证正确
2. 建立基准
3. 使用 profiler 找到真正热点
4. 优化瓶颈
5. 再次测量验证

常见优化方向：
- 减少不必要复制
- 合理使用移动语义
- 提升缓存局部性
- 预分配容器容量
- 选择合适算法和数据结构
- 减少频繁动态分配
- 避免过度同步

不要用更复杂的实现换取未经测量的“可能更快”。

## 常见错误
- 未初始化变量
- 数组或容器越界
- use-after-free
- 内存泄漏
- 悬空引用
- 多态基类缺少虚析构
- unsigned 反向循环错误
- 混淆 `=` 与 `==`
- 整数除法和整数溢出
- 捕获生命周期已结束的引用
- 多线程 data race
- 忽略返回状态或异常边界

## Style Guide
可以参考成熟项目的编码规范，但规范真正的价值是统一：
- 命名
- 格式
- include 顺序
- 所有权表达
- 错误处理
- API 设计
- 注释与文档

## 设计模式
### 创建型
Factory、Builder、Singleton 等。Singleton 应谨慎使用。

### 结构型
Adapter、Decorator、Facade 等。

### 行为型
Observer、Strategy、Command 等。

设计模式是描述重复设计问题的共同语言，不应为了“使用模式”而增加不必要的抽象层。

## 现代 C++ 工程原则
- RAII 优先
- Rule of Zero 优先
- 标准库优先
- 保持 const-correctness
- 用智能指针表达所有权
- 非拥有对象使用引用或观察指针
- 避免不必要的宏、裸 `new/delete` 和 C 风格 cast
- 接口保持小而稳定
- 将编译器警告、测试、静态分析和 sanitizer 纳入开发流程

## 参考
https://www.compilenrun.com/docs/language/cpp/cpp-best-practices/

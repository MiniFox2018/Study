# 16 · 测试、TDD、Mock 与覆盖率

## 1. 测试到底验证什么

自动化测试是可重复执行的行为证据。不同层次回答不同问题：

- unit test：一个小单元在隔离条件下是否正确；
- integration test：数据库、文件、网络客户端等组件组合是否正确；
- functional / end-to-end：从用户入口到结果的完整流程是否工作。

测试数量不是目标，关键是覆盖重要行为、边界和失败模式。

## 2. unittest

标准库 unittest 提供 TestCase、setUp/tearDown 和断言：

~~~python
# calculator.py
def divide(a, b):
    if b == 0:
        raise ValueError("b cannot be zero")
    return a / b
~~~

~~~python
import unittest
from calculator import divide

class DivideTests(unittest.TestCase):
    def test_divide(self):
        self.assertEqual(divide(6, 3), 2)

    def test_zero(self):
        with self.assertRaises(ValueError):
            divide(1, 0)

if __name__ == "__main__":
    unittest.main()
~~~

常见断言：assertEqual、assertTrue、assertIsNone、assertIn、assertIsInstance、assertRaises。

## 3. pytest

pytest 使用普通 assert，fixture 和参数化能力更强：

~~~python
import pytest
from calculator import divide

@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (6, 3, 2),
        (5, 2, 2.5),
        (-4, 2, -2),
    ],
)
def test_divide(a, b, expected):
    assert divide(a, b) == expected
~~~

异常：

~~~python
def test_zero():
    with pytest.raises(ValueError, match="zero"):
        divide(1, 0)
~~~

## 4. Fixture

Fixture 提供测试前置对象，并在需要时负责清理：

~~~python
import pytest

@pytest.fixture
def account():
    return BankAccount("Ada", balance=100)
~~~

fixture 可以有 function/module/session scope，但扩大 scope 会增加测试间共享状态风险。

conftest.py 可放共享 fixture；不要把整个测试环境都塞进一个巨型 fixture。

## 5. 测试隔离

好测试应尽量：

- 不依赖执行顺序；
- 不读取开发者机器固定路径；
- 不依赖真实当前时间；
- 不随机偶发失败；
- 不调用真实生产服务；
- 自己创建并清理数据。

临时文件使用 tmp_path，时间用可注入 clock，随机使用固定种子或性质测试策略。

## 6. TDD

TDD 的基本循环：

1. Red：先写一个失败测试；
2. Green：写最少实现使其通过；
3. Refactor：在测试保护下改善设计。

TDD 不是“先把所有测试写完”，而是短反馈循环。

例：先定义行为：

~~~python
def test_prime_rejects_one():
    assert is_prime(1) is False
~~~

再写最小实现，逐步增加 2、偶数、平方根边界等测试。

TDD 适合规则清晰、API 可设计的问题；探索性数据分析和一次性原型不必机械追求全程 TDD。

## 7. Mock 的角色

Mock 用来替换当前测试不想真实调用的协作者：

~~~python
from unittest.mock import Mock

gateway = Mock()
gateway.charge.return_value = "payment-123"

service = CheckoutService(gateway)
receipt = service.checkout(order)

gateway.charge.assert_called_once()
~~~

## 8. patch 要 patch 使用位置

如果模块 service.py 写了：

~~~python
from external import fetch_user
~~~

测试通常 patch "service.fetch_user"，而不是 "external.fetch_user"，因为代码运行时查找的是 service 命名空间中的引用。

这是 Mock 初学最常见错误之一。

## 9. Mock side_effect

~~~python
gateway.charge.side_effect = TimeoutError("gateway timeout")
~~~

也可用函数或序列模拟多次调用。

MagicMock 支持 __len__、迭代、上下文管理等魔术方法。

## 10. 不要过度 Mock

如果一个测试 mock 了十几个内部函数，它可能只是在验证“你写了这些调用”，而不是验证真实行为。

优先：

- unit test mock 外部慢/不稳定边界；
- integration test 使用真实数据库测试实例或临时 SQLite；
- 对 HTTP 使用本地 fake server / 传输层 mock；
- 不 mock 被测对象自己的实现细节。

## 11. 集成测试

数据库集成测试：

~~~python
def test_repository_round_trip(tmp_path):
    db_path = tmp_path / "test.db"
    repo = UserRepository(db_path)

    repo.save(User("Ada"))
    restored = repo.get_by_name("Ada")

    assert restored.name == "Ada"
~~~

真实项目可用测试容器/临时数据库，但必须确保与生产数据库方言差异不会被 SQLite 隐藏。

## 12. 事务回滚与清理

测试数据库常见隔离策略：

- 每个测试独立 schema/database；
- 事务开始后测试，结束 rollback；
- fixture 创建最小数据；
- 测试容器生命周期隔离。

选择取决于数据库行为和测试速度。

## 13. 异步测试

async 函数测试需要能运行 event loop 的测试插件或 unittest 异步支持。核心仍是：真正 await 被测协程，并控制 timeout、取消和外部 I/O。

不要因为异步代码复杂就只测同步 wrapper。

## 14. Coverage

覆盖率回答“哪些代码行/分支被测试执行过”，不回答“测试是否正确”。

100% line coverage 仍可能漏掉：

- 错误断言；
- 边界输入；
- 并发竞态；
- 数据库语义；
- 安全风险；
- 状态组合。

覆盖率适合作为发现盲区的仪表，不应当成为唯一质量 KPI。

常见命令：

~~~text
python -m pytest
python -m pytest --cov=your_package --cov-report=term-missing
~~~

具体插件版本以项目环境为准。

## 15. 分支覆盖与边界

比“跑到这一行”更有价值的是验证分支：

~~~python
def discount(total, member):
    if member and total >= 100:
        return total * 0.9
    return total
~~~

至少测试：

- member=True, total=100；
- member=True, total=99.99；
- member=False；
- 非法输入若 API 有约束。

## 16. 调试测试失败

失败时先保留：

- 最小失败输入；
- 实际值与期望值；
- traceback；
- 环境与依赖版本；
- 是否可重复；
- 最近变更。

pdb / breakpoint、IDE debugger、pytest -x -k 等都可缩小范围。

## 17. 一个测试结构

~~~text
project/
├── src/
│   └── app/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
└── pyproject.toml
~~~

不必为了目录“标准”强拆。核心是读者能看出测试层次与依赖。

## 18. 常见错误

- 测试依赖顺序；
- 直接调用真实外部 API；
- 只测 happy path；
- 断言过少，只看“不抛异常”；
- Mock 具体内部实现，重构就全坏；
- 覆盖率数字替代行为设计；
- 测试数据与生产数据共享；
- 慢集成测试没有分层；
- flaky test 长期忽略。

## 19. 练习与答案

**练习 1**：单元测试是否应该访问真实支付网关？  
**答案**：通常不应；它属于外部边界，应 mock/fake。另设集成或沙箱测试验证真实接口。

**练习 2**：覆盖率 100% 是否代表无 bug？  
**答案**：不代表。它只说明执行覆盖，不能证明断言、输入空间和并发/安全边界充分。

**练习 3**：为什么 patch 要 patch “使用位置”？  
**答案**：Python 代码运行时从当前模块绑定的名称取对象；patch 原定义不一定改变已经导入的引用。

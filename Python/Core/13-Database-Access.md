# 13 · 数据库访问与 ORM

## 1. Python 访问数据库的共同模型

无论 SQLite、PostgreSQL、MySQL 还是 ORM，核心流程都类似：

1. 建立连接；
2. 开始事务或获得会话；
3. 发送参数化语句；
4. 读取/修改数据；
5. commit 或 rollback；
6. 释放连接。

数据库边界最重要的不是“会写 CRUD”，而是事务、参数化查询、连接生命周期、约束和失败恢复。

## 2. DB-API 思维

Python 关系型数据库驱动大多遵循相似抽象：Connection、Cursor、execute、fetch、commit、rollback。

SQLite 在标准库 sqlite3 中，非常适合学习和小型本地应用：

~~~python
import sqlite3

with sqlite3.connect("app.db") as conn:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL
        )
        """
    )
~~~

## 3. 参数化 SQL

绝不要通过字符串拼接用户值构造 SQL：

~~~python
# 错误：存在 SQL 注入风险
sql = f"SELECT * FROM users WHERE email = '{email}'"
~~~

SQLite 正确写法：

~~~python
row = conn.execute(
    "SELECT id, name FROM users WHERE email = ?",
    (email,),
).fetchone()
~~~

不同驱动占位符语法可能不同，以驱动文档为准。原则不变：**SQL 结构与数据参数分离。**

## 4. CRUD

~~~python
with sqlite3.connect("app.db") as conn:
    conn.execute(
        "INSERT INTO users(name, email) VALUES (?, ?)",
        ("Ada", "ada@example.com"),
    )

    rows = conn.execute(
        "SELECT id, name, email FROM users ORDER BY id"
    ).fetchall()

    conn.execute(
        "UPDATE users SET name = ? WHERE email = ?",
        ("Ada L.", "ada@example.com"),
    )

    conn.execute(
        "DELETE FROM users WHERE email = ?",
        ("ada@example.com",),
    )
~~~

真实业务还要考虑唯一约束、外键、并发更新、分页、索引和审计，而不是只看四条语句。

## 5. 事务

事务保证一组操作整体成功或失败：

~~~python
conn = sqlite3.connect("app.db")

try:
    conn.execute(
        "UPDATE accounts SET balance = balance - ? WHERE id = ?",
        (100, 1),
    )
    conn.execute(
        "UPDATE accounts SET balance = balance + ? WHERE id = ?",
        (100, 2),
    )
    conn.commit()
except Exception:
    conn.rollback()
    raise
finally:
    conn.close()
~~~

支付、库存、转账等场景要先定义业务不变量，并让数据库约束参与保护。

## 6. SQLite

特点：

- 单文件、无独立服务器；
- 标准库直接支持；
- 适合本地工具、桌面应用、测试、小型服务；
- 并发写入模型与大型客户端/服务器数据库不同。

不要因为 SQLite 简单就忽略事务和约束。

## 7. PostgreSQL 与 MySQL

连接通常包括 host、port、database、user、password，并使用第三方驱动。生产环境还应考虑：

- 连接池；
- TLS；
- 超时；
- 事务隔离；
- 数据库端 statement timeout；
- 凭据轮换；
- 连接断开与重试策略。

不要把数据库密码硬编码在源码。

驱动 API 和 SQL 方言会变化，本仓库不固定某一驱动版本；使用时以 psycopg、mysql-connector 或选定驱动的当前官方文档为准。

## 8. 大结果集

不要无条件 fetchall 数百万行。可使用：

- 游标迭代；
- 分页；
- 服务器端/命名游标；
- 批处理；
- 把聚合尽量交给数据库执行。

“把整张表拉到 Python 再过滤”通常既慢又浪费内存。

## 9. MongoDB

MongoDB 用文档而非关系表组织数据。PyMongo 的典型模型：

~~~python
from pymongo import MongoClient

client = MongoClient(uri)
collection = client["shop"]["products"]

collection.insert_one({"name": "book", "price": 30})
doc = collection.find_one({"name": "book"})
collection.update_one(
    {"name": "book"},
    {"$set": {"price": 35}},
)
~~~

理解重点：

- document 与 BSON 类型；
- collection；
- filter；
- projection；
- update operators；
- index；
- aggregation pipeline；
- 一致性与事务边界。

不要把关系型数据库模式机械翻译成 MongoDB，也不要因为“无 schema”就不做数据验证。

## 10. ORM 的价值与代价

ORM 把表/行映射到对象或声明模型。优点：

- 模型与查询更接近应用语言；
- 可组合查询；
- 事务/关系/迁移工具链；
- 减少重复 SQL 样板。

代价：

- 仍然必须懂 SQL 和索引；
- 容易产生 N+1 查询；
- 抽象泄漏；
- 复杂报表和批处理有时原生 SQL 更清楚。

## 11. SQLAlchemy 的现代核心模型

现代 SQLAlchemy 区分 Core 与 ORM，但都建立在 Engine / Connection / Session 与显式语句上。

示意：

~~~python
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

engine = create_engine("sqlite:///app.db")

with Session(engine) as session:
    users = session.scalars(
        select(User).where(User.active.is_(True))
    ).all()
~~~

写入：

~~~python
with Session(engine) as session:
    user = User(name="Ada", email="ada@example.com")
    session.add(user)
    session.commit()
~~~

Session 是工作单元，不应作为全局永不关闭对象。

源站部分 SQLAlchemy 例子采用较旧教程风格；Study 版只保留稳定概念，并以现代 select/Session 思路作为主线。

## 12. 关系、加载与 N+1

一对多、多对多关系不能只关注对象属性。访问关联对象可能额外发 SQL。

需要根据查询场景选择：

- lazy loading；
- joined load；
- select-in load；
- 显式 join。

性能判断应查看实际 SQL 与查询计划，而不是只看 Python 代码“很短”。

## 13. 迁移

数据库 schema 会演进，需要版本化迁移。

常见工具：

- SQLAlchemy：Alembic；
- Flask 项目常见 Flask-Migrate 封装 Alembic；
- Django 自带 migrations。

迁移基本流程：

1. 修改模型/设计；
2. 生成或编写 migration；
3. 人工审查；
4. 测试升级；
5. 备份和回滚策略；
6. 部署执行；
7. 验证数据与应用兼容。

自动生成只能是起点，尤其涉及数据迁移、列重命名、非空约束、大表索引时必须审查。

## 14. Data Migration

Schema migration 改结构；data migration 转换已有数据。大表变更要考虑：

- 锁表时间；
- 分批更新；
- 双写/兼容期；
- 回填；
- 新旧应用版本共存；
- 可逆性。

## 15. 连接池

Web 服务不应每个请求无边界新建真实数据库连接。连接池复用连接并限制并发。需要配置：

- pool size；
- overflow；
- acquire timeout；
- idle/lifetime；
- health/pre-ping。

池大小要结合数据库最大连接数和服务实例数，而不是“越大越快”。

## 16. 数据库错误处理

区分：

- 输入/约束错误；
- 唯一键冲突；
- 连接不可用；
- 死锁/序列化失败；
- 超时；
- 编程错误。

只有明确可重试的瞬时错误才重试，并加入上限、退避和幂等设计。

## 17. 练习与答案

**练习 1**：为什么参数化 SQL 能防止典型 SQL 注入？  
**答案**：驱动把参数按数据绑定，而不是把用户文本重新解释为 SQL 结构。

**练习 2**：ORM 是否意味着不用学 SQL？  
**答案**：不是。索引、连接、事务、查询计划和 N+1 都需要 SQL/数据库基础。

**练习 3**：为什么 migration 自动生成后还要人工审查？  
**答案**：工具通常只能比较结构，无法理解业务数据转换、停机成本、锁和部署兼容窗口。

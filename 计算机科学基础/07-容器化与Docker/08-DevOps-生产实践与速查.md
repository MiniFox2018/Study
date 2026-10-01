# 08｜DevOps、生产实践与速查

## 1. Docker 在 DevOps 中的位置

Docker 最适合做“标准交付物”。

```text
code
→ test
→ build image
→ scan
→ sign
→ push registry
→ deploy same image
→ observe
→ rollback / promote
```

核心原则：**同一份镜像在不同环境中流转，不要每个环境重新构建。**

## 2. 不可变交付物

可靠发布应能回答：

- 这个实例运行的是哪个 commit？
- 对应哪个 image digest？
- 谁构建的？
- 构建时用了什么依赖？
- 是否通过测试和扫描？
- 是否签名？
- 从 staging 到 prod 是否还是同一产物？

推荐标识：

```text
git commit SHA
+
semantic version
+
image digest
```

tag 用于可读性，digest 用于不可变追踪。

## 3. CI/CD 最小闭环

### CI

```text
checkout
→ lint
→ static/type check
→ unit test
→ integration test
→ image build
→ vulnerability scan
→ artifact/image publish
```

### CD

```text
deploy staging
→ smoke test
→ approval/policy
→ production rollout
→ observe
→ rollback if needed
```

## 4. Secret 管理

CI/CD secret 应：

- 使用平台 secret store；
- 最小权限；
- 定期轮换；
- 避免出现在 shell trace；
- 避免写入镜像层；
- 避免持久保存在 artifact；
- 优先短期凭证 / OIDC，而不是永久 token。

Registry 登录应使用标准输入或凭证助手，避免密码出现在命令历史。

## 5. Registry 与构建缓存

大规模 CI 常见瓶颈：

- 拉基础镜像；
- 安装依赖；
- 重复编译；
- 推送大层。

优化手段：

- BuildKit cache；
- registry cache；
- dependency cache；
- 多阶段构建；
- 基础镜像预热；
- 内部 pull-through cache。

缓存不能牺牲可重现性和安全更新。

## 6. GitHub Actions / Drone 的通用知识

具体 YAML 会变化，但长期结构相同：

```text
trigger
→ runner
→ permissions
→ checkout
→ test
→ build
→ registry auth
→ push
→ deploy
```

重点关注：

- action/plugin 来源是否可信；
- pin version / commit；
- workflow token 权限最小化；
- fork PR 不泄漏 secret；
- artifact 保留时间；
- 构建 provenance；
- 并发与取消策略。

## 7. 开发环境一致性

开发容器可以把：

- compiler；
- runtime；
- SDK；
- formatter；
- database；
- cache；

变成可复现环境。

典型工作流：

```text
repo clone
→ open in dev container
→ compose starts dependencies
→ code mounted
→ test/debug
```

开发镜像与生产镜像目标不同：

- dev：可调试、工具齐全；
- prod：最小、只读、可审计。

## 8. Go / Rust 的镜像模式

编译型语言通常适合：

```text
builder image
→ compile static/small binary
→ runtime image
```

优点：

- 最终镜像不带编译器；
- 体积小；
- 攻击面低；
- 依赖边界清晰。

是否使用 scratch / distroless / Alpine / Debian slim，应以兼容性和可调试性为准。

## 9. 数据库容器化

数据库可以容器化，但必须显式设计：

- volume；
- backup；
- restore test；
- fsync / durability；
- memory；
- file descriptor；
- upgrade；
- replication；
- migration；
- secret。

“数据库运行在容器里”不是风险点本身；**没有持久化、备份和升级设计**才是。

## 10. 微服务 Compose 模式

一个简单微服务环境：

```text
gateway
 ├→ api-a
 ├→ api-b
 └→ worker
      ↓
 redis / db
```

必须控制：

- 服务依赖；
- retry / timeout；
- health；
- log correlation；
- network boundary；
- 数据归属；
- 配置来源。

不要让 Compose 文件变成没有边界的“所有服务都能访问所有东西”。

## 11. 常用命令按问题分类

### 我有哪些对象？

```bash
docker ps -a
docker image ls
docker volume ls
docker network ls
```

### 为什么容器退出？

```bash
docker ps -a
docker logs <container>
docker inspect <container>
```

### 容器里发生了什么？

```bash
docker exec -it <container> sh
docker top <container>
docker stats <container>
```

### 端口为什么不通？

检查：

1. 应用是否监听正确地址；
2. 容器端口；
3. `-p` / Compose `ports`；
4. host firewall；
5. Docker network；
6. DNS；
7. 反向代理；
8. 云安全组。

### 磁盘为什么满？

```bash
docker system df
docker image ls
docker container ls -a
docker volume ls
```

清理前先判断哪些 volume 是业务数据。不要把 `docker system prune` 当作无脑修复。

## 12. 常见误区

### “latest 就是最新版而且安全”

错。latest 只是可变标签。

### “EXPOSE 就等于开放端口”

错。它只是元数据。

### “容器删除，数据库还在”

只有数据放在持久 volume 等外部存储时才成立。

### “容器比虚拟机安全”

不能泛化。容器共享 kernel，安全模型不同。

### “Compose 可以直接替代 Kubernetes”

只在单机和较简单环境中成立。

### “镜像越小越好”

兼容性、可维护性、安全更新和调试能力同样重要。

### “进入容器手改就能修生产”

这会制造漂移。正确做法是修源码/配置、重新构建并重新部署。

## 13. 生产故障排查顺序

```text
现象
→ container state
→ logs
→ health
→ resource
→ network
→ mount/storage
→ dependency
→ image/version
→ host/runtime
```

先定位层级，再深入细节。

## 14. 学习完成标准

能够独立完成：

- 写 Dockerfile 并解释每层；
- 多阶段构建；
- 非 root 镜像；
- volume / bind / tmpfs 选型；
- 自定义网络与服务发现；
- Compose 多服务应用；
- Registry push/pull 与 digest；
- Buildx 多架构构建；
- 解释 namespace / cgroup / OverlayFS；
- 基础安全扫描、SBOM、签名；
- 用 metrics/logs 排查资源问题；
- 把同一镜像接入 CI/CD；
- 解释何时需要 Kubernetes。

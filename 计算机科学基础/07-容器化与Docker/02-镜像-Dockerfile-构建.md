# 02｜镜像、Dockerfile 与构建系统

## 1. 镜像是分层、只读、内容寻址的文件系统

一个镜像通常由多层只读层叠加而成。每一条会改变文件系统的构建步骤通常形成新的层。

分层带来：

- 基础层复用；
- 增量下载；
- 构建缓存；
- 多镜像共享；
- 内容可寻址。

但也带来一个重要陷阱：**上一层写入的数据，在下一层删除并不会让前一层消失。**

因此不应：

```dockerfile
RUN install-big-tool
RUN build
RUN remove-big-tool
```

更好的做法是同层清理，或直接使用多阶段构建。

## 2. Tag、Image ID 与 Digest

- **Tag**：人类可读，但可以重新指向别的内容；
- **Image ID**：本地镜像标识；
- **Digest**：基于内容的哈希，不可变，适合供应链追踪。

生产部署需要“可重现 + 可追踪”时，应保留 digest 或不可变版本标识。

## 3. Dockerfile 的角色

Dockerfile 是“如何构建镜像”的声明式构建入口。核心原则：

- 构建过程进入版本控制；
- 每一步可重现；
- 构建上下文最小化；
- 不把 secret 烘焙进镜像；
- 运行时镜像只包含运行所需内容。

## 4. 主要指令及语义

### `FROM`

指定基础镜像。优先：

- 官方或可信来源；
- 小而够用；
- 明确版本；
- 定期安全更新。

### `RUN`

构建阶段执行命令并产生层。

实践要点：

- 把强相关的“安装 + 清理”放在同一个 RUN；
- 包索引更新和包安装不要拆成彼此独立、可能被缓存错配的层；
- 避免产生无意义缓存。

### `COPY`

从构建上下文复制文件。默认优先使用 COPY。

### `ADD`

只有确实需要自动解包等语义时再用。远程下载通常应使用专门工具，以便校验、缓存和失败处理更明确。

### `CMD` 与 `ENTRYPOINT`

- ENTRYPOINT：定义镜像“主要执行什么”；
- CMD：提供默认参数或默认命令；
- 推荐 exec form，信号传递与参数边界更清晰。

典型组合：

```dockerfile
ENTRYPOINT ["myapp"]
CMD ["--help"]
```

### `ENV` 与 `ARG`

- ARG：构建期参数；
- ENV：镜像/运行时环境变量。

不要把 secret 放入二者并假定“构建后就消失”；构建历史和层可能泄漏敏感信息。

### `WORKDIR`

为后续构建和运行指令指定稳定工作目录，优于大量 `cd ... &&`。

### `USER`

生产镜像尽量使用非 root 用户。配合文件所有权和运行目录权限设计。

### `EXPOSE`

是镜像元数据/文档，不等于实际发布端口。真正主机端口映射由运行时或编排配置决定。

### `VOLUME`

声明持久化意图，但实际生产数据卷通常由 Compose / Kubernetes / 平台配置管理。

### `HEALTHCHECK`

给出进程“仍活着之外”的健康信号。检查应：

- 快；
- 稳定；
- 无副作用；
- 能反映服务是否真正可用。

### `LABEL`

用于维护者、版本、源码、构建信息、OCI 元数据等机器可读信息。

### `ONBUILD`

适合构建“下游构建镜像模板”，但隐藏行为较多，新项目应谨慎使用。

## 5. 构建上下文与 `.dockerignore`

`docker build .` 中的 `.` 是构建上下文，不只是“Dockerfile 所在目录”。

上下文过大会导致：

- 上传慢；
- 缓存频繁失效；
- 误把 `.git`、缓存、数据集、secret 送入构建器。

因此应维护 `.dockerignore`。

## 6. 多阶段构建

多阶段构建是生产镜像常用实践。下面是结构示意，`distroless-or-small-runtime` 和 app 构建参数为占位，不能原样运行；完整练习见文末：

```dockerfile
FROM golang AS builder
WORKDIR /src
COPY . .
RUN go build -o /out/app

FROM distroless-or-small-runtime
COPY --from=builder /out/app /app
ENTRYPOINT ["/app"]
```

价值：

- 编译工具不进入运行镜像；
- 降低镜像体积；
- 缩小攻击面；
- 提升分层清晰度；
- 一个 Dockerfile 表达完整构建链。

## 7. BuildKit

BuildKit 是现代 Docker 构建系统的核心。相较传统构建器，它更强调：

- 并行执行；
- 精确缓存；
- 跨构建缓存复用；
- secret / SSH mount；
- cache mount；
- 前端语法扩展；
- provenance / SBOM 等构建证明。

构建过程应尽量把“缓存友好的稳定依赖层”和“频繁变化的源码层”分开。

## 8. Buildx 与多架构镜像

Buildx 是 BuildKit 的 CLI 入口，可构建：

- linux/amd64；
- linux/arm64；
- 其他目标平台。

多架构镜像通常使用 OCI Image Index / Manifest List，把“同一个逻辑镜像名”映射到不同平台镜像。

原则：

- 构建前确认依赖是否支持目标架构；
- 避免把本机二进制直接 COPY 到异构镜像；
- 对跨架构仿真构建关注速度和兼容性；
- 发布后验证各平台 digest。

## 9. 镜像导入导出

需要区分：

- `docker save/load`：保留镜像层、标签和镜像元数据，适合镜像离线迁移；
- `docker export/import`：针对容器文件系统快照，会丢失大量镜像构建历史和配置语义。

因此标准镜像迁移优先 save/load。

## 10. 生产镜像检查清单

- [ ] 基础镜像可信且版本明确
- [ ] 无不必要包和编译器
- [ ] 多阶段构建
- [ ] `.dockerignore` 完整
- [ ] 非 root 运行
- [ ] 不包含密钥
- [ ] 依赖版本可重现
- [ ] 健康检查合理
- [ ] 标签与 OCI 元数据完整
- [ ] 生成 SBOM / provenance
- [ ] 漏洞扫描
- [ ] 以 digest 追踪发布物

## 11. 完整多阶段练习：编译一个命令行程序

在空练习目录保存 `main.go`：

```go
package main
import "fmt"
func main() { fmt.Println("多阶段构建成功") }
```

保存 `Dockerfile`：

```dockerfile
FROM golang:1-alpine AS builder
WORKDIR /src
COPY main.go .
RUN CGO_ENABLED=0 go build -trimpath -o /out/app main.go

FROM scratch
COPY --from=builder /out/app /app
USER 65532:65532
ENTRYPOINT ["/app"]
```

```bash
docker build -t study-multistage:local .
docker run --rm study-multistage:local
```

成功时输出 `多阶段构建成功`。前提是 Docker 构建器及镜像网络可用；本例不需要在宿主安装 Go。最终 scratch 镜像没有 shell、CA 证书或常见系统工具，这个只打印文本的静态程序才适合它；真实 TLS、时区、动态库需求应另行提供。

自测：为什么最终镜像没有 Go 编译器？答：只把 builder 的 `/out/app` 复制进最终阶段，前一阶段的其余层不是最终镜像祖先。`golang:1-alpine` 是方便练习的可变标签；要复现实验必须记录解析到的 digest，而生产升级还需要计划性更新和回归验证。

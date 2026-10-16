# 03｜SVD、PCA 与降维

> 先修：[向量、投影与正交基](01-向量空间与线性映射.md)、[特征值和最小二乘](02-矩阵变换与线性系统.md)。先把 1～6 节的低秩、PCA 算例跑通；核 PCA、推荐与可视化可在第二遍学习。目标是知道保留了什么、损失了什么、如何验证，不能把二维聚类图当作模型效果证明。

## 1. SVD 把任意有限矩阵分解为方向与尺度

实矩阵 $A\in\mathbb R^{m\times d}$ 都有奇异值分解

$$
A=U\Sigma V^T.
$$

完整形式中 $U$ 为 $m\times m$、$V$ 为 $d\times d$，均正交；$\Sigma$ 为 $m\times d$，主对角放非负奇异值。令 $q=\min(m,d)$，奇异值按 $\sigma_1\ge\cdots\ge\sigma_q\ge0$ 排序。约化形式只保留 $q$ 个方向：$U_q$ 为 $m\times q$，$\operatorname{diag}(\sigma)$ 为 $q\times q$，$V_q^T$ 为 $q\times d$。

对输入向量，从右向左：$V^T$ 换到正交输入坐标，$\Sigma$ 沿各坐标缩放或消去方向，$U$ 换到输出空间。正交因子可能含反射，不应无条件称为“三次纯旋转”。每一对方向满足

$$
Av_i=\sigma_i u_i.
$$

单位球经 $A$ 变成椭球，半轴长度为奇异值；奇异值为零的输入方向被压扁。矩形矩阵中输入、输出空间维数不同，SVD 仍然成立。

```python
import numpy as np
A = np.array([[3., 1.], [1., 3.]])
U, s, Vt = np.linalg.svd(A, full_matrices=False)
print(s)  # [4. 2.]
print(np.allclose((U * s) @ Vt, A))  # True，s 广播到 U 的各列。
print(np.allclose(U.T @ U, np.eye(2)))  # True
for i in range(len(s)):
    assert np.allclose(A @ Vt[i], s[i] * U[:, i])
```

`Vt` 已经是 $V^T$，不能再拿它当 $V$ 直接重建。奇异向量的正负号可以一起翻转；重根对应的子空间基也可以旋转。因此比较两个实现时，优先比较奇异值、重建结果和投影子空间，不能只检查每个向量逐元素相同。

## 2. 奇异值揭示秩、范数与稳定性

由 $A^TA=V\Sigma^T\Sigma V^T$ 可知，右奇异向量是 $A^TA$ 的特征向量；左奇异向量是 $AA^T$ 的特征向量，非零特征值均为 $\sigma_i^2$。

| 量 | 从奇异值得到的表达 | 用途 |
|---|---|---|
| 精确秩 | 非零奇异值个数 | 独立方向数量 |
| 数值秩 | 大于容差的奇异值个数 | 噪声、舍入下可辨认方向 |
| 谱范数 $\|A\|_2$ | $\sigma_1$ | 最大长度放大比 |
| Frobenius 范数 | $\sqrt{\sum_i\sigma_i^2}$ | 所有元素平方和的平方根 |
| 核范数 | $\sum_i\sigma_i$ | 低秩约束的凸替代等 |
| 方阵 $|\det A|$ | $\prod_i\sigma_i$ | 体积缩放的绝对值 |

非奇异方阵的条件数是 $\sigma_1/\sigma_q$。数值秩判断常用相对阈值，教学可取 `eps * max(A.shape) * s[0]`；真实测量噪声可能要求更大的阈值。固定 `1e-10` 不适合所有数据尺度。

虽然可以通过对 $A^TA$ 做特征分解来理解 SVD，但这个构造会平方满列秩矩阵的条件数。若 $A$ 的奇异值为 $1000,1,0.001$，条件数为 $10^6$；$A^TA$ 的特征值为 $10^6,1,10^{-6}$，条件数为 $10^{12}$。实际计算优先直接 SVD，避免为了照着数学推导而牺牲精度。

实对称半正定矩阵的特征值非负，可让 SVD 与正交特征分解对应；对称不定矩阵的奇异值是特征值的绝对值，符号信息须由左右向量体现。一般矩阵的特征值不是奇异值。

## 3. 低秩逼近：留哪些项，误差是多少

SVD 可写成秩一外积之和：

$$
A=\sum_{i=1}^r\sigma_i u_i v_i^T,
\qquad A_k=\sum_{i=1}^k\sigma_i u_i v_i^T.
$$

Eckart–Young–Mirsky 定理说明：在秩至多为 $k$ 的矩阵中，$A_k$ 对原矩阵的谱范数与 Frobenius 范数误差都达到最小值：

$$
\|A-A_k\|_2=\sigma_{k+1},\qquad
\|A-A_k\|_F^2=\sum_{i>k}\sigma_i^2.
$$

这里“最佳”针对未加权的矩阵近似误差，不表示最佳分类效果、最有意义的语义方向或最佳缺失值预测。若截断位置存在相等奇异值，最优解也不一定唯一。

对 $A=\operatorname{diag}(5,3,1)$：保留 rank 1 时 Frobenius 误差 $\sqrt{10}$、谱误差 3，保留 rank 2 时两种误差都是 1。保留能量比 $E_k=\sum_{i\le k}\sigma_i^2/\sum_i\sigma_i^2$，本例分别为 $25/35$ 与 $34/35$。

```python
import numpy as np
A = np.diag([5., 3., 1.])
U, s, Vt = np.linalg.svd(A, full_matrices=False)
for k in (1, 2, 3):
    Ak = (U[:, :k] * s[:k]) @ Vt[:k]
    error = np.linalg.norm(A - Ak, "fro")
    expected = np.sqrt(np.sum(s[k:] ** 2))
    energy = np.sum(s[:k] ** 2) / np.sum(s ** 2)
    print(k, round(error, 6), round(energy, 6))
    assert np.allclose(error, expected)
```

预期三行分别是 `1 3.162278 0.714286`、`2 1.0 0.971429`、`3 0.0 1.0`。

选 $k$ 可以结合能量阈值、谱间隙、验证集任务指标和领域因素。95% 是可选阈值，不是所有任务统一标准。零矩阵总能量为零，能量比未定义；直接返回零重建，不能除零。

### 图像压缩与去噪的实际边界

灰度图 $m\times d$ 原有 $md$ 个数，保留因子需要 $k(m+d+1)$ 个数。只有保存低秩因子才实现这一参数量缩减；保存已经重建的 $m\times d$ 图并未因此减少元素数。还需考虑原图 uint8、因子 float32 的字节差异、文件格式和熵编码。

例如 `800×600`，rank 50 的因子有 $50\times1401=70,050$ 个数，是原元素数的约 14.6%。若原来每像素 1 字节、因子每数 4 字节，纯数值存储约 280,200 字节，不能声称实际文件缩小 85%。纹理丰富或随机噪声图奇异值衰减慢，低秩重建会损失细节；彩色图可对各通道分别分解，但这不是最优通用图像编码器。

去噪的假设是信号近似低秩、噪声分布在更多方向。若有用信号本身高秩、噪声集中在大奇异值方向，简单截断可能伤害信号。下面用已知真值的合成测量演示，可复算而不依赖原网站图片：

```python
import numpy as np
rng = np.random.default_rng(7)
u = np.sin(np.linspace(0, 2 * np.pi, 40))
v = np.cos(np.linspace(0, 2 * np.pi, 30))
clean = 3 * np.outer(u, v)  # 精确 rank 1。
noisy = clean + rng.normal(0., 0.3, clean.shape)
U, s, Vt = np.linalg.svd(noisy, full_matrices=False)
denoised = (U[:, :1] * s[:1]) @ Vt[:1]
before = np.linalg.norm(noisy - clean)
after = np.linalg.norm(denoised - clean)
print(after < before)  # 本固定样例为 True。
print("保留因子数：", clean.shape[0] + clean.shape[1] + 1)  # 71，对比 1200。
```

扫 $k$ 并对照 `clean` 找最佳 rank，只适用于有合成真值的实验；真实数据通常没有无噪真值，需独立验证集、噪声模型或重复测量。不能把来源中“后几项都是噪声”作为必然规律。

## 4. 伪逆：把可辨认方向反向缩放

若 $A=U\Sigma V^T$，伪逆 $A^+=V\Sigma^+U^T$，将非零奇异值倒置、零值保持为零。它满足 $AA^+A=A$、$A^+AA^+=A^+$，且 $AA^+$ 与 $A^+A$ 对称。$A^+b$ 是最小范数最小二乘解。

```python
import numpy as np

def pinv_svd(A):
    A = np.asarray(A, dtype=float)
    U, s, Vt = np.linalg.svd(A, full_matrices=False)
    cutoff = np.finfo(float).eps * max(A.shape) * (s[0] if s.size else 0)
    inv_s = np.zeros_like(s)
    keep = s > cutoff
    inv_s[keep] = 1.0 / s[keep]  # 避免 np.where 两支先求值触发除零。
    return (Vt.T * inv_s) @ U.T

A = np.array([[1., 1.], [2., 1.], [3., 1.]])
b = np.array([3., 5., 6.])
x = pinv_svd(A) @ b
print(np.round(x, 6))  # [1.5 1.666667]，此例第一列是斜率列。
assert np.allclose(x, np.linalg.lstsq(A, b, rcond=None)[0])
assert np.allclose(A.T @ (A @ x - b), 0.)

wide = np.array([[1., 1.]])
print(pinv_svd(wide) @ [2.])  # [1. 1.]，欠定最小范数解。
singular = np.array([[1., 2.], [2., 4.]])
P = pinv_svd(singular)
assert np.allclose(singular @ P @ singular, singular)
print(P @ [3., 6.])  # [0.6 1.2]
```

小奇异值的倒数会放大噪声。截断它们相当于放弃难以辨认的方向，是有偏的稳定化选择，阈值应与噪声和任务有关。岭回归用 $\sigma_i/(\sigma_i^2+\lambda)$ 平滑替代 $1/\sigma_i$，对应的滤波和条件见[线性系统](02-矩阵变换与线性系统.md)。

## 5. PCA：先中心化，再找最大方差方向

数据矩阵 $X\in\mathbb R^{n\times d}$ 每行一个样本。均值 $\mu\in\mathbb R^d$，中心化 $X_c=X-\mu$。样本协方差为

$$
C=\frac{X_c^TX_c}{n-1}\quad(n\ge2).
$$

对单位方向 $w$，投影分数的样本方差为 $w^TCw$。在 $\|w\|=1$ 下最大化此值，其解是最大特征值的特征向量；后续方向再加与前面正交的约束。这解释了 PCA 为什么保留最大方差。

若 $X_c=U\Sigma V^T$，主方向是 $V$ 的列，主成分分数 $Z=X_cV_k=U_k\Sigma_k$，重建 $\widehat X=ZV_k^T+\mu$。方差 $\lambda_i=\sigma_i^2/(n-1)$，解释方差比 $\lambda_i/\sum_j\lambda_j$。

需要区分术语：主方向是长度为 $d$ 的轴；分数是每个样本在该轴上的坐标；一个主方向一般混合许多原特征，不是“挑出某些像素或列”。

### 一个完全可手算的 PCA

样本为 $(1,1),(2,2),(3,3)$，均值 $(2,2)$，中心化行是 $(-1,-1),(0,0),(1,1)$。协方差 $\begin{bmatrix}1&1\\1&1\end{bmatrix}$，主方向 $w=(1,1)/\sqrt2$，特征值 2；另一个正交方向特征值 0。

投影分数是 $(-\sqrt2,0,\sqrt2)$，用一维就能精确恢复所有三个二维样本。主方向变成 $-w$ 时分数全部变号，重建不变。

```python
import numpy as np

class PCAFromSVD:
    def __init__(self, k):
        self.k = k

    def fit(self, X):
        X = np.asarray(X, dtype=float)
        if X.ndim != 2 or X.shape[0] < 2 or not np.isfinite(X).all():
            raise ValueError("需要至少两个有限数值样本")
        if not 1 <= self.k <= min(X.shape):
            raise ValueError("主成分个数超出约化 SVD 的范围")
        self.mean_ = X.mean(axis=0)
        centered = X - self.mean_
        _, s, Vt = np.linalg.svd(centered, full_matrices=False)
        variance = s ** 2 / (len(X) - 1)
        self.components_ = Vt[:self.k]
        self.variance_ = variance[:self.k]
        total = variance.sum()
        self.ratio_ = variance[:self.k] / total if total > 0 else np.zeros(self.k)
        return self

    def transform(self, X):
        X = np.asarray(X, dtype=float)
        if X.shape[-1] != self.mean_.size:
            raise ValueError("输入特征维数与拟合时不同")
        return (X - self.mean_) @ self.components_.T

    def inverse_transform(self, Z):
        return np.asarray(Z) @ self.components_ + self.mean_

X = np.array([[1., 1.], [2., 2.], [3., 3.]])
pca = PCAFromSVD(1).fit(X)
Z = pca.transform(X)
print(pca.ratio_)  # [1.]
print(np.round(np.abs(Z[:, 0]), 6))  # [1.414214 0. 1.414214]
assert np.allclose(pca.inverse_transform(Z), X)
```

若所有样本相同，总方差为零，“解释百分比”本来没有定义，示例明确约定返回零比例供程序处理。一个样本无法估计样本协方差；常数列、重复特征、NaN 和尺度差异应在拟合前检查。

## 6. 方差、重建误差与任务价值不能混为一谈

中心化 PCA 的总平方重建误差为 $\sum_{i>k}\sigma_i^2$。若 MSE 按所有 $n d$ 个元素平均，则

$$
\operatorname{MSE}=\frac{\sum_{i>k}\sigma_i^2}{nd}
=\frac{n-1}{nd}\sum_{i>k}\lambda_i.
$$

不能把“舍弃特征值之和”不加归一化就当逐元素 MSE。每个样本的平方误差还可以用来找偏离训练子空间的异常，但阈值要在独立正常数据上校准，异常也可能恰好位于保留子空间中。

解释 95% 方差只说明保留了总平方变化的 95%。少数类别的判别线索可能处于低方差方向，重要的细纹也可能被删去。不能写成保留 95% 知识、准确率或“剩下都是噪声”。同样，“只有五个特征与标签相关”不表示数据几何秩为五；其余纯噪声特征也可能有很大方差。

量纲不同时，先考虑是否按训练集标准差标准化。标准化改变了各特征在 PCA 中的权重，需要领域解释；PCA 默认中心化而不会自动把各列除标准差。若尺度本身有价值，不应机械标准化。

白化在分数上再除以 $\sqrt{\lambda_i}$，令保留坐标的样本协方差接近单位阵。它可改善某些算法的尺度，但会放大小方差噪声，并丢掉原来的方差相对大小。特征值接近零时不能直接倒数缩放。

选择维数时可以：看累计解释方差、找拐点、比较重建误差，再用独立验证集的实际指标挑 $k$。拐点只是经验线索；验证集指标没有提升或计算成本没有下降时，不必强制降维。

### 防止预处理泄漏的工作流程

先划分训练、验证、测试，再只在训练数据上拟合标准化与 PCA；验证与测试只调用 `transform`。所有调参包括 $k$ 和核参数只看训练/验证，最终测试保留到最后。

可以用本地自带数字数据代替需要联网下载的 MNIST，减少首次学习的环境障碍。以下代码依赖 scikit-learn。首批验收时缺依赖未运行；2026-10-03 后续批次已用隔离的 scikit-learn 1.9.1 实际执行，同一数字数据得到验证准确率约0.9333、0.9644、0.9711，对应解释方差约0.7386、0.9599、0.9996。它只说明此数据与划分下的结果，不是PCA组件越多必然越好的保证：

```python
from sklearn.datasets import load_digits
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline

X, y = load_digits(return_X_y=True)  # 1797 个 8×8 灰度数字，64 个特征。
X_train, X_val, y_train, y_val = train_test_split(
    X, y, test_size=0.25, random_state=7, stratify=y)
for k in (10, 30, 50):
    model = make_pipeline(PCA(n_components=k, svd_solver="full"),
                          LogisticRegression(max_iter=2000))
    model.fit(X_train, y_train)
    print(k, round(model.score(X_val, y_val), 4),
          round(model[0].explained_variance_ratio_.sum(), 4))
```

预期输出三个 `k、验证准确率、解释方差`。具体数值受库版本和优化收敛影响，不能预先断言每次单调提升。可把无 PCA 的模型作为基线；来源中 784 维 MNIST 的数值不应套到这里的 64 维数据上。大规模 MNIST、全部参数搜索未因此自动算作完成。

## 7. 维度灾难与方法选择

高维中的困难来自几何和数据分布：若各维都是独立的噪声，点对距离的相对差异可能变小；为了在每个轴上保持相同网格分辨率，所需格子数按指数增长。若每维分十格，从 2 维变 20 维，格子数增加 $10^{18}$ 倍。

这个计数不表示任何学习任务都必须有 $10^{18}$ 倍样本，也不表示任意高维 embedding 的距离必然无意义。数据若集中在低维结构、有效特征经过学习或有稀疏性，仍然可以检索和建模。体积集中现象不能简单理解成“每个样本挤在某个角点”。检验自己数据的距离分布、邻域质量和下游指标比套一张固定维数比例表可靠。

PCA 保留线性子空间；弯曲的低维流形可能不能用少数线性方向表示。Kernel PCA、t-SNE、UMAP 各有目标，不能按“更新就更好”排列。

## 8. Kernel PCA：在核空间中进行主成分分析

核函数 $k(x_i,x_j)$ 表示某个特征空间中的内积。有效核产生半正定 Gram 矩阵 $K$。常用核：线性 $x^Ty$、RBF $\exp(-\gamma\|x-y\|^2)$（$\gamma>0$）、多项式 $(\gamma x^Ty+c)^p$（适当非负参数与整数次数）。Sigmoid 核并非任意参数都半正定，不能无条件使用。

在核空间中心化：$H=I-\mathbf1\mathbf1^T/n$、$K_c=HKH$。若 $K_c a_i=\lambda_i a_i$、$a_i$ 单位长度，则训练样本在第 $i$ 个核主方向的坐标是 $\sqrt{\lambda_i}a_i$。新点的坐标为中心化核向量与 $a_i/\sqrt{\lambda_i}$ 的内积，必须使用训练集均值完成核中心化。

```python
import numpy as np

def kernel_pca_train(X, k=2, gamma=0.5):
    X = np.asarray(X, float)
    if gamma <= 0 or not 1 <= k <= len(X):
        raise ValueError("核参数或成分数量不合法")
    squared = ((X[:, None, :] - X[None, :, :]) ** 2).sum(axis=-1)
    K = np.exp(-gamma * squared)
    Kc = K - K.mean(axis=0)[None, :] - K.mean(axis=1)[:, None] + K.mean()
    values, vectors = np.linalg.eigh(Kc)
    order = np.argsort(values)[::-1]
    values, vectors = values[order], vectors[:, order]
    keep = values > np.finfo(float).eps * len(X) * max(values[0], 1.)
    values, vectors = values[keep][:k], vectors[:, keep][:, :k]
    Z = vectors * np.sqrt(values)
    return Z, Kc

theta = np.linspace(0, 2 * np.pi, 12, endpoint=False)
circle = np.column_stack([np.cos(theta), np.sin(theta)])
X = np.vstack([circle, 3 * circle])
Z, Kc = kernel_pca_train(X)
print(Z.shape)  # (24, 2)
assert np.allclose(Kc.mean(axis=0), 0., atol=1e-12)
assert np.allclose(Kc, Kc.T)
```

同心圆展示线性 PCA 无法用一个轴把两圈彻底分开，合适的核和足够成分可以揭示非线性结构；具体前两成分是否能分开，取决于 $\gamma$、采样与谱排序，不能无条件宣称第一成分一定区分两圈。需实画/检查标签邻域与独立任务指标。

稠密核矩阵需 $O(n^2)$ 存储、完整特征分解约 $O(n^3)$。样本数量大时可考虑核近似或其他方法。核映射一般没有精确简单的逆，恢复原数据需要预像近似；不能把线性 PCA 的 `inverse_transform` 公式照搬。

## 9. t-SNE：学习邻域图，而非全局地图

t-SNE 先将高维邻近关系写成概率 $p_{ij}$，近点通常有较大概率；低维用长尾 Student t 分布定义 $q_{ij}$，优化 $\operatorname{KL}(P\|Q)$。长尾缓解把大量高维邻居挤进二维的拥挤问题。

perplexity 是邻域分布的有效规模，不是固定每点取该数目的邻居。通常从多组值尝试，必须小于样本数。参数会影响局部/更广邻域权衡；样本数很小时，30 的默认值也可能不合法。

读图时谨慎：簇的面积、密度、距离及空白都可能因优化和参数变化被扭曲，稳定出现的簇仍需在原空间和任务上验证。不能把二维分离看成自然真簇的证明，也不能把两个簇之间的空白读成精确语义距离。不同随机初始化可以得到旋转、重排或不同局部极小值。

高维稠密输入先做几十维 PCA 常能加速和减噪；稀疏文本可先 TruncatedSVD，避免密集中心化。但“所有输入都必须先 PCA 50 维”不是定理，不能在只有 20 个特征时强行取 50。

以下示例依赖 scikit-learn。首批缺依赖未运行；2026-10-03 后续批次已用隔离的 scikit-learn 1.9.1 实际计算得到 `(300, 2)`。未绘制和视觉验收完整邻域图，也未运行所有参数/种子组合：

```python
from sklearn.datasets import load_digits
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

X, y = load_digits(return_X_y=True)
X = X[:300]
pre = PCA(n_components=30, svd_solver="full").fit_transform(X)
embedding = TSNE(n_components=2, perplexity=20, init="pca",
                 learning_rate="auto", max_iter=1000,
                 random_state=7).fit_transform(pre)
print(embedding.shape)  # (300, 2)
```

2026-10-03 官方接口使用 `max_iter`；旧资料的 `n_iter` 已更名。scikit-learn 的默认 Barnes–Hut 近似不等于精确 $O(n^2)$ 全点对算法。常规 `TSNE` 没有用于任意新样本的通用 `transform`，因此不适合作为需要稳定新样本映射的默认分类预处理。

## 10. UMAP：局部模糊图与低维布局

UMAP 在原空间建立近邻图，对每点局部距离尺度做适配，形成模糊加权连接；再优化低维图使这些连接得到近似保持。它使用近邻近似和采样等手段，实践中常较高效，但速度与内存仍受规模、邻居搜索和参数影响。

- `n_neighbors` 决定构造局部图时考虑的邻域大小。更小强调局部，更多通常让布局考虑更广联系，但不保证全局距离正确。
- `min_dist` 控制低维点能挤得多紧。值小可以形成紧密团块，这种“更漂亮”可能主要来自参数，而非真实分离更强。
- `metric` 控制原空间相似性。embedding 用 cosine 还是 euclidean 应遵循其训练与归一化方式，不能仅凭文本/图片类型指定。
- `random_state` 便于重复实验；布局可能受随机性、库版本和近邻近似影响。

`umap-learn` 的典型调用是 `UMAP(n_neighbors=15,min_dist=0.1,metric="euclidean",random_state=7).fit_transform(X)`。它有针对新点的近似 `transform`，适合固定训练流形的后续映射；分布明显漂移时需重新评估。UMAP 并不保证簇间距离具有严格可量化含义。

| 需求 | 起点 | 验证要点 |
|---|---|---|
| 线性压缩、可逆近似、新点映射 | PCA | 重建、解释方差、下游指标 |
| 稀疏词项特征降维 | 不中心化的 TruncatedSVD / LSA | 稀疏性、检索质量 |
| 非线性核结构、样本不太多 | Kernel PCA | 核有效性、参数、内存 |
| 探索二维局部邻域 | t-SNE | 多参数多种子、原空间邻域 |
| 非线性图布局与近似新点映射 | UMAP | 邻域稳定性、映射漂移、实际任务 |

邻域保持可用 trustworthiness 等指标辅助；它们衡量特定邻域失真，也不替代标签任务或领域解释。UMAP/t-SNE 本文解释了可独立理解的方法、参数和读图边界；未安装 UMAP、未跑所有种子时不能写成图示实测完成。

## 11. 推荐、LSA 与低秩更新

推荐中的用户—物品矩阵多数条目未观察。缺失不是评分零；直接填零再分解，会把“未看过”当“极低评价”。均值填补+SVD可作教学基线，需要整行缺失时的退路，并保留真实观测的测试集。

更合适的目标是只在观察集合 $\Omega$ 上优化

$$
\min_{P,Q}\sum_{(u,i)\in\Omega}(R_{ui}-p_u^Tq_i)^2
+\lambda(\|P\|_F^2+\|Q\|_F^2).
$$

ALS 固定 $Q$ 解每个用户的正则最小二乘，再固定 $P$ 解物品参数；每轮都只用该用户/物品的观测条目。梯度法则对被观察的误差更新两个因子。这类方法俗称“推荐 SVD”，但并非对完整矩阵做一次严格 SVD。可加用户/物品偏置，冷启动需额外特征；隐式反馈还要明确置信度与负例假设。

把保留奇异值均分到两侧，$P=U_k\Sigma_k^{1/2}$、$Q=V_k\Sigma_k^{1/2}$，有 $A_k=PQ^T$，每个预测是潜在因子点积。因子并非自然对应“动作片偏好”等标签，它们可以整体正交旋转，只有经过解释与验证才赋予语义。

LSA 对词项—文档矩阵 $T\in\mathbb R^{\text{词数}\times\text{文档数}}$ 做截断 SVD。先规范分词、大小写与计数，可使用 TF-IDF；不能用 `str.count` 子串计数把 `cat` 和 `cattle` 混成同词。文档坐标可取 $\Sigma_kV_k^T$ 的列，词项坐标可取 $U_k\Sigma_k$ 的行；使用不同缩放会改变余弦结果，必须说清约定。

新文档词项向量 $t$ 若投到已有词项基，可用 $U_k^Tt$；然后在同一坐标约定下归一化比较。这是可解释的线性语义基线，不能保证所有同义词或多义词都处理正确。稀疏文档矩阵不中心化常用于 LSA，与中心化 PCA 的方差目标不同。

低秩因子也连接 LoRA 的更新约束，但 LoRA 通过任务训练两个因子，不是每次先做完整权重 SVD 再截断。两者共享秩的思想，算法目标不同。

## 12. 手写幂迭代：理解主方向，识别计算边界

反复做 $v\leftarrow Mv/\|Mv\|$，当最大模特征值独占且初值含该方向分量时，会逐渐突出主特征向量；收敛速度受谱间隙控制。取 $M=A^TA$ 可以找主要右奇异方向。

下面不显式形成 $A^TA$，通过两次乘法计算，减少存储；仍只是教学近似算法，不能替代成熟 SVD。

```python
import numpy as np

def dominant_singular(A, seed=7, max_iter=500, tol=1e-10):
    A = np.asarray(A, float)
    rng = np.random.default_rng(seed)
    v = rng.normal(size=A.shape[1])
    v /= np.linalg.norm(v)
    for _ in range(max_iter):
        w = A.T @ (A @ v)
        length = np.linalg.norm(w)
        if length == 0:
            return 0., np.zeros(A.shape[0]), v
        new_v = w / length
        close = min(np.linalg.norm(new_v - v), np.linalg.norm(new_v + v)) <= tol
        v = new_v
        if close:
            break
    sigma = np.linalg.norm(A @ v)
    u = A @ v / sigma if sigma else np.zeros(A.shape[0])
    return sigma, u, v

A = np.diag([5., 3., 1.])
sigma, u, v = dominant_singular(A)
print(round(sigma, 6))  # 5.0
assert np.allclose(A @ v, sigma * u)
```

找到一个秩一项后从残差矩阵减去 $\sigma uv^T$，再迭代下一项，称为 deflation。有限精度下方向可能失去正交性，需要再正交化；重奇异值或谱间隙很小可能慢收敛。比较时检查重建误差、$U^TU$ 和 $V^TV$，不能仅以打印出几个接近的奇异值为验收。

规模较大时：稠密完整 SVD 约 $O(md\min(m,d))$；若只需少量方向，可考虑 `scipy.sparse.linalg.svds` 或 randomized SVD。稀疏求解返回的奇异值排序须自行确认；随机方法的代价受 $k$、过采样、幂迭代与矩阵乘法有关，不能给所有实现套固定 `O(md log k)`。随机 SVD 是近似，设置种子并检查任务误差；流式数据考虑增量 PCA/在线近似。

非负表示需要 NMF，强非线性结构可考虑核或自编码器；这由目标决定，不表示 SVD 已过时。

## 13. 复习与实践任务

1. 对 `diag(5,3,1)` 要保留超过 95% 能量，取几维？**答案：**2，因为 $34/35\approx97.14\%$；rank 1 仅约71.43%。
2. 为什么 PCA 不能直接对未中心化数据做 SVD？**答案：**未中心化的分解可能优先解释均值，而不是围绕均值的变化；LSA 的未中心化目标是有意不同。
3. 对 `[[1,1],[2,2],[3,3]]` 取一个主成分，重建误差是多少？**答案：**仅有一个非零中心化方向，误差零；方向符号变化不影响重建。
4. 真实图片用多个 rank 重建。**判断标准：**记录原像素与因子字节数、相对误差、能量、细节视觉损失；不能拿白噪声矩阵证明自然图像压缩效果。
5. 构造 rank 3 合成矩阵，加不同标准差的噪声，扫 $k$ 比较与已知 `clean` 的误差。**判断标准：**真实记录最优 $k$，不预设它总等于 3；若只有 noisy，不能以 noisy 自重建误差挑去噪 rank，否则全秩永远最好。
6. 用同一数字子集比较 t-SNE perplexity 5、20、50，以及多个种子。**判断标准：**看哪些原空间邻域稳定、哪些布局变化，记录参数；不能只选最漂亮的一张。
7. 用留出的已观测评分评价均值填补 SVD 与观察掩码矩阵分解。**判断标准：**报告 MAE/RMSE、冷启动与缺失策略；对原训练评分“看起来合理”不算泛化验收。

## 来源与核验

- 吸收来源：[AI Engineering from Scratch](https://github.com/rohitg00/ai-engineering-from-scratch)，数学阶段第 10、11 课，基准提交 `3be078b37ffd8f0c04953c0678e48f5c6d0c7775`，整理日期 2026-10-03。已读所有正文、Python/Julia、测验、选择方法 prompt 和图示生成逻辑。
- 图示的 PCA 轴、奇异谱保留和秩变化含义已改写为可复算数据；上游 SVD 图以能量混灰模拟“重建”的部分不作为真实低秩实验结果保存。
- 官方核对：[NumPy SVD](https://numpy.org/doc/stable/reference/generated/numpy.linalg.svd.html)的约化因子维数与 `Vh`；[scikit-learn PCA](https://scikit-learn.org/stable/modules/generated/sklearn.decomposition.PCA.html)的中心化及求解器；[TSNE](https://scikit-learn.org/stable/modules/generated/sklearn.manifold.TSNE.html)的 `max_iter` 与近似方法；[UMAP 参数](https://umap-learn.readthedocs.io/en/latest/parameters.html)。核验日期 2026-10-03。
- 本文纠正“95%方差等于95%知识”“低方差必是噪声”“全部 PCA 实现只用直接 SVD”“核 PCA 第一成分必分同心圆”等过度结论。可运行小例子与选定本地数字示例单独验证；MNIST 下载、大规模推荐、UMAP 与多种子绘图不算已实测。

## 后续批次补验

首批保留当时的缺依赖记录；本轮补验结果单独保存于[前批补验](../../维护/五站吸收/02-前批补验.json)，以免把旧验收改写成当时已运行。

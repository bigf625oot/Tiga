"""
Architecture: Vector Store Abstraction & Hardware Acceleration Interface

First Principles (第一性原理): 
1. 内存布局 (Memory Layout): 向量计算的本质是密集型浮点运算。为了最大化 CPU L1/L2 缓存命中率 (Cache Line Alignment)，向量必须存储在连续的内存块中。
2. 零拷贝 (Zero-Copy): 在与底层向量数据库（或 C++ 核心库如 FAISS, HNSWLib）进行 IPC/FFI 通信时，必须避免 Python 对象的反序列化开销。

Trade-offs (权衡): 
抽象向量存储接口能防止厂商锁定 (Vendor Lock-in)，但泛化的抽象往往会破坏底层库的 SIMD 指令级优化。
我们通过暴露基于 numpy ndarray (即底层 C Array 缓冲区) 的 `batch_index_zero_copy` 接口来弥补这一性能损失。
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
import numpy as np

class VectorStore(ABC):
    """高维空间向量存储的抽象契约"""

    @abstractmethod
    def search(
        self, 
        query_vector: Union[List[float], np.ndarray], 
        top_k: int = 5, 
        ef_search: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        执行 KNN (K-Nearest Neighbor) 或 ANN (Approximate Nearest Neighbor) 检索。
        
        为什么暴露 ef_search 参数？
        因为基于 HNSW (Hierarchical Navigable Small World) 的算法中，ef_search 决定了搜索期间动态列表的大小。
        在 P10 架构中，我们需要将这种决定性能与召回率的 trade-off 权利上抛给调用方 (Strategy Pattern)，而不是在底层写死。
        """
        pass

    @abstractmethod
    def batch_index_zero_copy(
        self, 
        vectors: np.ndarray, 
        payloads: List[Dict[str, Any]], 
        ids: List[str]
    ) -> None:
        """
        零拷贝批量注入 (Zero-copy batch ingestion)。
        
        为什么强制要求 numpy.ndarray？
        要求 `vectors` 必须是内存连续的 C-order 数组 (如 float32)。这样我们可以直接通过 memoryview/Buffer Protocol
        将指针传递给底层的 Rust/C++ 扩展，彻底绕过 Python GIL 的限制，实现 10x 级别的写入吞吐提升。
        """
        pass
        
    @abstractmethod
    def delete_by_ids(self, ids: List[str]) -> None:
        """
        根据 ID 删除向量。
        注意：在实现层，应该倾向于使用 Tombstone (墓碑机制) 进行软删除，而后在后台异步 Compact，以保证读写的高并发可用性。
        """
        pass

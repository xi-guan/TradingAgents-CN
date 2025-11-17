"""
队列服务用到的 Redis 键名与配置常量（集中定义）
"""

# Redis键名常量
READY_LIST = "qa:ready"

TASK_PREFIX = "qa:task:"
BATCH_PREFIX = "qa:batch:"
SET_PROCESSING = "qa:processing"
SET_COMPLETED = "qa:completed"
SET_FAILED = "qa:failed"
BATCH_TASKS_PREFIX = "qa:batch_tasks:"

# 并发控制相关
USER_PROCESSING_PREFIX = "qa:user_processing:"
GLOBAL_CONCURRENT_KEY = "qa:global_concurrent"
VISIBILITY_TIMEOUT_PREFIX = "qa:visibility:"

# 配置常量 - 性能优化后的并发限制
DEFAULT_USER_CONCURRENT_LIMIT = 10  # 每用户最多10个并发任务
GLOBAL_CONCURRENT_LIMIT = 200  # 全局最多200个并发任务（优化后）
VISIBILITY_TIMEOUT_SECONDS = 300  # 5分钟


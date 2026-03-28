"""
Execution Policy Engine
Defines and enforces policies about what operations are allowed

Features:
- Rate limiting (max operations per user per time window)
- Tool blacklists/whitelists
- Pre-approval requirements for dangerous operations
- Cost limits
- Resource limits
"""

import logging
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


logger = logging.getLogger(__name__)


class OperationType(str, Enum):
    """Types of operations that can be restricted"""
    TOOL_EXECUTION = "tool_execution"
    LLM_CALL = "llm_call"
    FILE_ACCESS = "file_access"
    SYSTEM_MODIFICATION = "system_modification"
    DATA_EXPORT = "data_export"
    KNOWLEDGE_ACCESS = "knowledge_access"


class ApprovalLevel(str, Enum):
    """Required approval level for operations"""
    NONE = "none"  # No approval needed
    USER = "user"  # User confirms before execution
    ADMIN = "admin"  # Admin must approve
    SYSTEM = "system"  # System must verify


@dataclass
class RateLimit:
    """Rate limiting configuration"""
    max_calls: int  # Max calls in time window
    window_seconds: int  # Time window
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "max_calls": self.max_calls,
            "window_seconds": self.window_seconds,
        }


@dataclass
class ResourceLimit:
    """Resource usage limits"""
    max_tokens_per_call: int = 2000
    max_memory_mb: int = 1000
    max_disk_gb: float = 10.0
    max_duration_seconds: float = 300.0


@dataclass
class ExecutionPolicy:
    """Policy for what operations are allowed"""
    
    user_id: str
    enabled: bool = True
    
    # Rate limiting
    rate_limits: Dict[OperationType, RateLimit] = field(default_factory=lambda: {
        OperationType.TOOL_EXECUTION: RateLimit(max_calls=100, window_seconds=3600),
        OperationType.LLM_CALL: RateLimit(max_calls=50, window_seconds=3600),
        OperationType.FILE_ACCESS: RateLimit(max_calls=1000, window_seconds=3600),
    })
    
    # Tool restrictions
    allowed_tools: Optional[Set[str]] = None  # None = all allowed
    blocked_tools: Set[str] = field(default_factory=set)
    blocked_keywords: Set[str] = field(default_factory=set)  # Block if tool name contains
    
    # Approval requirements
    approval_requirements: Dict[OperationType, ApprovalLevel] = field(default_factory=lambda: {
        OperationType.SYSTEM_MODIFICATION: ApprovalLevel.ADMIN,
        OperationType.DATA_EXPORT: ApprovalLevel.USER,
    })
    
    # Resource limits
    resource_limits: ResourceLimit = field(default_factory=ResourceLimit)
    
    # Cost limits
    max_daily_cost: Optional[float] = None  # $ per day
    
    # Time restrictions
    allowed_hours: Optional[List[int]] = None  # 0-23, None = all hours allowed
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "enabled": self.enabled,
            "rate_limits": {k.value: v.to_dict() for k, v in self.rate_limits.items()},
            "allowed_tools": list(self.allowed_tools) if self.allowed_tools else None,
            "blocked_tools": list(self.blocked_tools),
            "approval_requirements": {k.value: v.value for k, v in self.approval_requirements.items()},
        }


@dataclass
class PolicyViolation:
    """Record of a policy violation attempt"""
    user_id: str
    operation_type: OperationType
    resource_name: str
    reason: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PolicyEngine:
    """
    Enforces execution policies
    
    Checks:
    - Rate limits (too many calls)
    - Tool whitelist/blacklist
    - Approval requirements
    - Resource limits
    - Cost limits
    - Time restrictions
    
    Usage:
        engine = PolicyEngine()
        
        # Create policy for user
        policy = ExecutionPolicy(user_id="user_1")
        engine.set_policy(policy)
        
        # Check if operation allowed
        ok, reason = engine.can_execute(
            user_id="user_1",
            operation_type=OperationType.TOOL_EXECUTION,
            resource_name="system_reboot",
            tokens_needed=100,
        )
        
        if not ok:
            print(f"Denied: {reason}")
        else:
            # Execute operation
            ...
            # Record it
            engine.record_operation(...)
    """
    
    def __init__(self):
        self._policies: Dict[str, ExecutionPolicy] = {}
        self._operation_history: Dict[str, List[Dict[str, Any]]] = {}
        self._violations: List[PolicyViolation] = []
        self._daily_costs: Dict[str, float] = {}  # user_id -> $ spent today
    
    def set_policy(self, policy: ExecutionPolicy) -> None:
        """Set execution policy for a user"""
        self._policies[policy.user_id] = policy
        logger.info(f"Policy set for {policy.user_id}")
    
    def get_policy(self, user_id: str) -> Optional[ExecutionPolicy]:
        """Get policy for user (or None if no policy)"""
        return self._policies.get(user_id)
    
    def can_execute(
        self,
        user_id: str,
        operation_type: OperationType,
        resource_name: str,
        tokens_needed: int = 0,
        cost: float = 0.0,
    ) -> tuple[bool, Optional[str]]:
        """
        Check if operation is allowed
        
        Args:
            user_id: User making request
            operation_type: Type of operation
            resource_name: Name of tool/resource
            tokens_needed: Number of tokens for LLM calls
            cost: Estimated cost in $
            
        Returns:
            (allowed: bool, reason: optional error message)
        """
        
        # Get policy
        policy = self._policies.get(user_id)
        
        # No policy = allow (conservative permissive)
        if not policy:
            return True, None
        
        # Policy disabled = allow
        if not policy.enabled:
            return True, None
        
        # Check 1: Tool restrictions
        if operation_type == OperationType.TOOL_EXECUTION:
            # Check blacklist
            if resource_name in policy.blocked_tools:
                violation = PolicyViolation(
                    user_id=user_id,
                    operation_type=operation_type,
                    resource_name=resource_name,
                    reason="Blocked tool",
                )
                self._violations.append(violation)
                return False, f"Tool '{resource_name}' is blocked"
            
            # Check keyword blocks
            if policy.blocked_keywords:
                for keyword in policy.blocked_keywords:
                    if keyword.lower() in resource_name.lower():
                        return False, f"Tool name contains blocked keyword: {keyword}"
            
            # Check whitelist (if set)
            if policy.allowed_tools is not None:
                if resource_name not in policy.allowed_tools:
                    return False, f"Tool '{resource_name}' is not on whitelist"
        
        # Check 2: Rate limits
        ok, reason = self._check_rate_limit(user_id, operation_type)
        if not ok:
            return False, reason
        
        # Check 3: Resource limits
        if tokens_needed > policy.resource_limits.max_tokens_per_call:
            return False, f"Tokens needed ({tokens_needed}) exceeds limit ({policy.resource_limits.max_tokens_per_call})"
        
        # Check 4: Cost limit
        if policy.max_daily_cost:
            daily_cost = self._daily_costs.get(user_id, 0.0)
            if daily_cost + cost > policy.max_daily_cost:
                return False, f"Daily cost limit exceeded: {daily_cost + cost:.2f}$ > {policy.max_daily_cost:.2f}$"
        
        # Check 5: Time restrictions
        if policy.allowed_hours:
            now = datetime.utcnow()
            if now.hour not in policy.allowed_hours:
                return False, f"Operation not allowed at this time (hour {now.hour})"
        
        # Check 6: Approval requirements
        approval_level = policy.approval_requirements.get(operation_type, ApprovalLevel.NONE)
        if approval_level != ApprovalLevel.NONE:
            # In production, would prompt user/admin for approval
            logger.info(f"Operation requires {approval_level.value} approval: {resource_name}")
            # For now, require user approval
            if approval_level == ApprovalLevel.ADMIN:
                return False, f"Admin approval required for {operation_type.value}"
        
        return True, None
    
    def record_operation(
        self,
        user_id: str,
        operation_type: OperationType,
        resource_name: str,
        success: bool,
        cost: float = 0.0,
        tokens_used: int = 0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record an executed operation for tracking"""
        
        if user_id not in self._operation_history:
            self._operation_history[user_id] = []
        
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation_type": operation_type.value,
            "resource_name": resource_name,
            "success": success,
            "cost": cost,
            "tokens_used": tokens_used,
            "metadata": metadata or {},
        }
        
        self._operation_history[user_id].append(record)
        
        # Update daily cost
        if cost > 0:
            if user_id not in self._daily_costs:
                self._daily_costs[user_id] = 0.0
            self._daily_costs[user_id] += cost
        
        logger.debug(f"Recorded operation for {user_id}: {operation_type.value} on {resource_name}")
    
    def _check_rate_limit(
        self,
        user_id: str,
        operation_type: OperationType,
    ) -> tuple[bool, Optional[str]]:
        """Check if rate limit exceeded"""
        
        policy = self._policies.get(user_id)
        if not policy or operation_type not in policy.rate_limits:
            return True, None
        
        limit = policy.rate_limits[operation_type]
        history = self._operation_history.get(user_id, [])
        
        # Count recent operations
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=limit.window_seconds)
        
        recent_ops = [
            op for op in history
            if op["operation_type"] == operation_type.value
            and datetime.fromisoformat(op["timestamp"]) > window_start
        ]
        
        if len(recent_ops) >= limit.max_calls:
            return False, f"Rate limit exceeded for {operation_type.value}: " \
                          f"{len(recent_ops)} / {limit.max_calls} in last {limit.window_seconds}s"
        
        return True, None
    
    def get_violations(self, user_id: Optional[str] = None) -> List[PolicyViolation]:
        """Get violation history"""
        if user_id:
            return [v for v in self._violations if v.user_id == user_id]
        return self._violations
    
    def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get operation statistics for a user"""
        history = self._operation_history.get(user_id, [])
        
        return {
            "total_operations": len(history),
            "successful_operations": len([h for h in history if h["success"]]),
            "failed_operations": len([h for h in history if not h["success"]]),
            "total_cost": self._daily_costs.get(user_id, 0.0),
            "total_tokens": sum(h.get("tokens_used", 0) for h in history),
            "violations": len([v for v in self._violations if v.user_id == user_id]),
        }

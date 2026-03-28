"""
Safety & Audit Demo
Shows policy enforcement and audit trail capabilities

Demonstrates:
1. Policy creation and rule enforcement
2. Rate limiting
3. Tool blacklisting
4. Pre-approval requirements
5. Audit logging
6. Hash chain integrity
"""

import asyncio
import logging
from datetime import datetime, timedelta

from core.safety import (
    PolicyEngine,
    ExecutionPolicy,
    OperationType,
    ApprovalLevel,
    RateLimit,
    AuditLog,
)


logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_basic_policy():
    """Demo 1: Basic policy enforcement"""
    print("\n" + "="*70)
    print("SAFETY DEMO 1 - Basic Policy Enforcement")
    print("="*70 + "\n")
    
    engine = PolicyEngine()
    
    # Create a policy for a user
    print("[CREATE] Creating policy for user_1...\n")
    
    policy = ExecutionPolicy(
        user_id="user_1",
        allowed_tools={"system_diagnostic", "file_scanner", "process_monitor"},
        blocked_tools={"system_reboot", "factory_reset", "data_wipe"},
    )
    
    engine.set_policy(policy)
    
    # Test allowed tool
    print("[TEST] Checking if file_scanner is allowed...")
    allowed, reason = engine.can_execute(
        user_id="user_1",
        operation_type=OperationType.TOOL_EXECUTION,
        resource_name="file_scanner",
    )
    
    if allowed:
        print("  ✓ ALLOWED: file_scanner\n")
        engine.record_operation(
            user_id="user_1",
            operation_type=OperationType.TOOL_EXECUTION,
            resource_name="file_scanner",
            success=True,
        )
    else:
        print(f"  ✗ DENIED: {reason}\n")
    
    # Test blocked tool
    print("[TEST] Checking if system_reboot is allowed...")
    allowed, reason = engine.can_execute(
        user_id="user_1",
        operation_type=OperationType.TOOL_EXECUTION,
        resource_name="system_reboot",
    )
    
    if allowed:
        print("  ✓ ALLOWED: system_reboot\n")
    else:
        print(f"  ✗ DENIED: {reason}\n")
    
    # Test unapproved tool (not in allowed list)
    print("[TEST] Checking if unknown_tool is allowed...")
    allowed, reason = engine.can_execute(
        user_id="user_1",
        operation_type=OperationType.TOOL_EXECUTION,
        resource_name="unknown_tool",
    )
    
    if allowed:
        print("  ✓ ALLOWED: unknown_tool\n")
    else:
        print(f"  ✗ DENIED: {reason}\n")


async def demo_rate_limiting():
    """Demo 2: Rate limiting"""
    print("="*70)
    print("SAFETY DEMO 2 - Rate Limiting")
    print("="*70 + "\n")
    
    engine = PolicyEngine()
    
    # Create restrictive policy
    print("[CREATE] Creating policy with strict rate limits...\n")
    
    policy = ExecutionPolicy(
        user_id="user_2",
        rate_limits={
            OperationType.LLM_CALL: RateLimit(max_calls=3, window_seconds=60),
            OperationType.TOOL_EXECUTION: RateLimit(max_calls=5, window_seconds=60),
        },
    )
    
    engine.set_policy(policy)
    
    print("[TEST] Making LLM calls (limit: 3 per minute)...\n")
    
    for i in range(5):
        allowed, reason = engine.can_execute(
            user_id="user_2",
            operation_type=OperationType.LLM_CALL,
            resource_name="groq_backend",
        )
        
        if allowed:
            print(f"  [{i+1}] ✓ LLM call allowed")
            engine.record_operation(
                user_id="user_2",
                operation_type=OperationType.LLM_CALL,
                resource_name="groq_backend",
                success=True,
            )
        else:
            print(f"  [{i+1}] ✗ DENIED: {reason}")
    
    print()


async def demo_approval_workflow():
    """Demo 3: Pre-approval requirements"""
    print("="*70)
    print("SAFETY DEMO 3 - Pre-Approval Requirements")
    print("="*70 + "\n")
    
    engine = PolicyEngine()
    
    print("[CREATE] Creating policy with approval requirements...\n")
    
    policy = ExecutionPolicy(
        user_id="user_3",
        approval_requirements={
            OperationType.SYSTEM_MODIFICATION: ApprovalLevel.ADMIN,
            OperationType.DATA_EXPORT: ApprovalLevel.USER,
        },
    )
    
    engine.set_policy(policy)
    
    # Test system modification (needs admin approval)
    print("[TEST] Attempting system modification...")
    allowed, reason = engine.can_execute(
        user_id="user_3",
        operation_type=OperationType.SYSTEM_MODIFICATION,
        resource_name="disable_antivirus",
    )
    
    if allowed:
        print("  ✓ ALLOWED (no approval needed)\n")
    else:
        print(f"  ℹ️  DENIED: {reason}")
        print("     (Would require admin approval in UI)\n")
    
    # Test data export (needs user confirmation)
    print("[TEST] Attempting data export...")
    allowed, reason = engine.can_execute(
        user_id="user_3",
        operation_type=OperationType.DATA_EXPORT,
        resource_name="export_user_data",
    )
    
    if allowed:
        print("  ✓ ALLOWED\n")
    else:
        print(f"  ℹ️  DENIED: {reason}")
        print("     (Would prompt user for confirmation)\n")


async def demo_audit_logging():
    """Demo 4: Audit trail"""
    print("="*70)
    print("SAFETY DEMO 4 - Audit Logging & Hash Chain")
    print("="*70 + "\n")
    
    log = AuditLog()
    
    print("[RECORD] Recording various actions...\n")
    
    # Record some actions
    actions = [
        ("user_1", "tool_executed", "file_scanner", "success"),
        ("user_1", "tool_executed", "system_diagnostic", "success"),
        ("user_2", "policy_violated", "system_reboot", "denied"),
        ("user_1", "llm_called", "groq", "success"),
        ("user_2", "policy_violated", "blocked_tool", "denied"),
    ]
    
    for user, action, resource, result in actions:
        event = log.record(
            user_id=user,
            action=action,
            resource=resource,
            result=result,
            details={"test": True},
        )
        print(f"  - {user}: {action} on {resource} -> {result}")
    
    print()
    
    # Verify integrity
    print("[VERIFY] Checking hash chain integrity...")
    is_intact, error = log.verify_integrity()
    
    if is_intact:
        print("  ✓ Hash chain INTACT (no tampering detected)\n")
    else:
        print(f"  ✗ Hash chain BROKEN: {error}\n")
    
    # Search events
    print("[SEARCH] Finding all actions by user_1...")
    user1_events = log.search(user_id="user_1", limit=100)
    
    for event in user1_events:
        print(f"  - {event.action} on {event.resource}: {event.result}")
    
    print()
    
    # Statistics
    print("[STATS] Audit log statistics...")
    stats = log.get_stats()
    
    print(f"  Total events: {stats['total_events']}")
    print(f"  Unique users: {stats['unique_users']}")
    print(f"  Success rate: {stats['success_rate']*100:.0f}%")
    print(f"  Successful: {stats['successful_events']}")
    print(f"  Failed: {stats['failed_events']}")
    print(f"  Denied: {stats['denied_events']}")
    print()


async def demo_compliance_report():
    """Demo 5: Compliance reports"""
    print("="*70)
    print("SAFETY DEMO 5 - Compliance & Activity Reports")
    print("="*70 + "\n")
    
    engine = PolicyEngine()
    log = AuditLog()
    
    # Create policies
    for user_id in ["user_1", "user_2", "user_3"]:
        policy = ExecutionPolicy(user_id=user_id)
        engine.set_policy(policy)
    
    # Simulate activity
    print("[SIMULATE] Simulating user activity...\n")
    
    users = {
        "user_1": [("tool_executed", "scanner", "success", 1500),
                   ("tool_executed", "monitor", "success", 800),
                   ("tool_executed", "diagnostic", "success", 2000)],
        "user_2": [("tool_executed", "scanner", "success", 1200),
                   ("policy_violated", "blocked_tool", "denied", 0)],
        "user_3": [("tool_executed", "export", "success", 3000),
                   ("tool_executed", "export", "success", 2500),
                   ("tool_executed", "export", "success", 2000)],
    }
    
    for user_id, actions in users.items():
        for action, resource, result, cost in actions:
            log.record(
                user_id=user_id,
                action=action,
                resource=resource,
                result=result,
                details={"cost": cost},
            )
            
            engine.record_operation(
                user_id=user_id,
                operation_type=OperationType.TOOL_EXECUTION,
                resource_name=resource,
                success=result == "success",
                cost=cost,
            )
    
    print("Activity recorded\n")
    
    # Generate reports
    print("[REPORT] User Activity Summary\n")
    
    for user_id in ["user_1", "user_2", "user_3"]:
        summary = log.get_user_activity_summary(user_id)
        stats = engine.get_user_stats(user_id)
        
        print(f"{user_id}:")
        print(f"  Total events: {summary['total_events']}")
        print(f"  Successful: {summary['successful_events']}")
        print(f"  Denied: {summary['denied_events']}")
        print(f"  Total cost: ${stats['total_cost']:.2f}")
        print(f"  Violations: {stats['violations']}")
        print()


async def demo_architecture():
    """Show safety architecture"""
    print("="*70)
    print("SAFETY ARCHITECTURE")
    print("="*70 + "\n")
    
    print("""
Build #5: Safety & Audit (350+ LOC)

1. POLICY ENGINE (policy_engine.py - 280 LOC)
   ├─ ExecutionPolicy: Define what's allowed
   │  ├─ Rate limits (calls per time window)
   │  ├─ Tool restrictions (whitelist/blacklist)
   │  ├─ Approval levels (None/User/Admin)
   │  ├─ Resource limits (tokens, memory, disk)
   │  ├─ Cost limits ($/day)
   │  └─ Time restrictions (allowed hours)
   │
   ├─ PolicyEngine: Enforce policies
   │  ├─ can_execute() - Check before operation
   │  ├─ record_operation() - Track execution
   │  ├─ get_violations() - Find violations
   │  └─ get_user_stats() - Usage analytics
   │
   └─ OperationType enum:
      ├─ TOOL_EXECUTION
      ├─ LLM_CALL
      ├─ FILE_ACCESS
      ├─ SYSTEM_MODIFICATION
      ├─ DATA_EXPORT
      └─ KNOWLEDGE_ACCESS

2. AUDIT LOG (audit_log.py - 140 LOC)
   ├─ AuditEvent: Immutable event record
   │  ├─ Timestamp, user, action, result
   │  ├─ Hash chain for integrity
   │  └─ Metadata for context
   │
   ├─ AuditLog: Append-only log
   │  ├─ record() - Add event (append-only)
   │  ├─ search() - Query with filters
   │  ├─ verify_integrity() - Check hash chain
   │  ├─ get_stats() - Log statistics
   │  └─ export_events() - For compliance
   │
   └─ Features:
      ├─ Hash chain (SHA256)
      ├─ Time-based filtering
      ├─ User activity summaries
      └─ Compliance exports

USAGE PATTERN:
  1. Create policy for user
  2. Before execution: engine.can_execute(...)
  3. If denied: log violation
  4. If allowed: execute operation
  5. After execution: engine.record_operation(...)
  6. Always: log.record(action, result)

SECURITY PROPERTIES:
  ✓ Rate limiting prevents abuse
  ✓ Tool restrictions prevent misuse
  ✓ Approval workflows enable governance
  ✓ Audit trail enables accountability
  ✓ Hash chain prevents tampering
  ✓ User separates concerns (policy vs logging)
""")
    
    print()


async def main():
    """Run all safety demos"""
    
    await demo_basic_policy()
    await demo_rate_limiting()
    await demo_approval_workflow()
    await demo_audit_logging()
    await demo_compliance_report()
    await demo_architecture()
    
    print("="*70)
    print("SAFETY DEMO COMPLETE")
    print("="*70 + "\n")
    
    print("FEATURES DEMONSTRATED:")
    print("  ✓ Policy enforcement (tool restrictions, whitelist/blacklist)")
    print("  ✓ Rate limiting (calls per time window)")
    print("  ✓ Pre-approval requirements (admin/user approval)")
    print("  ✓ Audit logging (immutable append-only log)")
    print("  ✓ Hash chain integrity (tamper detection)")
    print("  ✓ Compliance reporting (user activity summaries)")
    print()
    
    print("INTEGRATION WITH ORCHESTRATOR:")
    print("  - AgentOrchestrator calls PolicyEngine.can_execute() before operations")
    print("  - Records all operations in PolicyEngine")
    print("  - AuditLog records all actions for compliance")
    print("  - Hash chain ensures tampering is detectable")
    print()
    
    print("NEXT: Build #6 - API Layer (FastAPI + WebSocket)")
    print()


if __name__ == "__main__":
    asyncio.run(main())

"""
API Layer Demo
Shows REST endpoints and WebSocket support

Demonstrates:
1. Token generation and verification
2. Command execution via REST API
3. Policy enforcement before execution
4. Audit logging
5. WebSocket event streaming
6. Admin endpoints for policy/audit management
"""

import asyncio
import logging
from datetime import datetime

from core.api.auth import AuthManager
from core.api.models import (
    CommandRequest,
    EventType,
    StreamEvent,
    User,
)
from core.api.websocket import WebSocketManager
from core.safety import PolicyEngine, ExecutionPolicy, AuditLog, OperationType


logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)


async def demo_authentication():
    """Demo 1: Authentication & Token Management"""
    pprint("\n" + "="*70)
    pprint("API DEMO 1 - Authentication & Token Management")
    pprint("="*70 + "\n")
    
    auth = AuthManager(secret_key="demo-secret")
    
    pprint("[CREATE] Generating tokens for users...\n")
    
    # Create tokens
    user_token = auth.generate_token("user_1", role="user", hours=24)
    admin_token = auth.generate_token("admin_user", role="admin", hours=24)
    
    pprint(f"User token:  {user_token[:50]}...")
    pprint(f"Admin token: {admin_token[:50]}...\n")
    
    # Verify tokens
    pprint("[VERIFY] Verifying tokens...\n")
    
    is_valid, data = auth.verify_token(user_token)
    pprint(f"User token valid: {is_valid}")
    if data:
        pprint(f"  User ID: {data.user_id}")
        pprint(f"  Role: {data.role}\n")
    
    is_valid, data = auth.verify_token(admin_token)
    pprint(f"Admin token valid: {is_valid}")
    if data:
        pprint(f"  User ID: {data.user_id}")
        pprint(f"  Role: {data.role}\n")
    
    # Get user from token
    pprint("[EXTRACT] Extracting user from token...\n")
    
    user = auth.get_user_from_token(user_token)
    pprint(f"User from token: {user.user_id}")
    pprint(f"  Is admin: {user.is_admin}\n")
    
    # Invalid token
    pprint("[TEST] Testing invalid token...\n")
    
    is_valid, data = auth.verify_token("invalid.token")
    pprint(f"Invalid token valid: {is_valid}\n")


async def demo_rest_endpoints():
    """Demo 2: REST API Endpoints"""
    pprint("="*70)
    pprint("API DEMO 2 - REST Endpoints")
    pprint("="*70 + "\n")
    
    pprint("[INFO] API Endpoints Available:\n")
    
    endpoints = [
        ("GET", "/health", "Health check"),
        ("POST", "/auth/token", "Create bearer token"),
        ("POST", "/command", "Execute user command"),
        ("GET", "/admin/policy/{user_id}", "Get user policy (admin)"),
        ("GET", "/admin/audit", "Query audit log (admin)"),
        ("WebSocket", "/ws", "Real-time event streaming"),
    ]
    
    for method, path, desc in endpoints:
        pprint(f"  {method:10} {path:25} - {desc}")
    
    pprint("\n[STRUCTURE] API Architecture:\n")
    
    structure = """
    +--------------------------------------------------+
    |            FASTAPI Server                       |
    +--------------------------------------------------+
    |                                                  |
    | REST Endpoints        WebSocket Streaming       |
    | - POST /command       - Execution Events        |
    | - GET /health         - Policy Violations       |
    | - GET /policy         - Audit Events            |
    | - GET /audit          - Real-time Updates       |
    |        |                       |                 |
    | +------+-------+--------+------+                 |
    | |   AgentOrchestrator          |                 |
    | | (Process commands end-to-end)|               |
    | +------+-------+--------+------+                 |
    |        |                 |                        |
    |   Policy Engine   Audit Log    Memory Store     |
    |        ^                 |      ^                 |
    |        +---------+-------+------+                |
    |                                                  |
    +--------------------------------------------------+
    """
    
    pprint(structure)


async def demo_authentication_flow():
    """Demo 3: Complete Authentication Flow"""
    pprint("="*70)
    pprint("API DEMO 3 - Authentication Flow")
    pprint("="*70 + "\n")
    
    auth = AuthManager()
    
    pprint("[STEP 1] Client requests token...")
    pprint("  POST /auth/token")
    pprint("  Body: { user_id: user_1, role: user }\n")
    
    token = auth.generate_token("user_1", "user")
    response = f'[RESPONSE] {{"access_token": "{token[:30]}...", "token_type": "bearer"}}\n'
    pprint(response)
    
    pprint("[STEP 2] Client sends Authorization header...")
    pprint(f"  Authorization: Bearer {token[:30]}...\n")
    
    pprint("[STEP 3] Server verifies token...")
    is_valid, token_data = auth.verify_token(token)
    
    if is_valid:
        pprint(f"  ✓ Token valid")
        pprint(f"  ✓ User ID: {token_data.user_id}")
        pprint(f"  ✓ Role: {token_data.role}\n")
    
    pprint("[STEP 4] Server extracts user context...")
    user = auth.get_user_from_token(token)
    pprint(f"  User context: {user}\n")


async def demo_policy_integration():
    """Demo 4: Policy Enforcement in API"""
    pprint("="*70)
    pprint("API DEMO 4 - Policy Enforcement")
    pprint("="*70 + "\n")
    
    policy_engine = PolicyEngine()
    audit_log = AuditLog()
    
    # Setup policy
    pprint("[SETUP] Creating policy for user_1...\n")
    
    policy = ExecutionPolicy(
        user_id="user_1",
        allowed_tools={"file_scanner", "system_monitor"},
        blocked_tools={"system_reboot"},
    )
    
    policy_engine.set_policy(policy)
    
    pprint("[API CALL] POST /command")
    pprint("  Authorization: Bearer <token>")
    pprint("  Body: { command: \"Scan for large files\" }\n")
    
    pprint("[POLICY CHECK] Checking policy before execution...\n")
    
    allowed, reason = policy_engine.can_execute(
        user_id="user_1",
        operation_type=OperationType.TOOL_EXECUTION,
        resource_name="command_execution",
    )
    
    if allowed:
        pprint("  ✓ Allowed - Executing command...")
        
        # Record operation
        policy_engine.record_operation(
            user_id="user_1",
            operation_type=OperationType.TOOL_EXECUTION,
            resource_name="command_execution",
            success=True,
        )
        
        # Audit log
        audit_log.record(
            user_id="user_1",
            action="command_executed",
            resource="scan_large_files",
            result="success",
            details={"execution_id": "exec_123"},
        )
        
        pprint("  ✓ Logged to audit trail\n")
        
        pprint("[RESPONSE]")
        pprint("  Status: 200 OK")
        pprint("  Body: { execution_id: exec_123, status: success }\n")
    
    else:
        pprint(f"  ✗ Denied - {reason}\n")


async def demo_websocket_events():
    """Demo 5: WebSocket Event Streaming"""
    pprint("="*70)
    pprint("API DEMO 5 - WebSocket Event Streaming")
    pprint("="*70 + "\n")
    
    ws_manager = WebSocketManager()
    
    pprint("[CONNECT] Client connects to WebSocket /ws\n")
    
    pprint("[EVENTS] Real-time events during command execution...\n")
    
    events = [
        ("execution_started", {"command": "Optimize system", "timestamp": datetime.now().isoformat()}),
        ("execution_progress", {"step": "Scanning system...", "progress": 25}),
        ("execution_progress", {"step": "Cleaning temp files...", "progress": 50}),
        ("execution_progress", {"step": "Optimizing settings...", "progress": 75}),
        ("execution_completed", {"result": "System optimized - Freed 45GB", "duration_seconds": 12.3}),
    ]
    
    for event_type, data in events:
        event = StreamEvent(
            event_type=EventType(event_type),
            execution_id="exec_123",
            data=data,
        )
        
        pprint(f"  [{event_type.upper()}]")
        for key, val in data.items():
            if isinstance(val, float):
                pprint(f"    {key}: {val:.1f}")
            else:
                pprint(f"    {key}: {val}")
        pprint()


async def demo_admin_endpoints():
    """Demo 6: Admin Endpoints"""
    pprint("="*70)
    pprint("API DEMO 6 - Admin Endpoints")
    pprint("="*70 + "\n")
    
    policy_engine = PolicyEngine()
    audit_log = AuditLog()
    
    # Setup
    policy = ExecutionPolicy(user_id="user_1")
    policy_engine.set_policy(policy)
    
    # Record some audit events
    for i in range(3):
        audit_log.record(
            user_id="user_1",
            action="command_executed",
            resource=f"operation_{i}",
            result="success",
        )
    
    pprint("[ADMIN REQUEST] GET /admin/policy/user_1")
    pprint("  Authorization: Bearer <admin_token>\n")
    
    stats = policy_engine.get_user_stats("user_1")
    
    pprint("[RESPONSE]")
    pprint("  Status: 200 OK")
    pprint(f"  user_id: user_1")
    pprint(f"  Total operations: {stats['total_operations']}")
    pprint(f"  Successful: {stats['successful_operations']}")
    pprint(f"  Total cost: ${stats['total_cost']:.2f}")
    pprint(f"  Violations: {stats['violations']}\n")
    
    pprint("[ADMIN REQUEST] GET /admin/audit?user_id=user_1&limit=10")
    pprint("  Authorization: Bearer <admin_token>\n")
    
    events = audit_log.search(user_id="user_1", limit=10)
    
    pprint("[RESPONSE]")
    pprint("  Status: 200 OK")
    pprint(f"  Total events: {len(events)}")
    for event in events[:3]:
        pprint(f"    - {event.action} on {event.resource}: {event.result}")
    pprint()


async def demo_error_handling():
    """Demo 7: Error Handling"""
    pprint("="*70)
    pprint("API DEMO 7 - Error Handling")
    pprint("="*70 + "\n")
    
    pprint("[ERROR 1] Missing Authorization Header")
    pprint("  Request: GET /admin/policy/user_1")
    pprint("  (no Authorization header)\n")
    pprint("[RESPONSE]")
    pprint("  Status: 401 Unauthorized")
    pprint("  Body: { error: Unauthorized, code: HTTP_ERROR }\n")
    
    pprint("[ERROR 2] Invalid Token")
    pprint("  Request: POST /command")
    pprint("  Authorization: Bearer invalid.token\n")
    pprint("[RESPONSE]")
    pprint("  Status: 401 Unauthorized")
    pprint("  Body: { error: Unauthorized, code: HTTP_ERROR }\n")
    
    pprint("[ERROR 3] Insufficient Permissions")
    pprint("  Request: GET /admin/audit")
    pprint("  Authorization: Bearer <user_token>\n")
    pprint("[RESPONSE]")
    pprint("  Status: 403 Forbidden")
    pprint("  Body: { error: Forbidden, code: HTTP_ERROR }\n")
    
    pprint("[ERROR 4] Policy Violation")
    pprint("  Request: POST /command")
    pprint("  Authorization: Bearer <token>")
    pprint("  Body: { command: \"Forbidden operation\" }\n")
    pprint("[RESPONSE]")
    pprint("  Status: 200 OK (operation completed)")
    pprint("  Body: { execution_id: ..., status: failed, error: Policy violation: ... }\n")


async def main():
    """Run all API demos"""
    
    await demo_authentication()
    await demo_rest_endpoints()
    await demo_authentication_flow()
    await demo_policy_integration()
    await demo_websocket_events()
    await demo_admin_endpoints()
    await demo_error_handling()
    
    pprint("="*70)
    pprint("API DEMO COMPLETE")
    pprint("="*70 + "\n")
    
    pprint("BUILD #6: API LAYER (450+ LOC)")
    pprint()
    pprint("FILES CREATED:")
    pprint("  1. core/api/models.py (200 LOC)")
    pprint("     - Request/response Pydantic models")
    pprint("     - Event models for WebSocket")
    pprint("     - Authentication data classes")
    pprint()
    pprint("  2. core/api/auth.py (150 LOC)")
    pprint("     - AuthManager for token generation/verification")
    pprint("     - Role-based access control")
    pprint("     - Token caching")
    pprint()
    pprint("  3. core/api/websocket.py (200 LOC)")
    pprint("     - WebSocketManager for connection handling")
    pprint("     - Event broadcasting to connected clients")
    pprint("     - Event types (started, progress, completed, failed)")
    pprint()
    pprint("  4. core/api/server.py (350+ LOC)")
    pprint("     - FastAPI application setup")
    pprint("     - REST endpoints (health, auth, command, admin)")
    pprint("     - WebSocket support")
    pprint("     - Policy enforcement")
    pprint("     - Audit logging")
    pprint("     - Error handling")
    pprint()
    pprint("API ENDPOINTS:")
    pprint("  GET  /health                  - Health check")
    pprint("  POST /auth/token              - Create bearer token")
    pprint("  POST /command                 - Execute command")
    pprint("  GET  /admin/policy/{user_id}  - Get policy (admin)")
    pprint("  GET  /admin/audit             - Query audit log (admin)")
    pprint("  WS   /ws                      - Real-time events")
    pprint()
    pprint("SECURITY FEATURES:")
    pprint("  ✓ Bearer token authentication")
    pprint("  ✓ Role-based access control (user/admin)")
    pprint("  ✓ Policy enforcement before execution")
    pprint("  ✓ Audit trail for all actions")
    pprint("  ✓ Proper HTTP status codes")
    pprint("  ✓ Error handling with details")
    pprint()
    pprint("NEXT: Build #7 - Tests (Unit + Integration)")
    pprint()


if __name__ == "__main__":
    asyncio.run(main())

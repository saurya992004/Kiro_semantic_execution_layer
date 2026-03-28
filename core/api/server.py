"""
JARVIS API Server
FastAPI application with REST endpoints and WebSocket support
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.agent.master_agent import AgentOrchestrator
from core.api.auth import get_auth_manager
from core.api.models import (
    CommandRequest,
    ExecutionResult,
    ErrorResponse,
    HealthResponse,
    User,
)
from core.api.websocket import get_ws_manager
from core.safety import PolicyEngine, AuditLog, OperationType


logger = logging.getLogger(__name__)


class JARVISServer:
    """JARVIS API Server"""
    
    def __init__(
        self,
        orchestrator: Optional[AgentOrchestrator] = None,
        policy_engine: Optional[PolicyEngine] = None,
        audit_log: Optional[AuditLog] = None,
    ):
        """
        Initialize JARVIS server
        
        Args:
            orchestrator: AgentOrchestrator instance
            policy_engine: PolicyEngine instance
            audit_log: AuditLog instance
        """
        self.app = FastAPI(
            title="JARVIS API",
            description="JARVIS 2.0 - Intelligent Agent System",
            version="2.0.0",
        )
        
        self.orchestrator = orchestrator or AgentOrchestrator()
        self.policy_engine = policy_engine or PolicyEngine()
        self.audit_log = audit_log or AuditLog()
        self.ws_manager = get_ws_manager()
        self.auth_manager = get_auth_manager()
        
        self._setup_middleware()
        self._setup_routes()
    
    def _setup_middleware(self):
        """Setup middleware"""
        # CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _get_user_from_header(
        self,
        authorization: Optional[str] = Header(None),
    ) -> Optional[User]:
        """
        Extract and verify user from Authorization header
        
        Args:
            authorization: Authorization header value
            
        Returns:
            User object or None
        """
        if not authorization:
            return None
        
        try:
            # Expected format: "Bearer <token>"
            parts = authorization.split()
            if len(parts) != 2 or parts[0].lower() != "bearer":
                return None
            
            token = parts[1]
            return self.auth_manager.get_user_from_token(token)
        
        except Exception as e:
            logger.error(f"Authorization error: {e}")
            return None
    
    def _setup_routes(self):
        """Setup API routes"""
        app = self.app
        
        # ====== Health & Info ======
        
        @app.get("/health", response_model=HealthResponse)
        async def health_check():
            """Health check endpoint"""
            return HealthResponse(
                status="healthy",
                version="2.0.0",
                components={
                    "orchestrator": "operational",
                    "policy_engine": "operational",
                    "audit_log": "operational",
                    "websocket": "operational",
                },
                timestamp=datetime.now(),
            )
        
        # ====== Authentication ======
        
        @app.post("/auth/token")
        async def create_token(user_id: str, role: str = "user"):
            """
            Create a bearer token
            
            In production, verify credentials first
            """
            token = self.auth_manager.generate_token(user_id, role)
            
            logger.info(f"Token created for {user_id} with role {role}")
            
            return {
                "access_token": token,
                "token_type": "bearer",
                "user_id": user_id,
                "role": role,
            }
        
        # ====== Execution ======
        
        @app.post("/command", response_model=ExecutionResult)
        async def execute_command(
            request: CommandRequest,
            authorization: Optional[str] = Header(None),
        ):
            """Execute a user command"""
            
            # Get authenticated user
            user = self._get_user_from_header(authorization)
            if not user:
                raise HTTPException(status_code=401, detail="Unauthorized")
            
            execution_id = str(uuid.uuid4())
            
            try:
                # Check policy
                allowed, reason = self.policy_engine.can_execute(
                    user_id=user.user_id,
                    operation_type=OperationType.TOOL_EXECUTION,
                    resource_name="command_execution",
                )
                
                if not allowed:
                    # Log policy violation
                    self.audit_log.record(
                        user_id=user.user_id,
                        action="policy_violated",
                        resource="command_execution",
                        result="denied",
                        details={"reason": reason},
                    )
                    
                    return ExecutionResult(
                        execution_id=execution_id,
                        status="failed",
                        error=f"Policy violation: {reason}",
                    )
                
                # Send WebSocket event: started
                await self.ws_manager.send_execution_started(
                    user.user_id,
                    execution_id,
                    request.command,
                )
                
                # Execute command
                result_text = ""
                async for event in self.orchestrator.process_command(
                    user_id=user.user_id,
                    command=request.command,
                    execution_id=execution_id,
                ):
                    # Stream events to WebSocket
                    if hasattr(event, 'event_type'):
                        await self.ws_manager.broadcast_to_user(
                            user.user_id,
                            event,
                        )
                    
                    # Accumulate result
                    if hasattr(event, 'data') and 'result' in event.data:
                        result_text = event.data['result']
                
                # Record operation
                self.policy_engine.record_operation(
                    user_id=user.user_id,
                    operation_type=OperationType.TOOL_EXECUTION,
                    resource_name="command_execution",
                    success=True,
                )
                
                # Audit log
                self.audit_log.record(
                    user_id=user.user_id,
                    action="command_executed",
                    resource=request.command,
                    result="success",
                    details={"execution_id": execution_id},
                )
                
                # Send completion event
                await self.ws_manager.send_execution_completed(
                    user.user_id,
                    execution_id,
                    result_text,
                    0.0,
                )
                
                return ExecutionResult(
                    execution_id=execution_id,
                    status="success",
                    result=result_text,
                )
            
            except Exception as e:
                logger.error(f"Command execution error: {e}")
                
                # Audit log
                self.audit_log.record(
                    user_id=user.user_id,
                    action="command_failed",
                    resource=request.command,
                    result="error",
                    details={"error": str(e)},
                )
                
                return ExecutionResult(
                    execution_id=execution_id,
                    status="failed",
                    error=str(e),
                )
        
        # ====== Policy Management (Admin) ======
        
        @app.get("/admin/policy/{user_id}")
        async def get_user_policy(
            user_id: str,
            authorization: Optional[str] = Header(None),
        ):
            """Get policy for a user (admin only)"""
            
            user = self._get_user_from_header(authorization)
            if not user or not user.is_admin:
                raise HTTPException(status_code=403, detail="Forbidden")
            
            policy = self.policy_engine.policies.get(user_id)
            if not policy:
                raise HTTPException(status_code=404, detail="User not found")
            
            stats = self.policy_engine.get_user_stats(user_id)
            
            return {
                "user_id": user_id,
                "policy": {
                    "allowed_tools": policy.allowed_tools,
                    "blocked_tools": policy.blocked_tools,
                    "max_daily_cost": policy.max_daily_cost,
                },
                "stats": stats,
            }
        
        # ====== Audit Log (Admin) ======
        
        @app.get("/admin/audit")
        async def query_audit_log(
            user_id: Optional[str] = None,
            action: Optional[str] = None,
            resource: Optional[str] = None,
            limit: int = 100,
            authorization: Optional[str] = Header(None),
        ):
            """Query audit log (admin only)"""
            
            user = self._get_user_from_header(authorization)
            if not user or not user.is_admin:
                raise HTTPException(status_code=403, detail="Forbidden")
            
            events = self.audit_log.search(
                user_id=user_id,
                action=action,
                resource=resource,
                limit=limit,
            )
            
            return {
                "events": [e.to_dict() for e in events],
                "total": len(events),
            }
        
        # ====== WebSocket ======
        
        @app.websocket("/ws")
        async def websocket_endpoint(
            websocket: WebSocket,
            token: str,
        ):
            """WebSocket endpoint for real-time events"""
            
            # Verify token
            user = self.auth_manager.get_user_from_token(token)
            if not user:
                await websocket.close(code=4001, reason="Unauthorized")
                return
            
            # Connect
            if not await self.ws_manager.connect(user.user_id, websocket):
                await websocket.close(code=4002, reason="Connection failed")
                return
            
            try:
                # Keep connection alive
                while True:
                    # Listen for messages (or close event)
                    data = await websocket.receive_text()
                    
                    # Echo for now
                    await websocket.send_json({"message": "received", "data": data})
            
            except WebSocketDisconnect:
                await self.ws_manager.disconnect(user.user_id, websocket)
            
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await self.ws_manager.disconnect(user.user_id, websocket)
        
        # ====== Error Handlers ======
        
        @app.exception_handler(HTTPException)
        async def http_exception_handler(request, exc):
            """Handle HTTP exceptions"""
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": exc.detail,
                    "code": "HTTP_ERROR",
                    "timestamp": datetime.now().isoformat(),
                },
            )
        
        @app.exception_handler(Exception)
        async def general_exception_handler(request, exc):
            """Handle uncaught exceptions"""
            logger.error(f"Unhandled exception: {exc}")
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "code": "INTERNAL_ERROR",
                    "timestamp": datetime.now().isoformat(),
                },
            )
    
    def get_app(self) -> FastAPI:
        """Get FastAPI application"""
        return self.app


def create_jarvis_server(
    orchestrator: Optional[AgentOrchestrator] = None,
    policy_engine: Optional[PolicyEngine] = None,
    audit_log: Optional[AuditLog] = None,
) -> FastAPI:
    """
    Create JARVIS API server
    
    Args:
        orchestrator: AgentOrchestrator instance
        policy_engine: PolicyEngine instance
        audit_log: AuditLog instance
        
    Returns:
        FastAPI application
    """
    server = JARVISServer(orchestrator, policy_engine, audit_log)
    return server.get_app()

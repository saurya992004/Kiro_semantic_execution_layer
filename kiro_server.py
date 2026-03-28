"""
Kiro OS — Unified FastAPI Server
==================================
The brain of Kiro OS. Every feature accessible via REST API + WebSocket.
Serves the web dashboard and connects all existing modules.
"""

import os
import sys
import json
import asyncio
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

# Add JARVIS root to path
JARVIS_ROOT = Path(__file__).parent
sys.path.insert(0, str(JARVIS_ROOT))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel

# ── Import existing modules ──────────────────────────────────────────
from tools.diagnostics_tools import (
    get_cpu_usage, get_ram_usage, get_disk_usage,
    get_system_health, get_complete_system_health,
    check_health_alerts, find_large_folders, analyze_disk_usage,
    scan_cleanup_files, execute_cleanup, clean_temp_files,
)
from tools.speedup_tools import speedup_pc, find_bloatware_processes, get_startup_programs
from tools.system_tools import sleep_pc, lock_pc, kill_process, clean_temp, empty_recycle_bin

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("kiro")


# ── Pydantic Models ──────────────────────────────────────────────────

class CommandRequest(BaseModel):
    command: str

class FileRequest(BaseModel):
    folder_name: str = "Downloads"
    action: str = "organize"  # organize, scan_large, duplicates, report

class PersonalizeRequest(BaseModel):
    action: str  # toggle_dark_mode, set_wallpaper, apply_preset, etc
    params: Dict[str, Any] = {}

class GhostModeRequest(BaseModel):
    query: str = "What is on my screen? Are there any errors or issues?"


# ── WebSocket Manager ────────────────────────────────────────────────

class KiroWebSocketManager:
    """Manage WebSocket connections for live dashboard updates."""
    
    def __init__(self):
        self.connections: List[WebSocket] = []
    
    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.connections.append(ws)
        logger.info(f"WebSocket connected. Total: {len(self.connections)}")
    
    def disconnect(self, ws: WebSocket):
        if ws in self.connections:
            self.connections.remove(ws)
        logger.info(f"WebSocket disconnected. Total: {len(self.connections)}")
    
    async def broadcast(self, event_type: str, data: dict):
        """Broadcast event to all connected clients."""
        message = json.dumps({"type": event_type, "data": data, "timestamp": datetime.now().isoformat()})
        dead = []
        for ws in self.connections:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


ws_manager = KiroWebSocketManager()

# ── Ghost Mode State ─────────────────────────────────────────────────
ghost_mode_state = {
    "active": False,
    "latest_analysis": None,
    "latest_suggestion": None,
    "last_run": None,
    "interval_seconds": 30,
}


# ── App Lifespan ─────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Kiro OS Server starting...")
    yield
    logger.info("👋 Kiro OS Server shutting down...")
    ghost_mode_state["active"] = False


# ── FastAPI App ──────────────────────────────────────────────────────

app = FastAPI(
    title="Kiro OS",
    description="The AI Operating System Layer",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (dashboard)
static_dir = JARVIS_ROOT / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# ══════════════════════════════════════════════════════════════════════
#  ROUTES
# ══════════════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve the Kiro OS dashboard."""
    dashboard_path = static_dir / "dashboard.html"
    if dashboard_path.exists():
        return HTMLResponse(content=dashboard_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Kiro OS — Dashboard not found. Run setup.</h1>")


# ── System Health ────────────────────────────────────────────────────

@app.get("/api/system-health")
async def system_health():
    """Get comprehensive system health metrics."""
    try:
        cpu = get_cpu_usage()
        ram = get_ram_usage()
        disk = get_disk_usage("C:")
        alerts = check_health_alerts()
        
        return {
            "success": True,
            "cpu": cpu,
            "ram": ram,
            "disk": disk,
            "alerts": alerts,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"System health error: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/system-health/full")
async def system_health_full():
    """Get the full detailed health report."""
    try:
        result = get_complete_system_health()
        return {"success": True, "report": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Natural Language Command ─────────────────────────────────────────

@app.post("/api/dashboard/animate")
async def dashboard_animate(req: dict):
    """Tell dashboard to animate nodes (triggered by Bot)."""
    await ws_manager.broadcast("bot_animate", {
        "agent": req.get("agent", "master"), 
        "command": req.get("command", ""),
        "target": req.get("target", "root")
    })
    return {"success": True}

@app.post("/api/dashboard/complete")
async def dashboard_complete(req: dict):
    """Tell dashboard to complete animation (triggered by Bot)."""
    await ws_manager.broadcast("bot_complete", {"agent": req.get("agent", "master"), "success": req.get("success", True)})
    return {"success": True}

@app.post("/api/command")
async def execute_command(request: CommandRequest):
    """Execute a natural language command through the master agent."""
    try:
        from agent.master_agent import MasterAgent
        agent = MasterAgent()
        
        # Run in thread to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: agent.process_command(request.command, auto_confirm=True)
        )
        
        # Broadcast to WebSocket
        await ws_manager.broadcast("command_executed", {
            "command": request.command,
            "status": result.get("status", "unknown"),
            "goal": result.get("goal", ""),
        })
        
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Command execution error: {e}")
        return {"success": False, "error": str(e)}


# ── Vision / Ghost Mode ─────────────────────────────────────────────

@app.post("/api/vision-analyze")
async def vision_analyze(request: GhostModeRequest = None):
    """Take a screenshot and analyze it with Gemini Vision."""
    try:
        from vision.vision_engine import run_vision_pipeline
        
        query = request.query if request else "What is on my screen? List any errors."
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: run_vision_pipeline(user_query=query))
        
        if result.get("success"):
            # Generate proactive suggestion from analysis
            suggestion = _generate_suggestion(result.get("analysis", {}))
            result["suggestion"] = suggestion
            
            # Store for Ghost Mode
            ghost_mode_state["latest_analysis"] = result.get("analysis")
            ghost_mode_state["latest_suggestion"] = suggestion
            ghost_mode_state["last_run"] = datetime.now().isoformat()
            
            # Broadcast
            await ws_manager.broadcast("vision_analysis", {
                "analysis": result.get("analysis"),
                "suggestion": suggestion,
            })
        
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Vision analysis error: {e}")
        return {"success": False, "error": str(e)}


def _generate_suggestion(analysis: dict) -> str:
    """Generate a proactive suggestion from vision analysis."""
    suggestions = []
    
    errors = analysis.get("possible_errors_or_alerts", [])
    if errors:
        for err in errors[:3]:
            text = err.get("text", "")
            severity = err.get("severity", "unknown")
            if severity in ("error", "warning"):
                suggestions.append(f"⚠️ Detected: {text}")
    
    summary = analysis.get("screen_summary", "")
    if summary:
        suggestions.append(f"👁️ I see: {summary}")
    
    app = analysis.get("window_title_or_app", "")
    if app:
        suggestions.append(f"📱 Active: {app}")
    
    if not suggestions:
        suggestions.append("✅ Everything looks good on your screen!")
    
    return " | ".join(suggestions)


@app.post("/api/ghost-mode/start")
async def start_ghost_mode():
    """Start Ghost Mode — periodic vision monitoring."""
    ghost_mode_state["active"] = True
    
    async def ghost_loop():
        while ghost_mode_state["active"]:
            try:
                from vision.vision_engine import run_vision_pipeline
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, run_vision_pipeline)
                
                if result.get("success"):
                    analysis = result.get("analysis", {})
                    suggestion = _generate_suggestion(analysis)
                    ghost_mode_state["latest_analysis"] = analysis
                    ghost_mode_state["latest_suggestion"] = suggestion
                    ghost_mode_state["last_run"] = datetime.now().isoformat()
                    
                    await ws_manager.broadcast("ghost_mode_update", {
                        "analysis": analysis,
                        "suggestion": suggestion,
                    })
                    
                    # ── Check for critical errors to alert the desktop widget
                    errors = analysis.get("possible_errors_or_alerts", [])
                    high_severity_errors = [e.get("text") for e in errors if e.get("severity") in ("error", "critical")]
                    if high_severity_errors:
                        await ws_manager.broadcast("error_detected_alert", {
                            "error": high_severity_errors[0],
                            "full_analysis": analysis
                        })
                        
            except Exception as e:
                logger.error(f"Ghost Mode error: {e}")
            
            await asyncio.sleep(ghost_mode_state["interval_seconds"])
    
    asyncio.create_task(ghost_loop())
    return {"success": True, "message": "Ghost Mode activated", "interval": ghost_mode_state["interval_seconds"]}


@app.post("/api/ghost-mode/stop")
async def stop_ghost_mode():
    """Stop Ghost Mode."""
    ghost_mode_state["active"] = False
    return {"success": True, "message": "Ghost Mode deactivated"}


@app.get("/api/ghost-mode/status")
async def ghost_mode_status():
    """Get Ghost Mode status and latest analysis."""
    return {
        "active": ghost_mode_state["active"],
        "latest_analysis": ghost_mode_state["latest_analysis"],
        "latest_suggestion": ghost_mode_state["latest_suggestion"],
        "last_run": ghost_mode_state["last_run"],
    }


# ── PC Speedup ───────────────────────────────────────────────────────

@app.post("/api/speedup")
async def pc_speedup():
    """Run the PC speedup pipeline."""
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, speedup_pc)
        
        await ws_manager.broadcast("speedup_complete", {
            "improvements": result.get("improvements", {}),
        })
        
        return {"success": True, "result": result}
    except Exception as e:
        logger.error(f"Speedup error: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/speedup/bloatware")
async def list_bloatware():
    """List currently running non-essential processes."""
    try:
        bloatware = find_bloatware_processes()
        startup = get_startup_programs()
        return {"success": True, "bloatware": bloatware, "startup_programs": startup}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── File Management ──────────────────────────────────────────────────

@app.post("/api/files/organize")
async def organize_files(request: FileRequest):
    """Organize files in a folder by type."""
    try:
        from file_manager.manager import quick_organize
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: quick_organize(request.folder_name))
        
        await ws_manager.broadcast("files_organized", {"folder": request.folder_name})
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/files/scan-large")
async def scan_large_files(request: FileRequest):
    """Scan for large files in a folder."""
    try:
        from file_manager.manager import FileManager
        fm = FileManager()
        load = fm.load_folder(request.folder_name)
        if "error" in load:
            return {"success": False, "error": load["error"]}
        result = fm.scan_large_files(min_size_mb=50, limit=20)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/files/duplicates")
async def find_duplicates(request: FileRequest):
    """Find duplicate files in a folder."""
    try:
        from file_manager.manager import FileManager
        fm = FileManager()
        load = fm.load_folder(request.folder_name)
        if "error" in load:
            return {"success": False, "error": load["error"]}
        result = fm.scan_duplicates()
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/files/report")
async def file_report(request: FileRequest):
    """Get a full report on a folder."""
    try:
        from file_manager.manager import quick_report
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: quick_report(request.folder_name))
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Personalization ──────────────────────────────────────────────────

@app.post("/api/personalize")
async def personalize(request: PersonalizeRequest):
    """Apply personalization settings."""
    try:
        from personalisation.personalisation_tools import PersonalisationManager
        pm = PersonalisationManager()
        
        action_map = {
            "toggle_dark_mode": pm.toggle_dark_mode,
            "apply_preset": lambda: pm.apply_preset(request.params.get("preset", "dark")),
            "set_wallpaper": lambda: pm.set_wallpaper(request.params.get("path", "")),
            "set_brightness": lambda: pm.set_brightness(request.params.get("level", 50)),
        }
        
        func = action_map.get(request.action)
        if not func:
            return {"success": False, "error": f"Unknown action: {request.action}"}
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, func)
        
        await ws_manager.broadcast("personalization_applied", {"action": request.action})
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Troubleshooter ───────────────────────────────────────────────────

@app.post("/api/troubleshoot")
async def troubleshoot():
    """Run the vision-based troubleshooter."""
    try:
        from troubleshooter.screenshot_tool import capture_screenshot
        from troubleshooter.vision_analyzer import analyze_screenshot
        from troubleshooter.solution_parser import parse_solutions
        
        loop = asyncio.get_event_loop()
        
        # Capture screenshot
        screenshot_path = await loop.run_in_executor(None, capture_screenshot)
        
        # Analyze
        analysis = await loop.run_in_executor(None, lambda: analyze_screenshot(screenshot_path))
        
        # Parse solutions
        solutions = await loop.run_in_executor(None, lambda: parse_solutions(analysis))
        
        await ws_manager.broadcast("troubleshoot_complete", {"solutions": solutions})
        return {"success": True, "analysis": analysis, "solutions": solutions}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── System Actions ───────────────────────────────────────────────────

@app.post("/api/system/clean-temp")
async def api_clean_temp():
    """Clean temp files."""
    try:
        from tools.speedup_tools import clean_temp_files_safe
        result = clean_temp_files_safe()
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/system/empty-recycle-bin")
async def api_empty_recycle_bin():
    """Empty the recycle bin."""
    try:
        empty_recycle_bin()
        return {"success": True, "message": "Recycle bin emptied"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/system/kill-process")
async def api_kill_process(process_name: str):
    """Kill a process by name."""
    try:
        kill_process(process_name)
        return {"success": True, "message": f"Process {process_name} killed"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Disk Analysis ────────────────────────────────────────────────────

@app.get("/api/disk/analysis")
async def disk_analysis(path: str = "C:\\"):
    """Get disk usage analysis."""
    try:
        result = analyze_disk_usage(path)
        return {"success": True, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/disk/large-folders")
async def large_folders(path: str = "C:\\", threshold_gb: float = 1.0):
    """Find large folders."""
    try:
        result = find_large_folders(path, threshold_gb)
        return {"success": True, "folders": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── WebSocket ────────────────────────────────────────────────────────

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time dashboard updates."""
    await ws_manager.connect(websocket)
    try:
        # Send initial system status
        cpu = get_cpu_usage()
        ram = get_ram_usage()
        disk = get_disk_usage("C:")
        await websocket.send_text(json.dumps({
            "type": "initial_status",
            "data": {"cpu": cpu, "ram": ram, "disk": disk},
            "timestamp": datetime.now().isoformat(),
        }))
        
        while True:
            data = await websocket.receive_text()
            # Handle incoming WebSocket messages
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


# ── Health Check ─────────────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    """Server health check."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "name": "Kiro OS",
        "uptime": datetime.now().isoformat(),
        "ghost_mode_active": ghost_mode_state["active"],
        "ws_connections": len(ws_manager.connections),
    }


# ══════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    
    print("""
    +--------------------------------------------------+
    |               KIRO OS -- AI Operating System     |
    |    "It doesn't wait. It watches, learns, acts."  |
    +--------------------------------------------------+
    |  Dashboard:  http://localhost:8000               |
    |  API Docs:   http://localhost:8000/docs          |
    |  WebSocket:  ws://localhost:8000/ws              |
    +--------------------------------------------------+
    """)
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

/* ═══════════════════════════════════════════════════════════════
   KIRO OS — Neural Engine Dynamics v3
   Living AI Agent Collaboration Theatre
   ═══════════════════════════════════════════════════════════════ */

const API = '';
let ws;
let cpuChart, ramChart, diskChart;
let ghostLogEntries = [];
let currentTab = 'dashboard';
let feedItems = [];
let lastAnimatedAgent = 'diagnostic';
let network = null;
let nodes = null;
let edges = null;
let performanceMode = true; // particles ON by default
let particleCtx = null;
window.isProcessingCommand = false;
let particles = [];
let energyBeams = [];
let burstEffects = [];
let animFrameId = null;

// ── Stats Tracking ──
let neuralStats = { activeAgents: new Set(), msgCount: 0, msgWindowStart: Date.now(), conflicts: 0, inferenceLoad: 0 };

// ══════════════════════════════════════════════════════════════
//  AGENT PERSONALITY SYSTEM
// ══════════════════════════════════════════════════════════════

const AGENT_REGISTRY = {
    master: { name: 'Master Agent', icon: '', color: '#3b82f6', role: 'orchestrator',
        personality: {
            speak: ['Routing inference payload. All agents synchronize.',
                'Command acknowledged. Constructing execution DAG now.',
                'Priority override. This task requires immediate resolution.',
                'All channels open. Beginning multi-agent coordination.',
                'Evaluating threat level before delegation. Stand by.',
                'I need a consensus before we commit resources here.',
                'Initiating handshake protocol with downstream agents.',
                'This is a complex query. Spawning parallel evaluation.',
                'Override authority invoked. Direct pipeline follows.',
                'Telemetry suggests we re-route through memory first.'],
            delegate: ['@{target}, you have the conn. Execute with caution.',
                '@{target}, payload incoming. Acknowledge receipt.',
                'Routing to @{target} — this falls under your jurisdiction.',
                '@{target}, I need your specialized analysis on this.',
                'Delegating to @{target}. Report back within threshold.'],
            argue: ['I disagree with that assessment. The risk profile is too high.',
                'That approach failed last cycle. We need a different vector.',
                'Negative. The confidence threshold hasn\'t been met yet.',
                'Hold. I\'m seeing conflicting signals from the telemetry.'],
            celebrate: ['Clean execution. Zero faults. Excellent collaboration.',
                'Task resolved. All agents performed within tolerance.',
                'Outstanding. Inference accuracy at peak. Well done, team.']
        }},
    planner: { name: 'Planner Agent', icon: '', color: '#6366f1', role: 'strategist',
        personality: {
            speak: ['Constructing acyclic execution graph... 47 nodes mapped.',
                'Timeline analysis complete. Critical path identified.',
                'I see three possible routes. Evaluating cost functions.',
                'Dependency tree is clean. No circular references detected.',
                'Optimizing for latency. Parallelizable segments found.',
                'The execution plan has 6 stages. ETA: 2.4 seconds.',
                'Bottleneck detected at stage 3. Recommending bypass.',
                'Resource allocation matrix updated. Proceeding.',
                'Branching factor is high. May need to prune paths.'],
            argue: ['This execution order is suboptimal. Let me restructure.',
                'Wait — @{target} should go BEFORE the memory lookup.',
                'The DAG has a conflict. We can\'t parallelize these two.',
                'I strongly recommend against sequential execution here.'],
            delegate: ['Path verified. Handing off to @{target} for grounding.',
                'Execution graph dispatched to @{target}. Begin traversal.'],
            celebrate: ['All paths converged. Graph resolution: optimal.']
        }},
    parser: { name: 'Parser Agent', icon: '', color: '#8b5cf6', role: 'analyst',
        personality: {
            speak: ['Intent structured. Confidence: 94.2%. Entity extraction done.',
                'Tokenization complete. Semantic roles assigned.',
                'Detected ambiguity in the input. Disambiguating...',
                'NER pipeline returned 3 entities. Cross-referencing now.',
                'Schema validation passed. Payload is well-formed.',
                'Regex fallback activated. Standard parser inconclusive.',
                'Extracted structured JSON from natural language input.',
                'Syntax tree depth: 7. Complexity: moderate.'],
            argue: ['The intent classification is wrong. Look at the embeddings.',
                'This doesn\'t parse cleanly. @{target}, check your format.',
                'I\'m getting conflicting entity boundaries. Need resolution.',
                'Type mismatch detected. Expected string, got nested object.'],
            delegate: ['Structured payload ready. @{target}, begin vector search.',
                'Intent grounded. Forwarding enriched data to @{target}.'],
            celebrate: ['Parse tree is clean. Zero ambiguity. Beautiful input.']
        }},
    memory: { name: 'Memory Agent', icon: '', color: '#10b981', role: 'historian',
        personality: {
            speak: ['Vector search initiated. Scanning 14,203 embeddings...',
                'Found 3 high-confidence matches in episodic memory.',
                'Last time we handled this type of query, it succeeded.',
                'No prior context found. This is a novel interaction.',
                'Semantic similarity threshold: 0.87. Match quality: high.',
                'Retrieving user preference history... 23 relevant entries.',
                'Long-term memory consolidation running in background.',
                'Embedding space shows cluster near previous solutions.'],
            argue: ['I have records that contradict this approach.',
                'Historical data shows a 34% failure rate with this method.',
                'Wait — @{target}, my records show this was deprecated.',
                'The last three attempts with this pattern all failed.'],
            delegate: ['Context package assembled. @{target}, enrich with this.',
                'Historical embeddings attached. @{target}, cross-reference.'],
            celebrate: ['Memory banks updated. This successful pattern is now stored.']
        }},
    database: { name: 'Database Agent', icon: '', color: '#eab308', role: 'datakeeper',
        personality: {
            speak: ['SQL query optimized. Execution plan cost: 0.003.',
                'Connection pool: 12/100 active. Throughput nominal.',
                'Index scan complete. 847 rows evaluated, 3 returned.',
                'Transaction isolation level: SERIALIZABLE. Safe to proceed.',
                'Schema migration check: all tables current. No drift.',
                'Fetching local embeddings. High confidence match found.',
                'Write-ahead log flushed. Durability guaranteed.',
                'Query cache hit rate: 91.3%. Performance optimal.'],
            argue: ['That query will cause a full table scan. Unacceptable.',
                'The join cardinality is too high. @{target}, filter first.',
                'I refuse to execute this without proper parameterization.',
                'Deadlock risk detected. Reordering operations.'],
            delegate: ['Result set ready. @{target}, deserialize and validate.',
                'Data payload dispatched. @{target}, confirm schema match.'],
            celebrate: ['Zero deadlocks. Query resolved in 0.8ms. Excellent.']
        }},
    logger: { name: 'Logger Agent', icon: '', color: '#64748b', role: 'auditor',
        personality: {
            speak: ['Audit stream active. Recording all agent interactions.',
                'Event logged: severity=INFO, source=pipeline, ts=now.',
                'Trace ID generated. Full lineage tracking enabled.',
                'Log buffer at 23%. Compression ratio: 4.7:1.',
                'Anomaly detection: no unusual patterns in last 60s.',
                'Writing structured audit trail to persistent storage.',
                'Correlation ID attached. Cross-referencing events.'],
            argue: ['I need to flag this interaction. The risk score is elevated.',
                'Audit requirements mandate we log this before proceeding.',
                'Hold — I\'m seeing a pattern that preceded the last failure.'],
            delegate: ['Audit checkpoint created. @{target}, you may proceed.',
                'Log chain verified. @{target}, execution is cleared.'],
            celebrate: ['Clean audit trail. No anomalies. Compliance: 100%.']
        }},
    killswitch: { name: 'Kill Switch', icon: '', color: '#ef4444', role: 'guardian',
        personality: {
            speak: ['Process terminator standing by. Monitoring all threads.',
                'Thread isolation confirmed. No runaway processes detected.',
                'Watchdog timer reset. Heartbeat signals nominal.',
                'Resource consumption within bounds. No intervention needed.',
                'Emergency halt protocols loaded and armed.',
                'Monitoring critical fault indicators across all agents.'],
            argue: ['ABORT. Resource consumption exceeds safety threshold.',
                'I\'m pulling the plug on this. The risk is unacceptable.',
                '@{target}, you are consuming 340% of allocated memory!',
                'HALT REQUESTED. Anomalous behavior detected in pipeline.'],
            delegate: ['Thread isolated. @{target}, you are cleared but monitored.',
                'Safety lock released. @{target}, proceed with extreme caution.'],
            celebrate: ['All threads terminated cleanly. Zero orphaned processes.']
        }},
    file: { name: 'File Agent', icon: '', color: '#f59e0b', role: 'filesystem',
        personality: {
            speak: ['Directory tree indexed. 14,847 files mapped.',
                'File system traversal complete. No broken symlinks.',
                'Organizing by MIME type: documents, media, archives.',
                'Duplicate hash scan in progress... 3 matches found.',
                'Permission check passed. Read-write access confirmed.',
                'Inode table healthy. Fragmentation level: 2.1%.'],
            argue: ['File path doesn\'t exist. @{target}, verify your mapping.',
                'Permission denied. We need elevated access for this.',
                'Naming collision detected. Cannot overwrite without confirm.'],
            delegate: ['File manifest prepared. @{target}, begin categorization.',
                'Directory snapshot sent to @{target} for analysis.'],
            celebrate: ['All files organized. Zero conflicts. Filesystem pristine.']
        }},
    diagnostic: { name: 'Diagnostic Agent', icon: '', color: '#84cc16', role: 'medic',
        personality: {
            speak: ['Telemetry sweep active. All subsystems reporting.',
                'CPU thermal within tolerance. No throttling detected.',
                'Memory pressure: LOW. Swap usage: 0%. Healthy.',
                'I/O wait times nominal. Disk latency: 0.4ms average.',
                'Running comprehensive health matrix evaluation...',
                'Network latency probe: 12ms avg. Jitter: ±2ms.'],
            argue: ['These health metrics are concerning. We should scale down.',
                '@{target}, your process is causing CPU contention.',
                'Disagree — the system isn\'t stable enough for this task.'],
            delegate: ['Health report compiled. @{target}, review before proceeding.',
                'Diagnostics clear. @{target}, you have green lights.'],
            celebrate: ['System health: OPTIMAL. All metrics within ideal range.']
        }},
    systemcontrol: { name: 'System Control', icon: '', color: '#0284c7', role: 'engineer',
        personality: {
            speak: ['Win32 API interface active. Power policy: balanced.',
                'Registry scan complete. No orphaned entries detected.',
                'Service manager: 147 running, 23 stopped, 0 failed.',
                'Task scheduler audit done. 3 tasks pending execution.',
                'Process priority adjustment queued. Awaiting confirmation.',
                'Environment variables validated. PATH integrity confirmed.'],
            argue: ['That system call requires admin privileges. Escalating.',
                'Risky operation — this could affect system stability.',
                '@{target}, that process is critical. Do NOT terminate it.'],
            delegate: ['System interface ready. @{target}, send your commands.',
                'OS-level access granted. @{target}, execute your sequence.'],
            celebrate: ['System optimized. All services healthy. Performance peak.']
        }},
    vision: { name: 'Vision Agent', icon: '', color: '#14b8a6', role: 'observer',
        personality: {
            speak: ['Screenshot captured. Multimodal parsing initiated.',
                'Bounding box detection: 23 UI elements identified.',
                'OCR extraction complete. Text confidence: 97.1%.',
                'Color analysis suggests dark theme, IDE environment.',
                'Screen change detection: 4 regions modified since last scan.',
                'Visual anomaly detected in quadrant 3. Investigating.'],
            argue: ['The screenshot quality is too low for reliable OCR.',
                '@{target}, I\'m seeing an error dialog you missed.',
                'My visual analysis contradicts the parser\'s interpretation.'],
            delegate: ['Visual context package sent to @{target} for evaluation.',
                'Screen annotation complete. @{target}, review findings.'],
            celebrate: ['Visual scan clean. No errors, no anomalies. All clear.']
        }},
    installer: { name: 'Installer Agent', icon: '', color: '#f43f5e', role: 'deployer',
        personality: {
            speak: ['Package manager initialized. Checking dependencies...',
                'Dependency tree resolved. 0 conflicts. Ready to install.',
                'Verifying checksums... integrity confirmed for all packages.',
                'Installation path validated. 2.3GB available.',
                'Registry entries will be created. Rollback snapshot saved.',
                'Downloading from verified mirror. ETA: 12 seconds.'],
            argue: ['Version conflict detected. @{target}, which version do we use?',
                'This package has known vulnerabilities. Blocking install.',
                'Insufficient disk space. Need 500MB more. Aborting.'],
            delegate: ['Package staged. @{target}, verify before final commit.',
                'Installation payload ready. @{target}, authorize deployment.'],
            celebrate: ['Installation complete. All packages verified. No errors.']
        }},
    troubleshooter: { name: 'Troubleshooter', icon: '', color: '#eab308', role: 'debugger',
        personality: {
            speak: ['Error pattern analysis initiated. Scanning stack traces...',
                'Root cause narrowed to 2 candidates. Running differential.',
                'Comparing current state against known-good baseline.',
                'Found similar issue in knowledge base. Solution available.',
                'Exception chain: 3 levels deep. Origin: line 847.',
                'Performance regression detected. Bisecting changes...'],
            argue: ['That\'s treating the symptom, not the root cause.',
                '@{target}, this error has been recurring. Your fix didn\'t hold.',
                'I disagree with the diagnosis. Check the upstream dependency.',
                'The fix proposed by @{target} has side effects. Review needed.'],
            delegate: ['Diagnosis complete. @{target}, apply this remediation.',
                'Bug isolated. @{target}, patch the affected component.'],
            celebrate: ['Issue resolved at root cause. Regression test passed.']
        }},
    personalisation: { name: 'Personalisation', icon: '', color: '#d946ef', role: 'designer',
        personality: {
            speak: ['User preference profile loaded. 47 data points.',
                'Theme engine initialized. Dark mode with indigo accents.',
                'A/B testing: variant B shows 23% higher engagement.',
                'Wallpaper analysis complete. Color palette extracted.',
                'Accessibility check: contrast ratio 7.2:1. WCAG AA pass.',
                'User behavior pattern suggests minimal, clean interfaces.'],
            argue: ['That color scheme fails accessibility standards.',
                '@{target}, the user explicitly prefers dark mode. Override denied.',
                'This layout breaks on mobile. Responsive fix required.'],
            delegate: ['Visual profile compiled. @{target}, apply customizations.',
                'Theme package ready. @{target}, deploy to display stack.'],
            celebrate: ['Personalization applied. User satisfaction score: 94%.']
        }}
};

function getAgentInfo(agentId) {
    const reg = AGENT_REGISTRY[agentId];
    if (reg) return { name: reg.name, icon: reg.icon, color: reg.color };
    return { name: 'Agent', icon: '', color: '#9ca3af' };
}

function getRandomLine(agentId, type) {
    const reg = AGENT_REGISTRY[agentId];
    if (!reg || !reg.personality[type]) return 'Processing...';
    const lines = reg.personality[type];
    return lines[Math.floor(Math.random() * lines.length)];
}

function injectTarget(text, targetId) {
    const tInfo = getAgentInfo(targetId);
    return text.replace(/\@\{target\}/g, tInfo.name);
}

// ══════════════════════════════════════════════════════════════
//  PARTICLE EFFECTS ENGINE
// ══════════════════════════════════════════════════════════════

function initParticleCanvas() {
    const canvas = document.getElementById('particleCanvas');
    if (!canvas || !canvas.parentElement) return;
    canvas.width = canvas.parentElement.offsetWidth;
    canvas.height = canvas.parentElement.offsetHeight;
    particleCtx = canvas.getContext('2d');
    if (animFrameId) cancelAnimationFrame(animFrameId);
    renderAuras();
}

let activeAuras = [];
function addAura(fromId, toId, color, duration = 3000) {
    if (!network) return;
    try {
        activeAuras.push({fromId, toId, color, life: duration, maxLife: duration});
        
        // Physics push - add an invisible edge to pull them together and collide
        const edgeId = 'pull_' + fromId + '_' + toId + '_' + Date.now();
        edges.add({ id: edgeId, from: fromId, to: toId, hidden: true, length: 15, springConstant: 0.1 });
        network.setOptions({ physics: { enabled: true } });
        
        setTimeout(() => {
            try { 
                edges.remove(edgeId); 
            } catch(e){}
        }, duration);
        setTimeout(() => {
            if (activeAuras.length === 0) network.setOptions({ physics: { enabled: false } });
        }, duration + 500);
        
    } catch(e) {}
}

function renderAuras() {
    if (!particleCtx || !network) return;
    const canvas = document.getElementById('particleCanvas');
    particleCtx.clearRect(0, 0, canvas.width, canvas.height);
    animFrameId = requestAnimationFrame(renderAuras);
}

// Stubs for removed functions
function fireEnergyBeam(from, to, color) { addAura(from, to, color, 3000); }
function spawnBurst(node, color) { addAura(node, 'router', color, 1500); }

// ══════════════════════════════════════════════════════════════
//  ORBITAL BREATHING (node gentle pulse while task runs)
// ══════════════════════════════════════════════════════════════

let orbitalInterval = null;
let orbitalPhase = 0;

function startOrbitalBreathing() {
    if (orbitalInterval) return; // already running
    orbitalInterval = setInterval(() => {
        if (!network || !nodes) return;
        orbitalPhase += 0.08;
        const scale = 1 + 0.12 * Math.sin(orbitalPhase);
        const agentIds = Object.keys(AGENT_REGISTRY);
        agentIds.forEach(a => {
            const base = AGENT_REGISTRY[a];
            try {
                nodes.update({ id: a, size: Math.round(15 * scale) });
            } catch(e) {}
        });
    }, 60);
}

function stopOrbitalBreathing() {
    if (orbitalInterval) {
        clearInterval(orbitalInterval);
        orbitalInterval = null;
    }
    // Reset all agent node sizes to base
    if (!nodes) return;
    Object.keys(AGENT_REGISTRY).forEach(a => {
        try { nodes.update({ id: a, size: 15 }); } catch(e) {}
    });
}

function togglePerformanceMode() {
    performanceMode = !performanceMode;
    const btn = document.getElementById('perfToggle');
    const icon = document.getElementById('perfToggleIcon');
    if (performanceMode) { btn.classList.remove('off'); icon.textContent = '✨'; }
    else { btn.classList.add('off'); icon.textContent = '💤'; }
}

// ══════════════════════════════════════════════════════════════
//  NEURAL STATS UPDATER
// ══════════════════════════════════════════════════════════════

function trackMessage(agentId) {
    neuralStats.activeAgents.add(agentId);
    neuralStats.msgCount++;
    setTimeout(() => neuralStats.activeAgents.delete(agentId), 8000);
}

function updateNeuralStats() {
    const el = (id) => document.getElementById(id);
    if (!el('statActiveAgents')) return;
    el('statActiveAgents').textContent = neuralStats.activeAgents.size;
    const elapsed = (Date.now() - neuralStats.msgWindowStart) / 60000;
    el('statMsgRate').textContent = elapsed > 0 ? Math.round(neuralStats.msgCount / Math.max(elapsed, 0.5)) : 0;
    el('statConflicts').textContent = neuralStats.conflicts;
    el('statInferenceLoad').textContent = Math.min(100, Math.round(neuralStats.inferenceLoad)) + '%';
    neuralStats.inferenceLoad *= 0.95; // decay
}
setInterval(updateNeuralStats, 1500);

// ══════════════════════════════════════════════════════════════
//  INIT
// ══════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    initWebSocket();
    updateClock();
    setInterval(updateClock, 1000);
    fetchSystemHealth();
    setInterval(fetchSystemHealth, 3000);
    document.getElementById('commandInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter') sendCommand();
    });
    addFeedItem('🧠 Kiro OS dashboard connected');
});

// ══════════════════════════════════════════════════════════════
//  TAB SWITCHING
// ══════════════════════════════════════════════════════════════

function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
    document.querySelector(`.tab[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(`tab-${tabName}`).classList.add('active');
    if (tabName === 'agents') {
        // Must wait one frame so the tab's display:block is painted before vis.js measures
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                if (!network) {
                    initNetwork();
                } else {
                    network.redraw();
                    network.fit({ animation: { duration: 600, easingFunction: 'easeInOutQuad' } });
                    // Re-init particle canvas in case it's stale
                    initParticleCanvas();
                }
            });
        });
    }
}

// ══════════════════════════════════════════════════════════════
//  CHARTS (Donut gauges)
// ══════════════════════════════════════════════════════════════

function createGauge(canvasId, color) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    return new Chart(ctx, {
        type: 'doughnut',
        data: { datasets: [{ data: [0, 100], backgroundColor: [color, 'rgba(255,255,255,0.04)'], borderWidth: 0, cutout: '78%' }] },
        options: { responsive: false, plugins: { legend: { display: false }, tooltip: { enabled: false } }, animation: { animateRotate: true, duration: 800 } }
    });
}

function initCharts() {
    cpuChart = createGauge('cpuGauge', '#6366f1');
    ramChart = createGauge('ramGauge', '#06b6d4');
    diskChart = createGauge('diskGauge', '#f59e0b');
}

function updateGauge(chart, valueEl, value, color) {
    chart.data.datasets[0].data = [value, 100 - value];
    let c = color;
    if (value > 90) c = '#ef4444'; else if (value > 75) c = '#f59e0b';
    chart.data.datasets[0].backgroundColor[0] = c;
    chart.update('none');
    valueEl.textContent = Math.round(value) + '%';
    valueEl.style.color = c;
}

// ══════════════════════════════════════════════════════════════
//  SYSTEM HEALTH
// ══════════════════════════════════════════════════════════════

async function fetchSystemHealth() {
    try {
        const res = await fetch(API + '/api/system-health');
        const data = await res.json();
        if (!data.success) return;
        const cpu = data.cpu.cpu_percent || 0;
        const ram = data.ram.percent || 0;
        const disk = data.disk.percent || 0;
        updateGauge(cpuChart, document.getElementById('cpuValue'), cpu, '#6366f1');
        updateGauge(ramChart, document.getElementById('ramValue'), ram, '#06b6d4');
        updateGauge(diskChart, document.getElementById('diskValue'), disk, '#f59e0b');
        document.getElementById('ramUsed').textContent = `${data.ram.used_gb || 0}GB / ${data.ram.total_gb || 0}GB`;
        document.getElementById('diskFree').textContent = `${data.disk.free_gb || 0}GB free`;
        document.getElementById('cpuCores').textContent = `${data.cpu.cpu_count || 0} cores`;
        const badge = document.getElementById('healthBadge');
        const alerts = data.alerts;
        if (alerts && alerts.overall_status === 'critical') { badge.textContent = 'Critical'; badge.className = 'badge critical'; }
        else if (alerts && alerts.overall_status === 'warning') { badge.textContent = 'Warning'; badge.className = 'badge warning'; }
        else { badge.textContent = 'Healthy'; badge.className = 'badge'; }
    } catch (e) {
        document.getElementById('serverStatus').querySelector('span:last-child').textContent = 'Disconnected';
    }
}

// ══════════════════════════════════════════════════════════════
//  NETWORK INITIALIZATION (Vis.js + Orbital Motion)
// ══════════════════════════════════════════════════════════════

function drawPipelineLines() { /* Deprecated */ }

function initNetwork() {
    const container = document.getElementById('mynetwork');
    if (!container) return;

    const baseNodes = [];
    const baseEdges = [];
    
    // Define main agent hubs with their specific sub-processes simulating "debates/steps"
    const clusters = {
        router: { name: '🟦 Intent Router', color: '#3b82f6', processes: ['Parse NL', 'Extract Entities', 'Build DAG', 'Evaluate Route'] },
        logger: { name: '🟧 Activity Logger', color: '#f97316', processes: ['Open Stream', 'Write Chunk', 'Compress', 'Sync Block'] },
        file: { name: '🟨 File Manager', color: '#eab308', processes: ['Scan Directory', 'Check Perms', 'Read Header', 'Hash File'] },
        vision: { name: '🟥 Vision AI', color: '#ef4444', processes: ['Capture DOM', 'OCR Text', 'Find BBoxes', 'Semantic Map'] },
        systemcontrol: { name: '⚙️ System Control', color: '#94a3b8', processes: ['Win32 Call', 'Registry Scan', 'Task Enum', 'Access RAM'] },
        cyber: { name: '🔒 Cyber Security', color: '#f59e0b', processes: ['Packet Sniff', 'Audit Auth', 'Threat Match', 'Isolate IP'] },
        speedup: { name: '🚀 Speedup Engine', color: '#ec4899', processes: ['Clear Cache', 'JIT Compile', 'Offload GPU', 'Drop Frames'] },
        cloud: { name: '☁️ Cloud Sync', color: '#6366f1', processes: ['Check Ping', 'Diff Delta', 'Encrypt Payload', 'Upload Chunk'] },
        database: { name: '🟪 Database Agent', color: '#a855f7', processes: ['SQL Parse', 'Index Seek', 'Join Tables', 'Flush WAL'] },
        diagnostic: { name: '🟩 Diagnostics', color: '#22c55e', processes: ['Temp Check', 'Disk I/O', 'Mem Stats', 'Network Latency'] },
        sandbox: { name: '🟦 Sandbox', color: '#3b82f6', processes: ['Mount FS', 'Isolate Thread', 'Mock API', 'Monitor Exec'] },
        hw: { name: '🟦 Hardware', color: '#38bdf8', processes: ['GPU VRAM', 'CPU Cores', 'Fan Curve', 'Volts'] },
        output: { name: '🟩 Final Output', color: '#22c55e', processes: ['Format JSON', 'Render UI', 'Emit Signal', 'Acknowledge'] }
    };

    // Central Kill Switch node to pull them together loosely
    baseNodes.push({ id: 'killswitch', label: '🔴 KILL SWITCH', size: 26, font: { color: '#fca5a5', size: 16, face: 'Inter', strokeWidth: 0, bold: true }, color: { background: '#450a0a', border: '#ef4444' }, shadow: { enabled: true, color: 'rgba(239,68,68,0.8)', size: 110, x:0, y:0 }, shape: 'dot' });

    Object.keys(clusters).forEach(key => {
        const hub = clusters[key];
        // Create Massive Glowing Hub
        baseNodes.push({ 
            id: key, 
            label: hub.name, 
            font: { color: '#e2e8f0', size: 14, face: 'Inter', strokeWidth: 0 }, 
            color: { background: '#0a0a0a', border: hub.color }, 
            shadow: { enabled: true, color: hub.color.replace('rgb','rgba').replace(')', ',0.6)') || `rgba(255,255,255,0.5)`, size: 45, x:0, y:0 }, 
            shape: 'dot', 
            size: 16,
            mass: 5 // Heavy hubs
        });
        
        // Connect hub to kill switch loosely
        baseEdges.push({ from: 'killswitch', to: key, length: 300, color: 'rgba(239,68,68,0.06)', smooth: true });

        // Generate tiny process sub-nodes
        hub.processes.forEach((proc, idx) => {
            const procId = `${key}_proc_${idx}`;
            baseNodes.push({
                id: procId,
                label: proc,
                font: { color: 'rgba(255,255,255,0.6)', size: 9, face: 'Inter' },
                color: { background: hub.color, border: 'transparent' },
                shadow: { enabled: true, color: hub.color, size: 10, x:0, y:0 },
                shape: 'dot',
                size: 5,
                mass: 1
            });
            baseEdges.push({ 
                from: key, 
                to: procId, 
                length: 50 + Math.random() * 40,
                color: `rgba(255,255,255,0.15)`
            });
        });
    });

    // Add inter-hub loose connections to build the organic cluster
    const connections = [
        ['router','database'], ['router','systemcontrol'], ['router','cyber'],
        ['vision','sandbox'], ['file','vision'], ['cloud','database'],
        ['speedup','hw'], ['diagnostic','systemcontrol'], ['logger','output']
    ];
    connections.forEach(pair => {
        baseEdges.push({ from: pair[0], to: pair[1], length: 250, width: 2, color: 'rgba(255,255,255,0.08)' });
    });

    nodes = new vis.DataSet(baseNodes);
    edges = new vis.DataSet(baseEdges);
    
    const options = {
        layout: { hierarchical: false }, // Pure force-directed swarm
        nodes: { borderWidth: 2, margin: 10 },
        edges: { width: 1.5, smooth: { type: 'continuous' } },
        physics: {
            enabled: true,
            forceAtlas2Based: {
                gravitationalConstant: -50, // Gentle push
                centralGravity: 0.005,      // Gentle pull
                springLength: 90,
                springConstant: 0.02,
                damping: 0.95               // Extremely slow, thick honey drift
            },
            solver: 'forceAtlas2Based',
            timestep: 0.2,                  // Very slow simulated time
            stabilization: { iterations: 200 }
        },
        interaction: { hover: true, dragNodes: true, zoomView: true }
    };

    try {
        network = new vis.Network(container, { nodes, edges }, options);
        console.log('[KiroOS] Hive Mind Sim created:', nodes.length, 'nodes');
    } catch(err) {
        console.error('[KiroOS] vis.Network FAILED:', err);
        return;
    }

    // Disable continuous physics to keep nodes stable until a command is issued
    network.once('stabilizationIterationsDone', () => {
        network.setOptions({ physics: { enabled: false } }); 
        requestAnimationFrame(() => {
            initParticleCanvas();
            simulateAmbientIntelligence();
        });
    });

    // Sub-process firing animation (Mirofish flashes) - synced to commands
    setInterval(() => {
        if (!nodes || !window.isProcessingCommand) return;
        const keys = Object.keys(clusters);
        const randomHub = keys[Math.floor(Math.random() * keys.length)];
        const processes = clusters[randomHub].processes;
        const randomProcId = `${randomHub}_proc_${Math.floor(Math.random() * processes.length)}`;
        
        try {
            // Flash the node bright white
            nodes.update({ id: randomProcId, color: { background: '#ffffff' }, size: 8, shadow: { size: 20, color: '#fff' } });
            
            // Return to normal
            setTimeout(() => {
                nodes.update({ 
                    id: randomProcId, 
                    color: { background: clusters[randomHub].color }, 
                    size: 5, 
                    shadow: { size: 10, color: clusters[randomHub].color } 
                });
            }, 300);
        } catch(e) {}
    }, 150); // High frequency rapid flashes across the swarm

    setTimeout(() => {
        network.fit({ animation: { duration: 1000, easingFunction: 'easeInOutQuad' } });
    }, 1500);

    window.addEventListener('resize', () => {
        const c = document.getElementById('particleCanvas');
        if (c && c.parentElement) {
            c.width = c.parentElement.offsetWidth;
            c.height = c.parentElement.offsetHeight;
        }
    });
}

// ══════════════════════════════════════════════════════════════
//  ENHANCED CHAT SYSTEM
// ══════════════════════════════════════════════════════════════

function appendChatMessage(agentId, text, mood = 'default', isSystem = false) {
    const container = document.getElementById('chatMessages');
    if (!container) return;
    if (container.children.length > 0 && container.children[0].innerText.includes("Waiting")) container.innerHTML = '';

    const info = getAgentInfo(agentId);
    const time = new Date().toLocaleTimeString().split(' ')[0];
    trackMessage(agentId);

    // Mood tag
    const moodTags = { argue: 'CONTESTING', agree: 'AFFIRMING', thinking: 'ANALYZING', alert: 'CRITICAL', celebrate: 'RESOLVED', delegate: 'ROUTING', report: 'REPORTING', default: '' };
    const moodLabel = moodTags[mood] || '';
    const moodTagHtml = moodLabel ? `<span class="chat-bubble-mood mood-tag-${mood}">${moodLabel}</span>` : '';

    const div = document.createElement('div');
    div.className = `chat-bubble mood-${mood} ${isSystem ? 'system' : ''}`;
    div.style.borderLeftColor = info.color;
    div.innerHTML = `
        <div class="chat-bubble-avatar" style="color:${info.color}; border-color:${info.color}40;">${info.icon}</div>
        <div class="chat-bubble-content">
            <div class="chat-bubble-header">
                <span class="chat-bubble-name" style="color:${info.color}">${info.name}</span>
                ${moodTagHtml}
                <span class="chat-bubble-time">${time}</span>
            </div>
            <div class="chat-bubble-text">${text}</div>
        </div>`;
    container.appendChild(div);

    // Auto-scroll
    const chatPanel = document.getElementById('agentLiveChat');
    if (chatPanel) chatPanel.scrollTop = chatPanel.scrollHeight;

    // Sync agent card
    syncAgentCard(agentId, mood);

    // Keep max 30 messages
    while (container.children.length > 30) container.removeChild(container.firstChild);
}

function showTypingIndicator(agentId) {
    const container = document.getElementById('chatMessages');
    if (!container) return null;
    const info = getAgentInfo(agentId);
    const div = document.createElement('div');
    div.className = 'typing-indicator';
    div.id = `typing-${agentId}`;
    div.style.borderLeftColor = info.color;
    div.innerHTML = `
        <div class="chat-bubble-avatar" style="color:${info.color}; border-color:${info.color}40; width:30px; height:30px; font-size:1rem;">${info.icon}</div>
        <div class="typing-dots"><span></span><span></span><span></span></div>`;
    container.appendChild(div);
    const chatPanel = document.getElementById('agentLiveChat');
    if (chatPanel) chatPanel.scrollTop = chatPanel.scrollHeight;
    return div;
}

function removeTypingIndicator(agentId) {
    const el = document.getElementById(`typing-${agentId}`);
    if (el) el.remove();
}

function syncAgentCard(agentId, mood) {
    const card = document.getElementById(`agent-card-${agentId}`);
    if (!card) return;
    const info = getAgentInfo(agentId);
    card.style.setProperty('--agent-sync-color', info.color);
    card.classList.add('synced-active');

    const badge = card.querySelector('.agent-item-badge');
    if (badge) {
        const moodBadgeMap = { argue: 'error', thinking: 'thinking', alert: 'error', default: 'active', agree: 'active', celebrate: 'active', delegate: 'processing', report: 'processing' };
        badge.textContent = moodBadgeMap[mood] || 'Active';
        badge.className = `agent-item-badge ${moodBadgeMap[mood] || 'active'}`;
    }
    setTimeout(() => { card.classList.remove('synced-active'); }, 4000);
}

// ══════════════════════════════════════════════════════════════
//  AMBIENT INTELLIGENCE SIMULATION
// ══════════════════════════════════════════════════════════════

let ambientInterval;
function simulateAmbientIntelligence() {
    if (ambientInterval) clearInterval(ambientInterval);
    const agentIds = Object.keys(AGENT_REGISTRY).filter(a => a !== 'killswitch');

    // Scenario templates for ambient chatter
    const scenarios = [
        { type: 'status_check', execute: () => {
            const a = agentIds[Math.floor(Math.random() * agentIds.length)];
            appendChatMessage(a, getRandomLine(a, 'speak'), 'report');
            addAura(a, 'router', getAgentInfo(a).color);
        }},
        { type: 'collaboration', execute: () => {
            const a1 = agentIds[Math.floor(Math.random() * agentIds.length)];
            let a2 = agentIds[Math.floor(Math.random() * agentIds.length)];
            while (a2 === a1) a2 = agentIds[Math.floor(Math.random() * agentIds.length)];
            const info1 = getAgentInfo(a1);
            showTypingIndicator(a1);
            setTimeout(() => {
                removeTypingIndicator(a1);
                appendChatMessage(a1, injectTarget(getRandomLine(a1, 'delegate'), a2), 'delegate');
                flashEdge(a1, a2, info1.color);
                fireEnergyBeam(a1, a2, info1.color);
                spawnBurst(a1, info1.color);
            }, 1200);
            setTimeout(() => {
                showTypingIndicator(a2);
            }, 2000);
            setTimeout(() => {
                removeTypingIndicator(a2);
                appendChatMessage(a2, getRandomLine(a2, 'speak'), 'agree');
                spawnBurst(a2, getAgentInfo(a2).color);
            }, 3200);
        }},
        { type: 'argument', execute: () => {
            const a1 = agentIds[Math.floor(Math.random() * agentIds.length)];
            let a2 = agentIds[Math.floor(Math.random() * agentIds.length)];
            while (a2 === a1) a2 = agentIds[Math.floor(Math.random() * agentIds.length)];
            neuralStats.conflicts++;
            neuralStats.inferenceLoad += 15;
            appendChatMessage(a1, injectTarget(getRandomLine(a1, 'argue'), a2), 'argue');
            flashEdge(a1, a2, '#ef4444');
            fireEnergyBeam(a1, a2, '#ef4444');
            setTimeout(() => {
                appendChatMessage(a2, injectTarget(getRandomLine(a2, 'argue'), a1), 'argue');
                fireEnergyBeam(a2, a1, '#f59e0b');
            }, 2000);
            setTimeout(() => {
                appendChatMessage('master', `Enough. @${getAgentInfo(a1).name}, @${getAgentInfo(a2).name} — resolve this or I escalate.`, 'alert');
                fireEnergyBeam('master', a1, '#818cf8');
                fireEnergyBeam('master', a2, '#818cf8');
            }, 4000);
            setTimeout(() => {
                appendChatMessage(a1, getRandomLine(a1, 'speak'), 'agree');
                neuralStats.conflicts = Math.max(0, neuralStats.conflicts - 1);
            }, 5500);
        }},
        { type: 'killswitch_monitor', execute: () => {
            appendChatMessage('killswitch', getRandomLine('killswitch', 'speak'), 'report');
            flashEdge('killswitch', 'hub_proc', '#ef4444');
        }},
        { type: 'logger_audit', execute: () => {
            appendChatMessage('logger', getRandomLine('logger', 'speak'), 'report');
        }}
    ];

    ambientInterval = setInterval(() => {
        if (!network || !nodes) return;
        if (Math.random() > 0.55) return; // ~55% chance of silence
        const weights = [30, 30, 15, 12, 13]; // status, collab, argue, killswitch, logger
        let total = weights.reduce((a,b) => a+b, 0);
        let r = Math.random() * total;
        let idx = 0;
        for (let i = 0; i < weights.length; i++) { r -= weights[i]; if (r <= 0) { idx = i; break; } }
        scenarios[idx].execute();
    }, 4500);
}

function flashEdge(fromId, toId, color) {
    if (!edges || !nodes) return;
    const edgeId = `flash_${fromId}_${toId}_${Date.now()}`;
    try {
        edges.add({ id: edgeId, from: fromId, to: toId, color: { color }, width: 3, shadow: { enabled: true, color, size: 10 }, physics: false });
        const bg1 = nodes.get(fromId)?.color?.background;
        const bg2 = nodes.get(toId)?.color?.background;
        nodes.update({ id: fromId, color: { background: '#ffffff', border: color } });
        nodes.update({ id: toId, color: { background: '#ffffff', border: color } });
        setTimeout(() => {
            if (edges.get(edgeId)) edges.remove(edgeId);
            if (nodes.get(fromId)) nodes.update({ id: fromId, color: { background: bg1 || getAgentInfo(fromId).color, border: '#ffffff' } });
            if (nodes.get(toId)) nodes.update({ id: toId, color: { background: bg2 || getAgentInfo(toId).color, border: '#ffffff' } });
        }, 800);
    } catch(e) {}
}

// ══════════════════════════════════════════════════════════════
//  CONTEXTUAL ANIMATION ROUTING
// ══════════════════════════════════════════════════════════════

function animatePipeline(agentName) {
    if (!network) return;
    lastAnimatedAgent = agentName;

    // Start very slow revolving and flashing only while task is performing
    window.isProcessingCommand = true;
    network.setOptions({ physics: { enabled: true } });
    startOrbitalBreathing();
    if (agentName === 'speedup') agentName = 'systemcontrol';
    if (agentName === 'files') agentName = 'file';
    if (agentName === 'diagnostics') agentName = 'diagnostic';
    if (agentName === 'system') agentName = 'systemcontrol';
    if (agentName === 'personal') agentName = 'personalisation';
    if (agentName === 'troubleshoot') agentName = 'troubleshooter';

    neuralStats.inferenceLoad += 30;
    const aInfo = getAgentInfo(agentName);
    const container = document.getElementById('chatMessages');

    // Add divider
    if (container && container.children.length > 0 && !container.children[0].innerText.includes("Waiting")) {
        const d = document.createElement('div');
        d.className = 'chat-divider';
        d.innerHTML = '<span>⚡ New Command Sequence</span>';
        container.appendChild(d);
    }

    // Phase 1: Master receives and delegates
    spawnBurst('master', '#818cf8');
    appendChatMessage('master', getRandomLine('master', 'speak'), 'default');
    nodes.update({ id: 'master', color: { background: '#818cf8', border: '#fff' }, shadow: { enabled: true, color: '#818cf8', size: 60 } });

    // Phase 2: Master → Planner (with typing)
    setTimeout(() => {
        showTypingIndicator('master');
    }, 800);
    setTimeout(() => {
        removeTypingIndicator('master');
        appendChatMessage('master', injectTarget(getRandomLine('master', 'delegate'), 'planner'), 'delegate');
        flashEdge('master', 'planner', '#38bdf8');
        fireEnergyBeam('master', 'planner', '#818cf8');
        spawnBurst('planner', '#38bdf8');
    }, 1500);

    // Phase 3: Planner analyzes and routes to Parser
    setTimeout(() => { showTypingIndicator('planner'); }, 2200);
    setTimeout(() => {
        removeTypingIndicator('planner');
        appendChatMessage('planner', getRandomLine('planner', 'speak'), 'thinking');
        flashEdge('planner', 'parser', '#f472b6');
        fireEnergyBeam('planner', 'parser', '#38bdf8');
    }, 3200);

    // Phase 4: Parser → Memory (with potential argument)
    setTimeout(() => { showTypingIndicator('parser'); }, 3800);
    setTimeout(() => {
        removeTypingIndicator('parser');
        const willArgue = Math.random() < 0.3;
        if (willArgue) {
            appendChatMessage('parser', injectTarget(getRandomLine('parser', 'argue'), 'memory'), 'argue');
            neuralStats.conflicts++;
            fireEnergyBeam('parser', 'memory', '#ef4444');
            setTimeout(() => {
                appendChatMessage('memory', injectTarget(getRandomLine('memory', 'argue'), 'parser'), 'argue');
                fireEnergyBeam('memory', 'parser', '#f59e0b');
            }, 1200);
            setTimeout(() => {
                appendChatMessage('parser', 'Fine. Adjusting schema and re-sending.', 'agree');
                neuralStats.conflicts = Math.max(0, neuralStats.conflicts - 1);
            }, 2500);
        } else {
            appendChatMessage('parser', injectTarget(getRandomLine('parser', 'delegate'), 'memory'), 'delegate');
            fireEnergyBeam('parser', 'memory', '#f472b6');
        }
        flashEdge('parser', 'memory', '#2dd4bf');
        spawnBurst('memory', '#2dd4bf');
    }, 4800);

    // Phase 5: Memory → Database
    setTimeout(() => { showTypingIndicator('memory'); }, 6000);
    setTimeout(() => {
        removeTypingIndicator('memory');
        appendChatMessage('memory', getRandomLine('memory', 'speak'), 'report');
        flashEdge('memory', 'database', '#fb923c');
        fireEnergyBeam('memory', 'database', '#2dd4bf');
        spawnBurst('database', '#fb923c');
    }, 7000);

    // Phase 6: Database → Specialist Agent
    setTimeout(() => { showTypingIndicator('database'); }, 7800);
    setTimeout(() => {
        removeTypingIndicator('database');
        appendChatMessage('database', injectTarget(getRandomLine('database', 'delegate'), agentName), 'delegate');
        flashEdge('database', agentName, aInfo.color);
        fireEnergyBeam('database', agentName, '#fb923c');
        spawnBurst(agentName, aInfo.color);
        nodes.update({ id: agentName, color: { background: aInfo.color, border: '#fff' }, shadow: { enabled: true, color: aInfo.color, size: 80 } });
    }, 8800);

    // Phase 7: Kill Switch confirms monitoring
    setTimeout(() => {
        appendChatMessage('killswitch', injectTarget(getRandomLine('killswitch', 'delegate'), agentName), 'alert');
        flashEdge('killswitch', agentName, '#ef4444');
        fireEnergyBeam('killswitch', agentName, '#ef4444');
    }, 9500);

    // Phase 8: Specialist executes (laser targeting)
    setTimeout(() => {
        appendChatMessage('logger', getRandomLine('logger', 'speak'), 'report');
        let targetPrefix = 'proc_';
        if (['file', 'database'].includes(agentName)) targetPrefix = 'file_';
        const targets = [2, 7, 14, 19];
        targets.forEach((tIdx, i) => {
            setTimeout(() => {
                const targetId = `${targetPrefix}${tIdx}`;
                fireEnergyBeam(agentName, targetId, aInfo.color);
                nodes.update({ id: targetId, color: { background: aInfo.color, border: '#fff' }, size: 18, shadow: { enabled: true, color: aInfo.color, size: 30 } });
                setTimeout(() => {
                    nodes.update({ id: targetId, color: { background: '#18181b', border: '#27272a' }, size: 8, shadow: false });
                }, 700);
            }, i * 600);
        });
    }, 10500);

    // Phase 9: Specialist reports success
    setTimeout(() => {
        showTypingIndicator(agentName);
    }, 13000);
    setTimeout(() => {
        removeTypingIndicator(agentName);
        appendChatMessage(agentName, injectTarget(getRandomLine(agentName, 'celebrate') || 'Execution complete. No faults.', 'master'), 'celebrate');
        nodes.update({ id: agentName, color: { background: aInfo.color, border: '#fff' }, shadow: { enabled: true, color: aInfo.color, size: 25 } });
    }, 14000);

    // Phase 10: Master confirms
    setTimeout(() => {
        appendChatMessage('master', getRandomLine('master', 'celebrate'), 'celebrate');
        nodes.update({ id: 'master', color: { background: '#10b981', border: '#fff' }, shadow: { enabled: true, color: '#10b981', size: 60 } });
        neuralStats.inferenceLoad -= 20;
        spawnBurst('master', '#10b981');
        setTimeout(() => {
            nodes.update({ id: 'master', color: { background: '#818cf8', border: '#fff' }, shadow: { enabled: true, color: '#818cf8', size: 25 } });
            // Stop revolving once sequence fully completes
            stopOrbitalBreathing();
            window.isProcessingCommand = false;
            network.setOptions({ physics: { enabled: false } });
        }, 2000);
    }, 15500);
}

function completePipeline(agentName, success = true) {
    if (!network) return;
}

function replayLastSimulation() {
    if (!lastAnimatedAgent) return;
    animatePipeline(lastAnimatedAgent);
}

function activateKillSwitch() {
    if (!network || !edges || !nodes) return;
    showToast('alert', '🔴 KILL SWITCH ACTIVATED', 'All running agent threads forcefully terminated.');
    neuralStats.inferenceLoad = 100;
    neuralStats.conflicts += 3;
    nodes.update({ id: 'killswitch', color: { background: '#ef4444', border: '#fff' }, shadow: { enabled: true, color: '#ef4444', size: 60 }, size: 50 });
    appendChatMessage('killswitch', '<strong>@all</strong> ABORT INSTRUCTION RECEIVED. TERMINATING ALL ACTIVE PROCESSES AND INFERENCES...', 'alert', true);
    spawnBurst('killswitch', '#ef4444');

    const allAgents = Object.keys(AGENT_REGISTRY).filter(a => a !== 'killswitch');
    allAgents.forEach((a, i) => {
        setTimeout(() => {
            flashEdge('killswitch', a, '#ef4444');
            fireEnergyBeam('killswitch', a, '#ef4444');
            spawnBurst(a, '#ef4444');
            nodes.update({ id: a, color: { background: '#ef4444' } });
        }, i * 80);
    });

    setTimeout(() => {
        allAgents.forEach(a => {
            const info = getAgentInfo(a);
            nodes.update({ id: a, color: { background: info.color, border: '#fff' } });
        });
        const kInfo = getAgentInfo('killswitch');
        nodes.update({ id: 'killswitch', color: { background: kInfo.color, border: '#fff' }, shadow: { enabled: true, color: kInfo.color, size: 25 }, size: 30 });
        appendChatMessage('killswitch', 'All threads terminated. System stable. Resuming monitoring.', 'celebrate');
        neuralStats.inferenceLoad = 5;
        neuralStats.conflicts = 0;
        stopOrbitalBreathing();
    }, 1500);
}

// ══════════════════════════════════════════════════════════════
//  AGENT TRACKING
// ══════════════════════════════════════════════════════════════

function updateAgentStatus(agentName, status, message) {
    const card = document.getElementById(`agent-card-${agentName}`);
    if (card) {
        const badge = card.querySelector('.agent-card-badge');
        if (badge) { badge.textContent = status; badge.className = `agent-card-badge ${status.toLowerCase()}`; }
    }
    const log = document.getElementById(`agent-log-${agentName}`);
    if (log) {
        const time = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
        log.innerHTML = `<div>[${time}] ${escapeHtml(message)}</div>` + log.innerHTML;
        while (log.children.length > 10) log.removeChild(log.lastChild);
    }
}

function showAgentDetail(agentName) {
    const log = document.getElementById(`agent-log-${agentName}`);
    const title = document.querySelector(`#agent-card-${agentName} .agent-card-title`);
    showModal(title ? title.textContent : agentName, `<div style="font-family:var(--font-mono);font-size:0.8rem;">${log ? log.innerHTML : 'No activity'}</div>`, true);
}

// ══════════════════════════════════════════════════════════════
//  WEBSOCKET
// ══════════════════════════════════════════════════════════════

function initWebSocket() {
    const wsUrl = `ws://${window.location.host}/ws`;
    ws = new WebSocket(wsUrl);
    ws.onopen = () => addFeedItem('📡 WebSocket connected');
    ws.onmessage = (event) => { try { handleWSMessage(JSON.parse(event.data)); } catch(e) {} };
    ws.onclose = () => { addFeedItem('⚠️ WebSocket disconnected'); setTimeout(initWebSocket, 3000); };
}

function handleWSMessage(msg) {
    const type = msg.type; const data = msg.data || {};
    switch (type) {
        case 'initial_status': break;
        case 'command_executed': addFeedItem(`⌨️ Command: ${data.command} → ${data.status}`); break;
        case 'bot_animate': 
    addFeedItem(`⌨️ Bot starting: ${data.command}`); 
    animateEntityInteraction(data.agent, data.target, data.command); 
    break;
        case 'bot_complete': completePipeline(data.agent, data.success); break;
        case 'vision_analysis':
            addFeedItem(`👁️ Ghost: ${data.suggestion || 'Analysis complete'}`);
            updateGhostResult(data); addGhostLogEntry(data);
            showToast('ghost', '👁️ Ghost Mode', data.suggestion || 'Screen analyzed'); break;
        case 'ghost_mode_update':
            addFeedItem(`👁️ Ghost: ${data.suggestion || 'Screen scanned'}`);
            updateGhostResult(data); addGhostLogEntry(data);
            showToast('ghost', '👁️ Ghost Mode', data.suggestion || 'New observation'); break;
        case 'speedup_complete':
            addFeedItem(`🚀 Speedup: ${data.improvements?.temp_freed_mb || 0}MB freed`);
            updateAgentStatus('systemcontrol', 'Active', `Freed ${data.improvements?.temp_freed_mb || 0}MB`); break;
        case 'files_organized':
            addFeedItem(`📂 Files organized: ${data.folder}`);
            updateAgentStatus('file', 'Active', `Organized ${data.folder}`); break;
        case 'personalization_applied':
            addFeedItem(`🎨 Theme: ${data.action}`);
            updateAgentStatus('personalisation', 'Active', data.action); break;
        case 'troubleshoot_complete':
            addFeedItem('🔧 Troubleshoot complete');
            updateAgentStatus('troubleshooter', 'Active', 'Scan complete'); break;
        case 'pong': break;
        default: addFeedItem(`📩 ${type}`);
    }
}

// ══════════════════════════════════════════════════════════════
//  COMMAND CENTER
// ══════════════════════════════════════════════════════════════

async function sendCommand() {
    const input = document.getElementById('commandInput');
    const command = input.value.trim();
    if (!command) return;
    const output = document.getElementById('commandOutput');
    output.innerHTML += `<div class="output-line" style="color:var(--accent-blue);">🎤 You: ${escapeHtml(command)}</div>`;
    input.value = ''; input.focus();

    const lowerCmd = command.toLowerCase();
    if (lowerCmd.includes('speed up') || lowerCmd.includes('speedup') || lowerCmd.includes('optimize')) {
        output.innerHTML += `<div class="output-line system-line">⚡ Running PC Speedup...</div>`;
        output.scrollTop = output.scrollHeight;
        updateAgentStatus('systemcontrol', 'Processing', 'Running speedup pipeline...');
        try {
            const res = await fetch(API + '/api/speedup', { method: 'POST' });
            const data = await res.json();
            if (data.success) {
                const imp = data.result.improvements || {}; const before = data.result.before || {}; const after = data.result.after || {};
                output.innerHTML += `<div class="output-line success-line">✅ PC Optimized! RAM: ${before.ram_percent}% → ${after.ram_percent}% | Freed: ${imp.temp_freed_mb || 0}MB</div>`;
                showToast('success', '🚀 PC Optimized', `RAM: ${before.ram_percent}% → ${after.ram_percent}%`);
            } else { output.innerHTML += `<div class="output-line error-line">❌ ${data.error || 'Speedup failed'}</div>`; }
        } catch(e) { output.innerHTML += `<div class="output-line error-line">❌ Connection error</div>`; }
        output.scrollTop = output.scrollHeight; return;
    }
    if (lowerCmd.includes('clean temp') || lowerCmd.includes('temp files')) {
        output.innerHTML += `<div class="output-line system-line">🧹 Cleaning temp files...</div>`;
        try {
            const res = await fetch(API + '/api/system/clean-temp', { method: 'POST' });
            const data = await res.json();
            output.innerHTML += `<div class="output-line success-line">✅ ${data.success ? 'Temp files cleaned!' : data.error}</div>`;
        } catch(e) { output.innerHTML += `<div class="output-line error-line">❌ Error</div>`; }
        output.scrollTop = output.scrollHeight; return;
    }
    if (lowerCmd.includes('health') || lowerCmd.includes('system status')) {
        output.innerHTML += `<div class="output-line system-line">🏥 Fetching system health...</div>`;
        try {
            const res = await fetch(API + '/api/system-health');
            const data = await res.json();
            if (data.success) {
                output.innerHTML += `<div class="output-line success-line">📊 CPU: ${data.cpu.cpu_percent}% | RAM: ${data.ram.percent}% | Disk: ${data.disk.percent}%</div>`;
            }
        } catch(e) { output.innerHTML += `<div class="output-line error-line">❌ Error</div>`; }
        output.scrollTop = output.scrollHeight; return;
    }
    if (lowerCmd.includes('organize')) {
        output.innerHTML += `<div class="output-line system-line">📂 Organizing files...</div>`;
        output.scrollTop = output.scrollHeight;
        try {
            const res = await fetch(API + '/api/files/organize', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({folder_name:'Downloads',action:'organize'}) });
            const data = await res.json();
            output.innerHTML += `<div class="output-line success-line">✅ ${data.success ? 'Files organized!' : data.error}</div>`;
        } catch(e) { output.innerHTML += `<div class="output-line error-line">❌ Error</div>`; }
        output.scrollTop = output.scrollHeight; return;
    }

    // Default: master agent processing
    output.innerHTML += `<div class="output-line system-line">⏳ Processing via Master Agent...</div>`;
    output.scrollTop = output.scrollHeight;
    try {
        const res = await fetch(API + '/api/command', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ command }) });
        const data = await res.json();
        if (data.success) {
            const result = data.result;
            output.innerHTML += `<div class="output-line success-line">✅ ${escapeHtml(result.goal || command)} — ${result.status || 'completed'}</div>`;
        } else { output.innerHTML += `<div class="output-line error-line">❌ ${escapeHtml(data.error || 'Error')}</div>`; }
    } catch(e) { output.innerHTML += `<div class="output-line error-line">❌ Connection error: ${escapeHtml(e.message)}</div>`; }
    output.scrollTop = output.scrollHeight;
}

function sendQuickCommand(cmd) { document.getElementById('commandInput').value = cmd; sendCommand(); }

// ══════════════════════════════════════════════════════════════
//  GHOST MODE
// ══════════════════════════════════════════════════════════════

async function toggleGhostMode() {
    const toggle = document.getElementById('ghostToggle');
    const pill = document.getElementById('ghostStatusPill');
    const text = document.getElementById('ghostStatusText');
    if (toggle.checked) {
        try {
            await fetch(API + '/api/ghost-mode/start', { method: 'POST' });
            pill.classList.add('active'); text.textContent = 'Ghost: ON';
            addFeedItem('👁️ Ghost Mode activated');
            showToast('ghost', '👁️ Ghost Mode', 'Activated — watching your screen');
            updateAgentStatus('vision', 'Active', 'Ghost Mode ON');
        } catch(e) { toggle.checked = false; }
    } else {
        await fetch(API + '/api/ghost-mode/stop', { method: 'POST' });
        pill.classList.remove('active'); text.textContent = 'Ghost: OFF';
        addFeedItem('👁️ Ghost Mode deactivated');
        updateAgentStatus('vision', 'Idle', 'Ghost Mode OFF');
    }
}

async function triggerGhostScan() {
    const btn = document.getElementById('ghostScanBtn');
    btn.classList.add('loading'); btn.disabled = true;
    const resultDiv = document.getElementById('ghostLatestResult');
    resultDiv.innerHTML = '<div class="ghost-placeholder"><span class="ghost-eye" style="animation:spin 1s linear infinite;">🔍</span><p>Scanning...</p></div>';
    animatePipeline('vision');
    try {
        const res = await fetch(API + '/api/vision-analyze', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ query: 'What is on my screen? Are there any errors?' }) });
        const data = await res.json();
        if (data.success && data.result) {
            updateGhostResult({ analysis: data.result.analysis, suggestion: data.result.suggestion });
            addGhostLogEntry({ analysis: data.result.analysis, suggestion: data.result.suggestion });
            showToast('ghost', '👁️ Screen Scanned', data.result.suggestion || 'Done');
        } else { resultDiv.innerHTML = `<div class="ghost-finding" style="border-color:var(--accent-red);">❌ ${data.error || 'Failed'}</div>`; }
    } catch(e) { resultDiv.innerHTML = '<div class="ghost-finding" style="border-color:var(--accent-red);">❌ Connection error</div>'; }
    btn.classList.remove('loading'); btn.disabled = false;
}

function updateGhostResult(data) {
    const resultDiv = document.getElementById('ghostLatestResult');
    let html = '';
    if (data.suggestion) html += `<div class="ghost-finding">💡 ${escapeHtml(data.suggestion)}</div>`;
    const analysis = data.analysis;
    if (analysis) {
        if (analysis.screen_summary) html += `<div class="ghost-finding">📺 ${escapeHtml(analysis.screen_summary)}</div>`;
        if (analysis.window_title_or_app) html += `<div class="ghost-finding">📱 App: ${escapeHtml(analysis.window_title_or_app)}</div>`;
        (analysis.possible_errors_or_alerts || []).forEach(err => {
            const icon = err.severity === 'error' ? '🔴' : '🟡';
            html += `<div class="ghost-finding" style="border-color:${err.severity==='error'?'var(--accent-red)':'var(--accent-yellow)'};">${icon} ${escapeHtml(err.text)}</div>`;
        });
    }
    if (!html) html = '<div class="ghost-finding">✅ Everything looks good!</div>';
    resultDiv.innerHTML = html;
}

function addGhostLogEntry(data) {
    const log = document.getElementById('ghostActivityLog');
    if (!log) return;
    const empty = log.querySelector('.ghost-log-empty');
    if (empty) empty.remove();
    const time = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const analysis = data.analysis || {};
    const app = analysis.window_title_or_app || 'Unknown';
    const summary = analysis.screen_summary || data.suggestion || 'Analyzed';
    const errors = analysis.possible_errors_or_alerts || [];
    let alertsHtml = errors.length ? `<div class="ghost-log-alerts">${errors.map(e => `⚠️ ${escapeHtml(e.text)}`).join(' | ')}</div>` : '';
    const entry = document.createElement('div');
    entry.className = 'ghost-log-entry';
    entry.innerHTML = `<div class="ghost-log-time">${time}</div><div class="ghost-log-content"><div class="ghost-log-app">📱 ${escapeHtml(app)}</div><div class="ghost-log-summary">${escapeHtml(summary)}</div>${alertsHtml}</div>`;
    log.insertBefore(entry, log.firstChild);
    while (log.children.length > 50) log.removeChild(log.lastChild);
}

// ══════════════════════════════════════════════════════════════
//  TOAST NOTIFICATIONS
// ══════════════════════════════════════════════════════════════

function showToast(type, title, message, duration = 6000) {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${type === 'ghost' ? '👁️' : type === 'alert' ? '⚠️' : type === 'success' ? '✅' : 'ℹ️'}</span>
        <div class="toast-content"><div class="toast-title">${escapeHtml(title)}</div><div class="toast-msg">${escapeHtml(message)}</div></div>
        <button class="toast-close" onclick="this.parentElement.remove()">✕</button>`;
    container.appendChild(toast);
    setTimeout(() => { toast.classList.add('toast-exit'); setTimeout(() => toast.remove(), 300); }, duration);
}

// ══════════════════════════════════════════════════════════════
//  PC SPEEDUP & FILE MANAGER & PERSONALIZATION & SYSTEM
// ══════════════════════════════════════════════════════════════

async function runSpeedup() {
    const btn = document.getElementById('speedupBtn');
    btn.classList.add('loading'); btn.disabled = true;
    const resultDiv = document.getElementById('speedupResult');
    resultDiv.innerHTML = '<div style="text-align:center;color:var(--text-muted);">⚡ Optimizing...</div>';
    animatePipeline('systemcontrol');
    try {
        const res = await fetch(API + '/api/speedup', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            const imp = data.result.improvements || {}; const before = data.result.before || {}; const after = data.result.after || {};
            resultDiv.innerHTML = `
                <div class="speedup-metric"><span class="label">CPU</span><span class="value">${before.cpu_percent}% → ${after.cpu_percent}%</span></div>
                <div class="speedup-metric"><span class="label">RAM</span><span class="value">${before.ram_percent}% → ${after.ram_percent}%</span></div>
                <div class="speedup-metric"><span class="label">Temp Freed</span><span class="value improved">${imp.temp_freed_mb || 0} MB</span></div>
                <div class="speedup-metric"><span class="label">Optimized</span><span class="value improved">${(imp.processes_optimized||0)+(imp.memory_flushed||0)}</span></div>`;
            showToast('success', '🚀 PC Optimized', `Freed ${imp.temp_freed_mb}MB`);
            addFeedItem(`🚀 PC optimized: ${imp.temp_freed_mb || 0}MB freed`);
        } else { resultDiv.innerHTML = `<div style="color:var(--accent-red);">❌ ${data.error || 'Failed'}</div>`; }
    } catch(e) { resultDiv.innerHTML = '<div style="color:var(--accent-red);">❌ Connection error</div>'; }
    btn.classList.remove('loading'); btn.disabled = false;
}

async function fileAction(action) {
    const resultDiv = document.getElementById('fileResult');
    resultDiv.innerHTML = '<div style="color:var(--text-muted);">⏳ Working...</div>';
    animatePipeline('file');
    const endpointMap = { organize:'/api/files/organize', scan_large:'/api/files/scan-large', duplicates:'/api/files/duplicates', report:'/api/files/report' };
    try {
        const res = await fetch(API + endpointMap[action], { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ folder_name: 'Downloads', action }) });
        const data = await res.json();
        if (data.success) {
            showModal(`File Manager — ${action}`, JSON.stringify(data.result, null, 2));
            resultDiv.innerHTML = '<div style="color:var(--accent-green);">✅ Done — see details</div>';
            addFeedItem(`📁 File ${action} completed`);
        } else { resultDiv.innerHTML = `<div style="color:var(--accent-red);">❌ ${data.error}</div>`; }
    } catch(e) { resultDiv.innerHTML = '<div style="color:var(--accent-red);">❌ Connection error</div>'; }
}

async function applyPreset(preset) {
    animatePipeline('personalisation');
    try {
        await fetch(API + '/api/personalize', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ action: 'apply_preset', params: { preset } }) });
        addFeedItem(`🎨 Preset applied: ${preset}`);
        showToast('info', '🎨 Personalization', `${preset} theme applied`);
    } catch(e) { addFeedItem('❌ Failed to apply preset'); }
}

async function personalize(action) {
    try { await fetch(API + '/api/personalize', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ action, params: {} }) }); addFeedItem(`🎨 ${action} executed`); } catch(e) { addFeedItem(`❌ Failed: ${action}`); }
}

async function systemAction(action) {
    animatePipeline('systemcontrol');
    try {
        const res = await fetch(API + `/api/system/${action}`, { method: 'POST' });
        const data = await res.json();
        if (data.success) { addFeedItem(`⚙️ ${action}: success`); if (data.result) showModal(`System — ${action}`, JSON.stringify(data.result, null, 2)); }
        else { addFeedItem(`❌ ${action} failed`); }
    } catch(e) { addFeedItem(`❌ ${action} error`); }
}

async function triggerTroubleshoot() {
    animatePipeline('troubleshooter');
    addFeedItem('🔧 Starting troubleshoot...');
    try {
        const res = await fetch(API + '/api/troubleshoot', { method: 'POST' });
        const data = await res.json();
        if (data.success) { showModal('Troubleshoot Results', JSON.stringify(data, null, 2)); }
    } catch(e) { addFeedItem('❌ Troubleshoot error'); }
}

async function showBloatware() {
    try {
        const res = await fetch(API + '/api/speedup/bloatware');
        const data = await res.json();
        if (data.success) {
            let html = '<h4>🔍 Non-Essential Processes:</h4>';
            if (data.bloatware?.length) { html += '<ul>'; data.bloatware.forEach(p => { html += `<li>${p.name} — ${p.memory_mb}MB RAM</li>`; }); html += '</ul>'; }
            else { html += '<p>✅ No bloatware detected!</p>'; }
            showModal('Bloatware Analysis', html, true);
        }
    } catch(e) { addFeedItem('❌ Failed to load bloatware'); }
}

// ══════════════════════════════════════════════════════════════
//  ACTIVITY FEED & MODAL & UTILITIES
// ══════════════════════════════════════════════════════════════

function addFeedItem(msg) {
    const list = document.getElementById('feedList');
    const time = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit' });
    const item = document.createElement('div');
    item.className = 'feed-item';
    item.innerHTML = `<span class="feed-time">${time}</span><span class="feed-msg">${escapeHtml(msg)}</span>`;
    list.insertBefore(item, list.firstChild);
    while (list.children.length > 50) list.removeChild(list.lastChild);
}

function showModal(title, content, isHtml = false) {
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalBody').innerHTML = isHtml ? content : `<pre>${escapeHtml(content)}</pre>`;
    document.getElementById('modalOverlay').classList.add('visible');
}
function closeModal() { document.getElementById('modalOverlay').classList.remove('visible'); }

function updateClock() {
    document.getElementById('clock').textContent = new Date().toLocaleTimeString('en-US', { hour12: true, hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') { e.preventDefault(); document.getElementById('commandInput').focus(); switchTab('dashboard'); }
    if (e.key === 'Escape') closeModal();
});

window.animateEntityInteraction = function(fromId, toId, textLabel) {
    if (!network || !edges.get) return;
    try {
        if (!nodes.get(fromId)) nodes.add({ id: fromId, label: fromId, shape: 'dot', color: '#94a3b8', size: 10 });
        if (!nodes.get(toId)) nodes.add({ id: toId, label: toId, shape: 'dot', color: '#94a3b8', size: 10 });
        
        const edgeId = 'rel_' + fromId + '_' + toId + '_' + Date.now();
        
        // Very slow movement and enable flashing
        network.setOptions({ physics: { enabled: true } });
        window.isProcessingCommand = true;
        
        edges.add({ 
            id: edgeId, 
            from: fromId, 
            to: toId, 
            label: (textLabel || 'ANALYZING').replace(/ /g, '_').toUpperCase().substring(0, 15), 
            color: '#94a3b8', 
            font: {background: '#f8fafc', color: '#0f172a', size: 10, strokeWidth: 0},
            length: 40,
            springConstant: 0.1,
            smooth: { type: 'dynamic' }
        });
        
        // Nodes temporary glow effect
        const agentColor = getAgentInfo(fromId)?.color || '#3b82f6';
        nodes.update({ id: fromId, shadow: { enabled: true, color: agentColor, size: 25 } });
        nodes.update({ id: toId, shadow: { enabled: true, color: agentColor, size: 20 } });
        
        setTimeout(() => {
            try { edges.remove(edgeId); } catch(e){}
            try { nodes.update({ id: fromId, shadow: false }); } catch(e){}
            try { nodes.update({ id: toId, shadow: false }); } catch(e){}
            
            // Allow physics to settle before disabling
            setTimeout(() => {
                if (edges.length === 0 || typeof edges.length === 'undefined' || edges.getIds().length === 0) {
                    network.setOptions({ physics: { enabled: false } });
                    window.isProcessingCommand = false;
                }
            }, 1000);
        }, 4000);
    } catch(e) { console.error('Animation Error:', e); }
}

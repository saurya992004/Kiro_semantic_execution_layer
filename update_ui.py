import re

def update_app():
    with open('static/app.js', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update colors to muted shades
    colors = {
        'master': '#94a3b8',
        'planner': '#64748b',
        'parser': '#cbd5e1',
        'memory': '#86efac',
        'database': '#fef08a',
        'logger': '#e2e8f0',
        'killswitch': '#fca5a5',
        'speedup': '#93c5fd',
        'files': '#fef08a',
        'diagnostics': '#e2e8f0',
        'vision': '#86efac',
        'file': '#fef08a',
        'diagnostic': '#e2e8f0',
        'systemcontrol': '#93c5fd'
    }
    for agent, color in colors.items():
        content = re.sub(rf"({agent}:\s*{{[^}}]+color:\s*)'#[^']+'", rf"\1'{color}'", content)
    
    content = re.sub(r"icon:\s*'[^\x00-\x7F]+',", "icon: '',", content)

    # 2. Replace Particle Engine with Aura Engine
    particle_code_start = content.find('function initParticleCanvas() {')
    particle_code_end = content.find('function togglePerformanceMode() {')
    
    aura_engine = """function initParticleCanvas() {
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
    
    for (let i = activeAuras.length - 1; i >= 0; i--) {
        const aura = activeAuras[i];
        aura.life -= 16;
        if (aura.life <= 0) {
            activeAuras.splice(i, 1);
            continue;
        }
        
        try {
            const p1 = network.canvasToDOM(network.getPosition(aura.fromId));
            const p2 = network.canvasToDOM(network.getPosition(aura.toId));
            
            const dx = p2.x - p1.x;
            const dy = p2.y - p1.y;
            const len = Math.sqrt(dx*dx + dy*dy);
            if(len < 1) continue;
            
            const ux = dx/len;
            const uy = dy/len;
            const px = -uy;
            const py = ux;
            
            const width = 80; // wide beam base
            
            particleCtx.beginPath();
            particleCtx.moveTo(p1.x, p1.y);
            particleCtx.lineTo(p2.x + px * width, p2.y + py * width);
            particleCtx.lineTo(p2.x - px * width, p2.y - py * width);
            particleCtx.closePath();
            
            const grad = particleCtx.createLinearGradient(p1.x, p1.y, p2.x, p2.y);
            let colorStr = aura.color.replace('rgb', 'rgba').replace(')', '');
            if(colorStr.startsWith('#')) {
                let r = parseInt(colorStr.slice(1,3), 16);
                let g = parseInt(colorStr.slice(3,5), 16);
                let b = parseInt(colorStr.slice(5,7), 16);
                colorStr = `rgba(${r},${g},${b}`;
            }
            
            const progress = (aura.life / aura.maxLife);
            grad.addColorStop(0, colorStr + `, ${0.4 * progress})`);
            grad.addColorStop(1, colorStr + `, 0)`);
            
            particleCtx.fillStyle = grad;
            particleCtx.globalCompositeOperation = 'screen'; 
            particleCtx.fill();
            particleCtx.globalCompositeOperation = 'source-over';
            
            // Draw agent halo
            particleCtx.beginPath();
            particleCtx.arc(p1.x, p1.y, 60, 0, Math.PI*2);
            const rgrad = particleCtx.createRadialGradient(p1.x, p1.y, 0, p1.x, p1.y, 60);
            rgrad.addColorStop(0, colorStr + `, ${0.5 * progress})`);
            rgrad.addColorStop(1, colorStr + `, 0)`);
            particleCtx.fillStyle = rgrad;
            particleCtx.fill();
            
        } catch(e) {}
    }
    animFrameId = requestAnimationFrame(renderAuras);
}

// Stubs for removed functions
function fireEnergyBeam(from, to, color) { addAura(from, to, color, 3000); }
function spawnBurst(node, color) { addAura(node, 'root', color, 1500); }

"""
    content = content[:particle_code_start] + aura_engine + content[particle_code_end:]

    # 3. Replace initNetwork 
    init_start = content.find('function initNetwork() {')
    init_end = content.find('// ── Orbital Breathing (continuous subtle motion) ──')
    
    new_init = """function getAgentSVG(hex) {
    hex = hex.replace('#', '%23');
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512"><path fill="${hex}" d="M224 256c70.7 0 128-57.3 128-128S294.7 0 224 0 96 57.3 96 128s57.3 128 128 128zm89.6 32h-16.7c-22.2 10.2-46.9 16-72.9 16s-50.6-5.8-72.9-16h-16.7C60.2 288 0 348.2 0 422.4V464c0 26.5 21.5 48 48 48h352c26.5 0 48-21.5 48-48v-41.6c0-74.2-60.2-134.4-134.4-134.4z"/></svg>`;
    return 'data:image/svg+xml;charset=utf-8,' + svg;
}

function initNetwork() {
    const container = document.getElementById('mynetwork');
    if (!container) return;
    const baseNodes = [];
    const baseEdges = [];

    const struct = [
        {id:'root', label:'JARVIS', size:12, color:'#475569'},
        {id:'backend', label:'backend', size:10, color:'#64748b'},
        {id:'frontend', label:'frontend', size:10, color:'#64748b'},
        {id:'scripts', label:'scripts', size:8, color:'#94a3b8'},
        {id:'services', label:'services', size:8, color:'#94a3b8'},
        {id:'api', label:'api', size:8, color:'#94a3b8'},
        {id:'tests', label:'tests', size:8, color:'#94a3b8'},
        {id:'sys_proc', label:'Processes', size:8, color:'#94a3b8'},
        {id:'f_main', label:'run_bot.py', size:6, color:'#e2e8f0'},
        {id:'f_toml', label:'pyproject.toml', size:6, color:'#e2e8f0'},
        {id:'f_log', label:'logger.py', size:6, color:'#e2e8f0'},
        {id:'f_app', label:'app.py', size:6, color:'#e2e8f0'},
        {id:'f_api', label:'api_routes.py', size:6, color:'#e2e8f0'},
        {id:'f_ws', label:'websocket.py', size:6, color:'#e2e8f0'},
        {id:'f_test1', label:'test_agent.py', size:6, color:'#e2e8f0'},
        {id:'f_js', label:'app.js', size:6, color:'#e2e8f0'},
        {id:'f_html', label:'dashboard.html', size:6, color:'#e2e8f0'},
        {id:'f_css', label:'style.css', size:6, color:'#e2e8f0'}
    ];
    
    struct.forEach(n => {
        baseNodes.push({ id: n.id, label: n.label, shape: 'dot', color: { background: n.color, border: 'transparent' }, size: n.size });
    });
    
    const tree = [
        ['root','backend'], ['root','frontend'], ['root','scripts'],
        ['backend','services'], ['backend','api'], ['root','tests'],
        ['root','sys_proc'], ['root','f_main'], ['root','f_toml'], ['scripts','f_log'],
        ['backend','f_app'], ['api','f_api'], ['api','f_ws'],
        ['tests','f_test1'], ['frontend','f_js'], ['frontend','f_html'], ['frontend','f_css']
    ];
    
    tree.forEach(pair => {
        baseEdges.push({ from: pair[0], to: pair[1], color: 'rgba(255,255,255,0.06)', length: 60 });
    });

    // Agents as silhouettes
    const agentIds = Object.keys(AGENT_REGISTRY);
    agentIds.forEach(a => {
        const info = AGENT_REGISTRY[a];
        baseNodes.push({ 
            id: a, 
            label: info.name, 
            shape: 'image',
            image: getAgentSVG(info.color),
            size: 20, 
            mass: 5
        });
        baseEdges.push({ from: 'root', to: a, color: 'transparent', length: 250 });
    });

    nodes = new vis.DataSet(baseNodes);
    edges = new vis.DataSet(baseEdges);
    const options = {
        nodes: { font: { color: '#94a3b8', size: 10, face: 'Arial', strokeWidth: 0 }, borderWidth: 0 },
        edges: { width: 1.0, hoverWidth: 0, selectionWidth: 0, smooth: false, arrows: { to: { enabled: false } } },
        physics: { 
            barnesHut: { gravitationalConstant: -3000, centralGravity: 0.1, springLength: 95, springConstant: 0.04, damping: 0.6, avoidOverlap: 1 }, 
            solver: 'barnesHut', timestep: 0.35, enabled: true 
        }
    };
    network = new vis.Network(container, { nodes, edges }, options);

    network.once('stabilizationIterationsDone', () => {
        network.setOptions({ physics: { enabled: false } });
    });
    network.once('stabilized', () => {
        network.setOptions({ physics: { enabled: false } });
        initParticleCanvas();
    });
    setTimeout(() => {
        if (network) network.setOptions({ physics: { enabled: false } });
    }, 2500);

    window.addEventListener('resize', () => {
        const canvas = document.getElementById('particleCanvas');
        if (canvas && canvas.parentElement) { canvas.width = canvas.parentElement.offsetWidth; canvas.height = canvas.parentElement.offsetHeight; }
    });
}

"""
    content = content[:init_start] + new_init + content[init_end:]

    # Remove startOrbitalBreathing body and calls
    content = re.sub(r'function startOrbitalBreathing\([^\)]*\)\s*\{[^\}]*\}[^\}]*\}', 'function startOrbitalBreathing() {}', content)
    content = re.sub(r'function stopOrbitalBreathing\(\)\s*\{[^\}]*\}', 'function stopOrbitalBreathing() {}', content)

    # In animatePipeline, map target nodes
    # Let's dynamically map targets to interesting files in tree
    # when an agent activates, it "looks" at a file.
    mapping_code = """
    const targets = ['f_main', 'f_app', 'f_js', 'backend', 'api', 'services', 'f_log', 'f_ws'];
    const p1 = targets[Math.floor(Math.random() * targets.length)];
    const p2 = targets[Math.floor(Math.random() * targets.length)];
    const p3 = targets[Math.floor(Math.random() * targets.length)];
    """
    
    # We just replace `fireEnergyBeam(agentName, 'hub_fs', ...)` with `addAura(agentName, p1, ...)` etc
    content = re.sub(r"fireEnergyBeam\('([^']+)',\s*'hub_([^']+)',\s*([^)]+)\)", 
                     r"addAura('\1', 'f_' + '\2', \3)", content)
    # Generic replace for others
    content = re.sub(r"fireEnergyBeam\(([^,]+),\s*'hub_[^']+',\s*([^)]+)\)", 
                     r"addAura(\1, 'root', \2)", content)
                     
    with open('static/app.js', 'w', encoding='utf-8') as f:
        f.write(content)

    # Clean up CSS (muted text/shapes)
    with open('static/style.css', 'r', encoding='utf-8') as f:
        css = f.read()
    
    css = css.replace("font-family: 'Inter'", "font-family: 'Arial'")
    # remove bright borders
    css = re.sub(r'box-shadow:\s*0\s+0\s+\d+px\s+[^;]+;', '', css)

    with open('static/style.css', 'w', encoding='utf-8') as f:
        f.write(css)

if __name__ == '__main__':
    update_app()

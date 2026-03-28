import re

def main():
    with open('static/style.css', 'r', encoding='utf-8') as f:
        css = f.read()

    # Change to light theme
    css = css.replace('--bg-dark: #0f172a;', '--bg-dark: #f8fafc;')
    css = css.replace('--bg-panel: rgba(30, 41, 59, 0.7);', '--bg-panel: rgba(255, 255, 255, 0.9);')
    css = css.replace('--text-main: #f8fafc;', '--text-main: #334155;')
    css = css.replace('--text-muted: #94a3b8;', '--text-muted: #64748b;')

    with open('static/style.css', 'w', encoding='utf-8') as f:
        f.write(css)

    with open('static/app.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # Update colors to bright flat colors
    colors = {
        'master': '#3b82f6', # blue
        'planner': '#6366f1', # indigo
        'parser': '#8b5cf6', # purple
        'memory': '#10b981', # green
        'database': '#eab308', # yellow
        'logger': '#64748b', # slate
        'killswitch': '#ef4444', # red
        'speedup': '#0ea5e9', # light blue
        'files': '#f59e0b',
        'diagnostics': '#84cc16',
        'vision': '#14b8a6',
        'systemcontrol': '#0284c7',
        'file': '#f59e0b',
        'diagnostic': '#84cc16',
        'personalisation': '#d946ef'
    }

    for agent, color in colors.items():
        js = re.sub(rf"({agent}:\s*{{[^}}]+color:\s*)'#[^']+'", rf"\1'{color}'", js)

    # Change agent visual to solid circle (remove svg shape)
    init_net_start = js.find('function getAgentSVG(hex)')
    init_net_end = js.find('function initParticleCanvas()')

    new_init_net = """function initNetwork() {
    const container = document.getElementById('mynetwork');
    if (!container) return;
    const baseNodes = [];
    const baseEdges = [];

    // Central system nodes
    const struct = [
        {id:'root', label:'JARVIS', size:15, color:'#334155'},
        {id:'backend', label:'backend', size:10, color:'#64748b'},
        {id:'frontend', label:'frontend', size:10, color:'#64748b'},
        {id:'sys_proc', label:'Processes', size:10, color:'#64748b'},
        {id:'f_main', label:'run_bot.py', size:8, color:'#94a3b8'},
        {id:'f_app', label:'app.py', size:8, color:'#94a3b8'},
        {id:'f_js', label:'app.js', size:8, color:'#94a3b8'},
        {id:'logger', label:'logger.py', size:8, color:'#94a3b8'},
        {id:'f_ws', label:'websocket.py', size:8, color:'#94a3b8'}
    ];
    
    struct.forEach(n => {
        baseNodes.push({ id: n.id, label: n.label, shape: 'dot', color: { background: n.color, border: 'transparent' }, size: n.size });
    });
    
    const tree = [
        ['root','backend'], ['root','frontend'], ['root','sys_proc'],
        ['root','f_main'], ['backend','f_app'], ['frontend','f_js'], 
        ['backend','logger'], ['backend','f_ws']
    ];
    
    tree.forEach(pair => {
        baseEdges.push({ from: pair[0], to: pair[1], color: 'rgba(0,0,0,0.1)', length: 150 });
    });

    // Agents as simple colored dots
    const agentIds = Object.keys(AGENT_REGISTRY);
    agentIds.forEach(a => {
        const info = AGENT_REGISTRY[a];
        baseNodes.push({ 
            id: a, 
            label: info.name, 
            shape: 'dot',
            color: { background: info.color, border: 'transparent' },
            size: 15, 
            mass: 2
        });
        baseEdges.push({ id: 'invisible_'+a, from: 'root', to: a, color: 'transparent', length: 250 });
    });

    nodes = new vis.DataSet(baseNodes);
    edges = new vis.DataSet(baseEdges);
    const options = {
        nodes: { font: { color: '#334155', size: 12, face: 'Arial', strokeWidth: 0 }, borderWidth: 0 },
        edges: { width: 1.5, font: {size: 10, align: 'horizontal', color: '#64748b', strokeWidth: 0}, smooth: {type: 'dynamic'} },
        physics: { 
            repulsion: { centralGravity: 0.1, springLength: 200, springConstant: 0.05, nodeDistance: 150, damping: 0.09 },
            solver: 'repulsion', timestep: 0.5, enabled: true 
        }
    };
    network = new vis.Network(container, { nodes, edges }, options);
}

"""
    js = js[:init_net_start] + new_init_net + js[init_net_end:]

    # Update web socket handler
    js = js.replace("case 'bot_animate': addFeedItem(`⌨️ Bot starting: ${data.command}`); animatePipeline(data.agent); break;", 
"""case 'bot_animate': 
    addFeedItem(`⌨️ Bot starting: ${data.command}`); 
    animateEntityInteraction(data.agent, data.target, data.command); 
    break;""")

    new_anim = """
window.animateEntityInteraction = function(fromId, toId, textLabel) {
    if (!network || !edges.get) return;
    try {
        const edgeId = 'rel_' + fromId + '_' + toId + '_' + Date.now();
        edges.add({ id: edgeId, from: fromId, to: toId, label: textLabel.replace(/ /g, '_').toUpperCase().substring(0, 15), color: '#94a3b8', font: {background: '#f8fafc'} });
        setTimeout(() => {
            try { edges.remove(edgeId); } catch(e){}
        }, 5000);
    } catch(e) {}
}
"""
    js += new_anim

    with open('static/app.js', 'w', encoding='utf-8') as f:
        f.write(js)

if __name__ == '__main__':
    main()

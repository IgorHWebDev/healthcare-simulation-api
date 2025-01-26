// Dynamic Diagram Animation System
class DiagramAnimator {
    constructor() {
        this.physicsEngine = null;
        this.particles = new Float64Array(1000); // Pre-allocated particle buffer
        this.springs = new Float64Array(1000);   // Pre-allocated spring buffer
        this.lastFrameTime = 0;
        this.isAnimating = false;
    }

    async init() {
        // Initialize WebAssembly physics engine
        const response = await fetch('/src/wasm/physics_engine.wasm');
        const buffer = await response.arrayBuffer();
        const wasmModule = await WebAssembly.instantiate(buffer, {
            js: { mem: new WebAssembly.Memory({ initial: 1 }) },
            Math: { sin: Math.sin, cos: Math.cos }
        });
        this.physicsEngine = wasmModule.instance.exports;
    }

    // Force-directed layout algorithm
    calculateForces(nodes, edges) {
        const REPULSION = 500;
        const SPRING_K = 0.1;
        const DAMPING = 0.98;
        
        // Calculate repulsion between all nodes
        for (let i = 0; i < nodes.length; i++) {
            for (let j = i + 1; j < nodes.length; j++) {
                const dx = nodes[j].x - nodes[i].x;
                const dy = nodes[j].y - nodes[i].y;
                const distance = Math.sqrt(dx * dx + dy * dy);
                
                if (distance > 0) {
                    const force = REPULSION / (distance * distance);
                    const fx = (dx / distance) * force;
                    const fy = (dy / distance) * force;
                    
                    // Use WASM for vector addition
                    const [newX1, newY1] = this.physicsEngine.vectorAdd(
                        nodes[i].vx, nodes[i].vy, -fx, -fy
                    );
                    const [newX2, newY2] = this.physicsEngine.vectorAdd(
                        nodes[j].vx, nodes[j].vy, fx, fy
                    );
                    
                    nodes[i].vx = newX1;
                    nodes[i].vy = newY1;
                    nodes[j].vx = newX2;
                    nodes[j].vy = newY2;
                }
            }
        }
        
        // Calculate spring forces for edges
        for (const edge of edges) {
            const sourceNode = nodes[edge.source];
            const targetNode = nodes[edge.target];
            
            const dx = targetNode.x - sourceNode.x;
            const dy = targetNode.y - sourceNode.y;
            const distance = Math.sqrt(dx * dx + dy * dy);
            
            if (distance > 0) {
                const springForce = this.physicsEngine.calculateSpringForce(SPRING_K, distance);
                const fx = (dx / distance) * springForce;
                const fy = (dy / distance) * springForce;
                
                sourceNode.vx += fx;
                sourceNode.vy += fy;
                targetNode.vx -= fx;
                targetNode.vy -= fy;
            }
        }
        
        // Update positions using WASM
        for (const node of nodes) {
            const [newX, newY, newVx, newVy] = this.physicsEngine.updateParticle(
                node.x, node.y, node.vx, node.vy, 0.1, DAMPING
            );
            node.x = newX;
            node.y = newY;
            node.vx = newVx;
            node.vy = newVy;
        }
    }

    // SIMD-accelerated animation frame processing
    processSIMD(nodes) {
        if (crossOriginIsolated && self.SIMD) {
            const positions = new Float64Array(nodes.length * 2);
            for (let i = 0; i < nodes.length; i++) {
                positions[i * 2] = nodes[i].x;
                positions[i * 2 + 1] = nodes[i].y;
            }
            
            // Process 4 nodes at once using SIMD
            const simd = new SIMD.Float64x2Array(positions.buffer);
            for (let i = 0; i < simd.length; i += 2) {
                const pos = SIMD.Float64x2.load(simd, i);
                const vel = SIMD.Float64x2.load(simd, i + 1);
                const newPos = SIMD.Float64x2.add(pos, vel);
                SIMD.Float64x2.store(simd, i, newPos);
            }
            
            // Update node positions
            for (let i = 0; i < nodes.length; i++) {
                nodes[i].x = positions[i * 2];
                nodes[i].y = positions[i * 2 + 1];
            }
        }
    }

    // Smooth animation using RequestAnimationFrame
    animate(diagram) {
        if (!this.isAnimating) return;
        
        const currentTime = performance.now();
        const deltaTime = currentTime - this.lastFrameTime;
        this.lastFrameTime = currentTime;
        
        // Calculate new positions
        const nodes = diagram.getNodes();
        const edges = diagram.getEdges();
        
        this.calculateForces(nodes, edges);
        this.processSIMD(nodes);
        
        // Update diagram
        diagram.updatePositions(nodes);
        
        // Schedule next frame
        requestAnimationFrame(() => this.animate(diagram));
    }

    // Dynamic interaction handlers
    addInteraction(diagram) {
        const canvas = diagram.getCanvas();
        let isDragging = false;
        let selectedNode = null;
        
        canvas.addEventListener('mousedown', (e) => {
            const node = this.findNodeAtPosition(e.clientX, e.clientY, diagram);
            if (node) {
                isDragging = true;
                selectedNode = node;
                node.fixed = true;
            }
        });
        
        canvas.addEventListener('mousemove', (e) => {
            if (isDragging && selectedNode) {
                selectedNode.x = e.clientX;
                selectedNode.y = e.clientY;
            }
        });
        
        canvas.addEventListener('mouseup', () => {
            if (selectedNode) {
                selectedNode.fixed = false;
                selectedNode = null;
            }
            isDragging = false;
        });
    }

    // Utility functions
    findNodeAtPosition(x, y, diagram) {
        const nodes = diagram.getNodes();
        const CLICK_RADIUS = 10;
        
        return nodes.find(node => {
            const dx = node.x - x;
            const dy = node.y - y;
            return Math.sqrt(dx * dx + dy * dy) < CLICK_RADIUS;
        });
    }

    start(diagram) {
        this.isAnimating = true;
        this.lastFrameTime = performance.now();
        this.animate(diagram);
        this.addInteraction(diagram);
    }

    stop() {
        this.isAnimating = false;
    }
}

// Export animator
export const diagramAnimator = new DiagramAnimator();

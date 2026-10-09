/**
 * AeroQ-Route Canvas Visualizer & UI Interactions — Enhanced v2
 */

document.addEventListener("DOMContentLoaded", () => {

  // ========================================================================
  //  SPLASH SCREEN
  // ========================================================================
  const splashScreen = document.getElementById("splashScreen");
  const progressFill = document.getElementById("splashProgressFill");
  let splashProgress = 0;

  function advanceSplash() {
    splashProgress += Math.random() * 22 + 8;
    if (splashProgress > 100) splashProgress = 100;
    if (progressFill) progressFill.style.width = splashProgress + "%";

    if (splashProgress < 100) {
      setTimeout(advanceSplash, 80 + Math.random() * 100);
    } else {
      setTimeout(() => {
        if (splashScreen) splashScreen.classList.add("hidden");
      }, 250);
    }
  }
  advanceSplash();

  // Safety fallback: auto-dismiss splash screen after 2.5 seconds max
  setTimeout(() => {
    if (splashScreen && !splashScreen.classList.contains("hidden")) {
      splashScreen.classList.add("hidden");
    }
  }, 2500);

  // ========================================================================
  //  PARTICLE CANVAS BACKGROUND
  // ========================================================================
  const particleCanvas = document.getElementById("particleCanvas");
  if (particleCanvas) {
    const pctx = particleCanvas.getContext("2d");
    let particles = [];

    function resizeParticleCanvas() {
      const hero = particleCanvas.parentElement;
      if (!hero) return;
      particleCanvas.width = hero.offsetWidth;
      particleCanvas.height = hero.offsetHeight;
    }

    function initParticles() {
      particles = [];
      const w = particleCanvas.width;
      const h = particleCanvas.height;
      const count = Math.min(60, Math.floor((w * h) / 12000));
      for (let i = 0; i < count; i++) {
        particles.push({
          x: Math.random() * w,
          y: Math.random() * h,
          vx: (Math.random() - 0.5) * 0.4,
          vy: (Math.random() - 0.5) * 0.4,
          r: Math.random() * 1.6 + 0.5,
          opacity: Math.random() * 0.5 + 0.1,
        });
      }
    }

    function drawParticles() {
      const w = particleCanvas.width;
      const h = particleCanvas.height;
      pctx.clearRect(0, 0, w, h);

      // Draw subtle connecting lines
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 120) {
            pctx.strokeStyle = `rgba(0, 242, 254, ${0.07 * (1 - dist / 120)})`;
            pctx.lineWidth = 0.6;
            pctx.beginPath();
            pctx.moveTo(particles[i].x, particles[i].y);
            pctx.lineTo(particles[j].x, particles[j].y);
            pctx.stroke();
          }
        }
      }

      // Draw particle dots
      particles.forEach(p => {
        pctx.beginPath();
        pctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        pctx.fillStyle = `rgba(0, 242, 254, ${p.opacity})`;
        pctx.fill();

        p.x += p.vx;
        p.y += p.vy;

        // Wrap around borders
        if (p.x < 0) p.x = w;
        if (p.x > w) p.x = 0;
        if (p.y < 0) p.y = h;
        if (p.y > h) p.y = 0;
      });

      requestAnimationFrame(drawParticles);
    }

    resizeParticleCanvas();
    initParticles();
    drawParticles();
    window.addEventListener("resize", () => {
      resizeParticleCanvas();
      initParticles();
    });
  }

  // ========================================================================
  //  SCROLL ANIMATIONS (IntersectionObserver)
  // ========================================================================
  const scrollElements = document.querySelectorAll(".animate-on-scroll");
  const scrollObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add("visible");
        scrollObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.05, rootMargin: "0px 0px -20px 0px" });

  scrollElements.forEach(el => scrollObserver.observe(el));

  // Ensure top-of-page hero elements are visible immediately
  setTimeout(() => {
    document.querySelectorAll(".hero .animate-on-scroll").forEach(el => {
      el.classList.add("visible");
    });
  }, 400);

  // ========================================================================
  //  COUNTER ANIMATION
  // ========================================================================
  const counters = document.querySelectorAll(".counter");
  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const el = entry.target;
        const target = parseInt(el.dataset.target, 10);
        if (!isNaN(target)) {
          animateCounter(el, 0, target, 1200);
        }
        counterObserver.unobserve(el);
      }
    });
  }, { threshold: 0.15 });

  counters.forEach(c => counterObserver.observe(c));

  function animateCounter(el, from, to, duration) {
    const start = performance.now();
    function step(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      el.textContent = Math.round(from + (to - from) * eased);
      if (progress < 1) requestAnimationFrame(step);
      else el.textContent = to;
    }
    requestAnimationFrame(step);
  }

  // ========================================================================
  //  NAVBAR SCROLL EFFECT
  // ========================================================================
  const navbar = document.getElementById("mainNavbar");
  window.addEventListener("scroll", () => {
    if (navbar) {
      navbar.classList.toggle("scrolled", window.scrollY > 40);
    }
  });

  // Active nav link highlighting based on scroll position
  const navLinksAll = document.querySelectorAll(".nav-link");
  const sections = document.querySelectorAll("section[id], header.hero");

  function updateActiveNav() {
    const scrollPos = window.scrollY + 120;
    sections.forEach(section => {
      const top = section.offsetTop;
      const height = section.offsetHeight;
      const id = section.getAttribute("id");
      if (scrollPos >= top && scrollPos < top + height && id) {
        navLinksAll.forEach(link => {
          link.classList.toggle("active", link.getAttribute("href") === "#" + id);
        });
      }
    });
  }
  window.addEventListener("scroll", updateActiveNav);

  // ========================================================================
  //  HAMBURGER MOBILE MENU
  // ========================================================================
  const hamburgerBtn = document.getElementById("hamburgerBtn");
  const mobileOverlay = document.getElementById("mobileMenuOverlay");

  if (hamburgerBtn && mobileOverlay) {
    hamburgerBtn.addEventListener("click", () => {
      hamburgerBtn.classList.toggle("active");
      mobileOverlay.classList.toggle("active");
      document.body.style.overflow = mobileOverlay.classList.contains("active") ? "hidden" : "";
    });

    document.querySelectorAll(".mobile-menu-link").forEach(link => {
      link.addEventListener("click", () => {
        hamburgerBtn.classList.remove("active");
        mobileOverlay.classList.remove("active");
        document.body.style.overflow = "";
      });
    });
  }

  // ========================================================================
  //  BACK TO TOP BUTTON
  // ========================================================================
  const backToTopBtn = document.getElementById("backToTopBtn");
  window.addEventListener("scroll", () => {
    if (backToTopBtn) {
      backToTopBtn.classList.toggle("visible", window.scrollY > 400);
    }
  });
  if (backToTopBtn) {
    backToTopBtn.addEventListener("click", () => {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  // ========================================================================
  //  AIRSPACE RADAR CANVAS
  // ========================================================================
  const canvas = document.getElementById("airspaceCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  // State
  let currentMode = "dijkstra"; // dijkstra, ilp, neal, qaoa
  let flightCount = 10;
  let capacityLimit = 2;
  let animationFrameId = null;
  let planeProgress = 0;
  let radarSweepAngle = 0;

  // Cached solver solution to prevent heavy re-calculation inside requestAnimationFrame (60 FPS)
  let currentSolution = null;

  function updateSolution() {
    if (currentMode === "dijkstra") {
      currentSolution = window.AeroSimulator.solveDijkstra(flightCount);
    } else if (currentMode === "ilp") {
      currentSolution = window.AeroSimulator.solveExactILP(flightCount, capacityLimit);
    } else if (currentMode === "neal") {
      currentSolution = window.AeroSimulator.solveAnnealer(flightCount, capacityLimit);
    } else {
      currentSolution = window.AeroSimulator.solveQAOA(flightCount, capacityLimit);
    }
    updateMetricsDisplay(currentSolution);
  }

  // Coordinate projection bounds for Indian subcontinent
  const LON_MIN = 68.0, LON_MAX = 94.0;
  const LAT_MIN = 7.0, LAT_MAX = 33.0;

  function resizeCanvas() {
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
  }
  window.addEventListener("resize", resizeCanvas);
  resizeCanvas();

  function project(lon, lat) {
    const w = canvas.width / window.devicePixelRatio;
    const h = canvas.height / window.devicePixelRatio;
    const x = ((lon - LON_MIN) / (LON_MAX - LON_MIN)) * (w * 0.85) + (w * 0.08);
    // Invert lat for canvas Y
    const y = (1.0 - (lat - LAT_MIN) / (LAT_MAX - LAT_MIN)) * (h * 0.85) + (h * 0.08);
    return { x, y };
  }

  // Draw Background Radar Grids with rotating sweep
  function drawRadarBackground() {
    const w = canvas.width / window.devicePixelRatio;
    const h = canvas.height / window.devicePixelRatio;
    ctx.clearRect(0, 0, w, h);

    // Radar circles centered on central India (Nagpur)
    const center = project(79.0882, 21.1458);
    ctx.strokeStyle = "rgba(0, 242, 254, 0.06)";
    ctx.lineWidth = 1;
    for (let r = 50; r <= 350; r += 75) {
      ctx.beginPath();
      ctx.arc(center.x, center.y, r, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Rotating Radar sweep line
    const sweepLen = 350;
    const sweepX = center.x + Math.cos(radarSweepAngle) * sweepLen;
    const sweepY = center.y + Math.sin(radarSweepAngle) * sweepLen;
    const sweepGrad = ctx.createLinearGradient(center.x, center.y, sweepX, sweepY);
    sweepGrad.addColorStop(0, "rgba(0, 242, 254, 0.15)");
    sweepGrad.addColorStop(1, "rgba(0, 242, 254, 0)");
    ctx.strokeStyle = sweepGrad;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(center.x, center.y);
    ctx.lineTo(sweepX, sweepY);
    ctx.stroke();

    // Sweep arc glow
    ctx.fillStyle = "rgba(0, 242, 254, 0.03)";
    ctx.beginPath();
    ctx.moveTo(center.x, center.y);
    ctx.arc(center.x, center.y, sweepLen, radarSweepAngle - 0.5, radarSweepAngle, false);
    ctx.closePath();
    ctx.fill();

    radarSweepAngle += 0.012;

    // Latitude & Longitude grid lines
    ctx.strokeStyle = "rgba(255, 255, 255, 0.03)";
    ctx.lineWidth = 1;
    for (let lon = 70; lon <= 92; lon += 5) {
      const p1 = project(lon, 8);
      const p2 = project(lon, 32);
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.stroke();
    }
    for (let lat = 10; lat <= 30; lat += 5) {
      const p1 = project(69, lat);
      const p2 = project(93, lat);
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.stroke();
    }
  }

  // Draw Nodes
  function drawNodes() {
    const allAirports = window.AeroData.airports;
    const allWaypoints = window.AeroData.waypoints;

    // Draw waypoints
    for (const [code, wp] of Object.entries(allWaypoints)) {
      const pt = project(wp.lon, wp.lat);
      ctx.fillStyle = "rgba(157, 78, 221, 0.6)";
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, 3.5, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = "rgba(148, 163, 184, 0.7)";
      ctx.font = "9px 'JetBrains Mono'";
      ctx.fillText(code, pt.x + 6, pt.y + 3);
    }

    // Draw primary hubs
    for (const [code, ap] of Object.entries(allAirports)) {
      const pt = project(ap.lon, ap.lat);

      // Outer glow ring
      ctx.strokeStyle = "rgba(0, 242, 254, 0.4)";
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, 8, 0, Math.PI * 2);
      ctx.stroke();

      // Animated pulsing outer ring
      const pulseRadius = 8 + Math.sin(Date.now() * 0.003) * 3;
      ctx.strokeStyle = "rgba(0, 242, 254, 0.15)";
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, pulseRadius + 4, 0, Math.PI * 2);
      ctx.stroke();

      // Inner glowing core
      ctx.fillStyle = "#00f2fe";
      ctx.shadowColor = "#00f2fe";
      ctx.shadowBlur = 10;
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, 4.5, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0; // Reset glow

      // Label
      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 11px 'Outfit'";
      ctx.fillText(code, pt.x + 10, pt.y + 4);
    }
  }

  // Draw Active Flight Corridors
  function drawRoutes(assignments, edgeUsage) {
    if (!assignments || !edgeUsage) return;

    for (const [fId, path] of Object.entries(assignments)) {
      if (!path || path.length < 2) continue;

      for (let i = 0; i < path.length - 1; i++) {
        const uNode = window.AeroSimulator.getNodeCoord(path[i]);
        const vNode = window.AeroSimulator.getNodeCoord(path[i + 1]);
        if (!uNode || !vNode) continue;

        const p1 = project(uNode.lon, uNode.lat);
        const p2 = project(vNode.lon, vNode.lat);

        const edgeKey = [path[i], path[i + 1]].sort().join("<->");
        const usage = edgeUsage[edgeKey] || 1;
        const cap = edgeKey.includes("NAG") || edgeKey.includes("BHO") ? Math.max(1, capacityLimit - 1) : capacityLimit;
        const isViolated = usage > cap;

        // Stroke styling based on congestion
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);

        if (isViolated) {
          ctx.strokeStyle = "rgba(255, 77, 109, 0.85)";
          ctx.lineWidth = 3.0;
          ctx.shadowColor = "#ff4d6d";
          ctx.shadowBlur = 12;
        } else {
          ctx.strokeStyle = "rgba(0, 242, 254, 0.35)";
          ctx.lineWidth = 1.6;
          ctx.shadowBlur = 0;
        }
        ctx.stroke();
        ctx.shadowBlur = 0;

        // Animated plane particle
        const t = (planeProgress + (i * 0.25)) % 1.0;
        const planeX = p1.x + (p2.x - p1.x) * t;
        const planeY = p1.y + (p2.y - p1.y) * t;

        ctx.fillStyle = isViolated ? "#ff4d6d" : "#00f5a0";
        ctx.shadowColor = isViolated ? "#ff4d6d" : "#00f5a0";
        ctx.shadowBlur = 8;
        ctx.beginPath();
        ctx.arc(planeX, planeY, 3, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;

        // Trail effect
        const trailT = ((planeProgress + (i * 0.25)) - 0.05) % 1.0;
        if (trailT > 0) {
          const trailX = p1.x + (p2.x - p1.x) * trailT;
          const trailY = p1.y + (p2.y - p1.y) * trailT;
          ctx.fillStyle = isViolated ? "rgba(255, 77, 109, 0.3)" : "rgba(0, 245, 160, 0.3)";
          ctx.beginPath();
          ctx.arc(trailX, trailY, 2, 0, Math.PI * 2);
          ctx.fill();
        }
      }
    }
  }

  // Animation Loop (Silky 60 FPS without re-solving on every frame)
  function render() {
    drawRadarBackground();

    if (!currentSolution) {
      updateSolution();
    }

    drawRoutes(currentSolution.assignments, currentSolution.edgeUsage);
    drawNodes();

    planeProgress = (planeProgress + 0.0035) % 1.0;
    animationFrameId = requestAnimationFrame(render);
  }
  render();

  // ========================================================================
  //  SOLVER SYNCHRONIZATION FUNCTION
  // ========================================================================
  function setSolverMode(mode) {
    currentMode = mode;
    document.querySelectorAll(".mode-btn").forEach(b => {
      b.classList.toggle("active", b.dataset.mode === mode);
    });
    document.querySelectorAll(".solver-choice-card").forEach(c => {
      c.classList.toggle("selected", c.dataset.solver === mode);
    });
    updateSolution();
  }

  // Mode Switch Buttons
  document.querySelectorAll(".mode-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      setSolverMode(btn.dataset.mode);
    });
  });

  // Solver Choice Cards
  document.querySelectorAll(".solver-choice-card").forEach(card => {
    card.addEventListener("click", () => {
      setSolverMode(card.dataset.solver);
    });
  });

  // ========================================================================
  //  CONTROLS SLIDERS
  // ========================================================================
  const flightsSlider = document.getElementById("flightsSlider");
  const flightsVal = document.getElementById("flightsVal");
  if (flightsSlider) {
    flightsSlider.addEventListener("input", (e) => {
      flightCount = parseInt(e.target.value, 10);
      flightsVal.textContent = flightCount;
      updateSolution();
      populateScheduleTable();
    });
  }

  const capacitySlider = document.getElementById("capacitySlider");
  const capacityVal = document.getElementById("capacityVal");
  if (capacitySlider) {
    capacitySlider.addEventListener("input", (e) => {
      capacityLimit = parseInt(e.target.value, 10);
      capacityVal.textContent = capacityLimit;
      updateSolution();
    });
  }

  // ========================================================================
  //  ACTION BUTTON (BENCHMARK SUITE)
  // ========================================================================
  const runBtn = document.getElementById("runBenchmarkBtn");
  if (runBtn) {
    runBtn.addEventListener("click", () => {
      runBtn.innerHTML = `<span style="display:inline-flex;align-items:center;gap:8px;">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor" class="spin-icon">
          <path d="M12 2a10 10 0 1 0 10 10h-2a8 8 0 1 1-8-8V2z"/>
        </svg>
        Simulating Quantum Registers...
      </span>`;
      runBtn.disabled = true;
      setTimeout(() => {
        runBtn.disabled = false;
        runBtn.innerHTML = `
          <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
            <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
          </svg>
          Benchmark Complete!
        `;
        updateSolution();
        populateBenchmarkTable();

        setTimeout(() => {
          runBtn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <polygon points="5 3 19 12 5 21 5 3"></polygon>
            </svg>
            Run Full Benchmark Suite
          `;
        }, 2000);
      }, 700);
    });
  }

  // ========================================================================
  //  UPDATE RESULT CARDS
  // ========================================================================
  function updateMetricsDisplay(res) {
    if (!res) return;

    // Animate number changes
    animateValue("resFuel", `${res.totalFuel.toLocaleString()} kg`);
    animateValue("resCO2", `${res.totalCO2.toLocaleString()} kg`);
    
    const violEl = document.getElementById("resViolations");
    if (violEl) {
      violEl.textContent = res.violations;
      violEl.className = "result-card-val " + (res.violations > 5 ? "color-crimson" : "color-green");
    }

    animateValue("resRuntime", `${(res.runtimeSec * 1000).toFixed(1)} ms`);
    const titleEl = document.getElementById("activeSolverTitle");
    if (titleEl) {
      titleEl.textContent = res.solverName;
    }
  }

  function animateValue(elId, newValue) {
    const el = document.getElementById(elId);
    if (!el) return;
    el.style.transition = "opacity 0.15s ease, transform 0.15s ease";
    el.style.opacity = "0.3";
    el.style.transform = "translateY(-4px)";
    setTimeout(() => {
      el.textContent = newValue;
      el.style.opacity = "1";
      el.style.transform = "translateY(0)";
    }, 150);
  }

  // ========================================================================
  //  BENCHMARK TABLE
  // ========================================================================
  function populateBenchmarkTable() {
    const tbody = document.getElementById("benchmarkTableBody");
    if (!tbody) return;
    tbody.innerHTML = "";

    const allRes = window.AeroSimulator.runAll(flightCount, capacityLimit);
    allRes.forEach((r, idx) => {
      const tr = document.createElement("tr");
      tr.style.animation = `fadeInRow 0.4s ease ${idx * 0.1}s both`;
      tr.innerHTML = `
        <td><span class="badge-tag ${r.badgeClass}">${r.solverName}</span></td>
        <td><strong>${r.totalFuel.toLocaleString()} kg</strong></td>
        <td>${r.totalCO2.toLocaleString()} kg</td>
        <td><span class="violation-pill ${r.violations > 5 ? 'violation-high' : 'violation-low'}">${r.violations} Overflows</span></td>
        <td><code>${(r.runtimeSec * 1000).toFixed(2)} ms</code></td>
        <td><small class="text-muted">${r.method}</small></td>
      `;
      tbody.appendChild(tr);
    });
  }

  // ========================================================================
  //  FLIGHT SCHEDULE TABLE
  // ========================================================================
  function populateScheduleTable() {
    const tbody = document.getElementById("flightsTableBody");
    if (!tbody) return;
    tbody.innerHTML = "";

    const active = window.AeroData.sampleFlights.slice(0, flightCount);
    active.forEach((f, idx) => {
      const tr = document.createElement("tr");
      tr.style.animation = `fadeInRow 0.4s ease ${idx * 0.05}s both`;
      tr.innerHTML = `
        <td><code>${f.id}</code></td>
        <td><strong>${f.origin} &rarr; ${f.dest}</strong></td>
        <td>${f.aircraft}</td>
        <td>Slot ${f.slot}</td>
        <td><small class="font-mono">${f.paths[0].join(" &rarr; ")}</small></td>
      `;
      tbody.appendChild(tr);
    });
  }

  // ========================================================================
  //  SMOOTH SCROLL NAV LINKS
  // ========================================================================
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener("click", function(e) {
      const target = document.querySelector(this.getAttribute("href"));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    });
  });

  // ========================================================================
  //  INITIAL POPULATION
  // ========================================================================
  updateSolution();
  populateBenchmarkTable();
  populateScheduleTable();

  // Add CSS animation for table rows and spinners
  const style = document.createElement("style");
  style.textContent = `
    @keyframes fadeInRow {
      from { opacity: 0; transform: translateX(-10px); }
      to { opacity: 1; transform: translateX(0); }
    }
    .spin-icon {
      animation: spin 1s linear infinite;
    }
    @keyframes spin {
      from { transform: rotate(0deg); }
      to { transform: rotate(360deg); }
    }
  `;
  document.head.appendChild(style);
});

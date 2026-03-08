function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function hexToRgb(hex) {
  const cleaned = (hex || "").replace("#", "").trim();
  if (!/^[0-9a-fA-F]{6}$/.test(cleaned)) {
    return { r: 160, g: 34, b: 59 };
  }
  return {
    r: parseInt(cleaned.slice(0, 2), 16),
    g: parseInt(cleaned.slice(2, 4), 16),
    b: parseInt(cleaned.slice(4, 6), 16),
  };
}

function smoothstep(edge0, edge1, x) {
  const t = clamp((x - edge0) / Math.max(1e-6, edge1 - edge0), 0, 1);
  return t * t * (3 - 2 * t);
}

// 4x4 Bayer 阈值矩阵，用于像素抖动分层
const BAYER_4 = [
  [0, 8, 2, 10],
  [12, 4, 14, 6],
  [3, 11, 1, 9],
  [15, 7, 13, 5],
];

function bayerThreshold(x, y) {
  return (BAYER_4[y & 3][x & 3] + 0.5) / 16;
}

export function initPixelBlastBackground(options = {}) {
  const config = {
    variant: "circle",
    pixelSize: 4,
    color: "#a0223b",
    patternScale: 2,
    patternDensity: 1,
    pixelSizeJitter: 0,
    enableRipples: true,
    rippleSpeed: 0.4,
    rippleThickness: 0.12,
    rippleIntensityScale: 1.5,
    liquid: false,
    liquidStrength: 0.12,
    liquidRadius: 1.2,
    liquidWobbleSpeed: 5,
    speed: 0.5,
    edgeFade: 0.25,
    transparent: true,
    ...options,
  };

  if (typeof window === "undefined" || typeof document === "undefined") {
    return null;
  }

  const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const rgb = hexToRgb(config.color);
  const canvas = document.createElement("canvas");
  canvas.id = "pixel-blast-bg";
  canvas.setAttribute("aria-hidden", "true");
  document.body.prepend(canvas);

  const ctx = canvas.getContext("2d", { alpha: true, desynchronized: true });
  if (!ctx) {
    return null;
  }

  let width = 0;
  let height = 0;
  let cols = 0;
  let rows = 0;
  let rafId = null;
  let lastFrame = 0;
  const targetFrameMs = reduced ? 1000 / 12 : 1000 / 28;

  // 固定几个“场核”，模拟 PixelBlast 的团块结构
  const blobs = Array.from({ length: 6 }).map((_, i) => ({
    x: Math.random(),
    y: Math.random(),
    r: 0.13 + Math.random() * 0.2,
    vx: (Math.random() * 2 - 1) * (0.00022 + i * 0.00004),
    vy: (Math.random() * 2 - 1) * (0.00022 + i * 0.00004),
  }));

  function resize() {
    width = Math.max(1, window.innerWidth);
    height = Math.max(1, window.innerHeight);
    const dpr = clamp(window.devicePixelRatio || 1, 1, 2);
    canvas.width = Math.floor(width * dpr);
    canvas.height = Math.floor(height * dpr);
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    cols = Math.ceil(width / config.pixelSize);
    rows = Math.ceil(height / config.pixelSize);
  }

  function updateBlobs(dt) {
    const speedScale = config.speed * (reduced ? 0.45 : 1);
    blobs.forEach((b, idx) => {
      const wobble = config.liquid
        ? Math.sin(performance.now() * 0.001 * config.liquidWobbleSpeed + idx) * config.liquidStrength * 0.0005
        : 0;
      b.x += (b.vx + wobble) * dt * speedScale;
      b.y += (b.vy - wobble) * dt * speedScale;

      if (b.x < -0.15 || b.x > 1.15) {
        b.vx *= -1;
      }
      if (b.y < -0.15 || b.y > 1.15) {
        b.vy *= -1;
      }
    });
  }

  function sampleField(nx, ny, timeSec) {
    let value = 0;
    for (let i = 0; i < blobs.length; i += 1) {
      const b = blobs[i];
      const dx = nx - b.x;
      const dy = ny - b.y;
      const d2 = dx * dx + dy * dy;
      const r2 = b.r * b.r;
      value += Math.exp(-d2 / (r2 * (config.patternScale * 0.9)));
    }

    value = (value / blobs.length) * 1.9 * config.patternDensity;

    if (config.enableRipples) {
      const cx = 0.5;
      const cy = 0.5;
      const dx = nx - cx;
      const dy = ny - cy;
      const d = Math.sqrt(dx * dx + dy * dy);
      const wavePhase = d * 17 - timeSec * (2.3 * config.rippleSpeed);
      const thickness = clamp(config.rippleThickness, 0.04, 0.45);
      const envelope = Math.exp(-d * (4.2 / Math.max(0.1, thickness)));
      value += Math.sin(wavePhase) * envelope * 0.2 * config.rippleIntensityScale;
    }

    const edge = Math.min(nx, 1 - nx, ny, 1 - ny);
    const fade = smoothstep(0, clamp(config.edgeFade, 0.04, 0.49), edge);
    return value * fade;
  }

  function draw(now) {
    if (now - lastFrame < targetFrameMs) {
      rafId = window.requestAnimationFrame(draw);
      return;
    }
    const dt = Math.min(40, now - (lastFrame || now));
    lastFrame = now;

    if (!config.transparent) {
      ctx.fillStyle = "rgba(9, 11, 15, 1)";
      ctx.fillRect(0, 0, width, height);
    } else {
      ctx.clearRect(0, 0, width, height);
    }

    updateBlobs(dt);

    const t = now * 0.001;
    const baseA = reduced ? 0.16 : 0.24;
    for (let gy = 0; gy < rows; gy += 1) {
      for (let gx = 0; gx < cols; gx += 1) {
        const nx = (gx + 0.5) / cols;
        const ny = (gy + 0.5) / rows;
        const field = sampleField(nx, ny, t);
        const threshold = bayerThreshold(gx, gy);
        const on = field > threshold * 0.95;
        if (!on) {
          continue;
        }

        const jitter = config.pixelSizeJitter > 0
          ? (Math.random() - 0.5) * config.pixelSizeJitter
          : 0;
        const px = gx * config.pixelSize;
        const py = gy * config.pixelSize;
        const size = Math.max(1, config.pixelSize + jitter);
        const alpha = clamp(baseA + field * 0.18, 0.08, 0.62);
        ctx.fillStyle = `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${alpha})`;
        if (config.variant === "circle") {
          ctx.beginPath();
          ctx.arc(px + size * 0.5, py + size * 0.5, size * 0.38, 0, Math.PI * 2);
          ctx.fill();
        } else {
          ctx.fillRect(px, py, size, size);
        }
      }
    }

    rafId = window.requestAnimationFrame(draw);
  }

  function onResize() {
    resize();
  }

  resize();
  rafId = window.requestAnimationFrame(draw);
  window.addEventListener("resize", onResize);

  return () => {
    if (rafId) {
      window.cancelAnimationFrame(rafId);
    }
    window.removeEventListener("resize", onResize);
    canvas.remove();
  };
}

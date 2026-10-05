// SPACE RISK — interactive 3D Earth (Three.js)
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

const DEG = Math.PI / 180;
const UZ = { lat: 41.3, lng: 64.5 };

export function latLngToVec3(lat, lng, r = 1) {
  const phi = (90 - lat) * DEG;
  const theta = (lng + 180) * DEG;
  return new THREE.Vector3(-r * Math.sin(phi) * Math.cos(theta), r * Math.cos(phi), r * Math.sin(phi) * Math.sin(theta));
}

const isDark = () => document.documentElement.dataset.theme !== "light";

const earthVert = /* glsl */ `
  varying vec2 vUv; varying vec3 vNormalW; varying vec3 vViewDir;
  void main() {
    vUv = uv;
    vNormalW = normalize(mat3(modelMatrix) * normal);
    vec4 wp = modelMatrix * vec4(position, 1.0);
    vViewDir = normalize(cameraPosition - wp.xyz);
    gl_Position = projectionMatrix * viewMatrix * wp;
  }`;
const earthFrag = /* glsl */ `
  uniform sampler2D dayTex; uniform sampler2D nightTex; uniform sampler2D waterTex;
  uniform vec3 sunDir; uniform float nightBoost;
  varying vec2 vUv; varying vec3 vNormalW; varying vec3 vViewDir;
  void main() {
    vec3 n = normalize(vNormalW);
    float ndl = dot(n, normalize(sunDir));
    float dayMix = smoothstep(-0.18, 0.28, ndl);
    vec3 day = texture2D(dayTex, vUv).rgb * (0.25 + 0.95 * max(ndl, 0.0));
    vec3 night = texture2D(nightTex, vUv).rgb * nightBoost * vec3(1.0, 0.85, 0.62);
    vec3 col = mix(night, day, dayMix);
    // ocean specular glint
    float water = texture2D(waterTex, vUv).r;
    vec3 h = normalize(normalize(sunDir) + vViewDir);
    col += water * pow(max(dot(n, h), 0.0), 60.0) * 0.55 * dayMix * vec3(0.7, 0.85, 1.0);
    // rim light
    float rim = pow(1.0 - max(dot(n, vViewDir), 0.0), 3.0);
    col += rim * vec3(0.25, 0.65, 1.0) * 0.6;
    gl_FragColor = vec4(col, 1.0);
  }`;
const atmoFrag = /* glsl */ `
  uniform vec3 color; uniform float power; varying vec3 vNormalW; varying vec3 vViewDir;
  void main() {
    float d = -dot(normalize(vNormalW), vViewDir);   // 0 at outer edge → ~0.5 at Earth's limb
    float i = pow(smoothstep(0.0, 0.5, d), power) * 0.85;
    gl_FragColor = vec4(color * i, i);
  }`;

function makeSatellite(color = 0x22d3ee) {
  const g = new THREE.Group();
  const body = new THREE.Mesh(new THREE.BoxGeometry(0.035, 0.035, 0.06), new THREE.MeshStandardMaterial({ color: 0xe2e8f0, metalness: 0.8, roughness: 0.3 }));
  const panelMat = new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 0.6, metalness: 0.4, roughness: 0.4, side: THREE.DoubleSide });
  const p1 = new THREE.Mesh(new THREE.BoxGeometry(0.11, 0.004, 0.04), panelMat);
  p1.position.x = 0.075;
  const p2 = p1.clone();
  p2.position.x = -0.075;
  const light = new THREE.Mesh(new THREE.SphereGeometry(0.008, 8, 8), new THREE.MeshBasicMaterial({ color: 0xfbbf24 }));
  light.position.z = 0.035;
  g.add(body, p1, p2, light);
  return g;
}

function makeStars(count = 4000) {
  const geo = new THREE.BufferGeometry();
  const pos = new Float32Array(count * 3);
  const col = new Float32Array(count * 3);
  const palette = [new THREE.Color(0xffffff), new THREE.Color(0x9bdcff), new THREE.Color(0xc4b5fd), new THREE.Color(0xfde68a)];
  for (let i = 0; i < count; i++) {
    const r = 30 + Math.random() * 60;
    const u = Math.random() * 2 - 1, t = Math.random() * Math.PI * 2;
    const s = Math.sqrt(1 - u * u);
    pos.set([r * s * Math.cos(t), r * u, r * s * Math.sin(t)], i * 3);
    const c = palette[(Math.random() * palette.length) | 0];
    col.set([c.r, c.g, c.b], i * 3);
  }
  geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  geo.setAttribute("color", new THREE.BufferAttribute(col, 3));
  return new THREE.Points(geo, new THREE.PointsMaterial({ size: 0.12, vertexColors: true, transparent: true, opacity: 0.9, depthWrite: false }));
}

export function createGlobe(container, opts = {}) {
  const o = Object.assign({
    regions: [], textures: { day: "/static/img/textures/earth-day.jpg", night: "/static/img/textures/earth-night.jpg", water: "/static/img/textures/earth-water.png" }, offsetX: 0.22, offsetY: 0, narrowOffsetY: 0.18, distance: 3.4,
    satellites: 3, interactive: true, autoRotate: 0.0012, stars: true, onSelect: null, tooltip: null,
  }, opts);

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: "high-performance" });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  container.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 200);
  camera.position.set(0, 0.35, o.distance);

  scene.add(new THREE.AmbientLight(0xffffff, 0.5));
  const sun = new THREE.DirectionalLight(0xffffff, 1.6);
  scene.add(sun);

  // Tilt group (faces Uzbekistan), spin group (auto-rotation), earth inside.
  const tilt = new THREE.Group();
  const spin = new THREE.Group();
  tilt.add(spin);
  scene.add(tilt);

  const loader = new THREE.TextureLoader();
  const tex = (url) => { const t = loader.load(url); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8; return t; };
  const uniforms = {
    dayTex: { value: tex(o.textures.day) },
    nightTex: { value: tex(o.textures.night) },
    waterTex: { value: loader.load(o.textures.water) },
    sunDir: { value: new THREE.Vector3(1, 0.3, 0.6).normalize() },
    nightBoost: { value: 1.6 },
  };
  const earth = new THREE.Mesh(
    new THREE.SphereGeometry(1, 128, 128),
    new THREE.ShaderMaterial({ uniforms, vertexShader: earthVert, fragmentShader: earthFrag })
  );
  spin.add(earth);

  const atmoUniforms = { color: { value: new THREE.Color(0x38bdf8) }, power: { value: 2.2 } };
  const atmo = new THREE.Mesh(
    new THREE.SphereGeometry(1.12, 64, 64),
    new THREE.ShaderMaterial({ uniforms: atmoUniforms, vertexShader: earthVert, fragmentShader: atmoFrag, side: THREE.BackSide, blending: THREE.AdditiveBlending, transparent: true, depthWrite: false })
  );
  scene.add(atmo);

  // Orient so Uzbekistan faces the camera.
  const uz = latLngToVec3(UZ.lat, UZ.lng);
  spin.rotation.y = Math.atan2(-uz.x, uz.z);
  tilt.rotation.x = UZ.lat * DEG * 0.55;

  // --- Region markers: glowing risk beams + pulsing rings
  const markers = [];
  const ringGeo = new THREE.RingGeometry(0.009, 0.013, 32);
  o.regions.forEach((r, i) => {
    const color = new THREE.Color(r.color);
    const normal = latLngToVec3(r.lat, r.lng).normalize();
    const h = 0.03 + (r.score / 100) * 0.16;
    const beam = new THREE.Mesh(
      new THREE.CylinderGeometry(0.0025, 0.006, h, 10, 1, true),
      new THREE.MeshBasicMaterial({ color, transparent: true, opacity: 0.85, blending: THREE.AdditiveBlending, depthWrite: false })
    );
    beam.position.copy(normal.clone().multiplyScalar(1 + h / 2));
    beam.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), normal);
    const cap = new THREE.Mesh(new THREE.SphereGeometry(0.0075, 12, 12), new THREE.MeshBasicMaterial({ color }));
    cap.position.copy(normal.clone().multiplyScalar(1 + h));
    const ring = new THREE.Mesh(ringGeo, new THREE.MeshBasicMaterial({ color, transparent: true, side: THREE.DoubleSide, depthWrite: false }));
    ring.position.copy(normal.clone().multiplyScalar(1.002));
    ring.lookAt(normal.clone().multiplyScalar(2));
    // invisible, larger hit target
    const hit = new THREE.Mesh(new THREE.SphereGeometry(0.04, 8, 8), new THREE.MeshBasicMaterial({ visible: false }));
    hit.position.copy(cap.position);
    hit.userData = { region: r, ring, beam, cap };
    spin.add(beam, cap, ring, hit);
    markers.push({ hit, ring, cap, beam, phase: i * 0.37 });
  });

  // --- Satellites on inclined orbits
  const sats = [];
  const satColors = [0x22d3ee, 0xa78bfa, 0xf0abfc];
  for (let i = 0; i < o.satellites; i++) {
    const radius = 1.38 + i * 0.16;
    const orbit = new THREE.Group();
    orbit.rotation.set((25 + i * 30) * DEG, i * 70 * DEG, (i % 2 ? -1 : 1) * 15 * DEG);
    const path = new THREE.Mesh(
      new THREE.TorusGeometry(radius, 0.0018, 6, 200),
      new THREE.MeshBasicMaterial({ color: satColors[i % 3], transparent: true, opacity: 0.35, blending: THREE.AdditiveBlending, depthWrite: false })
    );
    path.rotation.x = Math.PI / 2;
    const sat = makeSatellite(satColors[i % 3]);
    orbit.add(path, sat);
    scene.add(orbit);
    sats.push({ sat, radius, speed: 0.22 - i * 0.05, angle: i * 2.1, orbit });
  }
  // Scanning beam from the first satellite to Earth
  let scanCone = null;
  if (sats.length) {
    const coneGeo = new THREE.ConeGeometry(0.16, 1, 32, 1, true);
    coneGeo.translate(0, -0.5, 0);
    scanCone = new THREE.Mesh(coneGeo, new THREE.MeshBasicMaterial({ color: 0x22d3ee, transparent: true, opacity: 0.08, blending: THREE.AdditiveBlending, side: THREE.DoubleSide, depthWrite: false }));
    scene.add(scanCone);
  }

  if (o.stars) scene.add(makeStars());

  // --- Controls
  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.06;
  controls.enablePan = false;
  controls.enableZoom = o.interactive;
  controls.enableRotate = o.interactive;
  controls.minDistance = 1.8;
  controls.maxDistance = 6;
  controls.rotateSpeed = 0.6;
  controls.zoomSpeed = 0.6;
  // Don't hijack page scrolling with the wheel unless the user holds Ctrl.
  renderer.domElement.addEventListener("wheel", (e) => { if (!e.ctrlKey) e.stopImmediatePropagation(); }, { capture: true });

  // --- Theme
  function applyTheme() {
    const dark = isDark();
    uniforms.sunDir.value.set(dark ? 1.2 : 0.5, dark ? 0.35 : 0.5, dark ? 0.3 : 1).normalize();
    uniforms.nightBoost.value = dark ? 1.7 : 0.9;
    atmoUniforms.color.value.set(dark ? 0x38bdf8 : 0x60a5fa);
  }
  applyTheme();
  window.addEventListener("themechange", applyTheme);

  // --- Resize
  function resize() {
    const w = container.clientWidth, h = container.clientHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    const narrow = w < 860;
    // On portrait phones the globe sits above the text: back off so the whole Earth fits.
    distance = o.distance * (w / h < 0.8 ? 1.32 : 1);
    if (intro >= 1) camera.position.setLength(distance);
    const ox = narrow ? 0 : -w * o.offsetX;
    const oy = h * (narrow ? o.narrowOffsetY : o.offsetY);
    camera.setViewOffset(w, h, ox, oy, w, h);
    camera.updateProjectionMatrix();
  }
  let distance = o.distance;
  let intro = 0;
  resize();
  new ResizeObserver(resize).observe(container);

  // --- Picking
  const ray = new THREE.Raycaster();
  const mouse = new THREE.Vector2();
  let hovered = null;
  let downAt = null;
  function pick(e) {
    const rect = renderer.domElement.getBoundingClientRect();
    mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
    ray.setFromCamera(mouse, camera);
    const hits = ray.intersectObjects(markers.map((m) => m.hit), false);
    if (!hits.length) return null;
    // ignore markers on the far side of the planet
    const earthHit = ray.intersectObject(earth, false)[0];
    if (earthHit && earthHit.distance < hits[0].distance - 0.05) return null;
    return hits[0].object;
  }
  if (o.interactive) {
    renderer.domElement.addEventListener("pointermove", (e) => {
      const obj = pick(e);
      if (obj !== hovered) {
        if (hovered) hovered.userData.cap.scale.setScalar(1);
        hovered = obj;
        renderer.domElement.style.cursor = obj ? "pointer" : "";
      }
      if (o.tooltip) {
        if (obj) {
          const r = obj.userData.region;
          o.tooltip.innerHTML = `<b>${r.name}</b><span class="badge" style="--c:${r.color}">${r.score}/100</span><div class="muted small" style="margin-top:6px">${r.top.join(" · ")}</div>`;
          o.tooltip.style.left = e.clientX + 16 + "px";
          o.tooltip.style.top = e.clientY + 16 + "px";
          o.tooltip.classList.add("show");
        } else o.tooltip.classList.remove("show");
      }
    });
    renderer.domElement.addEventListener("pointerdown", (e) => { downAt = [e.clientX, e.clientY]; });
    renderer.domElement.addEventListener("pointerup", (e) => {
      if (!downAt || Math.hypot(e.clientX - downAt[0], e.clientY - downAt[1]) > 5) return;
      const obj = pick(e);
      if (obj && o.onSelect) o.onSelect(obj.userData.region);
    });
    renderer.domElement.addEventListener("pointerleave", () => o.tooltip && o.tooltip.classList.remove("show"));
  }

  // --- Intro fly-in
  const startDist = distance * 2.4;
  camera.position.setLength(startDist);

  // --- Loop
  const clock = new THREE.Clock();
  const tmp = new THREE.Vector3();
  let visible = true;
  new IntersectionObserver(([e]) => { visible = e.isIntersecting; }).observe(container);

  function frame() {
    requestAnimationFrame(frame);
    if (!visible) return;
    const dt = Math.min(clock.getDelta(), 0.05);
    const t = clock.elapsedTime;

    if (intro < 1) {
      intro = Math.min(1, intro + dt * 0.45);
      const k = 1 - Math.pow(1 - intro, 3);
      camera.position.setLength(startDist + (distance - startDist) * k);
    }
    if (!hovered) spin.rotation.y += o.autoRotate;

    markers.forEach((m) => {
      const s = ((t * 0.6 + m.phase) % 1);
      m.ring.scale.setScalar(1 + s * 2.2);
      m.ring.material.opacity = 0.9 * (1 - s);
      m.beam.material.opacity = 0.55 + 0.35 * Math.sin(t * 2 + m.phase * 5);
    });
    if (hovered) hovered.userData.cap.scale.setScalar(1.8 + 0.3 * Math.sin(t * 8));

    sats.forEach((s, i) => {
      s.angle += dt * s.speed;
      s.sat.position.set(Math.cos(s.angle) * s.radius, 0, Math.sin(s.angle) * s.radius);
      s.sat.lookAt(0, 0, 0);
      if (i === 0 && scanCone) {
        s.sat.getWorldPosition(tmp);
        scanCone.position.copy(tmp);
        const len = tmp.length() - 0.98;
        scanCone.scale.set(1, len, 1);
        scanCone.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), tmp.clone().normalize());
        scanCone.material.opacity = 0.05 + 0.05 * (0.5 + 0.5 * Math.sin(t * 3));
      }
    });

    controls.update();
    renderer.render(scene, camera);
  }
  frame();

  return { scene, camera, renderer, controls };
}

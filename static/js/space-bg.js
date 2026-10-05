// Ambient 3D starfield with parallax and drifting nebula particles (inner pages).
import * as THREE from "three";

const canvas = document.getElementById("space-bg");
if (canvas && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
  const renderer = new THREE.WebGLRenderer({ canvas, alpha: true, antialias: false });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(60, 1, 0.1, 400);
  camera.position.z = 5;

  const N = 2600;
  const geo = new THREE.BufferGeometry();
  const pos = new Float32Array(N * 3);
  for (let i = 0; i < N; i++) {
    pos[i * 3] = (Math.random() - 0.5) * 160;
    pos[i * 3 + 1] = (Math.random() - 0.5) * 100;
    pos[i * 3 + 2] = -Math.random() * 150;
  }
  geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));

  const sprite = (() => {
    const c = document.createElement("canvas");
    c.width = c.height = 64;
    const g = c.getContext("2d");
    const grd = g.createRadialGradient(32, 32, 0, 32, 32, 32);
    grd.addColorStop(0, "rgba(255,255,255,1)");
    grd.addColorStop(0.25, "rgba(255,255,255,.8)");
    grd.addColorStop(1, "rgba(255,255,255,0)");
    g.fillStyle = grd;
    g.fillRect(0, 0, 64, 64);
    return new THREE.CanvasTexture(c);
  })();

  const mat = new THREE.PointsMaterial({ size: 0.5, map: sprite, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending });
  const stars = new THREE.Points(geo, mat);
  scene.add(stars);

  // a few large glowing "nebula" particles
  const neb = new THREE.Group();
  const cols = [0x22d3ee, 0x8b5cf6, 0xd946ef];
  for (let i = 0; i < 14; i++) {
    const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: sprite, color: cols[i % 3], transparent: true, opacity: 0.07, depthWrite: false, blending: THREE.AdditiveBlending }));
    s.position.set((Math.random() - 0.5) * 60, (Math.random() - 0.5) * 30, -30 - Math.random() * 40);
    s.scale.setScalar(20 + Math.random() * 30);
    neb.add(s);
  }
  scene.add(neb);

  function theme() {
    const dark = document.documentElement.dataset.theme !== "light";
    mat.color.set(dark ? 0xffffff : 0x6366f1);
    mat.opacity = dark ? 0.9 : 0.35;
    mat.blending = dark ? THREE.AdditiveBlending : THREE.NormalBlending;
    mat.needsUpdate = true;
    neb.visible = dark;
  }
  theme();
  addEventListener("themechange", theme);

  function resize() {
    renderer.setSize(innerWidth, innerHeight, false);
    camera.aspect = innerWidth / innerHeight;
    camera.updateProjectionMatrix();
  }
  resize();
  addEventListener("resize", resize);

  let mx = 0, my = 0, sy = 0;
  addEventListener("pointermove", (e) => { mx = e.clientX / innerWidth - 0.5; my = e.clientY / innerHeight - 0.5; });
  addEventListener("scroll", () => { sy = scrollY; }, { passive: true });

  const arr = geo.attributes.position.array;
  (function loop() {
    requestAnimationFrame(loop);
    for (let i = 2; i < arr.length; i += 3) {
      arr[i] += 0.04;
      if (arr[i] > 5) arr[i] = -150;
    }
    geo.attributes.position.needsUpdate = true;
    camera.position.x += (mx * 3 - camera.position.x) * 0.03;
    camera.position.y += (-my * 2 - sy * 0.002 - camera.position.y) * 0.03;
    neb.rotation.z += 0.0004;
    renderer.render(scene, camera);
  })();
}

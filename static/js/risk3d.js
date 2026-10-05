// 3D "risk constellation": one glowing crystal tower per hazard around a pulsing core.
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

function labelSprite(text, sub, color) {
  const c = document.createElement("canvas");
  c.width = 512; c.height = 160;
  const g = c.getContext("2d");
  const dark = document.documentElement.dataset.theme !== "light";
  g.font = "600 44px 'Space Grotesk', 'Inter', sans-serif";
  g.textAlign = "center";
  g.fillStyle = dark ? "#e8ecff" : "#0b1230";
  g.fillText(text, 256, 62);
  g.font = "700 52px 'Space Grotesk', sans-serif";
  g.fillStyle = color;
  g.fillText(sub, 256, 128);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: t, transparent: true, depthWrite: false }));
  s.scale.set(1.6, 0.5, 1);
  return s;
}

export function createRiskTowers(el, bars, score, coreColor) {
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  el.appendChild(renderer.domElement);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(40, 1, 0.1, 100);
  camera.position.set(0, 4.2, 7.8);

  scene.add(new THREE.AmbientLight(0xffffff, 0.6));
  const key = new THREE.PointLight(0x22d3ee, 30, 30);
  key.position.set(4, 6, 4);
  const fill = new THREE.PointLight(0xd946ef, 20, 30);
  fill.position.set(-4, 3, -4);
  scene.add(key, fill);

  // platform with concentric rings
  const base = new THREE.Group();
  const discMat = new THREE.MeshStandardMaterial({ transparent: true, metalness: 0.6, roughness: 0.5 });
  const disc = new THREE.Mesh(new THREE.CircleGeometry(3.4, 96), discMat);
  const themeDisc = () => {
    const dark = document.documentElement.dataset.theme !== "light";
    discMat.color.set(dark ? 0x0e1533 : 0xdbe4ff);
    discMat.opacity = dark ? 0.55 : 0.35;
  };
  themeDisc();
  addEventListener("themechange", themeDisc);
  disc.rotation.x = -Math.PI / 2;
  base.add(disc);
  [1.2, 2.2, 3.2].forEach((r, i) => {
    const ring = new THREE.Mesh(new THREE.TorusGeometry(r, 0.008, 6, 160), new THREE.MeshBasicMaterial({ color: i === 2 ? 0x8b5cf6 : 0x22d3ee, transparent: true, opacity: 0.45 }));
    ring.rotation.x = Math.PI / 2;
    base.add(ring);
  });
  scene.add(base);

  // core
  const core = new THREE.Mesh(
    new THREE.IcosahedronGeometry(0.42 + score / 400, 2),
    new THREE.MeshStandardMaterial({ color: coreColor, emissive: coreColor, emissiveIntensity: 0.9, wireframe: true })
  );
  core.position.y = 0.8;
  const coreGlow = new THREE.Mesh(new THREE.SphereGeometry(0.3 + score / 500, 32, 32), new THREE.MeshBasicMaterial({ color: coreColor, transparent: true, opacity: 0.5 }));
  coreGlow.position.y = 0.8;
  scene.add(core, coreGlow);

  // towers
  const towers = [];
  const R = 2.25;
  bars.forEach((b, i) => {
    const a = (i / bars.length) * Math.PI * 2;
    const h = Math.max(0.15, (b.score / 100) * 3);
    const color = new THREE.Color(b.color);
    const geo = new THREE.CylinderGeometry(0.17, 0.2, 1, 6);
    geo.translate(0, 0.5, 0);
    const mesh = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 0.45, metalness: 0.3, roughness: 0.25, transparent: true, opacity: 0.92 }));
    mesh.position.set(Math.cos(a) * R, 0, Math.sin(a) * R);
    mesh.scale.y = 0.001;
    const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geo), new THREE.LineBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.35 }));
    mesh.add(edges);
    const label = labelSprite(b.label, String(b.score), b.color);
    label.position.set(mesh.position.x * 1.12, h + 0.45, mesh.position.z * 1.12);
    label.material.opacity = 0;
    // data link from core to tower top
    const lineGeo = new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0.8, 0), new THREE.Vector3(mesh.position.x, h, mesh.position.z)]);
    const link = new THREE.Line(lineGeo, new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0 }));
    scene.add(mesh, label, link);
    towers.push({ mesh, label, link, h, delay: i * 0.12 });
  });

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.enablePan = false;
  controls.autoRotate = true;
  controls.autoRotateSpeed = 0.9;
  controls.minDistance = 5;
  controls.maxDistance = 13;
  controls.maxPolarAngle = Math.PI / 2.1;
  controls.target.set(0, 0.9, 0);
  renderer.domElement.addEventListener("wheel", (e) => { if (!e.ctrlKey) e.stopImmediatePropagation(); }, { capture: true });

  function resize() {
    const w = el.clientWidth, h = el.clientHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    // Narrow (phone) viewports: pull the camera back so side labels stay in frame.
    const dist = 8.9 * Math.max(1, Math.pow(1.6 / camera.aspect, 0.55));
    const dir = camera.position.clone().sub(controls.target).normalize();
    camera.position.copy(controls.target).add(dir.multiplyScalar(dist));
    controls.maxDistance = Math.max(13, dist * 1.4);
    camera.updateProjectionMatrix();
  }
  resize();
  new ResizeObserver(resize).observe(el);

  const clock = new THREE.Clock();
  (function loop() {
    requestAnimationFrame(loop);
    const t = clock.getElapsedTime();
    towers.forEach((tw) => {
      const k = Math.min(1, Math.max(0, (t - 0.3 - tw.delay) / 1.2));
      const e = 1 - Math.pow(1 - k, 3);
      tw.mesh.scale.y = Math.max(0.001, tw.h * e);
      tw.label.material.opacity = e;
      tw.link.material.opacity = 0.35 * e;
    });
    core.rotation.y = t * 0.6;
    core.rotation.x = t * 0.3;
    coreGlow.scale.setScalar(1 + 0.12 * Math.sin(t * 3));
    controls.update();
    renderer.render(scene, camera);
  })();
}

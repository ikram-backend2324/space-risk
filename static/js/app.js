// SPACE RISK — global UI behaviour
(function () {
  const root = document.documentElement;

  // ---- theme
  function setTheme(t) {
    root.dataset.theme = t;
    try { localStorage.setItem("sr-theme", t); } catch (e) {}
    window.dispatchEvent(new CustomEvent("themechange", { detail: t }));
  }
  document.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-theme-toggle]");
    if (!btn) return;
    // smooth cross-fade when supported
    const next = root.dataset.theme === "light" ? "dark" : "light";
    if (document.startViewTransition) document.startViewTransition(() => setTheme(next));
    else setTheme(next);
  });

  // ---- mobile menu & dropdowns
  document.addEventListener("click", (e) => {
    const menuBtn = e.target.closest("[data-menu-toggle]");
    if (menuBtn) document.querySelector(".nav-links")?.classList.toggle("open");
    const dd = e.target.closest("[data-dropdown]");
    document.querySelectorAll(".dropdown.open").forEach((d) => { if (!d.contains(e.target)) d.classList.remove("open"); });
    if (dd && e.target.closest("[data-dropdown-trigger]")) dd.classList.toggle("open");
  });

  // ---- toasts
  window.toast = function (text, kind = "info") {
    let box = document.querySelector(".toasts");
    if (!box) { box = document.createElement("div"); box.className = "toasts"; document.body.appendChild(box); }
    const el = document.createElement("div");
    el.className = "toast " + kind;
    el.textContent = text;
    box.appendChild(el);
    setTimeout(() => { el.classList.add("hide"); setTimeout(() => el.remove(), 400); }, 4500);
  };
  document.querySelectorAll(".toast").forEach((el, i) => {
    setTimeout(() => { el.classList.add("hide"); setTimeout(() => el.remove(), 400); }, 4500 + i * 400);
  });

  // ---- reveal on scroll + animated counters/bars
  function animateCount(el) {
    const target = parseFloat(el.dataset.count);
    const dec = (el.dataset.count.split(".")[1] || "").length;
    const dur = 1600, t0 = performance.now();
    (function step(now) {
      const k = Math.min(1, (now - t0) / dur);
      const v = target * (1 - Math.pow(1 - k, 4));
      el.textContent = v.toLocaleString("uz-UZ", { minimumFractionDigits: dec, maximumFractionDigits: dec });
      if (k < 1) requestAnimationFrame(step);
    })(t0);
  }
  const io = new IntersectionObserver((entries) => {
    entries.forEach((en) => {
      if (!en.isIntersecting) return;
      const el = en.target;
      el.classList.add("in");
      el.querySelectorAll("[data-count]").forEach(animateCount);
      if (el.matches("[data-count]")) animateCount(el);
      el.querySelectorAll("[data-width]").forEach((b) => (b.style.width = b.dataset.width + "%"));
      io.unobserve(el);
    });
  }, { threshold: 0.12 });
  document.querySelectorAll(".reveal, [data-count], .bars").forEach((el) => io.observe(el));

  // ---- 3D tilt cards
  if (matchMedia("(hover: hover)").matches) {
    document.querySelectorAll(".tilt").forEach((card) => {
      card.addEventListener("pointermove", (e) => {
        const r = card.getBoundingClientRect();
        const x = (e.clientX - r.left) / r.width - 0.5;
        const y = (e.clientY - r.top) / r.height - 0.5;
        card.style.transform = `perspective(900px) rotateY(${x * 8}deg) rotateX(${-y * 8}deg) translateY(-3px)`;
      });
      card.addEventListener("pointerleave", () => (card.style.transform = ""));
    });
  }

  // ---- password visibility + strength
  document.querySelectorAll(".toggle-pass").forEach((btn) => {
    btn.addEventListener("click", () => {
      const input = btn.parentElement.querySelector("input");
      input.type = input.type === "password" ? "text" : "password";
      btn.classList.toggle("on");
    });
  });
  document.querySelectorAll("[data-pw-meter]").forEach((input) => {
    const bar = document.querySelector(input.dataset.pwMeter + " span");
    input.addEventListener("input", () => {
      const v = input.value;
      let s = 0;
      if (v.length >= 8) s++;
      if (/[A-Z]/.test(v) && /[a-z]/.test(v)) s++;
      if (/\d/.test(v)) s++;
      if (/[^A-Za-z0-9]/.test(v) || v.length >= 12) s++;
      bar.style.width = (s / 4) * 100 + "%";
      bar.style.background = ["#f43f5e", "#f97316", "#eab308", "#22c55e", "#22c55e"][s];
    });
  });

  // ---- icons
  if (window.lucide) window.lucide.createIcons();
})();

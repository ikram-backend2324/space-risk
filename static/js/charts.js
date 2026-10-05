// Chart.js defaults that follow the site theme.
(function () {
  const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
  const charts = [];

  function applyDefaults() {
    Chart.defaults.font.family = "Inter, system-ui, sans-serif";
    Chart.defaults.color = css("--muted");
    Chart.defaults.borderColor = css("--border");
    Chart.defaults.plugins.tooltip.backgroundColor = css("--surface-solid");
    Chart.defaults.plugins.tooltip.titleColor = css("--text");
    Chart.defaults.plugins.tooltip.bodyColor = css("--text");
    Chart.defaults.plugins.tooltip.borderColor = css("--border-strong");
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.padding = 12;
    Chart.defaults.plugins.tooltip.cornerRadius = 10;
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.boxWidth = 8;
  }

  function restyle(chart) {
    const grid = css("--border"), muted = css("--muted");
    Object.values(chart.options.scales || {}).forEach((s) => {
      if (s.grid) s.grid.color = grid;
      if (s.angleLines) s.angleLines.color = grid;
      if (s.ticks) s.ticks.color = muted;
      if (s.pointLabels && typeof s.pointLabels.color !== "function") s.pointLabels.color = css("--text");
    });
    if (chart.options.plugins?.legend?.labels) chart.options.plugins.legend.labels.color = muted;
    chart.update("none");
  }

  window.srChart = function (el, config) {
    applyDefaults();
    const chart = new Chart(el, config);
    charts.push(chart);
    restyle(chart);
    return chart;
  };

  window.srGradient = function (ctx, area, from, to) {
    const g = ctx.createLinearGradient(0, area.top, 0, area.bottom);
    g.addColorStop(0, from);
    g.addColorStop(1, to);
    return g;
  };

  window.addEventListener("themechange", () => {
    applyDefaults();
    setTimeout(() => charts.forEach(restyle), 30);
  });
})();

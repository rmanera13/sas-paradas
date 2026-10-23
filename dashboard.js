"use strict";
(async () => {
  const get = (u) => fetch("/api/v1" + u).then((r) => r.json());
  const esc = (t) => String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const [r, p] = await Promise.all([get("/analytics/resumo"), get("/analytics/pareto")]);

  const kpis = [
    ["Paradas fechadas", r.total_paradas], ["Minutos parados", r.minutos_total],
    ["MTTR (min)", r.mttr_min], ["Programado (min)", r.min_programado],
    ["Não programado (min)", r.min_nao_programado], ["Abertas / sem motivo", r.paradas_abertas],
  ];
  document.querySelector("#kpis").innerHTML = kpis.map(([t, v]) => `<div class="kpi">${t}<b>${v}</b></div>`).join("");

  document.querySelector("#tab-pareto").innerHTML = p.map((x) => `<tr><td>${esc(x.codigo)} — ${esc(x.descricao)}</td>
    <td>${x.programado ? "Programado" : "Não programado"}</td><td>${x.ocorrencias}</td>
    <td>${x.minutos}</td><td>${x.pct_acumulado}%</td></tr>`).join("") || '<tr><td colspan="5">Sem dados.</td></tr>';

  if (window.Chart && p.length) {
    new Chart(document.querySelector("#pareto"), {
      data: {
        labels: p.map((x) => x.codigo),
        datasets: [
          { type: "bar", label: "Minutos", data: p.map((x) => x.minutos), backgroundColor: "#0b4f8a", yAxisID: "y" },
          { type: "line", label: "% acumulado", data: p.map((x) => x.pct_acumulado), borderColor: "#b00020", yAxisID: "y1" },
        ],
      },
      options: { maintainAspectRatio: false, scales: { y: { beginAtZero: true }, y1: { position: "right", min: 0, max: 100 } } },
    });
  }
})();

"use strict";
(() => {
  const $ = (s) => document.querySelector(s);
  const get = (u) => fetch("/api/v1" + u).then((r) => r.json());
  const esc = (t) => String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const num = (v, casas = 2) => (v === null || v === undefined ? "—" : Number(v).toLocaleString("pt-BR", { maximumFractionDigits: casas }));

  async function carregar() {
    const dias = $("#dias").value;
    $("#btn-excel").href = `/api/v1/export.xlsx?dias=${dias}`;
    const [r, p, m] = await Promise.all([get("/analytics/resumo"), get("/analytics/pareto"), get(`/analytics/mtbf?dias=${dias}`)]);

    const kpis = [
      [`MTBF ${dias}d (h)`, m.geral.mtbf_h === null ? "Sem falhas" : num(m.geral.mtbf_h)],
      ["MTTR (min)", num(r.mttr_min)],
      ["Paradas fechadas", r.total_paradas], ["Minutos parados", num(r.minutos_total)],
      ["Programado (min)", num(r.min_programado)], ["Não programado (min)", num(r.min_nao_programado)],
      ["Abertas / sem motivo", r.paradas_abertas],
    ];
    $("#kpis").innerHTML = kpis.map(([t, v]) => `<div class="kpi">${t}<b>${v}</b></div>`).join("");

    $("#tab-mtbf").innerHTML = m.por_equipamento.map((l) => `<tr><td>${esc(l.equipamento)}</td>
        <td>${num(l.horas_operacao)}</td><td>${num(l.horas_paradas)}</td><td>${l.falhas}</td>
        <td>${l.mtbf_h === null ? "Sem falhas" : num(l.mtbf_h)}</td><td>${num(l.mttr_min)}</td></tr>`).join("")
      + `<tr class="total"><td>Total</td><td>${num(m.geral.horas_operacao)}</td><td>—</td><td>${m.geral.falhas}</td>
        <td>${m.geral.mtbf_h === null ? "Sem falhas" : num(m.geral.mtbf_h)}</td><td>${num(m.geral.mttr_min)}</td></tr>`;

    $("#tab-pareto").innerHTML = p.map((x) => `<tr><td>${esc(x.codigo)} — ${esc(x.descricao)}</td>
      <td>${x.programado ? "Programado" : "Não programado"}</td><td>${x.ocorrencias}</td>
      <td>${num(x.minutos)}</td><td>${x.pct_acumulado}%</td></tr>`).join("") || '<tr><td colspan="5">Sem dados.</td></tr>';

    if (window.Chart && p.length && !carregar.grafico) {
      carregar.grafico = new Chart($("#pareto"), {
        data: {
          labels: p.map((x) => x.codigo),
          datasets: [
            { type: "bar", label: "Minutos", data: p.map((x) => x.minutos), backgroundColor: "#2b5fab", yAxisID: "y" },
            { type: "line", label: "% acumulado", data: p.map((x) => x.pct_acumulado), borderColor: "#111", backgroundColor: "#111", yAxisID: "y1" },
          ],
        },
        options: { maintainAspectRatio: false, scales: { y: { beginAtZero: true }, y1: { position: "right", min: 0, max: 100 } } },
      });
    }
  }

  $("#dias").addEventListener("change", carregar);
  carregar();
})();

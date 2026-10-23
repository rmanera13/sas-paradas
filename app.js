"use strict";
const API = "/api/v1";
const $ = (s) => document.querySelector(s);
const opInput = $("#operador");
let motivos = [];
let paradasAbertas = {}; // equipamento_id -> parada

const esc = (t) => String(t ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fmtData = (iso) => (iso ? new Date(iso).toLocaleString("pt-BR") : "—");

function aviso(msg, erro = false) {
  const el = $("#aviso");
  el.textContent = msg;
  el.className = "aviso on" + (erro ? " erro" : "");
  clearTimeout(aviso.t);
  aviso.t = setTimeout(() => (el.className = "aviso"), 4000);
}

async function api(url, opts = {}) {
  const r = await fetch(API + url, { headers: { "Content-Type": "application/json" }, ...opts });
  const dados = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(dados.erro || "Erro " + r.status);
  return dados;
}

function opcoesMotivo() {
  return '<option value="">Selecione o motivo…</option>' +
    motivos.map((m) => `<option value="${m.id}">${esc(m.codigo)} — ${esc(m.descricao)}${m.programado ? " (programado)" : ""}</option>`).join("");
}

function operador() {
  const nome = opInput.value.trim();
  if (nome.length < 2) {
    aviso("Digite o nome do operador antes de apontar.", true);
    opInput.focus();
    return null;
  }
  localStorage.setItem("sas_operador", nome);
  return nome;
}

function cronometro(inicio) {
  const s = Math.max(0, Math.floor((Date.now() - new Date(inicio)) / 1000));
  const p = (n) => String(n).padStart(2, "0");
  return `${p(Math.floor(s / 3600))}:${p(Math.floor((s % 3600) / 60))}:${p(s % 60)}`;
}

async function carregar() {
  const [eqs, abertas, pend, ult, ops] = await Promise.all([
    api("/equipamentos"), api("/paradas?status=ABERTA"),
    api("/paradas?status=AGUARDANDO_MOTIVO"), api("/paradas"), api("/operadores"),
  ]);
  paradasAbertas = Object.fromEntries(abertas.map((p) => [p.equipamento_id, p]));
  $("#lista-operadores").innerHTML = ops.map((o) => `<option value="${esc(o)}">`).join("");
  renderGrade(eqs);
  renderPendentes(pend);
  $("#ultimas").innerHTML = ult.slice(0, 20).map((p) => `<tr>
      <td>${esc(p.equipamento)}</td><td>${esc(p.operador)}</td><td>${fmtData(p.inicio)}</td>
      <td>${p.duracao_min ?? "—"}</td><td>${esc(p.motivo || "—")}</td><td>${esc(p.status)}</td></tr>`).join("")
    || '<tr><td colspan="6">Nenhuma parada registrada.</td></tr>';
}

function renderGrade(eqs) {
  $("#grade").innerHTML = eqs.map((e) => {
    const p = paradasAbertas[e.id];
    if (!p) {
      return `<article class="card" aria-label="${esc(e.nome)} rodando">
        <h3>${esc(e.nome)}</h3><span class="estado">● Rodando</span>
        <button class="btn parou" data-acao="parou" data-eq="${e.id}">PAROU</button></article>`;
    }
    return `<article class="card parada" aria-label="${esc(e.nome)} parada">
      <h3>${esc(e.nome)}</h3><span class="estado">■ Parada · ${esc(p.operador)}</span>
      <span class="crono" data-inicio="${p.inicio}" aria-hidden="true">${cronometro(p.inicio)}</span>
      <label for="mot-${p.id}">Motivo</label>
      <select id="mot-${p.id}">${opcoesMotivo()}</select>
      <label for="obs-${p.id}">Observação (opcional)</label>
      <input id="obs-${p.id}" type="text" maxlength="500">
      <button class="btn sec" data-acao="motivo" data-id="${p.id}">Salvar motivo</button>
      <button class="btn retomou" data-acao="retomou" data-id="${p.id}">RETOMOU</button></article>`;
  }).join("");
  eqs.forEach((e) => {
    const p = paradasAbertas[e.id];
    if (p && p.motivo_id) $(`#mot-${p.id}`).value = p.motivo_id;
    if (p && p.observacao) $(`#obs-${p.id}`).value = p.observacao;
  });
}

function renderPendentes(lista) {
  $("#secao-pend").hidden = lista.length === 0;
  $("#pendentes").innerHTML = lista.map((p) => `<div class="pend">
      <div><strong>${esc(p.equipamento)}</strong><br>${fmtData(p.inicio)} · ${p.duracao_min} min · ${esc(p.operador)}</div>
      <div><label for="mot-${p.id}">Motivo</label><select id="mot-${p.id}">${opcoesMotivo()}</select></div>
      <div><label for="obs-${p.id}">Observação</label><input id="obs-${p.id}" type="text" maxlength="500"></div>
      <button class="btn" data-acao="motivo" data-id="${p.id}">Classificar</button></div>`).join("");
}

document.addEventListener("click", async (ev) => {
  const b = ev.target.closest("button[data-acao]");
  if (!b) return;
  b.disabled = true;
  try {
    if (b.dataset.acao === "parou") {
      const nome = operador();
      if (!nome) return;
      await api("/paradas", { method: "POST", body: JSON.stringify({ equipamento_id: +b.dataset.eq, operador: nome }) });
      aviso("Parada registrada. Informe o motivo.");
    } else if (b.dataset.acao === "motivo") {
      const id = b.dataset.id, mot = $(`#mot-${id}`).value;
      if (!mot) { aviso("Selecione o motivo.", true); $(`#mot-${id}`).focus(); return; }
      await api(`/paradas/${id}`, { method: "PATCH", body: JSON.stringify({ motivo_id: +mot, observacao: $(`#obs-${id}`).value }) });
      aviso("Motivo salvo.");
    } else if (b.dataset.acao === "retomou") {
      const id = b.dataset.id, mot = $(`#mot-${id}`).value;
      if (mot) await api(`/paradas/${id}`, { method: "PATCH", body: JSON.stringify({ motivo_id: +mot, observacao: $(`#obs-${id}`).value }) });
      const p = await api(`/paradas/${id}/retomar`, { method: "POST" });
      aviso(p.status === "FECHADA" ? `Retomada. Duração: ${p.duracao_min} min.` : "Retomada. Falta classificar o motivo.");
    }
    await carregar();
  } catch (e) {
    aviso(e.message, true);
  } finally {
    b.disabled = false;
  }
});

setInterval(() => document.querySelectorAll(".crono").forEach((c) => (c.textContent = cronometro(c.dataset.inicio))), 1000);
// Atualiza a tela a cada 30 s (outros operadores), sem atrapalhar quem está preenchendo
setInterval(() => { if (!document.activeElement.closest(".card,.pend")) carregar().catch(() => {}); }, 30000);

(async () => {
  opInput.value = localStorage.getItem("sas_operador") || "";
  try {
    motivos = await api("/motivos");
    await carregar();
  } catch (e) {
    aviso("Falha ao carregar: " + e.message, true);
  }
})();

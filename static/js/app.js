// Navigation
document.querySelectorAll('.nav-item').forEach(item => {
  item.addEventListener('click', e => {
    e.preventDefault();
    const view = item.dataset.view;
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    item.classList.add('active');
    document.getElementById('view-' + view).classList.add('active');
    if (view === 'dashboard') loadDashboard();
    if (view === 'dataset') loadDataset();
    if (view === 'exportar') loadExportStats();
    if (view === 'nova') resetForm();
  });
});

// Badge helpers
function badgeClass(value, type) {
  const map = {
    classificacao: { fraude:'badge-fraude', legitima:'badge-legitima', suspeita:'badge-suspeita' },
    tipo: { smishing:'badge-smishing', phishing:'badge-phishing', scam:'badge-scam', outro:'badge-outro' }
  };
  return 'badge ' + (map[type]?.[value] || 'badge-outro');
}

function badgeLabel(value) {
  const labels = { fraude:'Fraude', legitima:'Legítima', suspeita:'Suspeita', smishing:'Smishing', phishing:'Phishing', scam:'Scam', outro:'Outro' };
  return labels[value] || value;
}

// DASHBOARD
async function loadDashboard() {
  const stats = await fetch('/api/stats').then(r => r.json());
  document.getElementById('stat-total').textContent = stats.total;
  document.getElementById('stat-fraudes').textContent = stats.fraudes;
  document.getElementById('stat-legitimas').textContent = stats.legitimas;
  document.getElementById('stat-suspeitas').textContent = stats.suspeitas;
  document.getElementById('stat-revisadas').textContent = stats.revisadas;
  document.getElementById('sidebar-total').textContent = stats.total;

  const pct = v => stats.total ? Math.round(v / stats.total * 100) : 0;
  document.getElementById('bar-fraudes').style.width = pct(stats.fraudes) + '%';
  document.getElementById('bar-legitimas').style.width = pct(stats.legitimas) + '%';
  document.getElementById('bar-suspeitas').style.width = pct(stats.suspeitas) + '%';
  document.getElementById('bar-revisadas').style.width = pct(stats.revisadas) + '%';

  const colors = { smishing:'#9b72e8', phishing:'#4f8ef7', scam:'#3dd6f5', outro:'#4a5068' };
  const fontColors = { sms:'#f0b429', whatsapp:'#3ec98a', email:'#4f8ef7', simulada:'#9b72e8' };

  renderBarChart('chart-tipos', stats.por_tipo, colors, stats.total);
  renderBarChart('chart-fontes', stats.por_fonte, fontColors, stats.total);

  const msgs = await fetch('/api/mensagens').then(r => r.json());
  const recent = msgs.slice(0, 5);
  document.getElementById('recent-list').innerHTML = recent.map(m => `
    <div class="recent-item">
      <span class="recent-id">#${m.id}</span>
      <span class="recent-text">${m.texto}</span>
      <span class="recent-badge badge ${badgeClass(m.classificacao,'classificacao').split(' ')[1]}">${badgeLabel(m.classificacao)}</span>
    </div>
  `).join('') || '<p style="color:var(--text3);font-size:13px">Nenhuma mensagem cadastrada.</p>';
}

function renderBarChart(containerId, data, colors, total) {
  const el = document.getElementById(containerId);
  if (!data || !Object.keys(data).length) { el.innerHTML = '<p style="color:var(--text3);font-size:12px">Sem dados</p>'; return; }
  const max = Math.max(...Object.values(data));
  el.innerHTML = Object.entries(data).map(([k, v]) => {
    const color = colors[k.toLowerCase()] || '#4a5068';
    const w = max ? Math.round(v / max * 100) : 0;
    return `<div class="bar-row">
      <span class="bar-label">${k}</span>
      <div class="bar-track"><div class="bar-fill" style="width:${w}%;background:${color}"></div></div>
      <span class="bar-val">${v}</span>
    </div>`;
  }).join('');
}

// DATASET
let debounceTimer;
async function loadDataset(params = {}) {
  const qs = new URLSearchParams(params).toString();
  const msgs = await fetch('/api/mensagens?' + qs).then(r => r.json());
  const body = document.getElementById('tabela-body');
  const empty = document.getElementById('empty-state');
  document.getElementById('dataset-count').textContent = msgs.length;
  document.getElementById('sidebar-total').textContent = msgs.length;

  if (!msgs.length) {
    body.innerHTML = '';
    empty.style.display = 'block';
    return;
  }
  empty.style.display = 'none';
  body.innerHTML = msgs.map(m => `
    <tr>
      <td class="td-id">#${m.id}</td>
      <td class="td-texto" title="${m.texto}">${m.texto}</td>
      <td><span class="${badgeClass(m.classificacao,'classificacao')}">${badgeLabel(m.classificacao)}</span></td>
      <td><span class="${badgeClass(m.tipo_golpe,'tipo')}">${badgeLabel(m.tipo_golpe)}</span></td>
      <td style="color:var(--text2);font-size:12px">${m.fonte}</td>
      <td style="color:var(--text3);font-family:var(--mono);font-size:11px">${m.data_cadastro}</td>
      <td>${m.revisada ? '<span class="rev-check">✓</span>' : '<span style="color:var(--text3)">—</span>'}</td>
      <td>
        <div class="td-actions">
          <button class="btn-action view" onclick="verDetalhe(${m.id})">Ver</button>
          <button class="btn-action" onclick="editarMensagem(${m.id})">Editar</button>
          <button class="btn-action del" onclick="excluir(${m.id})">Excluir</button>
        </div>
      </td>
    </tr>
  `).join('');
}

function getFilters() {
  return {
    busca: document.getElementById('busca').value,
    classificacao: document.getElementById('f-classificacao').value,
    tipo_golpe: document.getElementById('f-tipo').value,
    fonte: document.getElementById('f-fonte').value
  };
}

document.getElementById('busca').addEventListener('input', () => {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => loadDataset(getFilters()), 300);
});
['f-classificacao','f-tipo','f-fonte'].forEach(id => {
  document.getElementById(id).addEventListener('change', () => loadDataset(getFilters()));
});

function limparFiltros() {
  document.getElementById('busca').value = '';
  document.getElementById('f-classificacao').value = 'todos';
  document.getElementById('f-tipo').value = 'todos';
  document.getElementById('f-fonte').value = 'todos';
  loadDataset();
}

// FORM
function resetForm() {
  document.getElementById('edit-id').value = '';
  document.getElementById('form-title').textContent = 'Nova Mensagem';
  document.getElementById('btn-save-text').textContent = 'Salvar Mensagem';
  document.getElementById('f-texto').value = '';
  document.getElementById('f-class').value = '';
  document.getElementById('f-tipo-golpe').value = '';
  document.getElementById('f-fonte-form').value = '';
  document.getElementById('f-obs').value = '';
  document.getElementById('f-revisada').checked = false;
  document.getElementById('char-count').textContent = '0';
  document.getElementById('form-msg').style.display = 'none';
}

document.getElementById('f-texto').addEventListener('input', e => {
  document.getElementById('char-count').textContent = e.target.value.length;
});

async function editarMensagem(id) {
  const m = await fetch(`/api/mensagens/${id}`).then(r => r.json());
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelector('[data-view="nova"]').classList.add('active');
  document.getElementById('view-nova').classList.add('active');

  document.getElementById('edit-id').value = m.id;
  document.getElementById('form-title').textContent = `Editar Mensagem #${m.id}`;
  document.getElementById('btn-save-text').textContent = 'Atualizar Mensagem';
  document.getElementById('f-texto').value = m.texto;
  document.getElementById('char-count').textContent = m.texto.length;
  document.getElementById('f-class').value = m.classificacao;
  document.getElementById('f-tipo-golpe').value = m.tipo_golpe;
  document.getElementById('f-fonte-form').value = m.fonte;
  document.getElementById('f-obs').value = m.observacoes || '';
  document.getElementById('f-revisada').checked = !!m.revisada;
  document.getElementById('form-msg').style.display = 'none';
}

async function salvarMensagem() {
  const texto = document.getElementById('f-texto').value.trim();
  const classificacao = document.getElementById('f-class').value;
  const tipo_golpe = document.getElementById('f-tipo-golpe').value;
  const fonte = document.getElementById('f-fonte-form').value;
  const msg = document.getElementById('form-msg');

  if (!texto || !classificacao || !tipo_golpe || !fonte) {
    msg.textContent = 'Preencha todos os campos obrigatórios.';
    msg.className = 'form-message error';
    msg.style.display = 'block';
    return;
  }

  const body = {
    texto, classificacao, tipo_golpe, fonte,
    observacoes: document.getElementById('f-obs').value,
    revisada: document.getElementById('f-revisada').checked ? 1 : 0
  };

  const editId = document.getElementById('edit-id').value;
  const url = editId ? `/api/mensagens/${editId}` : '/api/mensagens';
  const method = editId ? 'PUT' : 'POST';

  const res = await fetch(url, { method, headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) });
  if (res.ok) {
    msg.textContent = editId ? '✓ Mensagem atualizada com sucesso!' : '✓ Mensagem cadastrada com sucesso!';
    msg.className = 'form-message success';
    msg.style.display = 'block';
    showToast(editId ? 'Mensagem atualizada!' : 'Mensagem cadastrada!');
    if (!editId) resetForm();
    loadStats();
  } else {
    msg.textContent = 'Erro ao salvar. Tente novamente.';
    msg.className = 'form-message error';
    msg.style.display = 'block';
  }
}

function cancelarEdicao() {
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelector('[data-view="dataset"]').classList.add('active');
  document.getElementById('view-dataset').classList.add('active');
  loadDataset();
}

async function excluir(id) {
  if (!confirm(`Excluir mensagem #${id}? Esta ação não pode ser desfeita.`)) return;
  await fetch(`/api/mensagens/${id}`, { method: 'DELETE' });
  showToast('Mensagem excluída.');
  loadDataset(getFilters());
  loadStats();
}

// DETALHE MODAL
async function verDetalhe(id) {
  const m = await fetch(`/api/mensagens/${id}`).then(r => r.json());
  document.getElementById('modal-id-badge').textContent = `ID #${m.id} · ${m.data_cadastro}`;
  document.getElementById('modal-texto').textContent = m.texto;
  document.getElementById('modal-class').innerHTML = `<span class="${badgeClass(m.classificacao,'classificacao')}">${badgeLabel(m.classificacao)}</span>`;
  document.getElementById('modal-tipo').innerHTML = `<span class="${badgeClass(m.tipo_golpe,'tipo')}">${badgeLabel(m.tipo_golpe)}</span>`;
  document.getElementById('modal-fonte').innerHTML = `<span style="color:var(--text2)">${m.fonte}</span>`;
  document.getElementById('modal-data').innerHTML = `<span style="font-family:var(--mono);font-size:12px;color:var(--text2)">${m.data_cadastro}</span>`;
  document.getElementById('modal-rev').innerHTML = m.revisada
    ? `<span class="badge badge-sim">✓ Sim</span>`
    : `<span class="badge badge-nao">Não</span>`;
  const obsSection = document.getElementById('modal-obs-section');
  if (m.observacoes) {
    document.getElementById('modal-obs').textContent = m.observacoes;
    obsSection.style.display = 'block';
  } else {
    obsSection.style.display = 'none';
  }
  document.getElementById('modal-bg').style.display = 'flex';
}

function fecharModal() { document.getElementById('modal-bg').style.display = 'none'; }

document.addEventListener('keydown', e => { if (e.key === 'Escape') fecharModal(); });

// EXPORTAR
async function loadExportStats() {
  const stats = await fetch('/api/stats').then(r => r.json());
  const grid = document.getElementById('export-stats');
  const items = [
    ['Total de registros', stats.total],
    ['Fraudes', stats.fraudes],
    ['Legítimas', stats.legitimas],
    ['Suspeitas', stats.suspeitas],
    ['Revisadas', stats.revisadas],
    ['Smishing', stats.por_tipo?.smishing || 0],
    ['Phishing', stats.por_tipo?.phishing || 0],
    ['Scam', stats.por_tipo?.scam || 0],
  ];
  grid.innerHTML = items.map(([label, val]) => `
    <div class="export-stat">
      <div class="export-stat-label">${label}</div>
      <div class="export-stat-val">${val}</div>
    </div>
  `).join('');
}

function exportar(format) {
  window.location.href = `/api/export/${format}`;
  showToast(`Exportando ${format.toUpperCase()}...`);
}

// TOAST
function showToast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.style.display = 'block';
  setTimeout(() => { t.style.display = 'none'; }, 2500);
}

// STATS sidebar counter
async function loadStats() {
  const stats = await fetch('/api/stats').then(r => r.json());
  document.getElementById('sidebar-total').textContent = stats.total;
}

// INIT
loadDashboard();
loadStats();

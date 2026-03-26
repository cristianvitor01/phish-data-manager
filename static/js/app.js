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
    // Close sidebar on mobile after navigation
    if (window.innerWidth <= 900) {
      document.querySelector('.sidebar').classList.remove('open');
      document.getElementById('sidebar-overlay').classList.remove('show');
    }
  });
});

// Mobile menu toggle
document.getElementById('mobile-menu-btn').addEventListener('click', () => {
  const sidebar = document.querySelector('.sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  sidebar.classList.toggle('open');
  overlay.classList.toggle('show');
});

// Close sidebar when clicking overlay
document.getElementById('sidebar-overlay').addEventListener('click', () => {
  const sidebar = document.querySelector('.sidebar');
  const overlay = document.getElementById('sidebar-overlay');
  sidebar.classList.remove('open');
  overlay.classList.remove('show');
});

// BADGES
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

// DATASET
async function loadDataset(params = {}) {
  const qs = new URLSearchParams(params).toString();
  const msgs = await fetch('/api/mensagens?' + qs).then(r => r.json());

  const body = document.getElementById('tabela-body');
  const emptyState = document.getElementById('empty-state');
  const datasetCount = document.getElementById('dataset-count');
  const sidebarTotal = document.getElementById('sidebar-total');

  datasetCount.textContent = msgs.length;
  sidebarTotal.textContent = msgs.length;
  emptyState.style.display = msgs.length ? 'none' : 'flex';

  body.innerHTML = msgs.map(m => `
    <tr>
      <td>#${m.id}</td>
      <td>${m.texto}</td>
      <td><span class="${badgeClass(m.classificacao,'classificacao')}">${badgeLabel(m.classificacao)}</span></td>
      <td>${m.tipo_golpe}</td>
      <td>${m.fonte}</td>
      <td>${m.origem || '-'}</td>
      <td>${m.data_cadastro}</td>
      <td>${m.revisada ? '✓' : '-'}</td>
      <td>
        <button class="btn-action view" onclick="verDetalhe(${m.id})">Ver</button>
        <button class="btn-action edit" onclick="editarMensagem(${m.id})">Editar</button>
        <button class="btn-action del" onclick="excluir(${m.id})">Excluir</button>
      </td>
    </tr>
  `).join('');
}

// FILTROS
function getFilters() {
  const filtros = {
    busca: document.getElementById('busca').value.trim(),
    classificacao: document.getElementById('f-classificacao').value,
    tipo_golpe: document.getElementById('f-tipo').value,
    fonte: document.getElementById('f-fonte').value,
    origem: document.getElementById('f-origem').value // NOVO
  };

  // remover filtros não aplicáveis para evitar query string redundante
  Object.keys(filtros).forEach(key => {
    if (filtros[key] === '' || filtros[key] === 'todos') {
      delete filtros[key];
    }
  });

  return filtros;
}

function applyFilters() {
  loadDataset(getFilters());
}

// FORM
function resetForm() {
  document.getElementById('edit-id').value = '';
  document.getElementById('f-texto').value = '';
  document.getElementById('f-class').value = '';
  document.getElementById('f-tipo-golpe').value = '';
  document.getElementById('f-fonte-form').value = '';
  document.getElementById('f-origem-form').value = ''; // NOVO
  document.getElementById('f-obs').value = '';
  document.getElementById('f-revisada').checked = false;
  document.getElementById('form-title').textContent = 'Nova Mensagem';
}

async function editarMensagem(id) {
  const m = await fetch(`/api/mensagens/${id}`).then(r => r.json());

  document.getElementById('edit-id').value = m.id;
  document.getElementById('f-texto').value = m.texto;
  document.getElementById('f-class').value = m.classificacao;
  document.getElementById('f-tipo-golpe').value = m.tipo_golpe;
  document.getElementById('f-fonte-form').value = m.fonte;
  document.getElementById('f-origem-form').value = m.origem; // NOVO
  document.getElementById('f-obs').value = m.observacoes || '';
  document.getElementById('f-revisada').checked = !!m.revisada;

  // Switch to form view
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelector('[data-view="nova"]').classList.add('active');
  document.getElementById('view-nova').classList.add('active');

  // Change title
  document.getElementById('form-title').textContent = 'Editar Mensagem';
}

async function salvarMensagem() {
  const texto = document.getElementById('f-texto').value.trim();
  const classificacao = document.getElementById('f-class').value;
  const tipo_golpe = document.getElementById('f-tipo-golpe').value;
  const fonte = document.getElementById('f-fonte-form').value;
  const origem = document.getElementById('f-origem-form').value; // NOVO

  if (!texto || !classificacao || !tipo_golpe || !fonte || !origem) {
    alert('Preencha todos os campos obrigatórios.');
    return;
  }

  const body = {
    texto,
    classificacao,
    tipo_golpe,
    fonte,
    origem, // NOVO
    observacoes: document.getElementById('f-obs').value,
    revisada: document.getElementById('f-revisada').checked
  };

  const editId = document.getElementById('edit-id').value;
  const url = editId ? `/api/mensagens/${editId}` : '/api/mensagens';
  const method = editId ? 'PUT' : 'POST';

  const res = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });

  if (res.ok) {
    alert('Salvo com sucesso!');
    resetForm();
    loadDataset();
    // Switch back to dataset view
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.querySelector('[data-view="dataset"]').classList.add('active');
    document.getElementById('view-dataset').classList.add('active');
  } else {
    alert('Erro ao salvar');
  }
}

// MODAL
async function verDetalhe(id) {
  const m = await fetch(`/api/mensagens/${id}`).then(r => r.json());

  document.getElementById('modal-texto').textContent = m.texto;
  document.getElementById('modal-class').textContent = m.classificacao;
  document.getElementById('modal-tipo').textContent = m.tipo_golpe;
  document.getElementById('modal-fonte').textContent = m.fonte;
  document.getElementById('modal-origem').textContent = m.origem || '-'; // NOVO
  document.getElementById('modal-data').textContent = m.data_cadastro;

  document.getElementById('modal-bg').style.display = 'flex';
}

function fecharModal() {
  document.getElementById('modal-bg').style.display = 'none';
}

async function loadDashboard() {
  try {
    const stats = await fetch('/api/stats').then(r => {
      if (!r.ok) throw new Error('Erro ao buscar stats');
      return r.json();
    });

    const total = stats.total || 0;
    document.getElementById('stat-total').textContent = total;
    document.getElementById('stat-fraudes').textContent = stats.fraudes || 0;
    document.getElementById('stat-legitimas').textContent = stats.legitimas || 0;
    document.getElementById('stat-suspeitas').textContent = stats.suspeitas || 0;
    document.getElementById('stat-revisadas').textContent = stats.revisadas || 0;

    const bar = (value) => `${total ? Math.round((value / total) * 100) : 0}%`;
    document.getElementById('bar-fraudes').style.width = bar(stats.fraudes || 0);
    document.getElementById('bar-legitimas').style.width = bar(stats.legitimas || 0);
    document.getElementById('bar-suspeitas').style.width = bar(stats.suspeitas || 0);
    document.getElementById('bar-revisadas').style.width = bar(stats.revisadas || 0);

    const recent = await fetch('/api/mensagens').then(r => r.json());
    const recentItems = (recent || []).slice(0, 5);
    document.getElementById('recent-list').innerHTML = recentItems.map(m =>
      `<div class="recent-item"><strong>#${m.id}</strong> ${m.texto.slice(0, 80)} ${m.texto.length > 80 ? '...' : ''}</div>`
    ).join('') || '<div class="recent-item">Nenhuma mensagem disponível.</div>';

    const buildGrid = (source, containerId) => {
      const section = document.getElementById(containerId);
      if (!section) return;
      const items = source || {};
      section.innerHTML = Object.entries(items).map(([k,v]) =>
        `<div class="bar-line"><span>${k}</span><div class="bar-wrapper"><div class="bar-fill" style="width:${total?Math.round((v/total)*100):0}%"></div></div><small>${v}</small></div>`
      ).join('') || '<p>Nenhum dado disponível</p>';
    };

    buildGrid(stats.por_tipo, 'chart-tipos');
    buildGrid(stats.por_fonte, 'chart-fontes');
  } catch (err) {
    console.error(err);
    alert('Erro ao carregar dashboard. Veja console.');
  }
}

async function loadExportStats() {
  try {
    const stats = await fetch('/api/stats').then(r => {
      if (!r.ok) throw new Error('Erro ao buscar stats');
      return r.json();
    });

    const container = document.getElementById('export-stats');
    container.innerHTML = `
      <div><strong>Total:</strong> ${stats.total || 0}</div>
      <div><strong>Fraudes:</strong> ${stats.fraudes || 0}</div>
      <div><strong>Legítimas:</strong> ${stats.legitimas || 0}</div>
      <div><strong>Suspeitas:</strong> ${stats.suspeitas || 0}</div>
      <div><strong>Revisadas:</strong> ${stats.revisadas || 0}</div>
      <div><strong>Origem:</strong> ${JSON.stringify(stats.por_origem || {})}</div>
    `;
  } catch (err) {
    console.error(err);
    alert('Erro ao carregar estatísticas de exportação.');
  }
}

function limparFiltros() {
  document.getElementById('busca').value = '';
  document.getElementById('f-classificacao').value = 'todos';
  document.getElementById('f-tipo').value = 'todos';
  document.getElementById('f-fonte').value = 'todos';
  document.getElementById('f-origem').value = 'todos';
  loadDataset();
}

async function excluir(id) {
  if (!confirm('Confirmar exclusão?')) return;
  const res = await fetch(`/api/mensagens/${id}`, { method: 'DELETE' });
  if (res.ok) {
    alert('Mensagem excluída com sucesso');
    loadDataset();
    loadDashboard();
  } else {
    alert('Falha ao excluir mensagem');
  }
}

function cancelarEdicao() {
  resetForm();
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelector('[data-view="dataset"]').classList.add('active');
  document.getElementById('view-dataset').classList.add('active');
  loadDataset();
}

function exportar(tipo) {
  window.location.href = `/api/export/${tipo}`;
}

document.addEventListener('DOMContentLoaded', () => {
  loadDashboard();
  loadDataset();

  document.getElementById('busca').addEventListener('input', () => applyFilters());
  document.getElementById('f-classificacao').addEventListener('change', () => applyFilters());
  document.getElementById('f-tipo').addEventListener('change', () => applyFilters());
  document.getElementById('f-fonte').addEventListener('change', () => applyFilters());
  document.getElementById('f-origem').addEventListener('change', () => applyFilters());
});
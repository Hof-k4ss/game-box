const state = { games: [], system: 'all', query: '' };
const gamesEl = document.getElementById('games');
const systemsEl = document.getElementById('systems');
const searchEl = document.getElementById('search');
const summaryEl = document.getElementById('summary');
const statusEl = document.getElementById('status');
const emptyEl = document.getElementById('empty');

function esc(value) {
  return String(value).replace(/[&<>\"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]));
}

function prettyName(name) {
  return name.replace(/\.(zip|7z)$/i, '').replace(/[._]+/g, ' ').replace(/\s+/g, ' ').trim();
}

function renderSystems(systems) {
  const all = [{ id: 'all', label: 'Tous', count: state.games.length }, ...systems];
  systemsEl.innerHTML = all.map(s => `<button class="system ${state.system === s.id ? 'active' : ''}" data-system="${esc(s.id)}">${esc(s.label)} <small>${s.count}</small></button>`).join('');
  systemsEl.querySelectorAll('.system').forEach(button => button.addEventListener('click', () => {
    state.system = button.dataset.system;
    render();
  }));
}

function filteredGames() {
  const q = state.query.toLocaleLowerCase('fr');
  return state.games.filter(game => {
    const systemOk = state.system === 'all' || game.system === state.system;
    const queryOk = !q || `${game.name} ${game.systemLabel}`.toLocaleLowerCase('fr').includes(q);
    return systemOk && queryOk;
  });
}

function launch(game) {
  if (!game.core) {
    alert('Ce jeu est dans « À trier » et n’a pas encore de système connu.');
    return;
  }
  const params = new URLSearchParams({
    rom: game.url,
    core: game.core,
    name: prettyName(game.name)
  });
  location.href = `/play.html?${params}`;
}

function render() {
  const visible = filteredGames();
  gamesEl.innerHTML = visible.map(game => `
    <button class="game-card" data-id="${esc(game.id)}">
      <div class="cover ${esc(game.system)}"><span>${esc(game.systemLabel)}</span></div>
      <div class="game-name">${esc(prettyName(game.name))}</div>
      <div class="game-system">${esc(game.systemLabel)}</div>
    </button>`).join('');
  emptyEl.hidden = visible.length !== 0;
  summaryEl.textContent = `${visible.length} jeu${visible.length > 1 ? 'x' : ''} affiché${visible.length > 1 ? 's' : ''} · ${state.games.length} au total`;
  gamesEl.querySelectorAll('.game-card').forEach(card => {
    card.addEventListener('click', () => launch(state.games.find(game => game.id === card.dataset.id)));
  });
}

async function load() {
  statusEl.textContent = 'Chargement…';
  try {
    const response = await fetch('/api/games', { cache: 'no-store' });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    state.games = data.games || [];
    renderSystems(data.systems || []);
    render();
    statusEl.textContent = '● Prêt';
  } catch (error) {
    statusEl.textContent = 'Erreur';
    gamesEl.innerHTML = `<div class="error">Impossible de charger la bibliothèque.<br><small>${esc(error.message)}</small></div>`;
  }
}

searchEl.addEventListener('input', event => {
  state.query = event.target.value;
  render();
});
document.getElementById('refresh').addEventListener('click', load);
load();

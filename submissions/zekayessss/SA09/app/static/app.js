'use strict';

// UI «Заявки практикума». Контракт: submissions/zekayessss/SA09/contract.md, разделы 3 и 7.
// Пользовательские данные вставляются только через textContent/createElement (РК-20).

const STATUSES = ['новая', 'в работе', 'готово'];

const els = {
  createForm: document.getElementById('create-form'),
  createTitle: document.getElementById('create-title'),
  createDescription: document.getElementById('create-description'),
  createError: document.getElementById('create-error'),
  filterQ: document.getElementById('filter-q'),
  filterStatus: document.getElementById('filter-status'),
  listError: document.getElementById('list-error'),
  tbody: document.getElementById('tasks-body'),
  listEmpty: document.getElementById('list-empty'),
  importForm: document.getElementById('import-form'),
  importFile: document.getElementById('import-file'),
  importError: document.getElementById('import-error'),
  importResult: document.getElementById('import-result'),
  importAccepted: document.getElementById('import-accepted'),
  importErrorsBlock: document.getElementById('import-errors-block'),
  importErrors: document.getElementById('import-errors'),
};

// Читает ответ: JSON, если возможно; иначе текст. Возвращает {ok, status, data}.
async function readResponse(resp) {
  let data = null;
  const text = await resp.text();
  try {
    data = text ? JSON.parse(text) : null;
  } catch (e) {
    data = null;
  }
  return { ok: resp.ok, status: resp.status, data, text };
}

function errorText(res) {
  if (res.data && typeof res.data.error === 'string') return res.data.error;
  return 'Ошибка сервера (HTTP ' + res.status + ')';
}

async function request(url, options) {
  try {
    const resp = await fetch(url, options);
    return await readResponse(resp);
  } catch (e) {
    return { ok: false, status: 0, data: { error: 'Сервер недоступен' }, text: '' };
  }
}

// ---------- Список: GET /api/tasks?q=…&status=… ----------

let listRequestSeq = 0;

async function loadTasks() {
  const params = new URLSearchParams();
  const q = els.filterQ.value;
  const status = els.filterStatus.value;
  if (q.trim() !== '') params.set('q', q);
  if (status !== '') params.set('status', status);
  const qs = params.toString();
  const url = '/api/tasks' + (qs ? '?' + qs : '');

  const seq = ++listRequestSeq;
  const res = await request(url, { method: 'GET' });
  if (seq !== listRequestSeq) return; // устаревший ответ

  if (!res.ok || !res.data || !Array.isArray(res.data.tasks)) {
    els.listError.textContent = errorText(res);
    return;
  }
  els.listError.textContent = '';
  renderTasks(res.data.tasks);
}

function cell(text, label, className) {
  const td = document.createElement('td');
  td.textContent = text;
  td.dataset.label = label;
  if (className) td.className = className;
  return td;
}

function button(text, onClick, secondary) {
  const b = document.createElement('button');
  b.type = 'button';
  b.textContent = text;
  if (secondary) b.className = 'secondary';
  b.addEventListener('click', onClick);
  return b;
}

function renderTasks(tasks) {
  els.tbody.replaceChildren();
  for (const task of tasks) {
    els.tbody.appendChild(renderViewRow(task));
  }
  els.listEmpty.hidden = tasks.length !== 0;
}

function renderViewRow(task) {
  const tr = document.createElement('tr');
  tr.appendChild(cell(task.id, 'id'));
  tr.appendChild(cell(task.title, 'Название'));
  tr.appendChild(cell(task.description, 'Описание', 'desc'));
  tr.appendChild(cell(task.status, 'Статус'));
  const actions = document.createElement('td');
  actions.className = 'actions';
  actions.dataset.label = 'Действия';
  actions.appendChild(button('Изменить', () => {
    tr.replaceWith(renderEditRow(task));
  }, true));
  tr.appendChild(actions);
  return tr;
}

// ---------- Редактирование: PATCH /api/tasks/<id> ----------

function renderEditRow(task) {
  const tr = document.createElement('tr');
  tr.appendChild(cell(task.id, 'id'));

  const titleTd = document.createElement('td');
  titleTd.dataset.label = 'Название';
  const titleInput = document.createElement('input');
  titleInput.type = 'text';
  titleInput.value = task.title;
  titleInput.setAttribute('aria-label', 'Название');
  titleTd.appendChild(titleInput);
  tr.appendChild(titleTd);

  const descTd = document.createElement('td');
  descTd.dataset.label = 'Описание';
  const descInput = document.createElement('textarea');
  descInput.rows = 2;
  descInput.value = task.description;
  descInput.setAttribute('aria-label', 'Описание');
  descTd.appendChild(descInput);
  tr.appendChild(descTd);

  const statusTd = document.createElement('td');
  statusTd.dataset.label = 'Статус';
  const statusSelect = document.createElement('select');
  statusSelect.setAttribute('aria-label', 'Статус');
  for (const s of STATUSES) {
    const opt = document.createElement('option');
    opt.value = s;
    opt.textContent = s;
    if (s === task.status) opt.selected = true;
    statusSelect.appendChild(opt);
  }
  statusTd.appendChild(statusSelect);
  tr.appendChild(statusTd);

  const actions = document.createElement('td');
  actions.className = 'actions';
  actions.dataset.label = 'Действия';
  const err = document.createElement('p');
  err.className = 'error';
  err.setAttribute('role', 'alert');

  const saveBtn = button('Сохранить', async () => {
    saveBtn.disabled = true;
    err.textContent = '';
    const body = {
      title: titleInput.value,
      description: descInput.value,
      status: statusSelect.value,
    };
    const res = await request('/api/tasks/' + encodeURIComponent(task.id), {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    saveBtn.disabled = false;
    if (!res.ok) {
      err.textContent = errorText(res);
      return;
    }
    await loadTasks();
  });
  const cancelBtn = button('Отмена', () => {
    tr.replaceWith(renderViewRow(task));
  }, true);

  actions.appendChild(saveBtn);
  actions.appendChild(cancelBtn);
  actions.appendChild(err);
  tr.appendChild(actions);
  return tr;
}

// ---------- Создание: POST /api/tasks ----------

els.createForm.addEventListener('submit', async (ev) => {
  ev.preventDefault();
  els.createError.textContent = '';
  const submitBtn = els.createForm.querySelector('button[type="submit"]');
  submitBtn.disabled = true;
  const res = await request('/api/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      title: els.createTitle.value,
      description: els.createDescription.value,
    }),
  });
  submitBtn.disabled = false;
  if (!res.ok) {
    els.createError.textContent = errorText(res);
    return;
  }
  els.createForm.reset();
  await loadTasks();
});

// ---------- Импорт: POST /api/import (сырые байты CSV, РК-11) ----------

function clearImportResult() {
  els.importError.textContent = '';
  els.importResult.hidden = true;
  els.importAccepted.textContent = '';
  els.importErrors.replaceChildren();
  els.importErrorsBlock.hidden = true;
}

els.importForm.addEventListener('submit', async (ev) => {
  ev.preventDefault();
  clearImportResult();
  const file = els.importFile.files && els.importFile.files[0];
  if (!file) {
    els.importError.textContent = 'Выберите CSV-файл';
    return;
  }
  const submitBtn = els.importForm.querySelector('button[type="submit"]');
  submitBtn.disabled = true;
  const res = await request('/api/import', {
    method: 'POST',
    headers: { 'Content-Type': 'text/csv' },
    body: file,
  });
  submitBtn.disabled = false;

  if (!res.ok || !res.data || !Array.isArray(res.data.accepted) || !Array.isArray(res.data.errors)) {
    els.importError.textContent = errorText(res);
    await loadTasks();
    return;
  }

  const r = res.data;
  els.importAccepted.textContent =
    'Принято: ' + r.accepted.length + ' (создано ' + r.created + ', обновлено ' + r.updated + ')';
  for (const e of r.errors) {
    const li = document.createElement('li');
    li.textContent = 'Строка ' + e.line + ' (id ' + e.id + '): ' + e.error;
    els.importErrors.appendChild(li);
  }
  els.importErrorsBlock.hidden = r.errors.length === 0;
  els.importResult.hidden = false;
  await loadTasks();
});

// ---------- Поиск и фильтр ----------

let searchTimer = null;
els.filterQ.addEventListener('input', () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(loadTasks, 250);
});
els.filterStatus.addEventListener('change', loadTasks);

loadTasks();

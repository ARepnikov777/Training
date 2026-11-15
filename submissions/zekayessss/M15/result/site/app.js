/* Учебный стенд; mode=shop-buggy и form-buggy содержат намеренные дефекты. */
const $ = (id) => document.getElementById(id);
const config = fetch('/api/config').then((r) => r.json());
const request = async (path, method, data) => {
  const r = await fetch(path, {method, headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data)});
  return {ok: r.ok, data: await r.json()};
};
if ($('register')) {
  const token = crypto.randomUUID();
  $('register').onsubmit = async (event) => {
    event.preventDefault();
    const r = await request('/api/register', 'POST', {name: $('name').value, email: $('email').value, consent: $('consent').checked, token});
    $('result').textContent = r.ok ? `Регистрация сохранена: ${r.data.id}` : `Ошибки: ${r.data.errors.join(', ')}`;
  };
}
if ($('shop')) {
  $('shop').onsubmit = async (event) => {
    event.preventDefault();
    // M15: проверка и скидка применяются всегда, независимо от режима config.json.
    const price = Number($('price').value), qty = Number($('quantity').value), discount = Number($('discount').value);
    if ([$('price'), $('quantity'), $('discount')].some((x) => !x.value.trim()) || !Number.isFinite(price) || price < 0 || !Number.isInteger(qty) || qty <= 0 || !Number.isFinite(discount) || discount < 0 || discount > 100) {
      $('total').textContent = 'Ошибка: проверьте цену, количество и скидку'; return;
    }
    $('total').textContent = (price * qty * (1 - discount / 100)).toFixed(2);
  };
}
if ($('ticket')) {
  const refresh = async () => {
    const records = await fetch('/api/tickets?q=' + encodeURIComponent($('search').value)).then((r) => r.json());
    $('tickets').replaceChildren();
    for (const record of records) {
      const card = document.createElement('section');
      const heading = document.createElement('h2'); heading.textContent = `${record.title} (${record.id})`; card.append(heading);
      const title = document.createElement('input'); title.value = record.title; title.setAttribute('aria-label', 'Название заявки'); card.append(title);
      const description = document.createElement('textarea'); description.value = record.description; description.setAttribute('aria-label', 'Описание заявки'); card.append(description);
      const select = document.createElement('select'); select.setAttribute('aria-label', 'Статус');
      for (const status of ['новая', 'в работе', 'готово']) { const option = document.createElement('option'); option.textContent = status; option.selected = status === record.status; select.append(option); }
      card.append(select);
      const button = document.createElement('button'); button.textContent = 'Сохранить';
      button.onclick = async () => { const r = await request('/api/tickets/' + record.id, 'PUT', {title: title.value, description: description.value, status: select.value}); $('result').textContent = r.ok ? 'Изменения сохранены' : r.data.error; await refresh(); };
      card.append(button); $('tickets').append(card);
    }
  };
  $('ticket').onsubmit = async (event) => { event.preventDefault(); const r = await request('/api/tickets', 'POST', {title: $('title').value, description: $('description').value}); $('result').textContent = r.ok ? 'Создана: ' + r.data.id : r.data.error; await refresh(); };
  $('find').onclick = refresh;
  refresh();
}

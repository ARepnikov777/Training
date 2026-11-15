// Регрессионный тест калькулятора /shop.
// Выполняет настоящий app.js из указанной папки сайта в изолированном контексте Node
// с минимальной моделью страницы /shop (поля price, quantity, discount, форма shop, итог total).
// /api/config отдаётся из config.json той же папки (режим shop-buggy не меняется).
//
// Запуск: node tests/test_shop.js <папка-сайта>
// Код выхода 0 — все сценарии прошли, 1 — есть падения.

'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const siteDir = path.resolve(process.argv[2] || path.join(__dirname, '..', 'result', 'site'));
const source = fs.readFileSync(path.join(siteDir, 'app.js'), 'utf8');
const config = JSON.parse(fs.readFileSync(path.join(siteDir, 'config.json'), 'utf8'));

function loadShop() {
  const elements = {};
  for (const id of ['shop', 'price', 'quantity', 'discount', 'total']) {
    elements[id] = {id, value: '', textContent: '', onsubmit: null};
  }
  const context = vm.createContext({
    document: {getElementById: (id) => elements[id] || null},
    fetch: async (url) => {
      if (url !== '/api/config') throw new Error('Неожиданный запрос: ' + url);
      return {ok: true, json: async () => config};
    },
    crypto: {randomUUID: () => 'test-token'},
    console,
  });
  vm.runInContext(source, context, {filename: path.join(siteDir, 'app.js')});
  return elements;
}

async function calculate(price, quantity, discount) {
  const el = loadShop();
  el.price.value = price;
  el.quantity.value = quantity;
  el.discount.value = discount;
  await el.shop.onsubmit({preventDefault() {}});
  return el.total.textContent;
}

const ERROR = Symbol('error');
// [описание, цена, количество, скидка, ожидание]
const cases = [
  // Исходные сценарии checks/scenarios.md
  ['S1 скидка учитывается: 1000×3, скидка 10', '1000', '3', '10', '2700.00'],
  ['S2 пустое количество → ошибка', '1000', '', '10', ERROR],
  ['S2 количество из пробелов → ошибка', '1000', '   ', '10', ERROR],
  ['S2 пустая цена → ошибка', '', '3', '10', ERROR],
  ['S2 пустая скидка → ошибка', '1000', '3', '', ERROR],
  ['S2 цена < 0 → ошибка', '-1', '3', '10', ERROR],
  ['S2 цена не число → ошибка', 'abc', '3', '10', ERROR],
  ['S2 количество 0 → ошибка', '1000', '0', '10', ERROR],
  ['S2 количество отрицательное → ошибка', '1000', '-2', '10', ERROR],
  ['S2 количество дробное 2.5 → ошибка', '1000', '2.5', '10', ERROR],
  ['S2 скидка < 0 → ошибка', '1000', '3', '-1', ERROR],
  ['S2 скидка > 100 → ошибка', '1000', '3', '101', ERROR],
  // Соседние сценарии checks/scenarios.md — поведение должно сохраниться
  ['N1 100×2, скидка 0 → 200.00', '100', '2', '0', '200.00'],
  ['N2 100×2, скидка 100 → 0.00', '100', '2', '100', '0.00'],
  // Границы правил input/requirements.md
  ['B1 цена 0 допустима → 0.00', '0', '5', '10', '0.00'],
  ['B2 округление до 2 знаков: 19.99×3, скидка 15 → 50.97', '19.99', '3', '15', '50.97'],
];

(async () => {
  console.log(`Сайт: ${path.relative(process.cwd(), siteDir)}`);
  console.log(`config.json mode: ${config.mode}`);
  let failed = 0;
  for (const [name, price, quantity, discount, expected] of cases) {
    const actual = await calculate(price, quantity, discount);
    const ok = expected === ERROR
      ? actual.startsWith('Ошибка') && !/\d/.test(actual)
      : actual === expected;
    if (!ok) failed++;
    const want = expected === ERROR ? 'сообщение об ошибке без числового итога' : expected;
    console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}\n      ввод: цена=${JSON.stringify(price)} кол-во=${JSON.stringify(quantity)} скидка=${JSON.stringify(discount)}\n      ожидается: ${want}; фактически: ${JSON.stringify(actual)}`);
  }
  console.log(`\nИтого: ${cases.length - failed} PASS, ${failed} FAIL из ${cases.length}`);
  process.exit(failed ? 1 : 0);
})().catch((e) => { console.error(e); process.exit(2); });

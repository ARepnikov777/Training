# Контракт извлечения и сопоставления SA08

Входы — source/H05/input/{contract,appendix,specification}.pdf. Только синтетические документы. Приоритет документа не установлен. checks/expected.json открывается только после сохранения первого результата сопоставления.

CSV UTF-8, запятая, заголовок: parameter,value,unit,source_file,page,quote,notes. Одна строка на условие, страница с 1. parameter: model,quantity,ram,storage,unit_price,total_price,delivery_date,warranty,vat,initial_setup,location; допускается отдельный дополнительный параметр при явном условии PDF. value передаёт исходное значение, числа с десятичной точкой; quote сохраняет точную формулировку. Если условия нет: value=NOT_STATED, page=1 и quote пустая, notes указывает проверенный диапазон страниц. Это не доказательство противоположного условия. source_file — имя PDF. Несколько связанных значений допускаются в одной ячейке с точной цитатой.

Матрица comparison.csv: parameter,contract_value,appendix_value,specification_value,contract_source,appendix_source,specification_source,classification,conclusion. Каждая source содержит файл, страницу, цитату. classification: match,contradiction,uncertainty. Для contradiction нужны несовместимые явные утверждения минимум двух PDF, а не отсутствие поля. Арифметическое следствие отмечается как расчёт с формулой, не как цитата документа.

findings.md: устойчивый ID, параметр, классификация, доказательства минимум двух документов для несовпадения, влияние, что согласовать. questions-to-supplier.md: вопрос, связанный ID, условие и документы для единой редакции. Это черновик, отправка запрещена. Не выбираем победившее условие, не даём юридическое заключение.

Извлечение каждого PDF — один worker в собственном worktree, только его CSV и evidence. Координатор интегрирует после проверки всех трёх. Синтез имеет одного владельца. Reviewer только читает, его ответ сохраняет координатор.

"""Учебный проект. Процентная скидка содержит намеренный дефект."""

def total(price, quantity, discount_percent=0):
    if price < 0 or quantity <= 0 or int(quantity) != quantity or not 0 <= discount_percent <= 100:
        raise ValueError('Недопустимый ввод')
    return round(price * quantity * (1 - discount_percent), 2)

if __name__ == '__main__':
    print(total(1000, 3, 10))

from modules.basket_module.commands_to_db import get_product_data_from_db


async def generate_basket_template(data):
    if len(data) == 0:
        result = "В корзине нет товаров"
        return result, None, None
    result = "Корзина:\n\n"
    sum = 0
    for line in data:
        count = line['count']
        product_data = get_product_data_from_db(line['product_id'])
        name = product_data['name']
        price = product_data['price']
        currency = product_data['currency']
        result += f"{name}:\n" \
                  f"{count} x {price} {currency} = {price*count} {currency}\n"
        sum += price*count
    result += f"\n Сумма корзины: {sum} {currency}"
    return result, sum, currency

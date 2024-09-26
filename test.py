import telebot
from telebot.types import LabeledPrice, ShippingOption
import config


token = "6713001953:AAHE_Ea-lfwyItE-QFgkafeblDTDThwEn50"
provider_token = '410694247:TEST:784078c4-60ac-4834-a487-bfe8e2ff26b4'
bot = telebot.TeleBot(token)

# More about Payments: https://core.telegram.org/bots/payments

prices = [LabeledPrice(label='Working Time Machine', amount=5750), LabeledPrice('Gift wrapping', 500)]

shipping_options = [
    ShippingOption(id='instant', title='WorldWide Teleporter').add_price(LabeledPrice('Teleporter', 1000)),
    ShippingOption(id='pickup', title='Local pickup').add_price(LabeledPrice('Pickup', 300))]


@bot.message_handler(commands=['start'])
def command_start(message):
    bot.send_message(message.chat.id,
                     "Hello, I'm the demo merchant bot."
                     " I can sell you a Time Machine."
                     " Use /buy to order one, /terms for Terms and Conditions")


@bot.message_handler(commands=['terms'])
def command_terms(message):
    bot.send_message(message.chat.id,
                     'Thank you for shopping with our demo bot. We hope you like your new time machine!\n'
                     '1. If your time machine was not delivered on time, please rethink your concept of time and try again.\n'
                     '2. If you find that your time machine is not working, kindly contact our future service workshops on Trappist-1e.'
                     ' They will be accessible anywhere between May 2075 and November 4000 C.E.\n'
                     '3. If you would like a refund, kindly apply for one yesterday and we will have sent it to you immediately.')


@bot.message_handler(commands=['buy'])
def command_pay(message):
    bot.send_message(message.chat.id,
                     "Real cards won't work with me, no money will be debited from your account."
                     " Use this test card number to pay for your Time Machine: `4242 4242 4242 4242`"
                     "\n\nThis is your demo invoice:", parse_mode='Markdown')
    bot.send_invoice(
                     message.chat.id,  #chat_id
                     'Working Time Machine', #title
                     ' Want to visit your great-great-great-grandparents? Make a fortune at the races? Shake hands with Hammurabi and take a stroll in the Hanging Gardens? Order our Working Time Machine today!', #description
                     'HAPPY FRIDAYS COUPON', #invoice_payload
                     provider_token, #provider_token
                     'usd', #currency
                     prices, #prices
                     photo_url='http://erkelzaar.tsudao.com/models/perrotta/TIME_MACHINE.jpg',
                     photo_height=512,  # !=0/None or picture won't be shown
                     photo_width=512,
                     photo_size=512,
                     is_flexible=False, 
                     need_shipping_address=True,
                     need_email=True,
                     # True If you need to set up Shipping Fee
                     start_parameter='time-machine-example')


@bot.shipping_query_handler(func=lambda query: True)
def shipping(shipping_query):
    print(shipping_query)
    bot.answer_shipping_query(shipping_query.id, ok=True, shipping_options=shipping_options,
                              error_message='Oh, seems like our Dog couriers are having a lunch right now. Try again later!')


@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True,
                                  error_message="Aliens tried to steal your card's CVV, but we successfully protected your credentials,"
                                                " try to pay again in a few minutes, we need a small rest.")


@bot.message_handler(content_types=['successful_payment'])
def got_payment(message: telebot.types.Message):

    payment_info = message.successful_payment

    formatted_message = f"🛑 WE GOT PAYMENT 💸\n"\
                        f"<b>User:</b> @{message.from_user.username}\n"\
                        f"<b>Email:</b> {payment_info.order_info.email}\n"\
                        f"<b>Address:</b> {payment_info.order_info.shipping_address}\n"\
                        f"<b>Total Amount:</b> ${payment_info.total_amount / 100:.2f}"

    bot.send_message(message.chat.id, formatted_message, parse_mode='HTML')
    


bot.infinity_polling(skip_pending = True)
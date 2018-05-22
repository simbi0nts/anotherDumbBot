# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import telebot
from telebot.util import async

from logic import *
import config


class Object(object):
    pass


FILE_URL = "https://api.telegram.org/file/bot{0}/{1}"

telebot.apihelper.proxy = config.proxy
bot = telebot.TeleBot(config.token)

engine = create_engine('mysql+pymysql://{0}@localhost/{1}?charset=utf8mb4'.format(config.us, config.db), encoding='utf8')
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

bot.mysql = Object()
bot.mysql.engine = engine
cursor = bot.mysql.cursor = Session()


def save_photo_in_db(usr_id, file_id):
    sql = "INSERT INTO `last_image` (`user_id`, `file_id`) VALUES ({0}, '{1}')"
    sql = sql.format(usr_id, file_id)
    bot.mysql.cursor.execute(sql)
    bot.mysql.cursor.commit()


def update_or_create_photo_in_db(usr_id, file_id):
    sql = "UPDATE `last_image` SET file_id='{0}' WHERE user_id={1}"
    sql = sql.format(file_id, usr_id)
    result = bot.mysql.cursor.execute(sql)
    bot.mysql.cursor.commit()
    if not result.rowcount:
        save_photo_in_db(usr_id, file_id)


def get_photo_in_db(usr_id):
    sql = 'SELECT file_id FROM `last_image` WHERE user_id={0}'
    sql = sql.format(usr_id)
    result = bot.mysql.cursor.execute(sql).fetchall()
    if len(result) == 0:
        return
    return result[0]['file_id']


def get_google_image(searchterm):
    url = "https://www.google.co.in/search?q=" + searchterm + "&source=lnms&tbm=isch"

    CHROME_PATH = config.CHROME_PATH
    CHROMEDRIVER_PATH = config.CHROMEDRIVER_PATH
    WINDOW_SIZE = config.WINDOW_SIZE

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--window-size=%s" % WINDOW_SIZE)
    chrome_options.binary_location = CHROME_PATH

    browser = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH,
                               chrome_options=chrome_options)
    browser.get(url)

    for _ in range(10):
        browser.execute_script("window.scrollBy(0,10000)")

    elms = browser.find_elements_by_xpath('//div[contains(@class,"rg_meta")]')
    try:
        random.shuffle(elms)
    except Exception as e:
        print(e)

    for x in elms:
        img = json.loads(x.get_attribute('innerHTML'))["ou"]
        try:
            response = requests.get(img, stream=True)

            if response.ok:
                _t = bytes()
                for block in response.iter_content(1024):
                    if not block:
                        break
                    _t += block
            break
        except:
            pass

    browser.close()
    return _t


def process_photo_message_with_url(message):
    try:
        url = message.text.split(' ')[-1]
        response = requests.get(url, stream=True)

        if response.ok:
            _t = bytes()
            for block in response.iter_content(1024):
                if not block:
                    break
                _t += block
            return url, _t

    except Exception:
        file_id = get_photo_in_db(message.from_user.id)
        if not file_id:
            return
        file_info = bot.get_file(file_id)
        url = FILE_URL.format(config.token, file_info.file_path)
        return url, bot.download_file(file_info.file_path)


def process_photo_message(message, no_google=False):
    url = message.text.split(' ')[-1]
    try:
        response = requests.get(url, stream=True)

        if response.ok:
            _t = bytes()
            for block in response.iter_content(1024):
                if not block:
                    break
                _t += block
            return _t
    except Exception:
        if not no_google and len(message.text.split(' ')) != 1:
            return get_google_image(url)

    file_id = get_photo_in_db(message.from_user.id)
    if not file_id:
        return
    file_info = bot.get_file(file_id)
    return bot.download_file(file_info.file_path)


@bot.message_handler(content_types=["photo"])
@async()
def on_photo(message):
    file_id = message.photo[-1].file_id
    update_or_create_photo_in_db(message.from_user.id, file_id)


@bot.message_handler(commands=['magik'])
@async()
def on_magik(message):
    try:
        magik_value = int(message.text.split(' ')[1])
        photo = process_photo_message(message, no_google=True) if len(message.text.split(' ')) == 2 \
            else process_photo_message(message)
    except (ValueError, IndexError):
        photo = process_photo_message(message)
        magik_value = 3
    bot.send_photo(message.chat.id, do_magik(photo, magik_value))


@bot.message_handler(commands=['gmagik'])
@async()
def on_gmagik(message):
    photo = process_photo_message(message, no_google=True) if message.text.split(' ')[-1] == 'ext' \
        else process_photo_message(message)
    try:
        magik_value = 2 if message.text.split(' ')[1] == 'ext' else 1
    except (ValueError, IndexError):
        magik_value = 1
    bot.send_document(message.chat.id, gmagik(photo, magik_value))


@bot.message_handler(commands=['trig', 'triggered'])
@async()
def on_triggered(message):
    photo = process_photo_message(message)
    bot.send_document(message.chat.id, triggered(photo))


@bot.message_handler(commands=['badmeme', 'bad_meme'])
@async()
def on_badmeme(message):
    meme = badmeme()
    bot.send_photo(message.chat.id, meme)


@bot.message_handler(commands=['jpeg'])
@async()
def on_jpeg(message):
    try:
        quality = int(message.text.split(' ')[1])
        photo = process_photo_message(message, no_google=True) if len(message.text.split(' ')) == 2 \
            else process_photo_message(message)
    except (ValueError, IndexError):
        photo = process_photo_message(message)
        quality = 1
    bot.send_photo(message.chat.id, jpeg(photo, quality))


@bot.message_handler(commands=['a'])
@async()
def on_a(message):
    user_name = message.from_user.first_name + ' ' + message.from_user.last_name
    bot.send_photo(message.chat.id, a(user_name))


@bot.message_handler(commands=['gif'])
@async()
def on_gif(message):
    try:
        text = ' '.join(message.text.split(' ')[1:])
    except (ValueError, IndexError):
        text = None
    bot.send_message(message.chat.id, giphy(text))


@bot.message_handler(commands=['retro1', 'retro'])
@async()
def on_retro1(message):
    bot.send_photo(message.chat.id, do_retro(' '.join(message.text.split(' ')[1:]), '5'))


@bot.message_handler(commands=['retro2'])
@async()
def on_retro2(message):
    bot.send_photo(message.chat.id, do_retro(' '.join(message.text.split(' ')[1:]), '2'))


@bot.message_handler(commands=['retro3'])
@async()
def on_retro3(message):
    bot.send_photo(message.chat.id, do_retro(' '.join(message.text.split(' ')[1:]), '4'))


@bot.message_handler(commands=['glitch', 'glitch1', 'gglitch'])
@async()
def on_glitch1(message):
    photo = process_photo_message(message)

    iterations = amount = seed = url = None
    opts = message.text.split(' ')
    if len(opts) == 2:
        url = opts[1]
    elif len(opts) == 3:
        seed = int(opts[1])
        url = opts[2]
    elif len(opts) == 4:
        amount = int(opts[1])
        seed = int(opts[2])
        url = opts[3]
    elif len(opts) == 5:
        iterations = int(opts[1])
        amount = int(opts[2])
        seed = int(opts[3])
        url = opts[4]

    _isgif = isgif(url) if url else None

    if _isgif:
        bot.send_document(message.chat.id, glitch(photo, iterations, amount, seed, url, _isgif))
    else:
        bot.send_photo(message.chat.id, glitch(photo, iterations, amount, seed, url, _isgif))


@bot.message_handler(commands=['glitch2'])
@async()
def on_glitch2(message):
    photo = process_photo_message(message)
    bot.send_photo(message.chat.id, glitch2(photo))


@bot.message_handler(commands=['eye', 'eyes'])
@async()
def on_eye(message):
    url, photo = process_photo_message_with_url(message)

    eye = resize = None
    opts = message.text.split(' ')
    if len(opts) == 2:
        eye = opts[1]
    elif len(opts) == 3:
        eye = opts[1]
        url = opts[2]
    elif len(opts) == 4:
        eye = opts[1]
        resize = opts[2]
        url = opts[3]

    if eye == 'list':
        bot.send_message(message.chat.id, eyes_list())
    else:
        bot.send_photo(message.chat.id, eyes(photo, eye=eye, resize=resize, url=url))


@bot.message_handler(commands=['help'])
@async()
def on_help(message):
    with open('files/help.txt', 'r') as help_file:
        help_msg = help_file.read()
    bot.send_message(message.chat.id, help_msg)


def run():
    bot.polling(none_stop=True)


def while_true_run():
    # for debug only
    import time
    while True:
        try:
            run()
        except:
            time.sleep(10)


if __name__ == "__main__":
    run()

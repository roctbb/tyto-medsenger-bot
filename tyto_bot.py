import json
import time
from threading import Thread
from flask import Flask, request, render_template
from config import *
import datetime
from medsenger_api import *
from mail_api import *
import requests


def get_id():
    try:
        with open('last_id.txt', 'r') as file:
            return file.read()
    except:
        return None


def set_id(last_id):
    with open('last_id.txt', 'w') as file:
        return file.write(last_id)


medsenger_api = AgentApiClient(APP_KEY, MAIN_HOST, debug=True)
app = Flask(__name__)


def gts():
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")


@app.route('/status', methods=['POST'])
def status():
    data = request.json

    if data['api_key'] != APP_KEY:
        return 'invalid key'

    answer = {
        "is_tracking_data": False,
        "supported_scenarios": [],
        "tracked_contracts": []
    }

    return json.dumps(answer)


@app.route('/init', methods=['POST'])
def init():
    data = request.json

    if data['api_key'] != APP_KEY:
        return 'invalid key'

    text = "Чтобы отправить врачу результаты обследования TyToCare, в приложении TyToCare на телефоне зайдите в раздел обследования и поделитесь с врачем на почту <strong>tyto+{}@medsenger.ru</strong>".format(
        data.get('contract_id'))
    medsenger_api.send_message(data.get('contract_id'),
                               only_patient=True,
                               text=text)

    return 'ok'


@app.route('/remove', methods=['POST'])
def remove():
    data = request.json

    if data['api_key'] != APP_KEY:
        print('invalid key')
        return 'invalid key'
    return 'ok'


@app.route('/settings', methods=['GET'])
def settings():
    key = request.args.get('api_key', '')

    if key != APP_KEY:
        return "<strong>Некорректный ключ доступа.</strong> Свяжитесь с технической поддержкой."

    return render_template('settings.html')


@app.route('/', methods=['GET'])
def index():
    return 'waiting for the thunder!'


def tasks():
    try:
        last_id, messages = get_messages(get_id())

        if last_id:
            set_id(last_id)

            for message in messages:
                try:
                    contract_id = extract_contract_id(message)

                    if not contract_id:
                        continue
                    for part in message.walk():
                        if part.get_content_type() in ['text/html']:
                            text = decode_body(part)
                            code = extract_code(text)
                            link = extract_link(text)

                            if link:
                                session_id = link.split('/')[-1]
                                print(session_id)
                                answer = requests.post("https://app-cloudeu.tytocare.com/tyto/v1/public/visitLinks/{}/codeRequests".format(session_id))
                                print(answer.status_code)
                                medsenger_api.send_message(contract_id=contract_id, text="Ссылка на обследование TytoCare: <a target='_blank' href='{}'>Открыть</a>".format(link), only_doctor=True)
                                medsenger_api.send_message(contract_id=contract_id, text="Результаты осмотра TytoCare отправлены Вашему лечащему врачу. Он свяжется с Вами в течение нескольких часов.".format(link),
                                                           only_patient=True)
                            if code:
                                medsenger_api.send_message(contract_id=contract_id, text="Код доступа для TytoCare: {}".format(code), only_doctor=True)
                except Exception as e:
                    print(e)


    except Exception as e:
        print(e)


def sender():
    while True:
        tasks()
        time.sleep(60)


@app.route('/message', methods=['POST'])
def save_message():
    data = request.json
    key = data['api_key']

    if key != APP_KEY:
        return "<strong>Некорректный ключ доступа.</strong> Свяжитесь с технической поддержкой."

    return "ok"


if __name__ == "__main__":
    t = Thread(target=sender)
    t.start()

    app.run(port=PORT, host=HOST)

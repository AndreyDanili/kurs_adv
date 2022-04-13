from random import randrange
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.upload import VkUpload
import requests
from io import BytesIO
from VK_bot.VK import VkUser
from bd.bd import update_user_info, add_to_black_list, add_to_favourite_list, create_table

token = input('Token group: ')

vk = vk_api.VkApi(token=token)
longpoll = VkLongPoll(vk)
state = 'init'
user_info = {}
finish_users_list = []


def write_msg(user_id, message):
    vk.method('messages.send', {'user_id': user_id, 'message': message, 'random_id': randrange(10 ** 7), })


def upload_photo(upload, url):
    img = requests.get(url).content
    f = BytesIO(img)
    response = upload.photo_messages(f)[0]
    owner_id = response['owner_id']
    photo_id = response['id']
    access_key = response['access_key']
    return owner_id, photo_id, access_key


def send_photo(vk, peer_id, owner_id, photo_id, access_key):
    attachment = f'photo{owner_id}_{photo_id}_{access_key}'
    vk.method('messages.send', {'peer_id': peer_id, 'attachment': attachment, 'random_id': randrange(10 ** 7), })


def send_all_info(finish_users_list, user_id, peer_id):
    href_user = f"https://vk.com/id{finish_users_list[0]['id']}"
    write_msg(user_id, f"{href_user}")
    photos = VkUser.get_photo(VkUser(finish_users_list[0]['id']))
    for photo_url in photos:
        send_photo(vk, peer_id, *upload_photo(VkUpload(vk), photo_url['url']))
    finish_users_list.pop(0)


def start():
    create_table()
    global state, user_info, finish_users_list
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                request = event.text
                if request == "привет":
                    write_msg(event.user_id, f"Привет, {event.user_id}")
                elif request == "дальше":
                    if finish_users_list:
                        send_all_info(finish_users_list, event.user_id, event.peer_id)
                        write_msg(event.user_id, f'Для вывода информации по следующему человеку введите "дальше"')
                    else:
                        write_msg(event.user_id, f"Вариантов больше нет")
                elif 'блок' in request:  # Черный список (в формате: блок partner_id)
                    add_to_black_list(event.user_id, request.split()[1])
                    write_msg(event.user_id, f"Пользователь ID{request.split()[1]} добавлен в черный список")
                elif 'избранный' in request:  # Список избранных (в формате: избранный partner_id)
                    add_to_favourite_list(event.user_id, request.split()[1])
                    write_msg(event.user_id, f"Пользователь ID{request.split()[1]} добавлен в список избранных")
                if state == 'bdate':
                    user_info['bdate'] = request
                    update_user_info(user_info['bdate'])
                    state = "bdate_ok"
                if request == "старт" or state == "bdate_ok":
                    if not state == "bdate_ok":
                        user_info = VkUser.get_user_info(VkUser(event.user_id))
                    if len(user_info['bdate']) > 6:
                        state = 'init'
                        users_list = VkUser.get_search_users()
                        finish_users_list = VkUser.get_parametrize_users_list(user_info, users_list)
                        if len(finish_users_list) == 0:
                            write_msg(event.user_id, f"Вариантов больше нет")
                        else:
                            send_all_info(finish_users_list, event.user_id, event.peer_id)
                            write_msg(event.user_id, f'Для вывода информации следующего человека введите "дальше"')
                    else:
                        state = 'bdate'
                        write_msg(event.user_id, f"Введите дату рождения в формате MM.DD.YYYY")

import operator
from datetime import datetime, timedelta
import vk_api
from random import randrange
from bd.bd import insert_user_info, insert_partner_info, duplicate_partner, duplicate_people, black_list

token_user = 'token_user'
vk_user = vk_api.VkApi(token=token_user)


class VkUser:
    url = 'https://api.vk.com/method/'

    def __init__(self, user_id):
        self.user_id = user_id
        self.params = {
            'access_token': token_user,
            'v': '5.131'
        }

    def get_user_id(self):
        user_id = vk_user.method('utils.resolveScreenName', {'screen_name': self.user_id,
                                                             'random_id': randrange(10 ** 7)
                                                             })
        return user_id['object_id']

    def get_user_info(self):
        if not self.user_id.isdigit():
            self.user_id = VkUser.get_user_id(VkUser(self.user_id))
        user = vk_user.method('users.get', {'user_ids': self.user_id,
                                            'fields': 'bdate, city, relation, sex',
                                            'random_id': randrange(10 ** 7)
                                            })
        user_info = {'id': user[0]['id'],
                     'bdate': user[0]['bdate'],
                     'sex': user[0]['sex'],
                     'city': user[0]['city']['title'],
                     'relation': user[0]['relation']
                     }
        VkUser.people_parameter_for_db(user_info)
        return user_info

    def get_photo(self):
        user_photo_list = []
        photos_profile = vk_user.method('photos.get', {'owner_id': self.user_id,
                                                       'album_id': 'profile',
                                                       'extended': 1,
                                                       'random_id': randrange(10 ** 7),
                                                       })
        for photo in photos_profile['items']:
            user_photo = {'count': photo['likes']['count'], 'url': photo['sizes'][-1]['url']}
            user_photo_list.append(user_photo)
            user_photo_list.sort(key=operator.itemgetter('count'))
            user_photo_list.reverse()
        return user_photo_list[0:3]

    @staticmethod
    def people_parameter_for_db(user_info):
        user_info_list = f"'{user_info['id']}', " \
                         f"'{user_info['bdate']}', " \
                         f"'{user_info['sex']}', " \
                         f"'{user_info['city']}', " \
                         f"'{user_info['relation']}'"
        if not duplicate_people(user_info['id']):
            insert_user_info(user_info_list)
        return True

    @staticmethod
    def get_search_users():
        users_list = []
        offset = 0
        while offset < 1001:
            request = vk_user.method('users.search', {'count': 1000,
                                                      'offset': offset,
                                                      'fields': 'bdate, city, relation, sex, photo_max_orig',
                                                      'random_id': randrange(10 ** 7),
                                                      })
            users_list = users_list + request['items']
            offset += 1000
        return users_list



    @staticmethod
    def get_parametrize_users_list(user_info, users_list):
        finish_users_list = []
        relation_list = [1, 6, 5]
        user_bdate = datetime.strptime(user_info['bdate'], '%d.%m.%Y')
        start_bdate = user_bdate - timedelta(days=1200)
        end_bdate = user_bdate + timedelta(days=1200)
        for user_profile in users_list:
            if 'bdate' in user_profile and len(user_profile['bdate']) > 7 and user_profile['sex'] != user_info['sex']:
                if 'city' in user_profile and user_profile['city']['title'] == user_info['city']:
                    if start_bdate < user_bdate < end_bdate:
                        if 'relation' in user_profile and user_profile['relation'] in relation_list:
                            if not duplicate_partner(user_info['id'], user_profile['id']):
                                if not black_list(user_info['id'], user_profile['id']):
                                    if VkUser.partner_parameter_for_db(user_info['id'], user_profile):
                                        finish_users_list.append(user_profile)
        return finish_users_list

    @staticmethod
    def partner_parameter_for_db(user_info_id, user_profile):
        partner_photo_list = VkUser.get_photo(VkUser(user_profile['id']))
        if len(partner_photo_list) > 2:
            partner_info_list = f"'{user_profile['id']}', " \
                                f"'{user_profile['bdate']}', " \
                                f"'{user_profile['sex']}', " \
                                f"'{user_profile['city']['title']}', " \
                                f"'{user_profile['relation']}', " \
                                f"'{partner_photo_list[0]['url']}', " \
                                f"'{partner_photo_list[1]['url']}', " \
                                f"'{partner_photo_list[2]['url']}'"
            insert_partner_info(user_info_id, partner_info_list)
            return True
        return False

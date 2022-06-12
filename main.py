from random import randrange
import DataBase as db
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from datetime import datetime
from vk_api.exceptions import ApiError
from sqlalchemy.exc import IntegrityError


bot_token = input('Введите токен сообщества: ')
my_token = input('Введите ваш токен: ')

bot_vk = vk_api.VkApi(token=bot_token)
user_vk = vk_api.VkApi(token=my_token)
longpoll = VkLongPoll(bot_vk)


def write_msg(user_id, message, attachment=''):
    bot_vk.method('messages.send', {'user_id': user_id, 'message': message, 'random_id': randrange(10 ** 7),
                                    'attachment': attachment})


class VKinder:
    def __init__(self, user_id):
        self.user_id = user_id
        self.couple_id = 0
        self.user = db.MainUser
        self.offset = 0
        self.couple_id = 0
        self.couple_name = ''
        self.top_photo = ''

    # инфо пользователя
    def info(self):
        info = bot_vk.method("users.get", {"user_ids": self.user_id,
                                           "fields": 'sex, bdate, city, relation'})
        return info

    # Имя
    def name(self):
        name = self.info()[0]['first_name']
        return name

    # Возраст
    def age(self):
        if 'bdate' in self.info()[0].keys():
            bdate = self.info()[0]['bdate']
            if bdate is not None and len(bdate.split('.')) == 3:
                birth = datetime.strptime(bdate, '%d.%m.%Y').year
                this = datetime.now().year
                age = this - birth
                return age
            else:
                return 'Возраст неизвестен'
        else:
            return 'Возраст неизвестен'

    # Пол
    def sex(self):
        sex = self.info()[0]['sex']
        if sex == 1:
            return 2
        elif sex == 2:
            return 1
        else:
            return 0

    # Город
    def city(self):
        if 'city' in self.info()[0].keys():
            city = self.info()[0]['city']['id']
            return city
        else:
            return 0

    # Семейное положение
    def relation(self):
        if 'relation' in self.info()[0].keys():
            relation = self.info()[0]['relation']
            return relation
        else:
            return 'Семейное положение скрыто!'

    # старт работы бота
    def bot_start(self):
        db.create_tables()
        self.name()
        self.age()
        self.city()
        self.relation()
        try:
            self.user = db.MainUser(vk_id=self.user_id, name=self.name(), age=self.age(),
                                    city=self.city(), relation=self.relation())
            db.add_user(self.user)
        except IntegrityError:
            pass
        self.find_couple()
        self.get_top_photo()
        write_msg(event.user_id, f'Смотри кого нашёл:\n'
                                 f'Имя: {self.couple_name}, ссылка: vk.com/id{self.couple_id}', self.top_photo)
        return self.couple()

    # обработка поиска пары
    def couple(self):
        write_msg(event.user_id, f'Напиши ДАЛЕЕ, чтобы продолжить поиск, и сохранить человека в базе данных, '
                                 f'или СТОП, если не хочешь больше искать, или ПРОПУСТИТЬ, чтобы пропустить человека '
                                 f'и искать следующего, не переживай, если пропустишь, потом пара снова попадётся.')
        while True:
            for new_event in longpoll.listen():
                if new_event.type == VkEventType.MESSAGE_NEW and event.to_me:
                    if new_event.message.lower() == 'далее':
                        try:
                            found_couple = db.CoupleUser(vk_id=self.couple_id, name=self.couple_name,
                                                         id_main_user=self.user_id)
                            db.add_user(found_couple)
                        except IntegrityError:
                            pass
                        write_msg(event.user_id, 'Ищу следующую пару...')
                        self.offset += 1
                        self.find_couple()
                        self.get_top_photo()
                        write_msg(event.user_id, f'Смотри кого нашёл:\n'
                                                 f'Имя: {self.couple_name}, ссылка: vk.com/id{self.couple_id}',
                                                 self.top_photo)
                        return self.couple()
                    elif new_event.message.lower() == 'стоп' or new_event.message.lower() == 'нет':
                        write_msg(event.user_id, 'Заканчиваем поиск, если желаешь продолжить, напиши ПРОДОЛЖИТЬ.')
                    elif new_event.message.lower() == 'продолжить' or new_event.message.lower() == 'пропустить':
                        write_msg(event.user_id, f'Подыскиваю следующую пару...')
                        self.offset += 1
                        self.find_couple()
                        self.get_top_photo()
                        write_msg(event.user_id, f'Смотри кого нашёл:\n'
                                                 f'Имя: {self.couple_name}, ссылка: vk.com/id{self.couple_id}',
                                  self.top_photo)
                        return self.couple()

    # поиск пары
    def find_couple(self):
        resp = user_vk.method('users.search', {'count': 1, 'city': self.city(), 'sex': self.sex(), 'age': self.age(),
                                               'relation': self.relation(), 'offset': self.offset, 'status': (1, 6),
                                               'has photo': 1, 'fields': 'is_closed'})
        if resp['items'][0]['id'] in db.check_user():
            self.offset += 1
            self.find_couple()
        else:
            if resp['items']:
                for couple in resp['items']:
                    if couple['is_closed']:
                        self.offset += 1
                        self.find_couple()
                    else:
                        self.couple_id = couple['id']
                        self.couple_name = couple['first_name']
            else:
                self.offset += 1
                self.find_couple()

    # поиск фото
    def get_top_photo(self):
        photo_list = []
        resp = user_vk.method('photos.get', {'owner_id': self.couple_id,
                                             'album_id': 'profile',
                                             'access_token': my_token,
                                             'extended': 1,
                                             'v': '5.131'})
        photos = []
        for photo in resp['items']:
            photo_info = {'id': photo['id'], 'owner_id': photo['owner_id'], }
            count = 0
            try:
                count_com = user_vk.method('photos.getComments', {'owner_id': self.couple_id, 'photo_id': photo['id']})
                count = count_com['count']
            except ApiError:
                pass
            photo_info['popular'] = photo['likes']['count'] + count
            photo_list.append(photo_info)
        photo_list = sorted(photo_list, key=lambda k: k['popular'], reverse=True)
        for i in photo_list:
            photos.append(f"photo{i['owner_id']}_{i['id']}")
        self.top_photo = ','.join(photos[:3])
        return self.top_photo


if __name__ == '__main__':
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            bot = VKinder(event.user_id)
            bot.info()
            req = event.text.lower()
            if req == 'привет' or req == 'ghbdtn':
                write_msg(event.user_id, 'Чтобы начать поиск напиши Старт, если передумал искать пару, напиши СТОП.')
            elif req == 'старт':
                write_msg(event.user_id, f"Я пошёл искать, {bot.name()}. Пожалуйста, ожидай...")
                bot.bot_start()
            elif req == 'стоп' or req == 'нет':
                write_msg(event.user_id, f'До свидания, {bot.name()}, но если всё же хочешь найти пару, напиши СТАРТ.')
            else:
                write_msg(event.user_id, f'Не понял вашего ответа, {bot.name()}, Для начала поздороваемся - '
                                         f'Привет тебе, {bot.name()}.')

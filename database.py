import sqlite3
import random, string
from sanic import Sanic
import hashlib
import datetime
import Levenshtein
import json

def hashPassword(password: str) -> str:
    """
    Хеширует пароль с использованием алгоритма sha256

    Args:
        password (str): пароль, который нужно хешировать

    Returns:
        str: хеш пароля, полученный с использованием sha256
    """
    return hashlib.sha256(password.encode()).hexdigest()

class Database:
    @staticmethod
    def get_all_videos_by_owner_id(OwnerId: str) -> list[dict]:
        """
        Возвращает список всех видео, принадлежащих пользователю с указанным id

        Args:
            OwnerId (str): id владельца видео

        Returns:
            list[dict]: список видео, принадлежащих пользователю с указанным id
        """
        videos = []
        with sqlite3.connect('database.db') as conn:
            cursor = conn.execute('SELECT Name, Path, ImagePath, Description, OwnerId, DateTime,id, TagsJSON FROM Videos WHERE OwnerId = ?', (OwnerId,))
            rows = cursor.fetchall()
            for row in rows:
                video = {
                    'Name': row[0],
                    'Path': row[1],
                    'ImagePath': row[2],
                    'Description': row[3],
                    'Owner': Database.get_user_data(row[4]), 
                    'DateTime':datetime.datetime.strptime(row[5], "%Y-%m-%d %H:%M:%S"),
                    'id':row[6],
                    'Tags': json.loads(row[7]) if row[7] else []
                }
                videos.append(video)
        return videos
    
    def get_user_favorite_tags(user_id: str) -> list[str]:
        """
        Возвращает список любимых тегов для пользователя с указанным id

        Args:
            user_id (str): id пользователя

        Returns:
            list[dict]: список любимых тегов пользователя с числом просмотров
        """
        tags = {}
        with sqlite3.connect('database.db') as conn:
            cursor = conn.execute('SELECT VideoId FROM VideoWatches WHERE WatcherId = ?', (user_id,))
            WatchedVideos = []
            for row in cursor.fetchall():
                video = Database.get_video_by_id(row[0])
                if video:
                    WatchedVideos.append(video)
            for video in WatchedVideos:
                for tag in video['Tags']:
                    if tag in tags:
                        tags[tag] += 1
                    else:
                        tags[tag] = 1
            return tags
    
    def get_reccomended_videos_by_user_id(user_id: str, count: int) -> list[dict]:
        """
        Возвращает рекомендованные видео, принадлежащие пользователю с указанным id

        Args:
            user_id (str): id владельца видео

        Returns:
            list[dict]: список рекомендованных видео, принадлежащих пользователю с указанным id
        """
        tags = Database.get_user_favorite_tags(user_id)
        videos = []
        with sqlite3.connect('database.db') as conn:
            for tag in tags:
                cursor = conn.execute('SELECT Name, Path, ImagePath, Description, OwnerId, DateTime, id, TagsJSON FROM Videos WHERE TagsJSON LIKE ?', (f'%{tags}%',))
                cursor = cursor.fetchall()
                if not cursor:
                    continue
                for row in cursor:
                    video = {
                        'Name': row[0],
                        'Path': row[1],
                        'ImagePath': row[2],
                        'Description': row[3],
                        'Owner':Database.get_user_data(row[4]), 
                        'DateTime':datetime.datetime.strptime(row[5], "%Y-%m-%d %H:%M:%S"),
                        'id':row[6],
                        'Tags': json.loads(row[7]) if row[7] else []
                    }
                    videos.append(video)
        while len(videos) < count:
            videos.append(Database.get_random_video())
        try:
            return random.sample(videos, count)
        except ValueError:
            return videos

    @staticmethod
    def get_video_reactions(VideoId: int) -> dict[str, int]:
        """
        Возвращает количество лайков и дизлайков для видео с указанным id

        Args:
            VideoId (int): id видео

        Returns:
            dict[str, int]: словарь, содержащий количество лайков и дизлайков для видео с указанным id
        """
        with sqlite3.connect('database.db') as conn:
            cursor = conn.execute('''SELECT 
                                SUM(CASE WHEN IsLike = 1 THEN 1 ELSE 0 END) AS LikesCount,
                                SUM(CASE WHEN IsLike = 0 THEN 1 ELSE 0 END) AS DislikesCount
                                FROM VideoReactions 
                                WHERE VideoId = ?''', (VideoId,))
            row = cursor.fetchone()
            if row:
                return {'Likes': row[0] if row[0] else 0, 'Dislikes':row[1] if row[1] else 0}
            return None
    
    @staticmethod
    def get_video_by_id(id: int) -> dict[str, str | int | datetime.datetime] | None:
        """
        Возвращает видео с указанным id

        Args:
            id (int): id видео

        Returns:
            dict[str, str | int | datetime] | None: словарь, содержащий информацию о видео с указанным id
        """
        with sqlite3.connect('database.db') as conn:
            cursor = conn.execute('SELECT Name, Path, ImagePath, Description, OwnerId, DateTime, id, TagsJSON FROM Videos WHERE id = ?', (id,))
            row = cursor.fetchone()
            if row:
                reactions = Database.get_video_reactions(row[6])
                if not reactions:
                    reactions = 0
                views = Database.get_video_watches(row[6])
                if not views:
                    views = 0
                return {'id': row[6], 'Name':row[0], 'Path':row[1], 'ImagePath':row[2],'Description':row[3],'Owner':Database.get_user_data(row[4]), 'DateTime':row[5], 'Tags': json.loads(row[7]) if row[7] else [], 'Reactions':reactions, 'ViewCount':views}
            return None
    
    @staticmethod
    def unreact_video(UserId: str, VideoId: int):
        """
        Удаляет реакцию пользователя на видео с указанным id

        Args:
            UserId (str): id пользователя
            VideoId (int): id видео
        """
        with sqlite3.connect('database.db') as conn:
            conn.execute('DELETE FROM VideoReactions WHERE ReactorId = ? AND VideoId = ?', (UserId, VideoId,))

    @staticmethod
    def is_video_reacted(UserId: str, VideoId: int) -> bool:
        """
        Проверяет, реагировал ли пользователь на видео с указанным id

        Args:
            UserId (str): id пользователя
            VideoId (int): id видео

        Returns:
            bool: True, если пользователь реагировал на видео, False в противном случае
        """
        with sqlite3.connect('database.db') as conn:
            cursor = conn.execute('SELECT Count() FROM VideoReactions WHERE ReactorId = ? AND VideoId = ?', (UserId, VideoId,))
            row = cursor.fetchone()
            return int(row[0]) == 1
    
    @staticmethod
    def react_video(UserId: str, VideoId: int, IsLike: int):
        """
        Добавляет реакцию пользователя на видео с указанным id

        Args:
            UserId (str): id пользователя
            VideoId (int): id видео
            IsLike (int): 1, если пользователь лайкнул видео, 0, если пользователь дизлайкнул видео
        """
        with sqlite3.connect('database.db') as conn:
            conn.execute('INSERT INTO VideoReactions (VideoId, ReactorId, IsLike) VALUES (?, ?, ?)', (VideoId, UserId, IsLike,))

    @staticmethod
    def get_video_by_path(Path: str) -> dict[str, str | int | datetime.datetime] | None:
        """
        Возвращает видео с указанным путем

        Args:
            Path (str): путь видео

        Returns:
            dict[str, str | int | datetime] | None: словарь, содержащий информацию о видео с указанным путем
        """
        with sqlite3.connect('database.db') as conn:
            cursor = conn.execute('SELECT Name, Path, ImagePath, Description, OwnerId, DateTime, id FROM Videos WHERE Path = ?', (Path,))
            row = cursor.fetchone()
            try:
                if row:
                    return {'Name':row[0], 'Path':row[1], 'ImagePath':row[2],'Description':row[3],'Owner':Database.get_user_data(row[4]), 'DateTime':datetime.datetime.strptime(row[5], "%Y-%m-%d %H:%M:%S"), 'id':row[6]}
                return None
            except:
                return None
    
    @staticmethod
    def get_random_video() -> dict[str, str | int | datetime.datetime] | None:
        """
        Возвращает случайное видео

        Returns:
            dict[str, str | int | datetime] | None: словарь, содержащий информацию о случайном видео
        """
        try:
            with sqlite3.connect('database.db') as conn:
                cursor = conn.execute('SELECT id FROM Videos ORDER BY RANDOM() LIMIT 1')
                row = cursor.fetchone()
                return Database.get_video_by_id(row[0])
        except ValueError:
            return None

    @staticmethod
    def get_video_watches(VideoId: int) -> int:
        """
        Возвращает количество просмотров видео

        Args:
            VideoId (int): id видео

        Returns:
            int: количество просмотров видео
        """
        with sqlite3.connect('database.db') as conn:
            cursor = conn.execute('SELECT COUNT() FROM VideoWatches Where VideoId = ?', (VideoId,))
            row = cursor.fetchone()
            return row[0]

    @staticmethod
    def add_video_watch(UserId: str, VideoId: int):
        """
        Добавляет просмотр видео

        Args:
            UserId (str): id пользователя
            VideoId (int): id видео
        """
        with sqlite3.connect('database.db') as conn:
            conn.execute('INSERT INTO VideoWatches (WatcherId, VideoId) VALUES (?, ?)', (UserId, VideoId))

    @staticmethod
    def unreact_comment(UserId: str, CommentId: int):
        """
        Удаляет реакцию на комментарий

        Args:
            UserId (str): id пользователя
            CommentId (int): id комментария
        """
        with sqlite3.connect('database.db') as conn:
            conn.execute('DELETE FROM CommentReactions WHERE ReactorId = ? AND CommentId = ?', (UserId, CommentId))

    @staticmethod
    def react_comment(UserId: str, CommentId: int, IsLike: bool):
        """
        Добавляет реакцию на комментарий

        Args:
            UserId (str): id пользователя
            CommentId (int): id комментария
            IsLike (bool): true, если лайк, false, если дизлайк
        """
        with sqlite3.connect('database.db') as conn:
            conn.execute('INSERT INTO CommentReactions (CommentId, ReactorId, IsLike) VALUES (?, ?, ?)', (CommentId, UserId, IsLike))

    @staticmethod
    def comment_reaction(UserId: str, CommentId: int):
        """
        Возвращает информацию о реакции на комментарий

        Args:
            UserId (str): id пользователя
            CommentId (int): id комментария

        Returns:
            dict[str, bool]: словарь, содержащий информацию о реакции на комментарий
        """
        with sqlite3.connect('database.db') as conn:
            cursor = conn.execute('SELECT COUNT(), IsLike FROM CommentReactions Where CommentatorId = ? And CommentId = ?', (UserId, CommentId))
            row = cursor.fetchone()
            return {'IsReacted': row[0], 'IsLike': row[1]}

    @staticmethod
    def comment_video(UserId: str, Text: str, VideoId: int):
        """
        Добавляет комментарий к видео

        Args:
            UserId (str): id пользователя
            Text (str): текст комментария
            VideoId (int): id видео
        """
        with sqlite3.connect('database.db') as conn:
            conn.execute('INSERT INTO Comments (CommentatorId, Text, VideoId, DateTime) VALUES (?, ?, ?, ?)', (UserId, Text, VideoId, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    @staticmethod
    def get_all_comments(VideoId: int):
        """
        Возвращает все комментарии к видео

        Args:
            VideoId (int): id видео

        Returns:
            list[dict]: список словарей, содержащих информацию о комментариях
        """
        with sqlite3.connect('database.db') as conn:
            cursor = conn.execute('''
                SELECT
                    CommentatorId,
                    VideoId,
                    Text,
                    DateTime
                FROM Comments 
                Where VideoId = ?  
            ''', (VideoId,))
            rows = cursor.fetchall()
            comments = []
            for row in rows:
                comment = {
                    'Commentatorid': row[0],
                    'Video': row[1],
                    'Text': row[2],
                    'DateTime': datetime.datetime.strptime(row[3], "%Y-%m-%d %H:%M:%S")
                }
                commentator_data = Database.get_user_data(comment['Commentatorid'])
                if commentator_data:
                    comment['CommentatorNickname'] = commentator_data['Name']
                comments.append(comment)
            return comments

    @staticmethod
    def update_description(Login: str, NewDescription: str) -> None:
        """
        Обновляет описание пользователя в базе данных

        Args:
            Login (str): Логин пользователя.
            NewDescription (str): Новое описание.

        Returns:
            None
        """
        with sqlite3.connect('database.db') as conn:
            conn.execute("UPDATE Users SET Description = ? where Login = ? ", (NewDescription, Login, ))

    @staticmethod
    def add_video(Name: str, Path: str, Description: str, OwnerLogin: str, Tags: list) -> None:
        """
        Добавляет видео в базу данных.

        Args:
            Name (str): Название видео.
            Path (str): Путь к видео.
            Description (str): Описание видео.
            OwnerLogin (str): Логин владельца видео.
            Tags (list): Список тегов видео.
        Returns:
            None
        """
        with sqlite3.connect('database.db') as conn:
            conn.execute('INSERT INTO Videos (Name, Path, ImagePath, Description, OwnerId, DateTime, TagsJSON) VALUES (?, ?, ?, ?, ?, ?, ?)', (Name, Path+'.mp4',Path+'.png', Description, OwnerLogin, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), json.dumps(Tags).replace("\\", '')))

    @staticmethod
    def get_user_data(UserId: str):
        """
        Получает информацию о пользователе из базы данных.

        Args:
            UserId (str): Логин пользователя.

        Returns:
            dict | None: Словарь с информацией о пользователе или None, если пользователь не найден.
        """
        with sqlite3.connect('database.db') as conn:
            cursor = conn.execute('SELECT Login, Name, Description, PfpPath FROM Users WHERE Login = ?', (UserId,))
            row = cursor.fetchone()
            if row:
                return {'Login':row[0], 'Name':row[1], 'Description':row[2], 'PfpPath':row[3]}
            return None

    @staticmethod
    def login_user(Login: str, Password: str):
        """
        Логин пользователя в базе данных.

        Args:
            Login (str): Логин пользователя.
            Password (str): Пароль пользователя.

        Returns:
            str | None: Логин пользователя или None, если пользователь не найден.
        """
        with sqlite3.connect('database.db') as conn:
            cursor = conn.execute('SELECT Login FROM Users WHERE Login = ? and Password = ?', (Login, Password))
            row = cursor.fetchone()
            if row:
                return row[0]
            return None

    @staticmethod
    def reg_user(Login: str, Password: str, Nickname: str) -> None:
        """
        Регистрация ползователя
        Args:
            Login (str):  Логин пользователя.
            Password (str): Пароль пользователя.
            Nickname (str): Ник пользователя.

        Returns:
            None
        """
        with sqlite3.connect('database.db') as conn:
            conn.execute('INSERT INTO Users (Login, Password, Name, PfpPath) VALUES (?, ?, ?, ?)', (Login, Password, Nickname, Login+'.png'))

    @staticmethod
    def get_video_comments(videoid: int):
        """
        Получает комментарии к видео

        Args:
            videoid (int): id видео.

        Returns:
            list | None: Список комментариев или None, если комментарии не найдены.
        """
        with sqlite3.connect('database.db') as conn:
            cursor = conn.execute('SELECT * FROM Comments WHERE VideoId = ?', (videoid,))
            rows = cursor.fetchall()
            if rows:
                for row in rows:
                    return {
                        'id': row[0],
                        'CommentatorId': row[1],
                        'VideoId': row[2],
                        'Text': row[3],
                        'DateTime': row[4]
                    }
            return None
    
    @staticmethod
    def search_in_database_slow(text:str, distance: int = 20) -> list:
        """
        Ищет видео и каналы в базе данных, медленнее, но применяет к результатам поиска дистанцию левенштейна.

        Returns:
            list[dict]: Список видео и каналов.
        """
        with sqlite3.connect('database.db') as conn:
            cursor = conn.execute('SELECT Name, Path, ImagePath, Description, OwnerId, DateTime, id, TagsJSON FROM Videos')
            rows = cursor.fetchall()
            videos = []
            for row in rows:
                video = {
                    'Name': row[0],
                    'Path': row[1],
                    'ImagePath': row[2],
                    'Description': row[3],
                    'Owner': Database.get_user_data(row[4]),
                    'DateTime': row[5],
                    'id': row[6],
                    'Tags': json.loads(row[7]) if row[7] else []
                }
                videos.append(video)
            cursor = conn.execute('SELECT Login, Name, Description, PfpPath FROM Users')
            rows = cursor.fetchall()
            channels = []
            for row in rows:
                channel = {
                    'Name': row[1],
                    'Login': row[0],
                    'Description': row[2],
                    'PfpPath': row[3]
                }
                channels.append(channel)
            filtered_videos = [video for video in videos if Levenshtein.distance(video['Name'], text) < distance]
            filtered_channels = [channel for channel in channels if Levenshtein.distance(channel['Name'], text) < distance]
            filtered_videos.sort(key=lambda video: Levenshtein.distance(video['Name'], text))
            filtered_channels.sort(key=lambda channel: Levenshtein.distance(channel['Name'], text))
            outputvideos = []
            for i in filtered_videos:
                outputvideos.append(Database.get_video_by_id(i['id']))
            return {'videos': outputvideos, 'channels': filtered_channels}
    
    @staticmethod
    def search_in_database_fast(text:str) -> list:
        """
        Ищет видео и каналы в базе данных.

        Returns:
            list[dict]: Список видео и каналов.
        """
        with sqlite3.connect('database.db') as conn:
            cursor = conn.execute('SELECT Name, Path, ImagePath, Description, OwnerId, DateTime, id, TagsJSON FROM Videos WHERE Name LIKE ?', (f'%{text}%',))
            rows = cursor.fetchall()
            videos = []
            for row in rows:
                video = {
                    'Name': row[0],
                    'Path': row[1],
                    'ImagePath': row[2],
                    'Description': row[3],
                    'Owner': Database.get_user_data(row[4]),
                    'DateTime': row[5],
                    'id': row[6],
                    'Tags': json.loads(row[7]) if row[7] else []
                }
                videos.append(video)
            cursor = conn.execute('SELECT Login, Name, Description, PfpPath, TagsJSON FROM Users WHERE Name LIKE ?', (f'%{text}%',))
            rows = cursor.fetchall()
            channels = []
            for row in rows:
                channels.append({
                    'Name': row[1],
                    'Login': row[0],
                    'Description': row[2],
                    'PfpPath': row[3]
                })
            output = {'videos':videos, 'channels':channels}
            return output
    
    
    @staticmethod
    def start_db() -> None:
        """
        Создает таблицы в базе данных.

        Returns:
            None
        """
        with sqlite3.connect('database.db') as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS Users (
                    Login TEXT NOT NULL PRIMARY KEY,
                    Password TEXT NOT NULL,
                    Name TEXT NOT NULL,
                    Description TEXT,
                    PfpPath TEXT NOT NULL
                )
                ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS Videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Name TEXT NOT NULL,
                    Path TEXT NOT NULL,
                    ImagePath TEXT NOT NULL,
                    Description TEXT NOT NULL,
                    OwnerId TEXT NOT NULL,
                    DateTime DATETIME NOT NULL,
                    TagsJSON TEXT,
                    FOREIGN KEY (OwnerId) REFERENCES Users (Login)
                )
                ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS VideoReactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    VideoId INTEGER NOT NULL,
                    ReactorId TEXT NOT NULL,
                    IsLike INTEGER NOT NULL,
                    FOREIGN KEY (VideoId) REFERENCES Videos (id),
                    FOREIGN KEY (ReactorId) REFERENCES Users (Login)
                )
                ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS VideoWatches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    WatcherId TEXT,
                    VideoId INTEGER NOT NULL,
                    FOREIGN KEY (WatcherId) REFERENCES Users (Login)
                    FOREIGN KEY (VideoId) REFERENCES Videos (id)
                )
                ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS Comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    CommentatorId TEXT NOT NULL,
                    VideoId INTEGER NOT NULL,
                    Text TEXT NOT NULL,
                    DateTime DATETIME NOT NULL,
                    FOREIGN KEY (CommentatorId) REFERENCES Users (Login)
                )
                ''')
            conn.execute('''
                CREATE TABLE IF NOT EXISTS CommentReactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    CommentId INTEGER NOT NULL,
                    ReactorId TEXT NOT NULL,
                    IsLike INTEGER NOT NULL,
                    FOREIGN KEY (CommentId) REFERENCES Comments (id),
                    FOREIGN KEY (ReactorId) REFERENCES Users (Login)
                )
                ''')
Database.start_db()

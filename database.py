import sqlite3
import random, string
from sanic import Sanic
import datetime
class Database:
    #session_id = request.cookies.get('session_id')
    #session_id = str(uuid.uuid4())
    '''
    @app.route('/login')
async def login(request):
    # В реальной ситуации аутентификация будет проводиться, и здесь
    # вы будете иметь user_id после успешной аутентификации.
    user_id = '123'  # Здесь вы должны использовать фактический user_id

    session_id = create_session(user_id)
    response = redirect('/')
    response.cookies['session_id'] = session_id
    return response
    '''
    def GetAllVideosByOwnerId(OwnerId):
        videos = []
        with sqlite3.connect('database.db') as conn:
            cursor = conn.execute('SELECT Name, Path, ImagePath, Description, OwnerId, DateTime FROM Videos WHERE OwnerId = ?', (OwnerId,))
            rows = cursor.fetchall()
            for row in rows:
                video = {
                    'Name': row[0],
                    'Path': row[1],
                    'ImagePath': row[2],
                    'Description': row[3],
                    'OwnerId':row[4], 
                    'DateTime':datetime.datetime.strptime(row[5], "%Y-%m-%d %H:%M:%S")
                }
                videos.append(video)
        return videos
    def GetVideoReactions(VideoId):
        with sqlite3.connect('database.db') as conn:
            cursor = conn.execute('''SELECT 
                                  SUM(CASE WHEN IsLike = 1 THEN 1 ELSE 0 END) AS LikesCount,
                                  SUM(CASE WHEN IsLike = 0 THEN 1 ELSE 0 END) AS DislikesCount
                                  FROM VideoReactions 
                                  WHERE VideoId = ?''', (VideoId,))
            row = cursor.fetchone()
            if row:
                return {'Likes': row[0], 'Dislikes':row[1]}
            return None
    def GetVideoById(id):
        with sqlite3.connect('database.db') as conn:
            cursor = conn.execute('SELECT Name, Path, ImagePath, Description, OwnerId, DateTime, id FROM Videos WHERE id = ?', (id,))
            row = cursor.fetchone()
            if row:
                return {'Id': row[6], 'Name':row[0], 'Path':row[1], 'ImagePath':row[2],'Description':row[3],'OwnerId':row[4], 'DateTime':datetime.datetime.strptime(row[5], "%Y-%m-%d %H:%M:%S")}
            return None
    
    def UnreactVideo(UserId, VideoId):
        with sqlite3.connect('database.db') as conn:
            conn.execute('DELETE FROM VideoReactions WHERE ReactorId = ? AND VideoId = ?', (UserId, VideoId,))

    def IsVideoReacted(UserId, VideoId):
        with sqlite3.connect('database.db') as conn:
            cursor = conn.execute('SELECT Count() FROM VideoReactions WHERE ReactorId = ? AND VideoId = ?', (UserId, VideoId,))
            row = cursor.fetchone()
            return int(row[0]) == 1
    def ReactOnVideo(UserId, VideoId, IsLike):
        with sqlite3.connect('database.db') as conn:
            conn.execute('INSERT INTO VideoReactions (VideoId, ReactorId, IsLike) VALUES (?, ?, ?)', (VideoId, UserId, IsLike,))

    def GetVideoByPath(Path):
        with sqlite3.connect('database.db') as conn:
            cursor = conn.execute('SELECT Name, Path, ImagePath, Description, OwnerId, DateTime, id FROM Videos WHERE Path = ?', (Path,))
            row = cursor.fetchone()
            try:
                if row:
                    return {'Name':row[0], 'Path':row[1], 'ImagePath':row[2],'Description':row[3],'OwnerId':row[4], 'DateTime':datetime.datetime.strptime(row[5], "%Y-%m-%d %H:%M:%S"), 'id':row[6]}
                return None
            except:
                return None
        
    def GetRandomVideo():
        try:
            with sqlite3.connect('database.db') as conn:
                cursor = conn.execute('SELECT COUNT() FROM Videos')
                row = cursor.fetchone()
                return Database.GetVideoById(random.randint(1,int(row[0])))
        except ValueError:
            return None
    def CookieExists(cookiestring):
        if(Database.GetUserData(Database.get_user_id(cookiestring))!=None):
            return False
        else: return True
    
    def GetVideoWatchesCount(VideoId):
        with sqlite3.connect('database.db') as conn:
            cursor = conn.execute('SELECT COUNT() FROM VideoWatches Where VideoId = ?', (VideoId,))
            row = cursor.fetchone()
            return row[0]

    def AddVideoToWatchList(UserId, VideoId):
        with sqlite3.connect('database.db') as conn:
            conn.execute('INSERT INTO VideoWatches (WatcherId, VideoId) VALUES (?, ?)', ( UserId, VideoId,))

    def UnreactComment(UserId, CommentId):
        with sqlite3.connect('database.db') as conn:
            conn.execute('DELETE FROM CommentReactions WHERE ReactorId = ? AND CommentId = ?', (UserId, CommentId,))

    
    def ReactOnComment(UserId, CommentId, IsLike):
        with sqlite3.connect('database.db') as conn:
            conn.execute('INSERT INTO CommentReactions (CommentId, ReactorId, IsLike) VALUES (?, ?, ?)', (CommentId, UserId, IsLike,))


    def CommentReacted(UserId, CommentId):
        with sqlite3.connect('database.db') as conn:
            cursor = conn.execute('SELECT COUNT(), IsLike FROM CommentReactions Where CommentatorId = ? And CommentId = ?', (UserId, CommentId,))
            row = cursor.fetchone()
            return {'IsReacted': row[0], 'IsLike': row[1]}

    def CommentVideo(UserId, Text, VideoId):
        with sqlite3.connect('database.db') as conn:
            conn.execute('INSERT INTO Comments (CommentatorId, Text, VideoId, DateTime) VALUES (?, ?, ?, ?)', (UserId, Text, VideoId, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    def GetAllVideoComments(VideoId):
        #try:
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

                    commentator_data = Database.GetUserData(comment['Commentatorid'])
                    if commentator_data:
                        comment['CommentatorNickname'] = commentator_data['Name']

                    comments.append(comment)

                return comments
        #except Exception as e:
        #    print(f"An error occurred: {e}")
        #    return []


    def LoginExists(Login):
        with sqlite3.connect('database.db') as conn:
            cursor = conn.execute('Select Login From Users Where Login = ?', (Login,)) 
            row = cursor.fetchone()
            if row:
                return True
            return False

    def NewDescription(Login, NewDescription):
        with sqlite3.connect('database.db') as conn:
            conn.execute("UPDATE Users SET Description = ? where Login = ? ", (NewDescription, Login, ))

    def AddVideo(Name, Path, Description, OwnerLogin):
        with sqlite3.connect('database.db') as conn:
            conn.execute('INSERT INTO Videos (Name, Path, ImagePath, Description, OwnerId, DateTime) VALUES (?, ?, ?, ?, ?, ?)', (Name, Path+'.mp4',Path+'.png', Description, OwnerLogin, datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

    def create_session(session_id, user_Login):
        with sqlite3.connect('database.db') as conn:
            conn.execute('INSERT INTO Sessions (session_id, User) VALUES (?, ?)', (session_id, user_Login)) 
        return session_id
    
    def GetUserData(UserId : str):
        with sqlite3.connect('database.db') as conn:
            cursor = conn.execute('SELECT Login, Name, Description, PfpPath FROM Users WHERE Login = ?', (UserId,))
            row = cursor.fetchone()
            if row:
                return {'Login':row[0], 'Name':row[1], 'Description':row[2], 'PfpPath':row[3]}
            return None

    def get_user_id(session_id):
        with sqlite3.connect('database.db') as conn:
            cursor = conn.execute('SELECT User FROM Sessions WHERE session_id = ?', (session_id,))
            row = cursor.fetchone()
            if row:
                return row[0]
            return None
    def LoginUser(Login,Password):
        with sqlite3.connect('database.db') as conn:
            cursor = conn.execute('SELECT * FROM Users WHERE Login = ? and Password = ?', (Login, Password))
            row = cursor.fetchone()
            if row:
                return row[0]
            return None
    def reg_user(SessionId,Login,Password, Nickname):
        with sqlite3.connect('database.db') as conn:
            conn.execute('INSERT INTO Users (Login, Password, Name, PfpPath) VALUES (?, ?, ?, ?)', (Login, Password, Nickname, Login+'.png'))
            
        Database.create_session(SessionId,Login)
    def get_video_comments(videoid):
        with sqlite3.connect('database.db') as conn:
            cursor = conn.execute('SELECT * FROM Comments WHERE VideoId = ?', (videoid,))
            row = cursor.fetchall()
            if row:
                return row
            return None
    @staticmethod
    def StartDatabase():
        with sqlite3.connect('database.db') as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS Sessions (
                         session_id TEXT PRIMARY KEY, 
                         User TEXT NOT NULL,
                         FOREIGN KEY (User) REFERENCES Users (Login)
                         )
                         ''')
        with sqlite3.connect('database.db') as conn:
            conn.execute('''
                 CREATE TABLE IF NOT EXISTS Users (
                    Login TEXT NOT NULL PRIMARY KEY,
                    Password TEXT NOT NULL,
                    Name TEXT NOT NULL,
                    Description TEXT,
                    PfpPath TEXT NOT NULL,
                    Admin BOOLEAN
                   )
                ''')
            cursor = conn.execute("SELECT Login FROM Users WHERE Login = 'Admin'")
            existing_record = cursor.fetchone()
            if existing_record is None:
                # Если записи нет, то вставляем новую
                conn.execute('''
                    INSERT INTO Users (Login, Password, Name, Description, PfpPath, Admin) 
                    VALUES ('Admin', '1', 'Vlad&Vlad', 'Сосать админы', 'no-photo.png', True)
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
Database.StartDatabase()
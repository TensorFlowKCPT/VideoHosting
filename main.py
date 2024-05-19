from PIL import Image
from sanic import Sanic, response, json, redirect, html, file
from sanic.request import Request
from sanic.response import text, html
from sanic_session import Session
import cv2
import os
import random

from database import *


app = Sanic("VideoHosting")
app.static("/static", "./static")

Session(app)

@app.post('/react/video')
async def react_on_video(request):
    """
    Функция для обработки реакций на видео. 
    Проверяет, была ли уже добавлена оценка, если да, то удаляет оценку; 
    в противном случае, оценивает видео на основе параметра 'IsLike'.
    """
    if Database.is_video_reacted(request.ctx.session.get('Auth'),request.json['VideoId']):
        Database.unreact_video(request.ctx.session.get('Auth'),request.json['VideoId'])
        return json({'message': 'Реакция удалена'})
    else:
        Database.react_video(request.ctx.session.get('Auth'),request.json['VideoId'], request.json['IsLike'])
        return json({'message': 'Реакция сохранена'})

@app.post('/search')
async def search(request):
    text = request.json.get('text')
    #return json(Database.search_in_database_fast(text))
    distance = request.json.get('distance')
    return json(Database.search_in_database_slow(text, int(distance) if distance else None))
    
@app.post('/comment/video')
async def comment_video(request):
    """
    Функция для обработки комментирования видео. 
    Принимает аутентифицированную сессию пользователя, текст комментария и идентификатор видео в качестве входных параметров.
    """
    Database.comment_video(request.ctx.session.get('Auth'), request.json.get('Text'), request.json.get('VideoId'))
    return json({'message': 'Реакция сохранена'})

@app.post('/react/comment')
async def reactComment(request):
    """
    Функция для обработки реакций на комментарии. 
    Принимает аутентифицированную сессию пользователя, идентификатор комментария и флаг "Like" в качестве входных параметров.
    """
    comment_id = request.json.get('CommentId')
    isLike = request.json.get('IsLike')
    Database.react_comment(request.ctx.session.get('Auth'), comment_id, isLike)

@app.get('/video/<filename:str>')
async def video(request, filename:str):
    """
    Обработчик запроса на получение видео.
    
    Принимает имя файла видео и возвращает данные о видео в виде JSON-объекта.
    Если видео не найдено, возвращает сообщение об ошибке.
    Добавляет информацию о просмотрах видео и реакциях на видео.
    Возвращает список рекомендованных видео.
    Возвращает список комментариев к видео.
    """
    if os.path.exists('video/'+filename):
        Data = Database.get_video_by_path(filename)
        Data['ViewCount'] = Database.get_video_watches(Data['id'])
        Data['Reactions'] = Database.get_video_reactions(Data['id'])
        for i in Data['Reactions']:
            if Data['Reactions'][i] is None:
                Data['Reactions'][i] = 0
        Data['OwnerNickname'] = Database.get_user_data(Data['OwnerId'])['Name']
        Database.add_video_watch(request.ctx.session.get('Auth'),Data['id'])
        
        Data['recommended_videos'] = []
        for i in range(5):
            Data['recommended_videos'].append(Database.get_random_video())
            
        Data['comments'] = Database.get_all_comments(Data['id'])
        return response.json(Data)
    return response.json({'message': 'Видео не найдено'})

@app.post('/newdescription')
async def update_description(request):
    """
    Обработчик запроса на изменение описания аккаунта.
    
    Принимает аутентифицированную сессию пользователя и новый текст описания аккаунта в качестве входных параметров.
    Проверяет, что текст описания не является пустым, и обновляет описание аккаунта в базе данных.
    Возвращает сообщение об успешном изменении описания.
    """
    newdes = request.form.get('description')
    if not newdes:
        return response.json({'message': 'Описание не может быть пустым'}, status=400)
    Database.update_description(request.ctx.session.get('Auth'), newdes)
    return response.json({'message': 'Описание изменено'}, status=200)

@app.route('/servevideo/<filename:str>')
async def serve_video(request, filename:str):
    """
    Обработчик запроса на получение потока видео.
    
    Принимает имя файла видео и информацию о конкретном байте видео в headerах запроса.
    
    Возвращает видео-поток начиная от указанного байта.
    """
    video_data = Database.get_video_by_path(filename)
    video_path = 'video/' + video_data['Path']
    
    # Открываем файл видео
    try:
        with open(video_path, 'rb') as video_file:
            video_data = video_file.read()
    except:
        return response.json({'message': 'Видео не найдено'}, status=404)
    
    headers = {'Accept-Ranges': 'bytes'}
    content_range = request.headers.get('Range')

    if content_range:
        # Разбираем значение Range заголовка
        start, end = content_range.replace('bytes=', '').split('-')
        start = int(start)
        end = int(end) if end else len(video_data) - 1

        # Определяем длину контента и формируем заголовок Content-Range
        content_length = end - start + 1
        headers['Content-Range'] = f'bytes {start}-{end}/{len(video_data)}'
        
        # Вырезаем запрошенный диапазон данных из файла
        video_chunk = video_data[start:end+1]
        return response.raw(video_chunk, headers=headers, status=206)

    # Если Range не указан, отправляем весь файл
    return await response.file_stream(video_path, headers=headers)

@app.route('/image/<filename:str>')
async def serve_image(request, filename):
    """
    Обработчик запроса на получение изображения.
    
    Принимает имя файла изображения, которое будет возвращено клиенту.
    
    Возвращает изображение в виде потока байтов.
    """
    return await response.file('Images/'+filename)

@app.post('/login')
async def login(request):
    """
    Обработчик запроса на вход в аккаунт.
    
    Принимает имя пользователя и пароль в формате form-data.
    
    Если вход в аккаунт успешен, возвращает json сообщение с http кодом 200.
    В противном случае возвращает json сообщение с http кодом 400.
    """
    username = request.form.get('username')
    password = request.form.get('password')
    logged_in = Database.login_user(username, password)
    if logged_in:
        request.ctx.session['user_id'] = logged_in
        return response.json({'message': 'Вы вошли в аккаунт'}, status=200)
    else:
        return response.json({'message': 'Неверное имя пользователя или пароль'}, status=400)

@app.route('/profile/<profilename:str>')
async def account_info(request: Request, profilename:str):
    """
    Обработчик запроса на получение информации о профиле пользователя.
    
    Принимает имя пользователя в параметрах маршрута.
    
    Возвращает json-объект, содержащий информацию о профиле пользователя,
    включая список видео, принадлежащих данному пользователю.
    В случае, если пользователь не найден, возвращает сообщение об ошибке с http кодом 404.
    """
    account_data = Database.get_user_data(profilename)
    if not account_data:
        return response.json({'message': 'Пользователь не найден'}, status=404)
    account_data['UserVideos'] = Database.get_all_videos_by_owner_id(profilename)
    return response.json(account_data, status=200)

@app.post('/videoupload')
async def upload_video(request):
    """
    Обработчик запроса на загрузку нового видео.
    
    Принимает видеофайл, изображение для видео, имя видео, и описание видео в формате form-data.
    
    Если пользователь авторизован и видео успешно загружено, возвращает json-объект, содержащий информацию о загруженном видео с http кодом 201.
    В противном случае возвращает json-объект с сообщением об ошибке и http кодом 401.
    """
    if not request.ctx.session.get('Auth'):
        return response.json({'message': 'Вы не авторизованы'}, status=401)
    
    uploaded_videofile = request.files.get('video')
    uploaded_videoimage = request.files.get('image')
    uploaded_videoname = request.form.get('name')
    uploaded_videodesc = request.form.get('desc')
    
    if not uploaded_videofile:
        return response.json({'message': 'Видеофайла не было прикреплено'}, status=400)
    
    # Сохраните видеофайл на сервере
    random_name_video = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
    
    video_file_path = os.path.join('video/', random_name_video + ".mp4")
    
    with open(video_file_path, 'wb') as file:
        file.write(uploaded_videofile.body)

    #Если не было прикреплено изображение к видео то берем случайный кадр из видео
    if not uploaded_videoimage:
        vidcap = cv2.VideoCapture(os.path.join('video/', random_name_video + ".mp4"))
        totalFrames = vidcap.get(cv2.CAP_PROP_FRAME_COUNT)
        randomFrameNumber=random.randint(0, totalFrames)
        vidcap.set(cv2.CAP_PROP_POS_FRAMES,randomFrameNumber)
        success, image = vidcap.read()
        if success:
            cv2.imwrite(os.path.join('Images/', random_name_video + ".png"), image)

    else:
        # Сохраняем загруженное изображение для видео
        image_file_path = os.path.join('Images/', random_name_video + ".png")
        with open(image_file_path, 'wb') as file:
            file.write(uploaded_videoimage.body)

    Database.add_video(uploaded_videoname, random_name_video, uploaded_videodesc, request.ctx.session.get('Auth'))
    
    return response.json({'message': 'Видеофайл успешно загружен'}, status=200)

@app.post('/register')
async def register(request):
    """
    Обработчик запроса на регистрацию нового пользователя.
    
    Принимает имя пользователя, пароль и никнейм пользователя в формате form-data.
    Если пользователь успешно зарегистрирован, возвращает json-объект с сообщением об успехе с http кодом 200.
    В противном случае возвращает json-объект с сообщением об ошибке и http кодом 400.
    """
    try:
        Database.reg_user(request.form.get('username'), request.form.get('password'), request.form.get('nickname'))
    except:
        return response.json({'message': 'Пользователь с таким именем уже существует'}, status=400)
    original_image = Image.open('Images/no-photo.png')
    copy_image = original_image.copy()
    copy_image.save('Images/'+request.form.get('username')+'.png')
    original_image.close()
    copy_image.close()
    return response.json({'message': 'Аккаунт успешно создан'}, status=200)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
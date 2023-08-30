from sanic import Sanic, response, json, redirect, html, file
import random
import cv2
import string
import os
from database import *
from sanic import Sanic
from sanic.response import text, html
from jinja2 import Environment, FileSystemLoader, select_autoescape
from sanic.request import Request



def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    password = ''.join(random.choice(characters) for i in range(length))
    return password


app = Sanic("MyHelloWorldApp")

# Настройка Jinja2 для Sanic
env = Environment(
    loader=FileSystemLoader('templates'),  # Папка с шаблонами
    autoescape=select_autoescape(['html', 'xml'])
)

@app.post('/react/video')
async def react_on_video(request):
    if Database.IsVideoReacted(Database.get_user_id(request.cookies.get('Auth')),request.json['VideoId']):
        Database.UnreactVideo(Database.get_user_id(request.cookies.get('Auth')),request.json['VideoId'])
        return json({'message': 'Реакция удалена'})
    else:
        Database.ReactOnVideo(Database.get_user_id(request.cookies.get('Auth')),request.json['VideoId'], request.json['IsLike'])
        return json({'message': 'Реакция сохранена'})
    
@app.route('/video/<filename:str>')
async def VideoPage(request, filename):
    if os.path.exists('video/'+filename):
        Data = Database.GetVideoByPath(filename)
        Data['ViewCount'] = Database.GetVideoWatchesCount(Data['id'])
        Data['Reactions'] = Database.GetVideoReactions(Data['id'])
        Database.AddVideoToWatchList(Database.get_user_id(request.cookies.get('Auth')),Data['id'])
        #Пример рекомендаций
        Data['recommended_videos'] = [
            Database.GetRandomVideo(),
            Database.GetRandomVideo(),
            Database.GetRandomVideo()
        ]
        template = env.get_template('video.html')
        # Отправляем HTML-страницу как ответ
        return response.html(template.render(data = Data))
    
    with open('templates/NotFound.html', 'r', encoding="UTF-8") as file:
        html_content = file.read()
    # Отправляем HTML-страницу как ответ
    return response.html(html_content)

@app.route('/newdescription', methods=["POST"])
async def changedescription(request):
    newdes = request.form.get('description')
    Database.NewDescription(Database.get_user_id(request.cookies.get('Auth')), newdes)
    template = env.get_template('MyAccount.html')
    cookies = str(request.cookies.get('Auth'))
    account_data = Database.GetUserData(Database.get_user_id(cookies))
    return response.redirect("/profile/" +  Database.get_user_id(cookies))

@app.route('/servevideo/<filename:str>')
async def serve_video(request, filename):
    video_data = Database.GetVideoByPath(filename)
    video_path = 'video/' + video_data['Path']
    # Открываем файл видео
    with open(video_path, 'rb') as video_file:
        video_data = video_file.read()

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
    return await response.file('Images/'+filename)
     
@app.route('/')
async def index(request):
    # Открываем файл с HTML-страницей и считываем его содержимое
    with open('templates/index.html', 'r', encoding="UTF-8") as file:
        html_content = file.read()
    template = env.get_template('index.html')
    if Database.get_user_id(request.cookies.get('Auth')) != None and Database.get_user_id(request.cookies.get('Auth')) != 'None':
            Data = {"auth":Database.get_user_id(request.cookies.get('Auth')), 'picture': Database.GetUserData(Database.get_user_id(request.cookies.get('Auth')))["PfpPath"]}
            return response.html(template.render(data = Data))
    else:
        Data = {"auth":Database.get_user_id(request.cookies.get('Auth')), 'picture': None}
        resp = html(template.render(data = Data))
        if request.cookies.get('Auth') != 'None' or request.cookies.get('Auth') != None:
            resp.cookies['Auth'] = None
        return resp

@app.route('/login', methods=["GET"])
async def loginGET(request):
    cookies = str(request.cookies.get('Auth'))
    if cookies != 'None':
        response = redirect('/')
        return response
    template = env.get_template('login.html')
    account_data = {"status":True}
    return html(template.render(account=account_data))

@app.route('/login', methods=["POST"])
async def loginPOST(request):
    login = request.form.get("login")
    password = request.form.get("password")
    a = Database.LoginUser(login, password)
    if a != None:
        cookiestring = generate_random_string(10)
        while not Database.CookieExists(cookiestring):
            cookiestring = generate_random_string(10)
        Database.create_session(cookiestring, request.form.get('login'))
        response = redirect('/')
        response.cookies['Auth'] = cookiestring
        return response
    else:
        template = env.get_template('login.html')
        account_data = {"status":False}
        return html(template.render(account=account_data))
        
@app.route('/admin', methods=["GET"])
async def admin(request):
    if request.cookies.get('Auth') == "None":
        return redirect("/login")
    else:
        template = env.get_template('adminmain.html')
        account_data = {"status":True}
        return html(template.render(account=account_data))

@app.route('/admin/users', methods=["GET"])
async def users(request):
    template = env.get_template('users.html')
    account_data = {"status":True}
    return html(template.render(account=account_data))


@app.route('/admin/videos', methods=["GET"])
async def videos(request):
    template = env.get_template('videos.html')
    account_data = {"status":True}
    return html(template.render(account=account_data))

@app.route('/addvideo')
async def addvideo(request):
    # Открываем файл с HTML-страницей и считываем его содержимое
    with open('templates/addvideo.html', 'r', encoding="UTF-8") as file:
        html_content = file.read()

    # Отправляем HTML-страницу как ответ
    return response.html(html_content)

@app.route('/profile/<profilename:str>')
async def account_info(request: Request, profilename):
    # Здесь вы можете получить информацию об аккаунте и передать ее в шаблон Jinja2
    template = env.get_template('MyAccount.html')
    account_data = Database.GetUserData(profilename)
    account_data['UserVideos'] = Database.GetAllVideosByOwnerId(profilename)
    return response.html(template.render(account=account_data))

@app.route('/videoupload', methods=['POST'])
async def upload_video(request):
    uploaded_videofile = request.files.get('video')
    uploaded_videoimage = request.files.get('image')
    uploaded_videoname = request.form.get('name')
    uploaded_videodesc = request.form.get('desc')
    
    if not uploaded_videofile:
        return text('Файл не загружен')
    
    # Сохраните видеофайл на сервере
    random_name_video = generate_random_string(10)
    video_file_path = os.path.join('video/', random_name_video + ".mp4")
    
    with open(video_file_path, 'wb') as file:
        file.write(uploaded_videofile.body)
    if uploaded_videoimage.name == '':
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

    Database.AddVideo(uploaded_videoname, random_name_video, uploaded_videodesc, Database.get_user_id(request.cookies.get('Auth')))
    
    return response.redirect('/profile/'+Database.get_user_id(request.cookies.get('Auth')))

@app.route('/reg', methods=['POST'])
async def reg(request):
    cookiestring = generate_random_string(10)
    while(Database.CookieExists(cookiestring)):
        cookiestring = generate_random_string(10)
        while not Database.CookieExists(cookiestring):
             cookiestring = generate_random_string(10)
        Database.reg_user(cookiestring, request.form.get('username'), request.form.get('password'), request.form.get('nickname'))
        response = redirect('/')
        response.cookies['Auth'] = cookiestring
        
        return response

@app.route('/register')
async def register(request):
    cookies = str(request.cookies.get('Auth'))
    if cookies != 'None':
        response = redirect('/')
        return response
    with open('templates/register.html', 'r', encoding="UTF-8") as file:
        html_content = file.read()
        response = html(html_content)
        return response

@app.route("/check")
async def check(request):
    return response.text(request.cookies.get('Auth'))

@app.route("/reset")
async def reset(request):
    response = redirect('/')
    response.cookies['Auth'] = None
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
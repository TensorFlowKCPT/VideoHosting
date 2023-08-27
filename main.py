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

@app.route('/video/<filename:str>')
async def VideoPage(request, filename):
    if os.path.exists('video/'+filename):
        Data = {
             'videoname': filename
        }
        #Пример рекомендаций
        Data['recommended_videos'] = [
        {
            'name': 'Рикролл :D',
            'link': 'prank.mp4',
            'image': 'Rickroll.jpg'
        },
        {
            'name': 'Рикролл :D',
            'link': 'prank.mp4',
            'image': 'no-photo.png'
        },
        {
            'name': 'Рикролл :D',
            'link': 'prank.mp4',
            'image': 'maxresdefault.jpg'
        }]
        template = env.get_template('video.html')
        # Отправляем HTML-страницу как ответ
        return response.html(template.render(data = Data))
    
    with open('templates/NotFound.html', 'r', encoding="UTF-8") as file:
        html_content = file.read()
    # Отправляем HTML-страницу как ответ
    return response.html(html_content)

@app.route('/servevideo/<filename:str>')
async def serve_video(request, filename):
    video_path = 'video/' + filename

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
    return await response.file(video_path, headers=headers)

@app.route('/image/<filename:str>')
async def serve_image(request, filename):
    return await response.file('Images/'+filename)
     

@app.route('/')
async def index(request):
    # Открываем файл с HTML-страницей и считываем его содержимое
    with open('templates/index.html', 'r', encoding="UTF-8") as file:
        html_content = file.read()

    if Database.get_user_id(request.cookies.get('Auth')) != None: 
        Data = {"auth":Database.get_user_id(request.cookies.get('Auth')), 'picture': Database.GetUserData(Database.get_user_id(request.cookies.get('Auth')))["PfpPath"]}
        print(Database.GetUserData(Database.get_user_id(request.cookies.get('Auth')))["PfpPath"])
        template = env.get_template('index.html')
        return response.html(template.render(data = Data))
    else:
        template = env.get_template('index.html')
        return response.html(html_content)


@app.route('/addvideo')
async def addvideo(request):
    # Открываем файл с HTML-страницей и считываем его содержимое
    with open('templates/addvideo.html', 'r', encoding="UTF-8") as file:
        html_content = file.read()

    # Отправляем HTML-страницу как ответ
    return response.html(html_content)

@app.route('/profile')
async def account_info(request: Request):
    # Здесь вы можете получить информацию об аккаунте и передать ее в шаблон Jinja2
    template = env.get_template('MyAccount.html')
    cookies = str(request.cookies.get('Auth'))
    account_data = Database.GetUserData(Database.get_user_id(cookies))
    return response.html(template.render(account=account_data))

@app.route('/videoupload', methods=['POST'])
async def upload_video(request):
    uploaded_videofile = request.files.get('video')
    uploaded_videoimage = request.files.get('image')
    uploaded_videoname = request.form.get('name')
    uploaded_videodesc = request.form.get('desc')
    if not uploaded_videofile:
        return response.text('Файл не загружен')

    # Сохраните файл на сервере
    random_name_video = generate_random_string(10)
    file_path = os.path.join('video/', random_name_video + ".mp4")

    with open(file_path, 'wb') as file:
        file.write(uploaded_videofile.body)

    if not uploaded_videoimage:
        #Если пользак не загрузил фотку для видео - берем рандомный кадр из видоса
        cap = cv2.VideoCapture(file_path)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        random_frame_number = random.randint(0, frame_count - 1)
        cap.set(cv2.CAP_PROP_POS_FRAMES, random_frame_number)
        ret, frame = cap.read()
        cap.release()
        random_screenshot_path = 'Images/'+random_name_video + ".png"
        cv2.imwrite(random_screenshot_path, frame)
    else:
        file_path = os.path.join('Images/', random_name_video + ".png")
        with open(file_path, 'wb') as file:
            file.write(uploaded_videofile.body)
    Database.AddVideo(uploaded_videoname, random_name_video, uploaded_videodesc, Database.get_user_id(request.cookies.get('Auth')))
    return response.text('Файл успешно загружен')
    

def validationpassword(password:str, passwordrepeat:str):
    len_password = False
    if len(password) < 8:
        len_password = False
    else:
        len_password = True

    digits_in_password = True
    # Проверка наличия цифр в пароле
    if not any(char.isdigit() for char in password):
        digits_in_password = False

    char_in_password = True
    # Проверка наличия букв в пароле
    if not any(char.isalpha() for char in password):
        char_in_password = False

    punctuation_in_password = True
    # Проверка наличия символов пунктуации в пароле
    if not any(char in string.punctuation for char in password):
        punctuation_in_password = False

    checkpassword = True
    if password != passwordrepeat:
        checkpassword = False
    
    return len_password and digits_in_password and char_in_password and punctuation_in_password and checkpassword

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
    
@app.route('/log', methods=['POST'])
async def log(request):
        cookiestring = generate_random_string(10)
        while not Database.CookieExists(cookiestring):
             cookiestring = generate_random_string(10)
        Login = request.form.get('username')
        if Database.LoginUser(Login,request.form.get('password')) != None:
             Database.create_session(cookiestring, Login)
        response = redirect('/')
        response.cookies['Auth'] = None
        return response

@app.route('/login')
async def login(request):
    cookies = str(request.cookies.get('Auth'))
    if cookies != 'None':
            response = redirect('/')
            return response
    with open('templates/login.html', 'r', encoding="UTF-8") as file:
        html_content = file.read()
        response = html(html_content)
    # Отправляем HTML-страницу как ответ
    return response
@app.route("/check")
async def check(request):
    return response.text(request.cookies.get('Auth'))
@app.route("/reset")
async def reset(request):
    response = text("Reset")
    response.cookies['Auth'] = None
    return response

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=8000)
import fastapi.responses
import numpy as np
import io
from PIL import Image
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Form, File, UploadFile

# Для капчи
from fastapi.responses import HTMLResponse
from fastapi import Depends
from google.auth.transport import requests
from google.oauth2 import id_token

import matplotlib.pyplot as plt
from typing import List
import hashlib

app = FastAPI()


#@app.get("/", response_class=HTMLResponse)
#def read_root(request: Request):
#  return templates.TemplateResponse("startPage.html",{"request": request})


app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
# возвращаем some.html, сгенерированный из шаблона
# передав туда одно значение something

@app.get("/")
async def get_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/")
async def post_index(request: Request):
    # Получение токена капчи из POST-запроса
    token = await request.form["g-recaptcha-response"]

    # Проверка токена капчи на сервере Google
    idinfo = id_token.verify_oauth2_token(
        token,
        requests.Request(),
        "6LfNj0kpAAAAAMT1G5d9G995YtljhFhs3LjKIfqb"  # Замените YOUR_SECRET_KEY на ваш ранее полученный secret key
    )

    if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
        return HTMLResponse(content="Invalid token", status_code=400)

    if idinfo['aud'] != "6LfNj0kpAAAAAOT_vhcGzdK_4xds1Ikw4CK0qBbD":  # Замените YOUR_SITE_KEY на ваш ранее полученный site key
        return HTMLResponse(content="Invalid token", status_code=400)

    return HTMLResponse(content="Success")


@app.post("/image_form", response_class=HTMLResponse)
async def make_image(request: Request,
                     r: int = Form(),
                     g: int = Form(),
                     files: List[UploadFile] = File(description="Multiple files as UploadFile")
                     ):
    # устанавливаем готовность прорисовки файлов, можно здесь проверить, что файлы вообще есть
    # лучше использовать исключения
    ready = False
    print(len(files))
    if (len(files) > 0):
        if (len(files[0].filename) > 0):
            ready = True
    images = []
    if ready:
        print([file.filename.encode('utf-8') for file in files])

        # преобразуем имена файлов в хеш -строку
        images = ["static/" + hashlib.sha256(file.filename.encode('utf-8')).hexdigest() for file in files]

        # берем содержимое файлов
        content = [await file.read() for file in files]

        # создаем объекты Image типа RGB
        p_images = [Image.open(io.BytesIO(con)).convert("RGB") for con in content]

        # Только для первой картинки из загруженных
        i = 0

        # Создаём новую картинку в локальной переменной
        shifted_x_image = p_images[i].copy()

        # Получаем ширину и высоту для процентной обработки
        width = shifted_x_image.width
        height = shifted_x_image.height

        iter_x = width - width * (r / 100)

        for j in range(0, width):

            for k in range(0, height):

                source_x = 0

                if iter_x < width:
                    source_x = iter_x
                else:
                    source_x = j - width * (r / 100)

                pixel = p_images[i].getpixel((source_x, k))

                shifted_x_image.putpixel((j, k), pixel)

                iter_x += 1

        # Создаём новую картинку на основе уже обработанной по оси X
        newOutputImage = shifted_x_image.copy()

        for j in range(0, width):

            iter_y = height - height * (g / 100)

            for k in range(0, height):

                source_y = 0

                if iter_y < height:
                    source_y = iter_y
                else:
                    source_y = k - height * (g / 100)

                pixel = shifted_x_image.getpixel((j, source_y))

                newOutputImage.putpixel((j, k), pixel)

                iter_y += 1

        p_images[i] = newOutputImage

        p_images[i].save("./" + images[i], 'JPEG')

    # Преобразуем изображение в массив numpy
    image_array = np.array(p_images[0])

    # Извлекаем значения красного (R), зеленого (G) и синего (B) каналов
    red_channel = image_array[:, :, 0]
    green_channel = image_array[:, :, 1]
    blue_channel = image_array[:, :, 2]

    # Вычисляем распределение цветов
    red_hist = np.histogram(red_channel, bins=256, range=(0, 255))
    green_hist = np.histogram(green_channel, bins=256, range=(0, 255))
    blue_hist = np.histogram(blue_channel, bins=256, range=(0, 255))

    # Координаты для гистограммы
    bin_centers = red_hist[1][:-1]

    # Строим графики
    plt.figure(figsize=(10, 6))
    plt.plot(bin_centers, red_hist[0], color='red', label='Red')
    plt.plot(bin_centers, green_hist[0], color='green', label='Green')
    plt.plot(bin_centers, blue_hist[0], color='blue', label='Blue')
    plt.xlabel('Значение пикселя')
    plt.ylabel('Частота')
    plt.title('Распределение цветов')
    plt.legend()
    plt.show()

    # возвращаем html с параметрами-ссылками на изображения, которые позже будут
    # извлечены браузером запросами get по указанным ссылкам в img src
    return templates.TemplateResponse("forms.html", {"request": request, "ready": ready, "images": images})


@app.get("/image_form", response_class=HTMLResponse)
async def make_image(request: Request):
 return templates.TemplateResponse("forms.html", {"request": request})

import fastapi.responses
import numpy as np
import io
from PIL import Image
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Form, File, UploadFile
import matplotlib.pyplot as plt
from typing import List
import hashlib
from PIL import ImageDraw
from fastapi.responses import RedirectResponse

app = FastAPI()
def sum_two_args(x,y):
 return x+y
# Hello World route


@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
  return templates.TemplateResponse("startPage.html",{"request": request})


app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
# возвращаем some.html, сгенерированный из шаблона
# передав туда одно значение something


@app.get("/some_url/{something}", response_class=HTMLResponse)
async def read_something(request: Request, something: str):
 return templates.TemplateResponse("some.html", {"request": request,
"something": something})
def create_some_image(some_difs):
 imx = 200
 imy = 200
 image = np.zeros((imx,imy, 3), dtype=np.int8)
 image[0:imy//2,0:imx//2,0] = some_difs
 image[imy//2:,imx//2:,2] = 240
 image[imy//2:,0:imx//2, 1] = 240
 return image
# возврат изображения в виде потока медиаданных по URL


@app.get("/bimage", response_class=fastapi.responses.StreamingResponse)
async def b_image(request: Request):
 # рисуем изображение, сюда можете вставить GAN, WGAN сети и т. д
 # взять изображение из массива в Image PIL
 image = create_some_image(100)
 im = Image.fromarray(image, mode="RGB")
 # сохраняем изображение в буфере оперативной памяти
 imgio = io.BytesIO()
 im.save(imgio, 'JPEG')
 imgio.seek(0)
 # Возвращаем изображение в виде mime типа image/jpeg
 return fastapi.responses.StreamingResponse(content=imgio, media_type="image/jpeg")
 # возврат двух изображений в таблице html, одна ячейка ссылается на url bimage
# другая ячейка указывает на файл из папки static по ссылке
# при этом файл туда предварительно сохраняется после генерации из массива


@app.get("/image", response_class=HTMLResponse)
async def make_image(request: Request):
 image_n = "image.jpg"
 image_dyn = request.base_url.path + "bimage"
 image_st = request.url_for("static", path=f'/{image_n}')
 image = create_some_image(250)
 im = Image.fromarray(image, mode="RGB")
 im.save(f"./static/{image_n}")
 # передаем в шаблон две переменные, к которым сохранили url
 return templates.TemplateResponse("image.html", {"request": request,
                                                  "im_st": image_st, "im_dyn": image_dyn})


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

    # возвращаем html с параметрами-ссылками на изображения, которые позже будут
    # извлечены браузером запросами get по указанным ссылкам в img src
    return templates.TemplateResponse("forms.html", {"request": request, "ready": ready, "images": images})


@app.get("/image_form", response_class=HTMLResponse)
async def make_image(request: Request):
 return templates.TemplateResponse("forms.html", {"request": request})

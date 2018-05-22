# -*- coding: utf-8 -*-

import config

import json
import glob
import jpglitch
import numpy as np
from io import BytesIO
import os
import PIL.Image
import random
import re
import requests
import subprocess as sub
import sys
from urllib.parse import quote
import uuid
from wand import image as wand_image


s = requests.session()


def d_path(path):
    return os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), path)


def files_path(path):
    return d_path('files/' + path)


def _random(image=False, ext: str = False):
    h = str(uuid.uuid4().hex)
    if image:
        return '{0}.{1}'.format(h, ext) if ext else h + '.png'
    return h


def get_json(url):
    with s.get(url) as resp:
        try:
            load = resp.json()
            return load
        except:
            return {}


def bytes_download(url):
    with s.get(url) as r:
        b = BytesIO(r.content)
        b.seek(0)
        return b


image_mimes = ['image/png', 'image/pjpeg', 'image/jpeg', 'image/x-icon']


def isimage(url):
    try:
        with s.head(url) as resp:
            if resp.status_code == 200:
                mime = resp.headers.get('Content-type', '').lower()
                if any([mime == x for x in image_mimes]):
                    return True
                else:
                    return False
    except:
        return False


def isgif(url):
    try:
        with s.head(url) as resp:
            if resp.status_code == 200:
                mime = resp.headers.get('Content-type', '').lower()
                if mime == "image/gif":
                    return True
                else:
                    return False
    except:
        return False


def do_magik(photo, scale):
    """Apply liquid rescale to image"""
    if scale > 50:
        scale = 50
    elif scale < 1:
        scale = 1
    try:
        b = BytesIO(photo)
        b.seek(0)
        i = wand_image.Image(file=b)
        i.format = 'jpg'
        i.alpha_channel = True
        if i.size >= (3000, 3000):
            return ':warning: `Image exceeds maximum resolution >= (3000, 3000).`', None
        i.transform(resize='800x800>')
        i.liquid_rescale(width=int(i.width * 0.5), height=int(i.height * 0.5),
                         delta_x=int(0.5 * scale) if scale else 1, rigidity=0)
        i.liquid_rescale(width=int(i.width * 1.5), height=int(i.height * 1.5), delta_x=scale if scale else 2,
                         rigidity=0)
        magikd = BytesIO()
        i.save(file=magikd)
        magikd.seek(0)
        return magikd
    except Exception as e:
        return str(e)


def do_gmagik(gif, gif_dir, rand, magik_value):
    try:
        frame = PIL.Image.open(gif)
    except:
        return ':warning: Invalid Gif.'
    if frame.size >= (3000, 3000):
        os.remove(gif)
        return ':warning: `GIF resolution exceeds maximum >= (3000, 3000).`'
    nframes = 0
    while frame:
        frame.save('{0}/{1}_{2}.png'.format(gif_dir, nframes, rand), 'GIF')
        nframes += 1
        try:
            frame.seek(nframes)
        except EOFError:
            break
    imgs = glob.glob(gif_dir + "*_{0}.png".format(rand))
    if len(imgs) > 150:
        for image in imgs:
            os.remove(image)
        os.remove(gif)
        return ":warning: `GIF has too many frames (>= 150 Frames).`"
    if len(imgs) == 1:
        from shutil import copyfile
        for x in range(25*magik_value):
            t = gif_dir + '{0}_{1}.png'.format(x+1, rand)
            copyfile(imgs[0], t)
        imgs = glob.glob(gif_dir + "*_{0}.png".format(rand))

    l = {int(x.split('/')[-1].split('_')[0]): x for x in imgs}
    _im = l[0]
    for idx in sorted(l):
        image = l[idx]
        try:
            im = wand_image.Image(filename=_im)
        except:
            continue
        i = im.clone()
        i.transform(resize='800x800>')
        i.liquid_rescale(width=int(i.width * 1.2), height=int(i.height * 1.2), delta_x=1, rigidity=0)
        i.liquid_rescale(width=int(i.width * 0.8), height=int(i.height * 0.8), delta_x=2, rigidity=0)
        i.resize(i.width, i.height)
        i.save(filename=image)
        _im = image
    return True


def gmagik(photo, magik_value=1):
    try:
        gif_dir = files_path('gif/')
        rand = _random()
        gifin = gif_dir + '1_{0}.gif'.format(rand)
        gifout = gif_dir + '2_{0}.gif'.format(rand)
        with open(gifin, "wb") as f:
            f.write(photo)
        do_gmagik(gifin, gif_dir, rand, magik_value)
        args = ['ffmpeg', '-y', '-nostats', '-loglevel', '0', '-i', gif_dir + '%d_{0}.png'.format(rand), '-r',
                '25', gifout]
        p = sub.Popen(args, stdout=sub.PIPE, stderr=sub.PIPE)
        p.communicate()

        f = open(gifout, 'rb')
        for image in glob.glob(gif_dir + "*_{0}.png".format(rand)):
            os.remove(image)
        os.remove(gifin)
        os.remove(gifout)
        return f
    except Exception as e:
        print(e)


def triggered(photo):
    """Generate a Triggered Gif for an Image"""
    path = files_path(_random(True))
    path2 = path[:-3] + 'gif'
    t_path = files_path('Triggered.jpg')

    with open(path, 'wb') as file:
        file.write(photo)

    code = ['convert',
            'canvas:none',
            '-size', '512x680!',
            '-resize', '512x680!',
            '-draw', 'image over -60,-60 640,640 "{0}"'.format(path),
            '-draw', 'image over 0,512 0,0 "{0}"'.format(t_path),
            '(',
            'canvas:none',
            '-size', '512x680!',
            '-draw', 'image over -45,-50 640,640 "{0}"'.format(path),
            '-draw', 'image over 0,512 0,0 "{0}"'.format(t_path),
            ')',
            '(',
            'canvas:none',
            '-size', '512x680!',
            '-draw', 'image over -50,-45 640,640 "{0}"'.format(path),
            '-draw', 'image over 0,512 0,0 "{0}"'.format(t_path),
            ')',
            '(',
            'canvas:none',
            '-size', '512x680!',
            '-draw', 'image over -45,-65 640,640 "{0}"'.format(path),
            '-draw', 'image over 0,512 0,0 "{0}"'.format(t_path),
            ')',
            '-layers', 'Optimize',
            '-set', 'delay', '2',
            path2]

    p = sub.Popen(code, stdout=sub.PIPE, stderr=sub.PIPE)
    p.communicate()

    f = open(path2, 'rb')
    os.remove(path)
    os.remove(path2)
    return f


def badmeme():
    """returns bad meme"""
    load = get_json("https://api.imgflip.com/get_memes")
    url = random.choice(load['data']['memes'])
    url = url['url']
    b = bytes_download(url)
    return b


def jpeg(photo, quality=1):
    """Add more JPEG to an Image\nNeeds More JPEG!"""
    if quality > 10:
        quality = 10
    elif quality < 1:
        quality = 1
    img = PIL.Image.open(BytesIO(photo)).convert('RGB')
    final = BytesIO()
    img.save(final, 'JPEG', quality=quality)
    final.seek(0)
    return final


def a(usr_name):
    """make dank meme (currently not working)"""
    payload = {'template_id': '57570410', 'username': '', 'password': '', 'text0': '',
               'text1': '{0} you'.format(usr_name)}
    with s.post("https://api.imgflip.com/caption_image", data=payload) as r:
        load = r.json()
    url = load['data']['url']
    return bytes_download(url)


def giphy(text=None):
    if text is None:
        api = 'http://api.giphy.com/v1/gifs/random?&api_key=dc6zaTOxFJmzC'
    else:
        api = 'http://api.giphy.com/v1/gifs/search?q={0}&api_key=dc6zaTOxFJmzC'.format(quote(text))
    load = get_json(api)
    try:
        gif = random.choice(load['data'])
    except:
        gif = load['data']
    url = gif['url']
    return url


retro_regex = re.compile(r"((https)(\:\/\/|)?u3\.photofunia\.com\/.\/results\/.\/.\/.*(\.jpg\?download))")


def do_retro(text, bcg):
    if '|' not in text:
        if len(text) >= 15:
            text = [text[i:i + 15] for i in range(0, len(text), 15)]
        else:
            split = text.split()
            if len(split) == 1:
                text = [x for x in text]
                if len(text) == 4:
                    text[2] = text[2] + text[-1]
                    del text[3]
            else:
                text = split
    else:
        text = text.split('|')
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:43.0) Gecko/20100101 Firefox/43.0'}
    payload = {'current-category': 'all_effects',
               'bcg': bcg,
               'txt': '4'}
    count = 1
    for _s in text:
        if count > 3:
            break
        payload['text' + str(count)] = _s.replace("'", "\'")
        count += 1
    try:
        with s.post('https://photofunia.com/effects/retro-wave?server=3', data=payload, headers=headers) as r:
            txt = r.text
    except TimeoutError:
        return
    match = retro_regex.findall(txt)
    if match:
        download_url = match[0][0]
        b = bytes_download(download_url)
        return b
    return False


def do_glitch(b, amount, seed, iterations):
    b.seek(0)
    img = jpglitch.Jpeg(bytearray(b.getvalue()), amount, seed, iterations)
    final = _random() + '.jpeg'
    img.save_image(final)
    f = open(final, 'rb')
    os.remove(final)
    return f


def do_gglitch(b):
    b = bytearray(b.getvalue())
    for x in range(0, sys.getsizeof(b)):
        if b[x] == 33:
            if b[x + 1] == 255:
                end = x
                break
            elif b[x + 1] == 249:
                end = x
                break
    for x in range(13, end):
        b[x] = random.randint(0, 255)
    return b


def glitch(photo, iterations, amount, seed, url, _isgif):
    if iterations is None:
        iterations = random.randint(1, 30)
    if amount is None:
        amount = random.randint(1, 20)
    elif amount > 99:
        amount = 99
    if seed is None:
        seed = random.randint(1, 20)
    if url and not photo:
        b = bytes_download(url)
        if not _isgif:
            img = PIL.Image.open(b)
            b = BytesIO()
            img.save(b, format='JPEG')
            final = do_glitch(b, amount, seed, iterations)
            return final
        else:
            final = do_gglitch(b)

            gif_dir = files_path('gif/')
            rand = _random()
            gifout = gif_dir + '2_{0}.gif'.format(rand)
            with open(gifout, "wb") as f:
                f.write(final)
            f = open(gifout, 'rb')
            os.remove(gifout)
            return f
    else:
        img = PIL.Image.open(BytesIO(photo))
        photo = BytesIO()
        img.save(photo, format='JPEG')
        final = do_glitch(photo, amount, seed, iterations)
        return final


def glitch2(photo):
    path = files_path(_random(True))

    with open(path, 'wb') as file:
        file.write(photo)

    code = ['convert', '(', path, '-resize', '1024x1024>', ')', '-alpha', 'on', '(', '-clone', '0',
            '-channel', 'RGB', '-separate', '-channel', 'A', '-fx', '0', '-compose', 'CopyOpacity',
            '-composite', ')', '(', '-clone', '0', '-roll', '+5', '-channel', 'R', '-fx', '0', '-channel',
            'A', '-evaluate', 'multiply', '.3', ')', '(', '-clone', '0', '-roll', '-5', '-channel', 'G',
            '-fx', '0', '-channel', 'A', '-evaluate', 'multiply', '.3', ')', '(', '-clone', '0', '-roll',
            '+0+5', '-channel', 'B', '-fx', '0', '-channel', 'A', '-evaluate', 'multiply', '.3', ')', '(',
            '-clone', '0', '-channel', 'A', '-fx', '0', ')', '-delete', '0', '-background', 'none',
            '-compose', 'SrcOver', '-layers', 'merge', '-rotate', '90', '-wave', '1x5', '-rotate', '-90',
            path]

    p = sub.Popen(code, stdout=sub.PIPE, stderr=sub.PIPE)
    p.communicate()

    f = open(path, 'rb')
    os.remove(path)
    return f


def posnum(num):
    if num < 0:
        return - (num)
    else:
        return num


def find_coeffs(pa, pb):
    matrix = []
    for p1, p2 in zip(pa, pb):
        matrix.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0] * p1[0], -p2[0] * p1[1]])
        matrix.append([0, 0, 0, p1[0], p1[1], 1, -p2[1] * p1[0], -p2[1] * p1[1]])
    A = np.matrix(matrix, dtype=np.float)
    B = np.array(pb).reshape(8)
    res = np.dot(np.linalg.inv(A.T * A) * A.T, B)
    return np.array(res).reshape(8)


def eyes(b, eye=None, resize=None, url=None):
    resize_amount = None
    monocle = False
    flipped = False
    flipped_count = 1
    if eye != None:
        eye = eye.lower()
    if eye is None or eye == 'default' or eye == '0':
        eye_location = files_path('eye.png')
    elif eye == 'spongebob' or eye == 'blue' or eye == '1':
        eye_location = files_path('spongebob_eye.png')
    elif eye == 'big' or eye == '2':
        eye_location = files_path('big_eye.png')
        resize_amount = 110
    elif eye == 'small' or eye == '3':
        eye_location = files_path('small_eye.png')
        resize_amount = 110
    elif eye == 'money' or eye == '4':
        eye_location = files_path('money_eye.png')
    elif eye == 'blood' or eye == 'bloodshot' or eye == '5':
        eye_location = files_path('bloodshot_eye.png')
        resize_amount = 200
    elif eye == 'red' or eye == '6':
        eye_location = files_path('red_eye.png')
        resize_amount = 200
    elif eye == 'meme' or eye == 'illuminati' or eye == 'triangle' or eye == '7':
        eye_location = files_path('illuminati_eye.png')
        resize_amount = 150
    elif eye == 'googly' or eye == 'googlyeye' or eye == 'plastic' or eye == '8':
        eye_location = files_path('googly_eye.png')
        resize_amount = 200
    elif eye == 'monocle' or eye == 'fancy' or eye == '9':
        eye_location = files_path('monocle_eye.png')
        resize_amount = 80
        monocle = True
    elif eye == 'flip' or eye == 'flipped' or eye == 'reverse' or eye == 'reversed' or eye == '10':
        eye_location = files_path('eye.png')
        eye_flipped_location = files_path('eye_flipped.png')
        flipped = True
    elif 'eyesCenter' in eye or eye == 'one' or eye == 'center' or eye == '11':
        eye_location = files_path('one_eye_center.png')
    else:
        eye_location = files_path('eye.png')
    if resize_amount is None:
        resize_amount = 130
    try:
        if resize != None:
            sigh = str(resize).split('.')
            if len(sigh) == 1:
                resize = int(resize)
            else:
                resize = float(resize)
            if resize == 0:
                resize_amount = 120
            else:
                resize_amount = resize * 100
    except ValueError:
        resize_amount = 120
    img = PIL.Image.open(BytesIO(b)).convert("RGBA")
    eyes = PIL.Image.open(eye_location).convert("RGBA")
    data = {"url": url}
    headers = {"Content-Type": "application/json",
               "Ocp-Apim-Subscription-Key": config.ocp_key}
    with s.post(
            'https://westcentralus.api.cognitive.microsoft.com/face/v1.0/detect?returnFaceId=false&returnFaceLandmarks=true&returnFaceAttributes=headPose',
            headers=headers, data=json.dumps(data)) as r:
            faces = r.json()
    eye_list = []
    for f in faces:
        if monocle == True:
            eye_list += ([((f['faceLandmarks']['pupilRight']['x'], f['faceLandmarks']['pupilRight']['y']),
                           f['faceRectangle']['height'], (f['faceAttributes']['headPose']))])
        else:
            eye_list += (((f['faceLandmarks']['pupilLeft']['x'], f['faceLandmarks']['pupilLeft']['y']),
                          f['faceRectangle']['height'], (f['faceAttributes']['headPose'])), (
                             (f['faceLandmarks']['pupilRight']['x'], f['faceLandmarks']['pupilRight']['y']),
                             f['faceRectangle']['height'], (f['faceAttributes']['headPose'])))
    for e in eye_list:
        width, height = eyes.size
        h = e[1] / resize_amount * 50
        width = h / height * width
        if flipped:
            if (flipped_count % 2 == 0):
                s_image = wand_image.Image(filename=eye_flipped_location)
            else:
                s_image = wand_image.Image(filename=eye_location)
            flipped_count += 1
        else:
            s_image = wand_image.Image(filename=eye_location)
        i = s_image.clone()
        i.resize(int(width), int(h))
        s_image = BytesIO()
        i.save(file=s_image)
        s_image.seek(0)
        inst = PIL.Image.open(s_image)
        yaw = e[2]['yaw']
        pitch = e[2]['pitch']
        width, height = inst.size
        pyaw = int(yaw / 180 * height)
        ppitch = int(pitch / 180 * width)
        new = PIL.Image.new('RGBA', (width + posnum(ppitch) * 2, height + posnum(pyaw) * 2), (255, 255, 255, 0))
        new.paste(inst, (posnum(ppitch), posnum(pyaw)))
        width, height = new.size
        coeffs = find_coeffs([(0, 0), (width, 0), (width, height), (0, height)],
                             [(ppitch, pyaw), (width - ppitch, -pyaw), (width + ppitch, height + pyaw),
                              (-ppitch, height - pyaw)])
        inst = new.transform((width, height), PIL.Image.PERSPECTIVE, coeffs, PIL.Image.BICUBIC).rotate(
            -e[2]['roll'], expand=1, resample=PIL.Image.BILINEAR)
        eyel = PIL.Image.new('RGBA', img.size, (255, 255, 255, 0))
        width, height = inst.size
        if monocle:
            eyel.paste(inst, (int(e[0][0] - width / 2), int(e[0][1] - height / 3.7)))
        else:
            eyel.paste(inst, (int(e[0][0] - width / 2), int(e[0][1] - height / 2)))
        img = PIL.Image.alpha_composite(img, eyel)
    final = BytesIO()
    img.save(final, "png")
    final.seek(0)
    return final


def eyes_list():
    eyes = ['Default - 0', 'Spongebob - 1', 'Big - 2', 'Small - 3', 'Money - 4', 'Bloodshot - 5', 'Red - 6',
            'Illuminati - 7', 'Googly - 8', 'Monocle - 9', 'Flipped - 10', 'Center - 11']
    return '\n'.join(eyes)

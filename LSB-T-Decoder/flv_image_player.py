import cv2
import time
import numpy as np
import win32gui
import win32con
import win32api
from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import win32ui
def change(ll):
    for index in range(len(ll)):
        i = ll[index][0]
        j = ll[index][1]

        if (i % 2 == 0):
            i += 1
        else:
            i -= 1

        if (j % 2 == 0):
            j += 1
        else:
            j -= 1

        ll[index] = (i, j)
    return ll
def random_change(image, size=8):

    # 获取图像的宽度和高度
    height, width, _ = image.shape

    # 定义每个小块的宽度和高度
    block_width = width // size
    block_height = height // size

    # 切割图像并存储到列表中
    blocks = []
    index_list = []  # 索引列表

    for i in range(size):
        for j in range(size):
            block = image[i * block_height:(i + 1) * block_height, j * block_width:(j + 1) * block_width]
            blocks.append(block)
            index_list.append((i, j))  # 记录小块的索引


    # 打乱小块的顺序
    # shuffled_index_list = np.random.permutation(index_list)



    shuffled_index_list = change(index_list)

    # 按照打乱后的索引列表重新组合小块
    restored_image = np.zeros_like(image)
    # cv2.imshow('Restored Image1', restored_image)
    for k, (i, j) in enumerate(shuffled_index_list):
        block = blocks[k]
        restored_image[i * block_height:(i + 1) * block_height, j * block_width:(j + 1) * block_width] = block

    # 显示图像
    cv2.imshow('Restored Image', restored_image)
    return restored_image
def equal(px,px0):
    flag = True
    for i in range(0,3):
        # print(i)
        if(abs(int(px[i])-int(px0[i]))>30):
            flag = False


    return flag
def check(x,y,w,h,img):
    left=0
    right=0
    top=0
    bottom=0

    px = img[int(y+h/2),x]
    for i in range(0,w):
        px0 = img[int(y+h/2),x+i]
        if (equal(px,px0)):
            pass
        else:
            left = i
            break
    # print("left")
    # print(left)

    px = img[int(y + h / 2), x+w-1]
    for i in range(0, w):
        px0 = img[int(y + h / 2), x+w-1-i]
        if (equal(px, px0)):
            pass
        else:
            right = i
            break
    # print("right")
    # print(right)

    px = img[y, int(x + w / 2)]
    for i in range(0, h):
        px0 = img[y+i, int(x + w / 2)]
        if (equal(px, px0)):
            pass
        else:
            top = i
            break
    # print("top")
    # print(top)

    px = img[y+h-1, int(x + w / 2)]
    for i in range(0, h):
        px0 = img[y+h-1-i, int(x + w / 2)]
        if (equal(px, px0)):
            pass
        else:
            bottom = i
            break
    # print("bottom")
    # print(bottom)

    return left,right,top,bottom
def getOrigin(img):
    # 提取绿色边框的区域
    lower_green = np.array([0, 200, 0])
    upper_green = np.array([40, 255, 40])
    mask = cv2.inRange(img, lower_green, upper_green)
    # 找到绿色边框的轮廓
    contours, hierarchy = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # 找到包含轮廓的最小矩形
    x, y, w, h = cv2.boundingRect(contours[0])


    left,right,top,bottom = check(x,y,w,h,img)

    # 截取原始图像中的区域
    cropped = img[y+top:y+h-bottom, x+left:x+w-right]
    # 在图像中绘制矩形框以显示截取的区域（可选）
    # cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
    # cv2.imshow('rectangle', img)
    # 显示结果图像
    # cv2.imshow('Result', cropped)
    # cv2.imwrite('S1_result.png', cropped)
    # cv2.waitKey(0)
    return cropped

def window_capture(hwnd):
    # 获取窗口客户区的大小和位置
    client_rect = win32gui.GetClientRect(hwnd)

    # 获取窗口设备上下文
    hwndDC = win32gui.GetWindowDC(hwnd)
    mfcDC = win32ui.CreateDCFromHandle(hwndDC)
    saveDC = mfcDC.CreateCompatibleDC()

    # 创建截图对象
    saveBitMap = win32ui.CreateBitmap()
    saveBitMap.CreateCompatibleBitmap(mfcDC, client_rect[2], client_rect[3])

    # 将截图对象选入截图DC
    saveDC.SelectObject(saveBitMap)

    # 截图
    # saveDC.BitBlt((0, 0), (client_rect[2], client_rect[3]), mfcDC, (0+8, 0+31), win32con.SRCCOPY)
    saveDC.BitBlt((0, 0), (client_rect[2], client_rect[3]), mfcDC, (0, 0), win32con.SRCCOPY)
    # 将截图转换为numpy数组
    signedIntsArray = saveBitMap.GetBitmapBits(True)
    img = np.frombuffer(signedIntsArray, dtype="uint8")
    img.shape = (client_rect[3], client_rect[2], 4)

    # bit图转mat图

    win32gui.DeleteObject(saveBitMap.GetHandle())
    mfcDC.DeleteDC()
    saveDC.DeleteDC()
    # 释放内存
    return cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)  # 转为RGB图返回

def concat(img1):
    alpha = 0.3
    # cv2.imshow("img1_decode-0", img1)
    # height, width = img1.shape[:2]
    # split_position = width // 2

    # 切分图像
    # left_half = img1[:, :split_position]
    # right_half = img1[:, split_position:]
    # # 水平翻转
    # right_half = cv2.flip(right_half, 1)
    # # 显示切分后的图像
    # # cv2.imshow('Left Half', left_half)
    # # cv2.imshow('Right Half', right_half)
    #
    # # img1 = getOrigin(img1)
    # img1 = right_half
    # img2 = left_half
    # img1 = cv2.resize(img1, (1530, 835))
    # img2 = cv2.resize(img2, (1530, 835))
    img2 = img1
    img1 = cv2.flip(img1, 1)
    img2 = cv2.convertScaleAbs(img2, alpha=(1 - alpha))

    enc_img = cv2.subtract(img1, img2)
    # 将enc_img的像素值缩放到4倍
    enc_img = cv2.convertScaleAbs(enc_img, alpha=(1 / alpha))
    # enc_img = cv2.resize(enc_img, (1530, 835))
    # cv2.imshow("enc_img", enc_img)
    height, width = enc_img.shape[:2]
    split_position = width // 2

    left_half = enc_img[:, :split_position]
    left_half = random_change(left_half, 16)
    left_half = cv2.resize(left_half, (1530, 835))
    cv2.imshow("decode", left_half)


def play(location):
    count = 0
    time.sleep(5)
    # video_path = 'recorder/21150669/1684313859.flv'
    video_path = location
    print(video_path)
    cap = cv2.VideoCapture(video_path)
    origin_timestamp = cap.get(cv2.CAP_PROP_POS_MSEC)
    origin_time = time.time()
    print("origin_timestamp",origin_timestamp)
    print("origin_time",origin_time)
    while True:

        count+=1

        ret, frame = cap.read()

        if not ret:
            break
        cv2.imshow("frame", frame)
        concat(img1=frame)
        # cv2.imshow('Video Playback', frame)

        timestamp = cap.get(cv2.CAP_PROP_POS_MSEC)
        nowtime = time.time()

        wait_time = (timestamp - origin_timestamp) - (nowtime - origin_time) * 1000
        if(count%60==0):
            print("timestamp", timestamp)
            print("time", nowtime)
            print(wait_time)

        # 检测按键，按下 'q' 键退出循环
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        if wait_time > 0:
            time.sleep(wait_time / 1000.0)
        # if wait_time < -200:
        #     for i in range(5):
        #         cap.read()

    # 释放资源
    cap.release()
    cv2.destroyAllWindows()

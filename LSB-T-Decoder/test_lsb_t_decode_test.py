
import cv2
import numpy as np
import win32gui
import win32con
import win32ui

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


while True:
    alpha = 0.2
    # alpha = 0.03125
    # 获取窗口截图
    # img1 = window_capture(hwnd)

    hwnd_child = 0x00360B52

    # 获取窗口截图
    img1 = window_capture(hwnd_child)

    # img1 = cv2.resize(img1, (550, 300))
    # img2 = cv2.resize(img2, (550, 300))

    cv2.imshow("img1_decode-0", img1)
    height, width = img1.shape[:2]
    split_position = width // 2

    # 切分图像
    left_half = img1[:, :split_position]
    right_half = img1[:, split_position:]
    #水平翻转
    right_half = cv2.flip(right_half, 1)
    # 显示切分后的图像
    cv2.imshow('Left Half', left_half)
    cv2.imshow('Right Half', right_half)

    # img1 = getOrigin(img1)
    img1 = right_half
    img2 = left_half
    # img1 = cv2.resize(img1, (1530, 835))
    # img2 = cv2.resize(img2, (1530, 835))

    img2 = cv2.convertScaleAbs(img2, alpha=(1 - alpha))

    enc_img = cv2.subtract(img1, img2)
    # 将enc_img的像素值缩放到4倍
    enc_img = cv2.convertScaleAbs(enc_img, alpha=(1/alpha))

    enc_img_bk = cv2.resize(enc_img, (850, 550))
    # cv2.imshow("lsb_t_decode", enc_img_bk)
    cv2.imshow("enc_img_end_decode", enc_img)

    if cv2.waitKey(1) == 27:  # 按ESC退出
        break

cv2.destroyAllWindows()

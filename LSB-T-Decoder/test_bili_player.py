import cv2
import time

video_path = 'recorder/21150669/1684823331.flv'

# video_path = 'recorder/21150669/1684313859.flv'
cap = cv2.VideoCapture(video_path)

# ret, frame = cap.read()
# cv2.imshow('Video Playback', frame)

origin_timestamp = cap.get(cv2.CAP_PROP_POS_MSEC)
origin_time = time.time()
print("origin_timestamp",origin_timestamp)
print("origin_time",origin_time)
while True:
    ret, frame = cap.read()
    timestamp = cap.get(cv2.CAP_PROP_POS_MSEC)
    nowtime = time.time()
    if not ret:
        break
    cv2.imshow('Video Playback', frame)
    wait_time = (timestamp - origin_timestamp) - (nowtime - origin_time) * 1000
    print("timestamp", timestamp)
    print("time", nowtime)
    print(wait_time)

    # 检测按键，按下 'q' 键退出循环
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    if wait_time > 0:
        time.sleep(wait_time / 1000.0)

# 释放资源
cap.release()
cv2.destroyAllWindows()
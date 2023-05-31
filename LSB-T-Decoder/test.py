import subprocess as sp
import numpy as np
import cv2
import time
import json

def get_video_dimensions(filename):
    # 构建ffprobe命令
    command = ['D:\\ffmpeg-master-latest-win64-gpl-shared\\ffmpeg-master-latest-win64-gpl-shared\\bin\\ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'json', filename]

    # 执行命令并捕获输出
    result = sp.run(command, capture_output=True, text=True)

    # 解析输出为JSON格式
    output = result.stdout.strip()
    info = json.loads(output)

    # 获取视频长宽信息
    width = info['streams'][0]['width']
    height = info['streams'][0]['height']

    return width, height


cmd = "D:/ffmpeg-master-latest-win64-gpl-shared/ffmpeg-master-latest-win64-gpl-shared/bin/ffmpeg"
cmd2 = "D:/ffmpeg-master-latest-win64-gpl-shared/ffmpeg-master-latest-win64-gpl-shared/bin/ffplay"
path1 = 'recorder/21150669/1684326759.flv'
path2 = "test/test.mp4"

path = path1


command = [ cmd,
            '-i', path,
            '-f', 'image2pipe',
            # '-vf', 'fps=30',
            # '-vsync', 'cfr',
            '-pix_fmt', 'rgb24',
            '-vcodec', 'rawvideo', '-']

# command = ['ffmpeg',
#            '-i', path,
#            '-r', '30',
#            '-y',  # 覆盖输出文件
#            output_file]

width, height = get_video_dimensions(path)
print('视频尺寸：', width, 'x', height)

pipe = sp.Popen(command, stdout = sp.PIPE, bufsize=10**7)

# width = 1280
# height = 720

# time.sleep(1)
start_time = time.time()
frame_count = 0
while True:
    # print(frame_count)
    frame_count+=1
    if frame_count % 10 == 0:
        elapsed_time = time.time() - start_time
        current_fps = frame_count / elapsed_time
        print(f'当前帧率: {current_fps:.2f} fps')

    #读取420 * 360 * 3字节（= 1帧）
    raw_image = pipe.stdout.read(width*height*3)

    #将读取的字节转换为numpy数组
    # image =  np.frombuffer(raw_image, dtype='uint8')
    image_temp = np.frombuffer(raw_image, dtype=np.uint8)
    image_temp_2 = image_temp.reshape((height,width,3))
    cv2.imshow("image", image_temp_2)

    # random_image = np.random.randint(0, 256, (360, 640, 3), dtype=np.uint8)
    # cv2.imshow("random_image", random_image)

    # cv2.waitKey(1)
    if cv2.waitKey(1) == 27:  # 按ESC退出
        break


#丢弃管道缓冲区中的数据。
# pipe.stdout.flush()

#
# stream = ffmpeg.input(path2)
# stream = ffmpeg.hflip(stream)
# stream = ffmpeg.output(stream, 'output.mp4')
# ffmpeg.run(stream)
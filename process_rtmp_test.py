import sys
import os
import time

import cv2
from PIL import Image
import datetime
import numpy as np

from server.rtpm_url_config import *
from LOG import *
from paddle_detection import Yolov3Detection

QUEUE_SIZE = 2


SHOW_TIME = True


class DetectionStage:
    def __init__(self,target,pre_queue,next_queue, queue_size=None):
        self.target = target
        self.stopped = False
        self.prev = pre_queue
        self.Q = next_queue

    def get_next(self, timeout=None):
        if self.prev:
            return self.prev.get(timeout=timeout)
        else:
            return None
    def is_empty(self):
        if self.prev:
            if self.prev.qsize() > 0:
                return False
            else:
                return True
        return True

    def wait_for_queue(self, time_step):
        while self.Q.full():
            time.sleep(time_step)

    def wait_for_stop(self, time_step):
        if self.prev is not None:
            while not self.prev.stopped:
                time.sleep(time_step)
        while not self.Q.empty():
            time.sleep(time_step)

    def parseImName(self, imName):
        pass



def load_im(next_queue,pre_queuq):
    image_loader =  ImageLoader(None,next_queue)
    image_loader.loop_load_image()

def first_layer_detection(pre_queue,next_queue):
    first_layer = FirstLayerDetection(pre_queue,next_queue)
    first_layer.fstlayer_detection()

class ImageLoader(DetectionStage):
    '''Load images for prediction'''

    def __init__(self, pre_queue,next_queue, queue_size=QUEUE_SIZE):
        super(ImageLoader, self).__init__(self.loop_load_image, pre_queue,next_queue, queue_size)
        print("server started")

    def loop_load_image(self):


        ip = '192.168.101.64'
        port = '8000'
        channel_num = '1'
        device_name = 'test'
        update_type = '0'

        #cv2.namedWindow('hello', flags=cv2.WINDOW_FREERATIO)
        toc_refresh = time.time()
        while True:
            tic_refresh = time.time()

            tm_inter = tic_refresh - toc_refresh
            if tm_inter > 600:
                logger.info("heart detecting")
                toc_refresh = tic_refresh


            cap = cv2.VideoCapture('/home/zzj/work1/20200506_170555.mp4')
            if cap.isOpened():
                ret, image = cap.read()

                tic = time.time()
                frame = image
                time.sleep(0.01)
                if not ret or frame is None:
                    logger.info('invalid cap:' + device_name)
                    continue
                cv2.putText(frame, strftime("%H:%M:%S"), (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 2,
                            (0, 255, 0), 2, cv2.LINE_AA)
                cv2.imshow('hello', frame)
                cv2.waitKey(1)
                while self.Q.qsize() > 1:
                    self.Q.get()

                im = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                im = np.array(im)
                self.wait_for_queue(0.3)
                self.Q.put((update_type, im))
                toc = time.time()
                time.sleep(0.05)
                if SHOW_TIME:
                    pass
                    #logger.info('\t' + 'load all image time:' + str(toc - tic)

        self.wait_for_stop(1)
        # logger.info('ImageLoader: %fs' % (np.mean(time_rec)))

class FirstLayerDetection(DetectionStage):
    def __init__(self, pre_queue,next_queue, queue_size=QUEUE_SIZE):
        super(FirstLayerDetection, self).__init__(self.fstlayer_detection,pre_queue,next_queue, queue_size)
        self.model = Yolov3Detection(1)

    def fstlayer_detection(self):
        while True:
            if self.is_empty():
                continue
            try:
                update_type, im = self.get_next(
                    timeout=10)
            except Exception:
                continue
            tic = time.time()
            logger.info("first layer detection")
            tic = time.time()

            detect1dict = self.model.single_image_detect(im)

            toc = time.time()
            if SHOW_TIME:
                logger.info('first layer time:' + str(toc - tic))
            self.wait_for_queue(1)
            self.Q.put(
                (update_type, im, detect1dict))


        self.wait_for_stop(1)
        self.stopped = True
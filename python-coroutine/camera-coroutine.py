import logging
from datetime import datetime as dt
from datetime import timedelta
from time import sleep

import matplotlib.pyplot as plt
import numpy as np
import pygame
import pygame.camera


def display(image_list):
    fig = plt.figure()
    side = int(np.sqrt(len(image_list))) + 1
    for i, img in enumerate(image_list, 1):
        fig.add_subplot(side, side, i)
        plt.imshow(img)
    fig.savefig('captured_pics.png')


def get_logger(loggername):
    logger = logging.getLogger(loggername)
    logger.setLevel(logging.DEBUG)
    return logger


def timer(func):
    interval = timedelta(seconds=1)
    timer_log = get_logger('Timer')

    def wrapper(*args, **kwargs):
        start_time = dt.now()
        while True:
            if dt.now() > start_time + interval:
                timer_log.info('Trigger a function')
                func(*args, **kwargs)
                return
        else:
            sleep(interval.seconds/20)
    return wrapper


class Camera(object):
    def __init__(self):
        pygame.init()
        pygame.camera.init()
        self.size = (640, 480)
        self.display = pygame.display.set_mode(self.size, 0)
        self.clist = pygame.camera.list_cameras()
        if not self.clist:
            raise ValueError('No cameras detected')
        self.cam = pygame.camera.Camera(self.clist[0], self.size)
        self.cam.start()
        self.snapshot = pygame.surface.Surface(self.size, 0, self.display)
        self.camera_log = get_logger('Camera')
        self.camera_log.info('The live stream capture is started')

    def __enter__(self):
        return self.cam, self.snapshot, self.display

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.cam.stop()
        self.camera_log.info('The live stream capture is ended')


class HSVequalInterval(object):
    def __init__(self):
        self.log_init()
        self.pygame_cam = Camera()
        self.coroutine_init()
        self.image_list = []

    def log_init(self):
        logging.basicConfig()
        self.coroutine_log = get_logger('Coroutine')

    def coroutine_init(self):
        self.coro = self.coroutine()
        next(self.coro)

    def __call__(self):
        with self.pygame_cam as c:
            self.cam, self.snapshot, self.display = c
            while True:
                try:
                    self.capture()
                except KeyboardInterrupt:
                    return self.image_list

    @timer
    def capture(self):
        if self.cam.query_image():
            current_image = self.cam.get_image(self.snapshot)
            self.coro.send(current_image)
            self.display.blit(current_image, (0, 0))
            pygame.display.update()
            self.coroutine_log.info('Sending an Image')

    def coroutine(self):
        self.coroutine_log.info('The coroutine is started')
        while True:
            self.snapshot = yield
            self.image_list.append(pygame.surfarray.array3d(self.snapshot))


if __name__ == '__main__':
    counting = HSVequalInterval()
    counting_images = counting()
    display(counting_images)

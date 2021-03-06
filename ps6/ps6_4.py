import numpy as np
import cv2
import algo
import os
import math


def sample_init(img_size, num):
    sample_set = []
    width = img_size[1]
    height = img_size[0]
    interval = width * height / num

    for i in range(0, num):
        y = (i * interval) / width
        x = (i * interval) % width
        sample_set.append([x, y, 1 / num])

    return sample_set


cap = cv2.VideoCapture('input\\pedestrians.avi')

x0 = 211
y0 = 36
w = 100
h = 294

t = 0
template = np.zeros((h, w))

num_sample = 1000
sample_set = []

center_x = float(x0 + w / 2)
center_y = float(y0 + h / 2)

delta_d = 10.0
delta_mse = 10.0
weight_vec = []

alpha = 0.2

while (cap.isOpened()):
    ret, frame = cap.read()
    if not ret:
        break

    #frame = cv2.resize(frame, (int(0.5 * frame.shape[1]), int(0.5 * frame.shape[0])), interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    if t == 0:
        template = gray[y0: y0 + h, x0: x0 + w]
        sample_set = sample_init(gray.shape, num_sample)
        cv2.imwrite(os.path.join('output', 'test1.png'), template)
    else:
        sample_set = algo.stochastic_universal_sampling(weight_vec)

    padded = np.pad(gray, ((h / 2, h / 2), (w / 2, w / 2)), 'edge')

    weight_vec = []
    weight_sum = 0
    best_mse = float('inf')
    best_template = np.zeros(template.shape)
    for i in range(0, num_sample):
        x = sample_set[i][0] + int(np.random.normal(0, delta_d))
        if x < 0:
            x = 0
        if x >= padded.shape[1] - w:
            x = padded.shape[1] - w - 1

        y = sample_set[i][1] + int(np.random.normal(0, delta_d))
        if y < 0:
            y = 0
        if y >= padded.shape[0] - h:
            y = padded.shape[0] - h - 1

        target = padded[y: y + h, x: x + w]
        p_dynamics = math.exp(-((x - center_x) ** 2 + (y - center_y) ** 2) / (2 * delta_d ** 2))
        mse = algo.mean_squared_error(template, target)
        if (mse < best_mse):
            best_mse = mse
            best_template = target

        p_mse = math.exp(-mse / (2 * delta_mse ** 2))

        weight = p_mse * p_dynamics
        weight_sum = weight_sum + weight
        weight_vec.append([x, y, weight])

    template = alpha * best_template.astype(float) + (1 - alpha) * template.astype(float)
    template = template.astype(np.uint8)
    cv2.imshow('temp', template)

    center_x = 0
    center_y = 0
    radius = 0

    for i in range(0, num_sample):
        weight_vec[i][2] = weight_vec[i][2] / weight_sum
        center_x += weight_vec[i][2] * weight_vec[i][0]
        center_y += weight_vec[i][2] * weight_vec[i][1]
        cv2.circle(frame, (int(weight_vec[i][0]), int(weight_vec[i][1])), 1, (0, 255, 0))

    for i in range(0, num_sample):
        dist = math.sqrt((weight_vec[i][0] - center_x) ** 2 + (weight_vec[i][0] - center_y) ** 2)
        radius += weight_vec[i][2] * dist

    cv2.circle(frame, (int(center_x), int(center_y)), 3, (0, 255, 0))
    cv2.circle(frame, (int(center_x), int(center_y)), int(radius), (255, 0, 0))
    cv2.rectangle(frame, (int(center_x - w / 2), int(center_y - h / 2)), (int(center_x + w / 2), int(center_y + h / 2)),
                  (0, 0, 255))

    cv2.imshow('frame', frame)

    '''
    if (t == 15):
        cv2.imwrite(os.path.join('output', 'ps6-2-b-1.png'), frame)
    if (t == 50):
        cv2.imwrite(os.path.join('output', 'ps6-2-b-2.png'), frame)
    if (t == 140):
        cv2.imwrite(os.path.join('output', 'ps6-2-b-3.png'), frame)
    '''




    t = t + 1
    if cv2.waitKey(25) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
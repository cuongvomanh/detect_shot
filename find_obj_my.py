#!/usr/bin/env python

'''
Feature-based image matching sample.

Note, that you will need the https://github.com/opencv/opencv_contrib repo for SIFT and SURF

USAGE
  find_obj.py [--feature=<sift|surf|orb|akaze|brisk>[-flann]] [ <image1> <image2> ]

  --feature  - Feature to use. Can be sift, surf, orb or brisk. Append '-flann'
               to feature name to use Flann-based matcher instead bruteforce.

  Press left mouse button on a feature point to see its matching point.
'''

# Python 2/3 compatibility
from __future__ import print_function

import numpy as np
import cv2 as cv
# relative module
import pickle
import video
from common import anorm, getsize

FLANN_INDEX_KDTREE = 1  # bug: flann enums are missing
FLANN_INDEX_LSH    = 6


def init_feature(name):
    chunks = name.split('-')
    if chunks[0] == 'sift':
        detector = cv.xfeatures2d.SIFT_create()
        norm = cv.NORM_L2
    elif chunks[0] == 'surf':
        detector = cv.xfeatures2d.SURF_create(800)
        norm = cv.NORM_L2
    elif chunks[0] == 'orb':
        detector = cv.ORB_create(400)
        norm = cv.NORM_HAMMING
    elif chunks[0] == 'akaze':
        detector = cv.AKAZE_create()
        norm = cv.NORM_HAMMING
    elif chunks[0] == 'brisk':
        detector = cv.BRISK_create()
        norm = cv.NORM_HAMMING
    else:
        return None, None
    if 'flann' in chunks:
        if norm == cv.NORM_L2:
            flann_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
        else:
            flann_params= dict(algorithm = FLANN_INDEX_LSH,
                               table_number = 6, # 12
                               key_size = 12,     # 20
                               multi_probe_level = 1) #2
        matcher = cv.FlannBasedMatcher(flann_params, {})  # bug : need to pass empty dict (#1329)
    else:
        matcher = cv.BFMatcher(norm)
    return detector, matcher


def filter_matches(kp1, kp2, matches, ratio = 0.75):
    mkp1, mkp2 = [], []
    for m in matches:
        if len(m) == 2 and m[0].distance < m[1].distance * ratio:
            m = m[0]
            mkp1.append( kp1[m.queryIdx] )
            mkp2.append( kp2[m.trainIdx] )
    p1 = np.float32([kp.pt for kp in mkp1])
    p2 = np.float32([kp.pt for kp in mkp2])
    kp_pairs = zip(mkp1, mkp2)
    return p1, p2, list(kp_pairs)

def explore_match(win, img1, img2, kp_pairs, status = None, H = None):
    h1, w1 = img1.shape[:2]
    h2, w2 = img2.shape[:2]
    vis = np.zeros((max(h1, h2), w1+w2), np.uint8)
    vis[:h1, :w1] = img1
    vis[:h2, w1:w1+w2] = img2
    vis = cv.cvtColor(vis, cv.COLOR_GRAY2BGR)

    if H is not None:
        corners = np.float32([[0, 0], [w1, 0], [w1, h1], [0, h1]])
        corners = np.int32( cv.perspectiveTransform(corners.reshape(1, -1, 2), H).reshape(-1, 2) + (w1, 0) )
        cv.polylines(vis, [corners], True, (255, 255, 255))

    if status is None:
        status = np.ones(len(kp_pairs), np.bool_)
    p1, p2 = [], []  # python 2 / python 3 change of zip unpacking
    for kpp in kp_pairs:
        p1.append(np.int32(kpp[0].pt))
        p2.append(np.int32(np.array(kpp[1].pt) + [w1, 0]))

    green = (0, 255, 0)
    red = (0, 0, 255)
    kp_color = (51, 103, 236)
    for (x1, y1), (x2, y2), inlier in zip(p1, p2, status):
        if inlier:
            col = green
            cv.circle(vis, (x1, y1), 2, col, -1)
            cv.circle(vis, (x2, y2), 2, col, -1)
        else:
            col = red
            r = 2
            thickness = 3
            cv.line(vis, (x1-r, y1-r), (x1+r, y1+r), col, thickness)
            cv.line(vis, (x1-r, y1+r), (x1+r, y1-r), col, thickness)
            cv.line(vis, (x2-r, y2-r), (x2+r, y2+r), col, thickness)
            cv.line(vis, (x2-r, y2+r), (x2+r, y2-r), col, thickness)
    vis0 = vis.copy()
    for (x1, y1), (x2, y2), inlier in zip(p1, p2, status):
        if inlier:
            cv.line(vis, (x1, y1), (x2, y2), green)

    # cv.imshow(win, vis)

    def onmouse(event, x, y, flags, param):
        cur_vis = vis
        if flags & cv.EVENT_FLAG_LBUTTON:
            cur_vis = vis0.copy()
            r = 8
            m = (anorm(np.array(p1) - (x, y)) < r) | (anorm(np.array(p2) - (x, y)) < r)
            idxs = np.where(m)[0]

            kp1s, kp2s = [], []
            for i in idxs:
                (x1, y1), (x2, y2) = p1[i], p2[i]
                col = (red, green)[status[i][0]]
                cv.line(cur_vis, (x1, y1), (x2, y2), col)
                kp1, kp2 = kp_pairs[i]
                kp1s.append(kp1)
                kp2s.append(kp2)
            cur_vis = cv.drawKeypoints(cur_vis, kp1s, None, flags=4, color=kp_color)
            cur_vis[:,w1:] = cv.drawKeypoints(cur_vis[:,w1:], kp2s, None, flags=4, color=kp_color)

        # cv.imshow(win, cur_vis)
    cv.setMouseCallback(win, onmouse)
    return vis


if __name__ == '__main__':
    print(__doc__)

    import sys, getopt
    opts, args = getopt.getopt(sys.argv[1:], '', ['feature='])
    opts = dict(opts)
    feature_name = opts.get('--feature', 'brisk')
    # try:
    #     fn1, fn2 = args
    # except:
    #     fn1 = '../data/box.png'
    #     fn2 = '../data/box_in_scene.png'
    try:
        fn = sys.argv[2]
        print('hell')
    except:
        fn = 0
    # img1 = cv.imread(fn1, 0)
    # img2 = cv.imread(fn2, 0)
    detector, matcher = init_feature(feature_name)

    # if img1 is None:
    #     print('Failed to load fn1:', fn1)
    #     sys.exit(1)

    # if img2 is None:
    #     print('Failed to load fn2:', fn2)
    #     sys.exit(1)

    if detector is None:
        print('unknown feature:', feature_name)
        sys.exit(1)

    print('using', feature_name)

    def match_and_draw(win, pre_img, next_img):
        print('matching...')
        raw_matches = matcher.knnMatch(desc1, trainDescriptors = desc2, k = 2) #2
        p1, p2, kp_pairs = filter_matches(kp1, kp2, raw_matches)
        if len(p1) >= 4:
            H, status = cv.findHomography(p1, p2, cv.RANSAC, 5.0)
            match_ratio = 1.0*np.sum(status)/len(status)
            print('%d / %d  inliers/matched = %f' % (np.sum(status), len(status), match_ratio))
        else:
            H, status = None, None
            match_ratio = 0.0
            print('%d matches found, not enough for homography estimation' % len(p1))

        _vis = explore_match(win, pre_img, next_img, kp_pairs, status, H)
        return match_ratio
    
    cap = video.create_capture(fn)
    flag, pre_img = cap.read()
    pre_img = cv.cvtColor(pre_img, cv.COLOR_BGR2GRAY)
    next_img = None
    match_ratios = []
    

    video = []
    video.append(pre_img)
    while True:
        flag, next_img = cap.read()
        
        # print(next_img.shape)
        if next_img is None:
            break
        video.append(next_img)
        next_img = cv.cvtColor(next_img, cv.COLOR_BGR2GRAY)
        kp1, desc1 = detector.detectAndCompute(pre_img, None)
        kp2, desc2 = detector.detectAndCompute(next_img, None)
        print('img1 - %d features, img2 - %d features' % (len(kp1), len(kp2)))

    

        match_ratio = match_and_draw('find_obj', pre_img, next_img)
        match_ratios.append(match_ratio)
        ch = cv.waitKey(5)
        if ch == 27:
            break
        
        pre_img = next_img
    cv.destroyAllWindows()
    K = 5
    UPPER_DELTA = 0.3
    LOWER_DELTA = 0.28
    sum = 0.0
    begin = False
    boundary_type = None
    cut_shot_boundarys = []
    gradual_shot_boundarys = []
    for i in xrange(len(match_ratios)):
        match_ratio = match_ratios[i]
        if i - K >= 0:
            sum -= match_ratios[i- K]
        sum += match_ratio
        if i < K -1:
            avarage = None
            continue
        else:
            avarage = 1.0*sum/K
        valuation = abs(avarage - match_ratio)
        print('i, valuation = ', i, valuation)
        if valuation >= UPPER_DELTA:
            if begin == False:
                cut_shot_boundarys.append([i, None])
                begin = True
                boundary_type = 'CUT'
                print('begin cut')
                
        elif valuation  >= LOWER_DELTA and valuation < UPPER_DELTA:
            if begin == False:
                gradual_shot_boundarys.append([i, None])
                begin = True
                boundary_type = 'GRADUAL'
                print('begin gradual')
            elif begin == True and boundary_type == 'CUT':
                cut_shot_boundarys[-1][1] = i
                begin = False
                print('end cut')
        else:
            if begin == True and boundary_type == 'GRADUAL':
                gradual_shot_boundarys[-1][1] = i
                begin = False
                print('end gradual')
            elif begin == True and boundary_type == 'CUT':
                cut_shot_boundarys[-1][1] = i
                begin = False
                print('end cut')
    # if gradual_shot_boundarys[-1][1] is None:
    #     gradual_shot_boundarys[-1][1] = len(video) - 1
    with open('video.pickle', 'wb') as handle:
        pickle.dump(video, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open('cut_shot_boundarys.pickle', 'wb') as handle:
        pickle.dump(cut_shot_boundarys, handle, protocol=pickle.HIGHEST_PROTOCOL)
    with open('gradual_shot_boundarys.pickle', 'wb') as handle:
        pickle.dump(gradual_shot_boundarys, handle, protocol=pickle.HIGHEST_PROTOCOL)
    # output = list(video)
    # for boundary in cut_shot_boundarys:
    #     left, right = boundary
    #     left_frame = output[left]
    #     left_frame[:] = [0, 0, 255]
        
    #     right_frame = output[right]
    #     right_frame[:] = [0, 0, 255]
    # for boundary in gradual_shot_boundarys:
    #     left, right = boundary
    #     left_frame = output[left]
    #     left_frame[:] = [0, 0, 255]
    #     right_frame = output[right]
    #     right_frame[:] = [0, 0, 255]
    # cv.destroyAllWindows()
    # with open('output.pickle', 'wb') as handle:
    #     pickle.dump(output, handle, protocol=pickle.HIGHEST_PROTOCOL)

                
        

        
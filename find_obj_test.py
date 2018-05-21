import cv2 as cv
import pickle
with open('video.pickle', 'rb') as handle:
    video = pickle.load(handle)
with open('cut_shot_boundarys.pickle', 'rb') as handle:
    cut_shot_boundarys = pickle.load(handle)
with open('cut_shot_boundarys.pickle', 'rb') as handle:
    cut_shot_boundarys = pickle.load(handle)
with open('gradual_shot_boundarys.pickle', 'rb') as handle:
    gradual_shot_boundarys = pickle.load(handle)
# with open('output.pickle', 'rb') as handle:
#     output = pickle.load(handle)
output = list(video)
print(cut_shot_boundarys)
print(gradual_shot_boundarys)
for boundary in cut_shot_boundarys:
    left, right = boundary
    left_frame = output[left]
    left_frame[:] = [255, 0, 255]
    
    right_frame = output[right]
    right_frame[:] = [0, 255, 255]
for boundary in gradual_shot_boundarys:
    left, right = boundary
    left_frame = output[left]
    left_frame[:] = [255, 0, 0]
    right_frame = output[right]
    right_frame[:] = [0, 0, 255]
# for frame in video:
#     cv.imshow('output',frame)
cv.destroyAllWindows()
with open('output.pickle', 'wb') as handle:
    pickle.dump(output, handle, protocol=pickle.HIGHEST_PROTOCOL)
for i, frame in zip(xrange(len(video)), video):
    print(i)
    cv.imshow('output',frame)
    cv.waitKey(0)
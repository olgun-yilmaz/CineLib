import cv2

path = "verification_background.jpg"

img = cv2.imread(path)
img = cv2.resize(img,(600,300))
cv2.imwrite(path,img)
"""r_img = cv2.resize(img, (1600,900))
cv2.imwrite(path, r_img)"""

import numpy as np
import cv2
from PIL import Image
import matplotlib.pyplot as plt
import scipy.misc 
import copy
import time


def crop(im, bbox):
	'''
		Crop the image without any warping
		Input Arguments
			im  : image
			bbox: x1, y1, x2, y2 format 
	'''
	im_size = im.shape
	bbox    = bbox.astype(int)
	w       = bbox[2] - bbox[0]
	h       = bbox[3] - bbox[1]
	assert w <= im_size[0] and h <= im_size[1], 'bbox is bigger than image'
  im_crp  = im[bbox[1]:bbox[3] + 1,  bbox[0]:bbox[2]+1, :]
  return im_crp

  
def resize(im, sz):
	'''
		Resize the iamge
		Input Arguments
			im  : image
			sz  : tuple (y,x)  
	'''
	sz   = sz.astype(int)
  img  = scipy.misc.imresize(im, (sz[0],sz[1]), 'bilinear')
  return img


def crop_with_warp(cfg, im, bbox):
	'''
	Input Arguments
		im  : 3d array
		bbox: 1x4 array

	cfg.CROP_SIZE: Image size that the n/w takes as input
	bbox         : The desired region to be cropped

	Warp the image based on cfg.CROP_SIZE/bbox_width,
													cfg.CROP_SIZE/bbox_height
	It is possible that the bbox coordinates are outside
	the image size, so we need to account for that.
	Solution:
		1. Find the clipped bbox coordinates so that new bbox
			 fits inside the image.
		2. Scale the bbox by warp factor
		3. Fill in the rest of the pixels by mean values
	'''  

	#Image data
	img_ori = im
	imsize  = im.shape
	#bbox coordinates
	x1 = bbox[0]
	y1 = bbox[1]
	x2 = bbox[2]
	y2 = bbox[3]
	#print("input bbox x1:",x1,"x2:",x2,"y1:",y1,"y2:",y2)

	unclipped_height = y2-y1+1
	unclipped_width  = x2-x1+1
	pad_x1 = max(0, -x1)
	pad_y1 = max(0, -y1)
	pad_x2 = max(0, x2 - imsize[1] + 1)
	pad_y2 = max(0, y2 - imsize[0] + 1)

	#Clip the bbox dimensions so that they are within
	#the image
	x1 = x1 + pad_x1
	x2 = x2 - pad_x2
	y1 = y1 + pad_y1
	y2 = y2 - pad_y2
	#print("RIGHT BEFORE ROI x1:",x1,"x2:",x2,"y1:",y1,"y2:",y2)
	assert (x1>-1)
	assert (y1>-1)
	assert (x2<imsize[1])
	assert (y2<imsize[0])

	clipped_height = y2-y1+1
	clipped_width  = x2-x1+1
	# scale factors that would be used to warp the unclipped
	# expanded region
	scale_x = cfg.CROP_SIZE/unclipped_width
	scale_y = cfg.CROP_SIZE/unclipped_height
	#print("scale_x:",scale_x,"scale_y",scale_y)
	#exit(1)
	# // size to warp the clipped expanded region to
	cv_crop_size_width  = round(clipped_width*scale_x,0)
	cv_crop_size_height = round(clipped_height*scale_y,0)
	pad_x1 = round(pad_x1*scale_x,0)
	pad_x2 = round(pad_x2*scale_x,0)
	pad_y1 = round(pad_y1*scale_y,0)
	pad_y2 = round(pad_y2*scale_y,0)
	#print("AFTER ROUNDING padx1:",pad_x1,"padx2:",pad_x2,"pady1:",pad_y1,"pady2:",pad_y2)
	pad_h = pad_y1
	pad_w = pad_x1
	# ensure that the warped, clipped region plus the padding fits in the
	# cfg.CROP_SIZE x cfg.CROP_SIZE image (it might not due to rounding)
	if (pad_h + cv_crop_size_height > cfg.CROP_SIZE):
			cv_crop_size_height = cfg.CROP_SIZE - pad_h
			
	if (pad_w + cv_crop_size_width > cfg.CROP_SIZE):
			cv_crop_size_width = cfg.CROP_SIZE - pad_w

	#Clipped bbox coords
	bbox= np.array([x1,y1,x2,y2])
	#Crop the bboc 
	cv_cropped_img = im[int(bbox[1]):int(bbox[3]+1), int(bbox[0]):int(bbox[2]+1),:]
	cv_cropped_img_resized = scipy.misc.imresize(cv_cropped_img, 
													 (int(cv_crop_size_height),int(cv_crop_size_width),3), 
													 'bilinear')
	#Prepare the image
	img = np.zeros((cfg.CROP_SIZE,cfg.CROP_SIZE,3))
	img = img + cfg.PIXEL_MEANS
	img[int(pad_h):int(pad_h+cv_cropped_img_resized.shape[0]),
			int(pad_w):int(pad_w+cv_cropped_img_resized.shape[1]),:] = cv_cropped_img_resized
	img = img - cfg.PIXEL_MEANS

	#Visualize the output 
	if 0:
		imgshow=copy.deepcopy(img)
		imgshow=np.round(imgshow+cfg.PIXEL_MEANS);
		print(imgshow.shape)
		plt.imshow(imgshow)
		plt.show()
		vis.save_image_from_array(imgshow,"./crop.jpg")
		print(imgshow)
	return img

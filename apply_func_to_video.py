from __future__ import print_function
from __future__ import division
import os, time
import numpy as np
import cv2


'''
changlog:
- updated to use opencv 3.0 and python3

apply_func_to_video.py

work in progress

check main() for example usage
'''

class VideoObject:
    def __init__(self, filename, out_name='out.avi', encoding='XVID'):
        '''Get properties from input file and prepares opencv object
        
           filename     path to input video file
           out_name     path to output video file
           encoding     4 character string for opencv FOURCC
           
           Usage:
           v = VideoObject('filename.avi')
           f.write_video(function,*args)
                                                         
           OpenCV 3.0 python bindings changed from previous versions.  To get
           video properties with python, you must now use an integer code.
           Relevant for cap.get(<integer>):
               1: CV_CAP_PROP_POS_FRAMES - 0-based index of the frame to be 
                                           decoded/captured next
               3: CV_CAP_PROP_FRAME_WIDTH
               4: CV_CAP_PROP_FRAME_HEIGHT
               5: CV_CAP_PROP_FPS
               6: CV_CAP_PROP_FOURCC
               7: CV_CAP_PROP_FRAME_COUNT
               
           more propid's to be found at 
           http://docs.opencv.org/modules/highgui/doc/reading_and_writing_images_and_video.html
           The order they are listed in is the integer order w/ 0-based index
                        
        '''
        self.filename = filename
        self.out_name = out_name
    
        self.fourcc = cv2.VideoWriter_fourcc(*encoding)
        self.cap = cv2.VideoCapture(self.filename)
        #print(self.cap.CV_CAP_PROP_FPS)
        try:
            self.fps = int(round(self.cap.get(5)))
        except Exception as e:
            print('Could not identify framerate of video.  Program may encounter errors')
            self.fps = 24 
        self.width = int(round(self.cap.get(3)))
        self.height = int(round(self.cap.get(4)))
        self.total_frames = self.cap.get(7)
        self.out_writer = cv2.VideoWriter(
                              filename = self.out_name, 
                              fourcc = self.fourcc, 
                              fps = self.fps, 
                              frameSize = (self.width, self.height) )
        

    def apply_function_to_vid(self, function, write_changes=True, 
               preserve_audio=False, view_while_processing=False):
        ''' Apply a function to each frame in the video.  This is the main function
            to process the video and write the output video file
        
           function        should accept 3d numpy array and return 2d/3d numpy array
                           of same shape in lowest 2 dimensions (i.e. width/height)
           write_changes   True will write to output file, False would be for a dry 
                           run (likely to be used with view_while_processing)
           preserve_audio  If audio present in input file, set this to True if you
                           want to retain the audio in the new video
           view_while_processing   When True,  two screens showing original frame
                                   and new frame will appear
        '''
        while self.cap.isOpened():
            next_frame_exists, frame = self.cap.read()
            if next_frame_exists:
                new_frame = function(frame)

                if write_changes: self.out_writer.write(new_frame)

                if view_while_processing: 
                    cv2.imshow('new',new_frame)
                    cv2.imshow('original',frame)

                #Track progress
                print ('\r%.2f %s complete' %\
                      (self.cap.get(1) / self.total_frames * 100, '%'), end='') 

                #Need this for playback to work
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            else:
                print('Finished processing video.')
                self.cap.release()
                
        if preserve_audio and write_changes:
            print('Processing audio ...')
            self.process_audio()#FIX WHEN FIXED BELOW, WITH ADDED ARGS

    def process_audio(self): #change to create tempdir?
        cmds = []
        #Strip audio from original file
        cmds.append('ffmpeg -i %s -vn -ac 2 -ar 44100 -ab 320k -f mp3 tmp_output.mp3' % self.filename)
        #Attach audio to transformed video
        cmds.append('ffmpeg -i %s -i tmp_output.mp3 -map 0 -map 1 -codec copy -shortest tmp_out.avi' % self.out_name)
        for cmd in cmds: os.system(cmd)        
        #Cleanup
        os.remove('tmp_output.mp3')
        os.rename('tmp_out.avi',self.out_name)

def normalize(arr, max_=255.0, dtype=np.uint8, nan_check=False):
    '''By default will normalize array to 0-255 as np.uint8'''
    if nan_check:
        arr = np.nan_to_num(arr) #Slows it down, but safer to do this
    arr *= np.absolute( (max_/arr.max()) ) #Normalize to 0-255 after ft
    return arr.astype(dtype) #Dtype needed by opencv

'''
The following two functions are helpers. The video you work with will most 
likely be in RGB color space, which is a 3d numpy array.  You may want to
do work on the video with a custom function using a 2d array, as that code
is generally cleaner (though you will lose color information)

To be implemented...
'''
def to_2d_from_3d(arr): #do checks on input
    pass
    
def to_3d_from_2d(arr):
    pass

def main():
    video = VideoObject('test.mpg')
    print(video.__dict__)
    
    def transform_function(arr):
        fx,fy,fz = arr.shape
        frame = np.reshape(arr,(fx,fy*fz))
        ftFrame = np.real(np.fft.fft2(frame)) 
        frame = np.reshape(ftFrame,(fx,fy,fz))
        return normalize(np.fft.fftshift(frame))
    
    video.apply_function_to_vid(transform_function, 
                                write_changes=True,
                                preserve_audio=True, 
                                view_while_processing=False)
                                
    print('Finished')
    # Add helper function to assert input properties == output properties


if __name__ == '__main__':
    main()

from __future__ import print_function
from __future__ import division
import os
import time
import numpy as np
import cv2

'''
apply_func_to_video.py

requires opencv 2.6+ (only tested on 3 so far, with python3.4)
requires ffmpeg to be in path 
numpy==1.8.2 used for testing 
ensure you have write access (or run as admin) if you want to write output.

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
           video properties with py3, you must now use an integer code.
           Relevant for cap.get(<integer>):
               1: CV_CAP_PROP_POS_FRAMES - 0-based index of the frame to be 
                                           decoded/captured next
               3: CV_CAP_PROP_FRAME_WIDTH
               4: CV_CAP_PROP_FRAME_HEIGHT
               5: CV_CAP_PROP_FPS
               6: CV_CAP_PROP_FOURCC
               7: CV_CAP_PROP_FRAME_COUNT
               
        more propid's to be found at 
        http://docs.opencv.org/modules/highgui/doc/
            reading_and_writing_images_and_video.html
        The order they are listed in is the integer order w/ 0-based index
                        
        '''
        self.filename = filename
        self.out_name = out_name
        # Get relevant properties of input video   
        self.fourcc = cv2.VideoWriter_fourcc(*encoding)
        self.cap = cv2.VideoCapture(self.filename)
        try:
            self.fps = self.cap.get(5)
        except Exception as e:
            print('Could not identify framerate of video.'
                  ' Program may encounter errors')
            self.fps = 24 
        self.width = int(self.cap.get(3))
        self.height = int(self.cap.get(4))
        self.total_frames = self.cap.get(7)
        # Initialize OpenCV VideoWriter
        self.out_writer = cv2.VideoWriter(
                filename = self.out_name, 
                fourcc = self.fourcc, 
                fps = self.fps, 
                frameSize = (self.width, self.height)
                )
        

    def apply_function_to_vid(self, function, write_changes=True, 
               preserve_audio=False, view_while_processing=False):
        ''' Apply a function to each frame in the video.  This is the main 
            function to process the video and write the output video file
        
           function        should accept 3d numpy array and return 2d/3d numpy
                           array of same shape in lowest 2 dimensions 
                           (i.e. width/height)
           write_changes   True will write to output file, False would be for
                           a dry run 
                           (likely to be used with view_while_processing)
           preserve_audio  If audio present in input file, set this to True if
                           you want to retain the audio in the new video
           view_while_processing   When True, two screens showing original 
                                   frame and new frame will appear. No audio.
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
                print ('\r%d%s complete' %\
                      (self.cap.get(1) / self.total_frames * 100, '%'), end='') 

                #Need this for playback to work
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            else:
                print('\nFinished processing video.')
                self.cap.release()
                
        if preserve_audio and write_changes:
            print('Processing audio ...')
            self.process_audio()

    def process_audio(self):
        ''' to do: fix to allow for different formats '''
        tmp_mp3_out = 'tmp_' + str(time.time()) + '.mp3'
        tmp_vid_out = tmp_mp3_out[:-4] + '.avi'
        #Strip audio from original file
        os.system('ffmpeg -i %s -vn -ac 2 -ar 44100 -ab 320k '
                  '-f mp3 %s' % (self.filename, tmp_mp3_out))
        #Attach audio to transformed video
        os.system('ffmpeg -i %s -i %s -map 0 -map 1 -codec copy '
                  '-shortest %s' % (tmp_mp3_out, self.out_name, tmp_vid_out))   
        #Clean up
        os.remove(tmp_mp3_out)
        os.rename(tmp_vid_out, self.out_name)


######################### Helper functions ###################################

def normalize(arr, max_=255.0, dtype=np.uint8, nan_check=False):
    '''By default will normalize array to 0-255 as np.uint8'''
    if nan_check:
        arr = np.nan_to_num(arr) #Slows it down, but safer to do this
    arr = np.asarray(arr)
    arr *= np.absolute( (max_/arr.max()) ) #Normalize to 0-255 after ft
    return arr.astype(dtype) #Dtype needed by opencv

def extract_rgb(arr3d): 
    '''Extracts r, g, b channels from one 3D array --> three 2D arrays'''
    try:
        arr3d = np.asarray(arr3d)
        if arr3d.ndim < 3:
            raise ValueError('must pass 3d sequence to extract_rgb')
    except Exception as e:
        print(e)
        return None, None, None
    r, g, b = arr3d[:,:,0], arr3d[:,:,1], arr3d[:,:,2]
    return r, g, b
    
def combine_rgb(r, g=None, b=None, dtype=np.uint8):
    '''Combines separate color channels of same shape to 3D array
       To do r,g,b as grayscale, pass the grayscale img as the r channel.
    '''
    if g is None or b is None:
        g = r
        b = r
    try:
        r, g, b = np.asarray(r), np.asarray(g), np.asarray(b)
        if r.shape != b.shape or b.shape != g.shape:
            raise ValueError('combine_rgb inputs must be of same shape')
        elif r.ndim != 2:
            raise ValueError('combine_rgb only accepts 2d arrays')
    except AttributeError as e:
        print(e)
        return None
    except Exception as e:
        print(e)
        return None
    result = np.zeros((r.shape[0], r.shape[1], 3))
    result[:,:,0], result[:,:,1], result[:,:,2] = r, g, b
    return result.astype(dtype)

##############################################################################

def main():
    # Initialize our VideoObject with the path to the input file
    video = VideoObject('test.mpg')
    
    # Let's see the info we extracted from the video
    print('\n', video.__dict__)
    
    # Make some arbitrary function to apply to the video
    def transform_function(arr):
        # Separate image channels
        r, g, b = extract_rgb(arr)
        # Perform 2D-FFT (just using this as an example)
        r = normalize(np.fft.fftshift(np.real(np.fft.fft2(r))))
        g = normalize(np.fft.fftshift(np.real(np.fft.fft2(g))))
        b = normalize(np.fft.fftshift(np.real(np.fft.fft2(b))))  
        # Combine channels   
        return combine_rgb(r, g, b)
    
    # Process the video with the function we defined
    video.apply_function_to_vid(
            function=transform_function, 
            write_changes=True,
            preserve_audio=True, 
            view_while_processing=True
            )
                                
    print('\nFinished successfully\n')
    # Add test to assert input properties == output properties


if __name__ == '__main__':
    main()

from __future__ import print_function
from __future__ import division
import numpy as np
import cv2
import cv2.cv as cv
import os, time


'''
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
        '''
        self.filename = filename
        self.out_name = out_name
    
        self.fourcc = cv.CV_FOURCC(*encoding)
        self.cap = cv2.VideoCapture(self.filename)
        try:
            self.fps = int(round(self.cap.get(cv.CV_CAP_PROP_FPS)))
        except Exception as e:
            print('Could not identify framerate of video.  Program may encounter errors')
            self.fps = 24
            
        self.width = int(round(self.cap.get(cv.CV_CAP_PROP_FRAME_WIDTH)))
        self.height = int(round(self.cap.get(cv.CV_CAP_PROP_FRAME_HEIGHT)))
        self.total_frames = self.cap.get(cv.CV_CAP_PROP_FRAME_COUNT)
        self.out_writer = cv2.VideoWriter(self.out_name, self.fourcc, self.fps, (self.width, self.height))
        

    def apply_function_to_vid(self, function, write_changes=True, preserve_audio=False, view_while_processing=False):
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
                    cv2.imshow('orig',frame)

                #Track progress
                print ("%.2f" % (self.cap.get(cv.CV_CAP_PROP_POS_FRAMES) / self.total_frames * 100)), "% complete \r",

                #Need this for playback to work
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            else:
                print('Finished processing video.')
                self.cap.release()
                
        if preserve_audio and write_changes:
            print('Processing audio ...')
            self.process_audio()#FIX WHEN FIXED BELOW, WITH ADDED ARGS

    def process_audio(self):
        pass #######FIX THIS FUNCTION
        #Strip audio from original file
        cmd = "ffmpeg -i %s -vn -ac 2 -ar 44100 -ab 320k -f mp3 output.mp3" % filename
        os.system(cmd)

        #Attach audio to transformed video
        cmd = "ffmpeg -i %s -i output.mp3 -map 0 -map 1 -codec copy -shortest final.avi" % outName
        os.system(cmd)

        #Delete temporary files
        cmd = "rm output.mp3 %s" % outName
        os.system(cmd)


def main():
    video = VideoObject('transformed.avi')
    print(video.__dict__)
    
    def frame_printer(arr):
        print(arr)
        return(arr*2)
    
    video.apply_function_to_vid(frame_printer, write_changes=False, view_while_processing=True)


if __name__ == '__main__':
    main()

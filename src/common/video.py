import os

def renderVideo(folder, fps):
  os.system(f'ffmpeg -framerate {fps} -pattern_type glob -i "{folder}/*.png" -c:v libx264 -pix_fmt yuv420p -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2" {folder}.mp4')

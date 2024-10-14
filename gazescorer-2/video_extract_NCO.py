import pandas as pd
import re
import os
import subprocess

### CUSTOM FUNCTIONS ###

# Reads in raw files from various versions of Gorilla tasks. removes merged uploads folders
def read_files(target, directory):
    dir_list = os.listdir(directory)
    dir_list.remove('raw_uploads')
    dir_list.remove('processed_uploads')
    process_files = []
    
    for idir in dir_list:
        file_list = os.listdir(os.path.join(directory, idir))
        for ifile in file_list:
            if target in ifile:
                process_files.append(os.path.join(directory, idir, ifile))
    
    data_frames = [pd.read_csv(file) for file in process_files]
    data_frame = pd.concat(data_frames, ignore_index=True)
    
    return data_frame

# function used to get meta data from the video
def get_meta_data(vfname):

    frames = subprocess.check_output(
        f"ffprobe -hide_banner -loglevel error {vfname} -show_frames -show_entries frame=pkt_pts_time -of csv=p=0",
        shell=True,
    )
        
    tstamps = frames.decode().splitlines()
    duration = float(tstamps[-1])
    frame_count = len(tstamps)

    fps = frame_count / duration
    
    meta = {
        "fps": fps,
        "duration": duration,
        "frame_count": frame_count,
        "time_stamps": tstamps
    }

    return meta

### EXTRACT TRIAL DATA AND VIDEO PATHS ###

# Data path of the raw videos
data_path = 'data/'

# Load the data
numComp_fname = 'task-wk8y'
numComp_raw = read_files(numComp_fname, data_path)

# Define delays
numComp_vid_delay = 1600
numComp_delay = numComp_vid_delay + 750

# Data manipulation - select only trials and relevant zone types
numComp_df_raw = numComp_raw[
    (numComp_raw['Screen Name'] == 'trial') &
    ((numComp_raw['Zone Type'] == 'response_keyboard') | (numComp_raw['Zone Type'] == 'timelimit_screen'))
]

# makes copy of raw df to work on
numComp_df = numComp_df_raw.copy()

# neaten up data - rename image files names to usable format, calculate accurate RT and Video RT, setup trial_n, 
# calcualte meta info, and replace Resp and ANS to usable formats
numComp_df[['LeftImage', 'RightImage']] = numComp_df[['LeftImage', 'RightImage']].replace({'00': '', '.png': ''}, regex=True)
numComp_df['RT'] = numComp_df['Reaction Time'] - numComp_delay
numComp_df['RT_vid'] = numComp_df['Reaction Time'] - numComp_vid_delay
numComp_df['Trial Number'] = pd.to_numeric(numComp_df['Trial Number'])
numComp_df['meta_ratio'] = numComp_df.apply(lambda row: min(float(row['LeftImage']), float(row['RightImage'])) / max(float(row['LeftImage']), float(row['RightImage'])), axis=1)
numComp_df['meta_distance'] = abs(numComp_df['LeftImage'].astype(float) - numComp_df['RightImage'].astype(float))
numComp_df[['Response', 'ANSWER']] = numComp_df[['Response', 'ANSWER']].replace({'keyq_': '', 'keyp_': ''}, regex=True)

# Finds relvant video files
numComp_vid_raw = numComp_raw[
    (numComp_raw['Zone Type'] == 'video_recording') &
    (numComp_raw['Response'].str.contains('webm')) &
    (numComp_raw['Response'].str.contains('https') == False)
][['Participant Public ID', 'Trial Number', 'Response']].rename(columns={'Response': 'vid_fname', 'Participant Public ID': 'PID', 'Trial Number': 'trial'})

#Makes copy of df to work from
numComp_vid = numComp_vid_raw.copy()

# renames files 
numComp_df = numComp_df[
    ['Experiment Version', 'Participant Public ID', 'Trial Number', 'Response', 'ANSWER', 'Correct', 'Reaction Time', 'RT', 'RT_vid', 'LeftImage', 'RightImage', 'meta_ratio', 'meta_distance']
].rename(columns={'Experiment Version': 'exp_version', 'Participant Public ID': 'PID', 'Trial Number': 'trial', 'Reaction Time': 'raw_RT'})

#find relevant files, convert to same types and merge
numComp_df.loc[:, 'trial'] = numComp_df['trial'].astype(str)
numComp_vid.loc[:, 'trial'] = numComp_vid['trial'].astype(str)
numComp_df = pd.merge(numComp_df, numComp_vid, how='left', on=['PID', 'trial'])

# Sort values by PID then trial then rest index
numComp_df = numComp_df.sort_values(by=['PID', 'trial'])
numComp_df = numComp_df.reset_index(drop='True')


### PROCESS VIDEOS ###


skip_processed = False
    
# set input and output video paths
video_path = 'data/raw_uploads'
processed_path = 'data/processed_uploads'


# Setup participant ID's that should be skipped
exclude_id = []
error_code = []
process_file_list = []

verbose = True

# Loop through each trial row
for i, row in numComp_df.iterrows():

    # Print current file name
    if verbose: print(f'{video_path}/{row["vid_fname"]}')

    # Check if the video was recorded and whether path is valid and file does exist, appends relevant error code based on output
    if pd.isna(row['vid_fname']):
        if verbose: print(f'No video recorded - PID: {row["PID"]}, Trial: {row["trial"]}')
        error_code.append('No video recorded')
        process_file_list.append('NaN')
        continue
    elif os.path.exists(f'{video_path}/{row["vid_fname"]}'):
        vid_fname = f'{video_path}/{row["vid_fname"]}'
        out_vid_fname = f'{processed_path}/{row["vid_fname"]}'
    else:
        if verbose: print(f'No video file found - PID: {row["PID"]}, Trial: {row["trial"]}')
        error_code.append(1)
        continue

     # set path for the output file
    out_fname =  f'{os.path.splitext(row["vid_fname"])[0]}_processed.mp4'
    out_path = f'{os.path.splitext(out_vid_fname)[0]}_processed.mp4'

    # Checks if processed files already exists and whether to skip them
    if os.path.exists(out_path) and skip_processed:
        if verbose: print(f'file already exists and will be skipped - PID: {row["PID"]}, Trial: {row["trial"]}')
        error_code.append(0)
        process_file_list.append(out_fname)
        continue
    else:
        
       
        
        # Get length of video in seconds
        vid_length = row['RT_vid']/1000

        #get meta data from video
        # meta = get_meta_data(vid_fname)
        try:
            meta = get_meta_data(vid_fname)
        except:
            if verbose: print(f'Could not probe video, possibly corrupted - PID: {row["PID"]}, Trial: {row["trial"]}')
            error_code.append('Could not probe video')
            process_file_list.append('NaN')
            continue

        # Works out relevant time information based on the meta data
        stop_time = meta['duration']
        start_time = stop_time - vid_length

        

        # Checks for possible errors in the timing for the videos
        if start_time < 0:
            error_code.append('start time < 0')
            process_file_list.append('NaN')
            if verbose: (f'Start time ({start_time}) was less than 0 - PID: {row["PID"]}, Trial: {row["trial"]}')
            continue
        elif stop_time > meta['duration']:
            error_code.append('stop time beyond duration')
            process_file_list.append('NaN')
            if verbose:(f'Stop top ({stop_time}) was beyond the length of the video file ({meta["duration"]} - PID: {row["PID"]}, Trial: {row["trial"]}')
            continue
        
       

        # Makes the video processing command
        command_video = f"ffmpeg -fflags +genpts -ss {start_time} -i {vid_fname} -r {meta['fps']} -qscale 0 -y {out_path}"

        # Attempts to run the video processing command. Appends error code if not possible
        try:
            if verbose: print(f'Cutting video betweeen {start_time} and {stop_time}  - PID: {row["PID"]}, Trial: {row["trial"]}')
            subprocess.run(command_video, shell=True, check=True)
            error_code.append(0)
            process_file_list.append(out_fname)
            continue
        except:
            if verbose: print(f'Could not run ffmpeg command, possibly corrupted - PID: {row["PID"]}, Trial: {row["trial"]}')
            error_code.append('could not run ffmpeg')
            process_file_list.append('NaN')
            continue


additional_df = pd.DataFrame({'error_codes': error_code, 'processed_fname': process_file_list})

numComp_df_output = pd.concat([numComp_df, additional_df], axis=1)

numComp_df_output.to_csv('number_comparison_processed_output.csv')
import os.path
import time

import cv2
import pandas
from l2cs import Pipeline, render
import torch
import pathlib

"""
This script uses the L2CS model to predict gaze direction in video files from the Number Comparison Online dataset.
Each video is processed frame by frame, the gaze direction is predicted, and results are saved to a CSV file.
"""

# Configuration options
save_videos = True  # Option to save the processed video output
max_videos = 0  # Limit the number of videos to process (0 means no limit)

# Define the input and output directories
input_dir = os.path.join(r"./video_input/Number_comparison_online_new")
output_dir = os.path.join(r".output/L2CS_NCO_new")

# Initialize the gaze detection pipeline using the L2CS model
gaze_pipeline = Pipeline(
    weights=pathlib.Path('models/Gaze360/L2CSNet_gaze360.pkl'),  # Load pretrained model weights
    arch='ResNet50',  # Use ResNet50 architecture
    device=torch.device(0)  # Use GPU (or specify CPU if needed)
)

start_time = time.time()  # Start the timer to measure processing time

# DataFrame to store the results (video, frame, face count, pitch, yaw)
results = pandas.DataFrame(columns=["video", "frame", "face_count", "pitch", "yaw"])

# Iterate over each video file in the input directory
video_file_count = 0
for video_file in os.listdir(input_dir):
    # Limit the number of processed videos based on max_videos setting
    if 0 < max_videos <= video_file_count:
        break
    video_file_count += 1
    video_file_time = time.time()  # Track processing time per video

    # Load the video and extract frames
    video = cv2.VideoCapture(os.path.join(input_dir, video_file))
    frame_number = 0
    frames = []  # List to store frames if saving the video output
    errors = []  # List to track errors per video
    while video.isOpened():
        face_count_warning = True

        ret, frame = video.read()  # Read each frame
        if not ret:
            break

        # Process each frame through the gaze pipeline to get predictions
        try:
            frame_results = gaze_pipeline.step(frame)  # Predict gaze direction for the current frame
            yaw = frame_results.yaw  # Get yaw (horizontal) angles
            pitch = frame_results.pitch  # Get pitch (vertical) angles

            # Handle multiple faces in a frame and log warnings if necessary
            face_count = 1
            if len(yaw) != 1 or len(pitch) != 1:
                face_count = max(len(yaw), len(pitch))
                if face_count_warning:
                    print(f"WARNING: Found {face_count} faces in frame {frame_number} of {video_file}. Using the first entry.")
                    face_count_warning = False

            # Store the first detected face's yaw and pitch values
            yaw = yaw[0]
            pitch = pitch[0]

            # Append the result to the DataFrame
            results.loc[len(results)] = [
                video_file,
                frame_number,
                face_count,
                float(pitch),
                float(yaw),
            ]

            # If saving videos, render the frame with the gaze predictions
            if save_videos:
                frames.append(render(frame, frame_results))
        except Exception as e:
            errors.append(e)  # Log any errors encountered during frame processing
        frame_number += 1
    video.release()  # Release the video capture after processing

    # Save the processed video if required
    if save_videos and len(frames) > 0:
        os.makedirs(os.path.join(output_dir, "videos"), exist_ok=True)  # Ensure output directory exists
        video_out = cv2.VideoWriter(
            os.path.join(output_dir, "videos", f"{video_file}.mp4"),  # Save as .mp4
            0,  # Codec specification (default)
            30,  # Frame rate
            (frames[0].shape[1], frames[0].shape[0])  # Frame size (width, height)
        )
        for frame in frames:
            video_out.write(frame)  # Write each frame to the output video
        video_out.release()
    elif save_videos:
        print(f"WARNING: No frames found for {video_file}")  # Warn if no frames were processed

    # Log errors or successful processing for each video
    if len(errors):
        print(f"Processed {video_file} in {round(time.time() - video_file_time, 2)}s with {len(errors)} errors: {errors}")
    else:
        print(f"Processed {video_file} in {round(time.time() - video_file_time, 2)}s")

# Save the results to a CSV file
fname = os.path.join(output_dir, "results.csv")
os.makedirs(os.path.dirname(fname), exist_ok=True)  # Ensure output directory exists
results.to_csv(fname, index=False)  # Save results without the index

# Print total processing time
print(f"Finished processing. Time elapsed: {round(time.time() - start_time, 2)}s")

pass

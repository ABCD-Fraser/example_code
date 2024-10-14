
# example_code

This repo contains several code examples from various projects during my Postdoc positions. 

### EX2_data_extract

This folder contains a data extraction script for behavioural data collected using a package called PsychoPy (https://www.psychopy.org/). The folder includes an R script that reads in raw behavioural outputs, filters the relevant rows and columns for the two phases (Check and Test phases), and then outputs a file to be used for analysis.

There are 5 anonymised sample files that can be used to test the code.

### EX1_EX2_data_analysis

This folder contains three R Markdown files. The files provide analyses of different data across two experiments: 
- `EX1_EEG_behavioural.Rmd` uses EEG data extracted from Experiment 1 using proprietary EEG processing software (Brain Vision Analyzer; https://www.brainproducts.com/solutions/analyzer/) and runs analyses comparing amplitudes and latency of participants' brainwaves.
- `EX1_behavioural.Rmd` uses extracted behavioural data from Experiment 1 to run several analyses of the two phases. This includes non-parametric tests, Analysis of Variance (GLM), and Generalised Linear Mixed Models.
- `EX2_behavioural.Rmd` uses extracted data from Experiment 2 to run similar analyses as in Experiment 1.

### EX3_ECG_samples

This folder contains a Jupyter notebook with code to identify timestamps for sub-sampling periods of ECG data for use with heart rate variability (HRV) analysis software (Kubios; https://www.kubios.com/). Each cell processes a separate sub-task. The first half processes children's data, and the second half processes the adults' data.

### Gazescorer-2

This folder contains the second iteration of the webcam project. It uses an open-source, appearance-based gaze estimation package (L2CS; https://github.com/Ahmednull/L2CS-Net) rather than our custom package. The folder includes two Python scripts for processing a number comparison task collected with children over the internet during the COVID lockdowns:
- `video_extract_NCO.py` processes and trims videos to the correct length for further processing.
- `L2CS_run_NCO.py` runs the processed videos through the L2CS model to identify gaze orientation estimates, which are then output as a .csv file.

### IMBES_EEG_processing

This folder contains two Jupyter notebooks for processing, analysing, and visualising the EEG data from Experiment 1 using open-source EEG processing packages (MNE; https://mne.tools) rather than the proprietary software used in previous examples.

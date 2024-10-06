import numpy as np
import pandas as pd
from pydub import AudioSegment
import simpleaudio as sa

# Input Parameters File Path and start of quake
data_directory = './data/lunar/training/data/S12_GradeA/'
data_file = 'xa.s12.00.mhz.1970-01-19HR00_evid00002.csv'
start_quake = 73500.0

# Program Settings
seconds_to_extract = 60
# Load your samples
ding = AudioSegment.from_file("ding.wav")
donk = AudioSegment.from_file("donk.wav")
# Constants for pitch shifting and volume scaling
piano_min_hz = 27.5  # A0
piano_max_hz = 4186.01  # C8
min_volume = -12.0  # dB for 50%
max_volume = 0.0  # dB for 100%

def main():
    cat_directory = './data/lunar/training/catalogs/'
    catalog_file = 'apollo12_catalog_GradeA_final.csv'
    data_directory = './data/lunar/training/data/S12_GradeA/'
    process_catalog_files(cat_directory, catalog_file, data_directory)
    #global data_directory, data_file, start_quake
    #generate_audio(data_directory, data_file, start_quake)

# Load data for each filename and generate audio
def process_catalog_files(cat_directory, catalog_file, data_directory):
    # Load the catalog data
    cat = load_catalog_data(cat_directory, catalog_file)
    
    #print_custom_dataframe(cat)
    
    for index, row in cat.iterrows():
        
        test_filename = row['filename'] 
        quake_start = row['time_rel(sec)']
        
        print(test_filename, quake_start)
        
        # Construct the CSV file path
        csv_file = f"{test_filename}.csv"
        
        # Call the generate_audio function with the extracted values
        generate_audio(data_directory, csv_file, quake_start)


def generate_audio(data_directory, data_file, start_quake):
    filepath = f"{data_directory}{data_file}"
    data_set = load_data(filepath)
    
    # Group the data to the whole second and average the time_rel and velocity
    # What if I don't average it out?
    # data_set = group_by_seconds(data_set)
    
    # Find the location of the index
    index,a  = find_closest_avg_time_rel_index(data_set, start_quake)
    data_set = calculate_and_set_time_diff(data_set, index)
    
    data_set = add_average_amplitude(data_set)
    data_set = filter_dataframe_by_seconds(data_set)
    
    print_custom_dataframe(data_set)
    
    audio_properties = create_audio_properties(data_set)
    
    print_custom_dataframe(audio_properties)
    
    audio = create_audio(audio_properties)
    save_audio(audio, data_file + "_" + str(start_quake))
    
# Load the catalog data
def load_catalog_data(cat_directory, catalog_file):
    cat_file = f"{cat_directory}{catalog_file}"
    cat = pd.read_csv(cat_file)
    return cat

# Load data from CSV file
def load_data(csv_file):
    data_set = pd.read_csv(csv_file)
    return data_set

# Group the data by the timestamp for the full second.
# Get the average of the time_rel and velocity
def group_by_seconds(data_set):
    # Create DataFrame
    df = pd.DataFrame(data_set)

    # Convert 'time_abs' to datetime format
    df['time_abs'] = pd.to_datetime(df['time_abs(%Y-%m-%dT%H:%M:%S.%f)'], format='%Y-%m-%dT%H:%M:%S.%f')

    # Create a new column 'time_abs_sec' with the time truncated to whole seconds
    df['time_abs_sec'] = df['time_abs'].dt.floor('s')

    # Group by the new 'time_abs_sec' and calculate the mean of 'time_rel' and 'velocity'
    df_grouped = df.groupby('time_abs_sec').agg({
        'time_rel(sec)': 'mean',
        'velocity(m/s)': 'mean'
    }).reset_index()
    
    # Rename the columns to indicate they are averaged
    df_grouped.rename(columns={
        'time_rel(sec)': 'avg_time_rel(sec)',
        'velocity(m/s)': 'avg_velocity(m/s)'
    }, inplace=True)

    return df_grouped

def add_time_diff(df):
    df['time_diff(sec)'] = df['avg_time_rel(sec)'].diff().fillna(0)  # Set the first value to 0
    return df

# Function to add a column that calculates the difference between avg_time_rel and a specified index
def add_time_diff_with_reference(df, ref_index):
    df = df.copy()  # To avoid modifying the original DataFrame
    # Calculate differences
    df['time_diff(sec)'] = df['avg_time_rel(sec)'] - df['avg_time_rel(sec)'].iloc[ref_index]
    
    # Set the reference index value to 0
    df.loc[ref_index, 'time_diff(sec)'] = 0
    
    # Make values above the reference index negative
    df.loc[:ref_index - 1, 'time_diff(sec)'] = df.loc[:ref_index - 1, 'time_diff(sec)'].apply(lambda x: x)

    # Make values below the reference index positive
    df.loc[ref_index + 1:, 'time_diff(sec)'] = df.loc[ref_index + 1:, 'time_diff(sec)'].apply(lambda x: x)

    return df

def calculate_and_set_time_diff(df, ref_index):
    df = df.copy()  # Create a copy to avoid modifying the original DataFrame
    
    column_name = ""
    if 'avg_time_rel(sec)' in df.columns:
        column_name = "avg_time_rel(sec)"
    else:
        column_name = "time_rel(sec)"
    
    # Calculate differences
    time_diff = df[column_name] - df[column_name].iloc[ref_index]
    
    # Set the reference index value to 0
    time_diff.iloc[ref_index] = 0
    
    # Set values above the reference index to negative
    time_diff.iloc[:ref_index] = time_diff.iloc[:ref_index].apply(lambda x: x)

    # Set values below the reference index to positive
    time_diff.iloc[ref_index + 1:] = time_diff.iloc[ref_index + 1:]

    # Add the fixed time difference column to the DataFrame
    df['time_diff(sec)'] = time_diff.values  # Assign the fixed time difference

    return df

# Function to find the index of the closest value in avg_time_rel
def find_closest_avg_time_rel_index(df, target_value):
    # Check if 'avg_time_rel(sec)' exists in the DataFrame
    column_name = ""
    if 'avg_time_rel(sec)' in df.columns:
        column_name = "avg_time_rel(sec)"
    else:
        column_name = "time_rel(sec)"

    # Calculate the absolute difference using 'avg_time_rel(sec)'
    difference = (df[column_name] - target_value).abs()
    # Get the index of the minimum difference
    closest_index = difference.idxmin()
    
    return closest_index, df.iloc[closest_index]  # Return index and corresponding row

def add_average_amplitude(df):
    df = df.copy()  # Create a copy to avoid modifying the original DataFrame
    avg_amplitude = []

    column_name = ""
    if 'avg_velocity(m/s)' in df.columns:
        column_name = 'avg_velocity(m/s)'
    else:
        column_name = 'velocity(m/s)'


    # Calculate average amplitude for each index
    for i in range(len(df)):
        # Determine the start and end indices for the rolling average
        start_index = max(0, i - 60)
        end_index = min(len(df), i + 60 + 1)  # +1 because the end index is exclusive
        
        # Calculate the average of avg_velocity in the specified range
        average = df[column_name].iloc[start_index:end_index].mean()
        avg_amplitude.append(average)

    # Assign the computed average amplitude to a new column
    df['intensity'] = avg_amplitude
    return df

# Function to display the first 5, last 5, and 10 middle records
def print_custom_dataframe(df, mid_start = -1):    
    # Set display options to show all columns
    pd.set_option('display.max_columns', None)  # None means show all columns
    pd.set_option('display.expand_frame_repr', False)  # Don't wrap to multiple lines

    # Print the first 5 rows
    print("First 5 rows:")
    print(df.head(5))

    if mid_start == -1:
        # Calculate the start and end indices for the middle records
        mid_start = len(df) // 2 - 5  # 5 records before the midpoint
        mid_end = len(df) // 2 + 5     # 5 records after the midpoint
    
    else:
        mid_start = mid_start -5
        mid_end = mid_start + 10

    # Print the middle 10 rows
    print("\nMiddle 10 rows:")
    print(df.iloc[mid_start:mid_end])

    # Print the last 5 rows
    print("\nLast 5 rows:")
    print(df.tail(5))
    
# Function to filter the DataFrame based on seconds_to_extract
def filter_dataframe_by_seconds(df):
    global seconds_to_extract
    # Filter the DataFrame to get rows where time_diff is between 0 and seconds_to_extract
    filtered_df = df[(df['time_diff(sec)'] >= 0) & (df['time_diff(sec)'] <= seconds_to_extract)]
    return filtered_df

# Creates new DataFrame for audio properties
def create_audio_properties(df):
    
    velocity_column_name = ""
    if 'avg_velocity(m/s)' in df.columns:
        velocity_column_name = 'avg_velocity(m/s)'
    else:
        velocity_column_name = 'velocity(m/s)'

    
    
    audio_properties = pd.DataFrame()
    audio_properties['time_diff(sec)'] = df['time_diff(sec)']
    audio_properties['pitch_shift'] = (
        (df[velocity_column_name] - df[velocity_column_name].min()) / 
        (df[velocity_column_name].max() - df[velocity_column_name].min()) * 
        (piano_max_hz - piano_min_hz) + piano_min_hz)
    

    # Calculate volume in dB
    audio_properties['volume'] = (
        (df['intensity'] - df['intensity'].min()) / 
        (df['intensity'].max() - df['intensity'].min()) * 
        (max_volume - min_volume) + min_volume
    )
    return audio_properties

def create_audio(audio_properties):
    combined_audio = AudioSegment.silent(duration=60 * 1000)  # 1-minute silence
    # Create the audio samples based on the new DataFrame
    for index, row in audio_properties.iterrows():
        # Determine sample and apply pitch shift
        sample = ding if index % 2 == 0 else donk  # Alternate samples
        sample = donk
        shifted_sample = sample._spawn(sample.raw_data, overrides={"frame_rate": int(sample.frame_rate * (row['pitch_shift'] / 440.0))})
        
        # Set volume
        adjusted_sample = shifted_sample + row['volume']

        # Calculate start time in milliseconds
        start_time = int(row['time_diff(sec)'] * 1000)  # Convert seconds to milliseconds
        
        # Overlay the adjusted sample on the combined audio
        combined_audio = combined_audio.overlay(adjusted_sample, position=start_time)
    return combined_audio

def save_audio(audio, file_name):
    audio.export(file_name + ".wav", format="wav")
    print("Saved '" + file_name + ".wav'")
main()
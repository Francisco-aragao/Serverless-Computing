import multiprocessing
import streamlit as slit
import matplotlib.pyplot as plt
import json
import time
import redis
import os
from queue import Queue

# Load env variables from deployment.yaml for Task 2
host       = os.environ.get('REDIS_HOST')
port       = os.environ.get('REDIS_PORT')
redis_Key  = os.environ.get('REDIS_KEY')

# Open connection with redis
r = redis.Redis(host, int(port))

# Width of the web page in streamlit
slit.set_page_config(layout="wide")
slit.title("Dashboard - Task2 - TP3 - Cloud Computing")
slit.success("Francisco Aragão e Gabriel Pains")

# Allocate space to plot percentages of network and memory use
slit.subheader('Percentage outgoing traffic bytes')
draw_network = slit.empty()

slit.subheader('Percentage of memory caching content')
draw_memory = slit.empty()

# Allocate space to plot moving average
slit.subheader('Moving average for each CPU')
draw_graph = slit.empty()

### END OF STREAMLIT INIT ###

# Graph will have at most 5 points (last entry is discarded as new ones arrive)
MAX_ENTRIES_PER_PLOT = 5

# Initialize plot data (circular buffer)
cpus = multiprocessing.cpu_count()
cpu_all_data = [Queue() for x in range(0, cpus)]

# Get data from redis
old_data = r.get(redis_Key)

# Main dashboard loop
while True:
    # Get data from redis
    data = r.get(redis_Key)

    # Wait for new data to arrive
    if (old_data != data):
        old_data = data    

        # Convert to dict and proceed to calculate dashboard data
        data_dict = json.loads(data.decode("utf-8"))
        
        # Get all cpu moving average values and store them
        cpu_values = [value for key, value in data_dict.items() if key.startswith("avg_util_60sec_cpu-")]

        # Accumulate entries to fill plot
        if (cpu_all_data[0].qsize() < MAX_ENTRIES_PER_PLOT): 
            for i in range(0, len(cpu_values)):
                cpu_all_data[i].put(cpu_values[i])
        # Plot is already full, remove last entry and add a new one 
        else:
            for i in range(0, len(cpu_values)):
                cpu_all_data[i].put(cpu_values[i])
                cpu_all_data[i].get()

        # Plot configuration (4 x 4 plots)
        subplots_per_row = 4
        total_rows = (len(cpu_values) + subplots_per_row - 1) // subplots_per_row

        # Total entries so far
        num_entries = cpu_all_data[0].qsize()

        # Create 16 subplots (one for each cpu)
        plt.style.use('bmh')
        fig, axs = plt.subplots(total_rows, subplots_per_row, figsize=(25, total_rows * 4))        

        # Plot data for every cpu
        for i, key in enumerate(data_dict.keys()):
            if key.startswith("avg_util_60sec_cpu-"):
                cpu_number = int(key.split('-')[-1])
                row, col = divmod(cpu_number, subplots_per_row)

                # Configure axis and plot data 
                xs = [5 * x for x in range(0, num_entries)] # X values (0 to 20 seconds)
                ys = list(cpu_all_data[i].queue)            # Y values (last 5 values of average cpu usage)

                # Y axis goes from 0% usage to 100% usage
                axs[row, col].set_ylim(0, 100)

                # Plot usage
                axs[row, col].plot(xs, ys, linewidth=3, marker='.', color='#025eb5')
                axs[row, col].fill_between(xs, ys, color='#8fd6ff')

                # Info
                axs[row, col].set_title(f'CPU-{cpu_number}')
                axs[row, col].set_ylabel('% average cpu usage last minute')
                axs[row, col].set_xlabel('Time (s)')  

        ### END OF DASHBOARD DATA CALCULATIONS ###

        # Adjust layout to avoid overlap
        plt.tight_layout()

        # Display the plot using streamlit.pyplot previously initialized
        draw_graph.pyplot(fig)

        # Close plot to free memory
        plt.close(fig)
        
        # Display the percentage of memory caching content (using a progress bar, not a chart)
        mem_cache = data_dict["percent_memory_caching"]
        draw_memory.progress(mem_cache, text=f'{mem_cache} %')

        # Display the percentage of network outgoing (using a progress bar again)
        net_out = data_dict["percent_network_outgoing"]
        draw_network.progress(net_out, text=f'{net_out} %')

    # Avoid polling redis too often
    time.sleep(1)
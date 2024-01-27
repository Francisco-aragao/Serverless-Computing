from queue import Queue # Needed for moving average buffer

import multiprocessing
import datetime as dt
import time

def handler(input: dict, context: object) -> dict:
    # Results dict
    metrics = dict()

    # Save initialization time
    initial_time = dt.datetime.fromisoformat(input['timestamp'])
    
    if 'initial_timestamp' not in context.env:
        context.env['initial_timestamp'] = initial_time.timestamp()

    # Moving average of cpu utilization for the last minute
    # For every cpu
    cpus = multiprocessing.cpu_count()

    for idx in range(0, cpus):
        # Get common keys
        mov_avg = f"mov_avg-{idx}"
        buffer  = f"circular_buffer-{idx}"
        
        # Add keys to env dict on startup
        if mov_avg not in context.env:
            context.env[mov_avg] = 0

        if buffer not in context.env:
            context.env[buffer] = Queue()

        # Get current value and add to circular buffer
        new_usage   = input[f"cpu_percent-{idx}"]
        context.env[buffer].put(new_usage)

        num_entries = context.env[buffer].qsize()
        last_avg    = context.env[mov_avg]

        # Less than one minute has passed
        # So this is the first filling of the circular buffer
        if time.time() - context.env['initial_timestamp'] < 60:
            # Update moving average with a new entry (cumulative moving average)
            # This allows the average to be readily available without needing to wait 60 seconds
            context.env[mov_avg] = last_avg + (new_usage - last_avg) / num_entries
        
        # One minute has passed, always update average (circular buffer size will remain constant)
        else:
            last_usage = context.env[buffer].get()
            
            # Add average from new value and drop average from last value
            context.env[mov_avg] = last_avg + (new_usage - last_usage) / num_entries

        # Add this metric to result
        metrics[f"avg_util_60sec_cpu-{idx}"] = context.env[mov_avg]

    # Calculate other metrics
    # Percentage of outgoing traffic bytes
    bytes_sent     = input['net_io_counters_eth0-bytes_sent']
    bytes_received = input['net_io_counters_eth0-bytes_recv']

    # Percentage of memory caching content
    mem_cache = input['virtual_memory-cached'] + input['virtual_memory-buffers']
    mem_total = input['virtual_memory-total']

    # Add other metrics
    metrics['percent_network_outgoing'] = 100 * bytes_sent / (bytes_sent + bytes_received)
    metrics['percent_memory_caching']   = 100 * mem_cache  / mem_total

    return metrics
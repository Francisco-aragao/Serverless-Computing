import redis

# Used to manipulate context
import os
import time
import json
import datetime as dt
import multiprocessing

# Import user function
import usermodule

# Context class
class Context:
    def __init__(self, host, port, input_key, output_key):
        self.host               = host 
        self.port               = port 
        self.input_key          = input_key 
        self.output_key         = output_key 
        self.function_getmtime  = os.path.getmtime("usermodule.py") 
        self.last_execution     = None
        self.env                = dict()

    def updateTimes(self):
        self.last_execution     = dt.datetime.now()
        self.function_getmtime  = os.path.getmtime("usermodule.py")

# Runtime main function
def run():
    # Get env variables defined in deployment.yaml for Task 1
    host       = os.environ.get('REDIS_HOST')
    port       = os.environ.get('REDIS_PORT')
    input_key  = os.environ.get('REDIS_INPUT_KEY')
    output_key = os.environ.get('REDIS_OUTPUT_KEY')

    # Init context and redis connection
    context = Context(host, int(port), input_key, output_key)

    r = redis.Redis(host, int(port))

    # Runtime loop
    old_input = r.get(input_key)

    while (True):
        new_input = r.get(input_key)

        # Check if new data has arrived
        if old_input != new_input:
            old_input = new_input

            # Convert input to dict and call user handler
            input_json  = json.loads(new_input.decode('utf-8'))

            output      = usermodule.handler(input_json, context)

            # Check for correct output
            expected = multiprocessing.cpu_count() + 2

            if (len(output) != expected):
                print(f"Expected {expected} values from usermodule.handler, will not add output to redis!")
                continue
                
            # Got correct output, proceed
            output_json = json.dumps(output)

            # Save user output as json in redis
            r.set(output_key, output_json)

            # User function has been executed, so update context.last_execution time
            context.updateTimes()
            
        # Avoid polling redis too often
        time.sleep(1)

# Init runtime
run()
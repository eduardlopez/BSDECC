# BSDECC
BSDECC Multiprocess Streaming Processing Engine - Data Engineering Project

## How it works? You may ask..
Easy!
Look this image:
![data-streaming-processing-architecture](https://github.com/eduardlopez/BSDECC/blob/master/images/data-streaming-processing-architecture.png?raw=true)

The principal components are Tasks and Queues. Each task receives an input via a queue, computes something, and then produce an output or can transfer this output to another task with another queue.

Then you can wrap a task with a supervisor and automatically will create new processes to reduce the workload and empty the queue as fast as possible. And when the workload decreases, it will kill some processes automatically. The ratio of workload/processes (per task) is controlled by some constants. But you can use, for example, the difference of timestamps between different tasks to calculate another heuristic.

## Tasks
### NLP SENTIMENT ANALYSIS TASK
I've created this task as an example.
It detects the language and performs a sentiment analysis for each message that receive.
This task is very computing-intensive. In this case, the multiprocessing comes very handy.

### Wally alert
Every time he detects that the connections to the server have been lost. Sends a HTTP post message to our front end flask app.

### Permanent storage
This task saves the each message to a db. In this case I've chosen mongodb for some factors. One of them is that is very easy to install and operate for an example program like this.
If you want to perform some types of queries to the db, remember to create an index.



## Do you want to read the code?
It couldn't be more easy! 

Each block of the image adobe, corresponds to a function in the code

Can you tell me to which block (of the image above) corresponds this function? "def language_sentiment_worker(q, exit_event):"

# What do I need to run this program?
I've only tested this program on Ubuntu. The instructions are similar for others systems.

## Install mongodb
Here the instructions for each system. The installation is very fast.
https://docs.mongodb.com/manual/administration/install-on-linux/

### Start the service
```sudo service mongod start```

### You can use a program to see more nicely the dbs and collections:
Robomongo (now called Robo 3T) is very easy to install:
https://robomongo.org/download

### Here the direct instructions for ubuntu 16.x (for mongodb and Robo 3T)
https://github.com/eduardlopez/BSDECC/blob/master/useful%20commands/mongodb_install_ubuntu-16__commands.txt

## Install miniconda
I've used miniconda as a python environment management. Try it. It works well.
##### Source and instructions to install conda: https://conda.io/miniconda.html
The installation it's very easy.

### Create a conda enviroment from enviroment.yml. 
I've added an environment.yml file with all the dependencies.

```conda env create --name BSDECC --file environment.yml```

### Now it's time to initiate the enviroment:
```source activate BSDECC```

### Test that you are using the new python of the new enviroment
```which python```

### Now we only have to run the main python file!
```python stream_processing.py```


## Run flask
```FLASK_APP=app.py flask run -h localhost -p 5478```


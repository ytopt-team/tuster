#!/usr/bin/env python
import os
import subprocess
import json
import socket
import logging
logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

import ray
import time
from mpi4py import MPI

# opening ports as suggested in: https://github.com/ray-project/ray/issues/4393
REDIS_PORT          = 6379
REDIS_SHARD_PORTS   = 6380
NODE_MANAGER_PORT   = 12345
OBJECT_MANAGER_PORT = 12346

comm = MPI.COMM_WORLD
rank = comm.Get_rank()

def ray_stop():
    with open('stop.out', 'wb') as fp:
        subprocess.run(
            "ray stop",
            shell=True,
            check=True,
            stdout=fp,
            stderr=subprocess.STDOUT
        )


def run_ray_head(port):
    with open('ray.log.head', 'wb') as fp:
        subprocess.run(
            f'ray start --head \
                    --node-ip-address=0.0.0.0 \
                    --redis-port={port} \
                    --redis-shard-ports={REDIS_SHARD_PORTS} \
                    --node-manager-port={NODE_MANAGER_PORT} \
                    --object-manager-port={OBJECT_MANAGER_PORT}',
            shell=True,
            check=True,
            stdout=fp,
            stderr=subprocess.STDOUT
        )


def run_ray_worker(redis_address):
    with open(f'ray.log.{rank}', 'wb') as fp:
        subprocess.run(
            f'ray start --redis-address={redis_address} \
                    --node-manager-port={NODE_MANAGER_PORT} \
                    --object-manager-port={OBJECT_MANAGER_PORT}',
            shell=True,
            check=True,
            stdout=fp,
            stderr=subprocess.STDOUT
        )

def fetch_ip():
    #p = subprocess.run(
    #    '/sbin/ifconfig',
    #    stdout=subprocess.PIPE,
    #    stderr=subprocess.STDOUT,
    #    shell=True,
    #    encoding='utf-8',
    #    check=True,
    #)
    #stdout = p.stdout.strip()
    #lines = stdout.split('\n')
    #for i, line in enumerate(lines):
    #    if 'ipogif0' in line:
    #        return lines[i+1].split()[1].split(':')[1]
    return socket.gethostname()

@ray.remote
def calc(*args):
    res = sum(args)
    with open('res.txt', 'w') as f:
        f.write(f'[{time.time}]: {res}')
    return res

def master():
    head_ip = fetch_ip()
    if head_ip is None:
        raise RuntimeError("could not fetch head_ip")
    
    print('Ready to run ray head')
    run_ray_head(REDIS_PORT)
    print('Head started...')

    redis_address = f'{head_ip}:{REDIS_PORT}'
    print('Ready to broadcast redis_address of head: ', redis_address)

    redis_address = comm.bcast(redis_address, root=0)
    print('Broadcast done... received redis_address=', redis_address)
    
    print('Waiting for workers to start...')
    comm.barrier() # waiting for ray_workers to start
    print('Workers are all running!')

    print('Ready to start driver on: ', fetch_ip())
    ray.init(redis_address=redis_address)
    print('Driver started on: ', fetch_ip())

    val_id = [calc.remote(*[i for i in range(10)]) for _ in range(10)]
    res = ray.get(val_id)
    print('res: ', res)
    
    # with open('ytopt.out', 'wb') as fp:
    #     print("about to run ytopt subprocess...")
    #     # os.system(f'python -m ytopt.search.ambs --evaluator ray --redis-address {redis_address} --problem ytopt.benchmark.ackley.problem.Problem')
    #     subprocess.run(
    #        f'python -m ytopt.search.ambs --evaluator ray --redis-address {"localhost"} --problem ytopt.benchmark.ackley.problem.Problem',
    #        shell=True,
    #        stdout=fp,
    #        stderr=subprocess.STDOUT,
    #        check=True,
    #     )
    #     print("ytopt subprocess is finished. exiting.")

    comm.barrier() # waiting for driver to complete
    ray_stop()


def worker():
    redis_address = None

    print('Waiting for broadcast...')
    redis_address = comm.bcast(redis_address, root=0)
    print('Broadcast done... received redis_address=', redis_address)

    print(f"Worker on rank {rank} will connect to redis-address={redis_address}")
    run_ray_worker(redis_address)

    comm.barrier() # waiting for all workers to start
    comm.barrier() # waiting for driver to finish
    ray_stop()

if __name__ == "__main__":
    if rank == 0: master()
    else: worker()

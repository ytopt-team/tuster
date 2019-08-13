#!/usr/bin/env python
import os
import sys
import subprocess
import socket
import signal
import logging
import psutil
from pprint import pformat
import ray
import time
from mpi4py import MPI

from redis.exceptions import ConnectionError

# opening ports as suggested in: https://github.com/ray-project/ray/issues/4393
REDIS_PORT          = 10100
REDIS_SHARD_PORTS   = 20200
NODE_MANAGER_PORT   = 30300
OBJECT_MANAGER_PORT = 40400

comm = MPI.COMM_WORLD
RANK = rank = comm.Get_rank()


# EXIT

def on_exit(signum, stack):
    ray_stop()

def ray_stop():
    with open('stop.out', 'wb') as fp:
        subprocess.run(
            "ray stop",
            shell=True,
            check=True,
            stdout=fp,
            stderr=subprocess.STDOUT
        )

signal.signal(signal.SIGINT, on_exit)
signal.signal(signal.SIGTERM, on_exit)

# ...

def run_ray_head(head_ip):
    with open('ray.log.head', 'wb') as fp:
        # --redis-shard-ports={REDIS_SHARD_PORTS} \
        # --node-manager-port={NODE_MANAGER_PORT} \
        # --object-manager-port={OBJECT_MANAGER_PORT} \
        subprocess.run(
            f'ray start --head \
                    --num-cpus 1 \
                    --node-ip-address={head_ip} \
                    --redis-port={REDIS_PORT}',
            shell=True,
            check=True,
            stdout=fp,
            stderr=subprocess.STDOUT
        )


def run_ray_worker(head_redis_address):
    with open(f'ray.log.{rank}', 'wb') as fp:
        # --node-manager-port={NODE_MANAGER_PORT} \
        # --object-manager-port={OBJECT_MANAGER_PORT}',
        subprocess.run(
            f'ray start --redis-address={head_redis_address} \
                    --num-cpus 1 \
                    --node-ip-address={fetch_ip()}',
            shell=True,
            check=True,
            stdout=fp,
            stderr=subprocess.STDOUT
        )

def fetch_ip():
    return socket.gethostbyname(socket.gethostname())


def master():
    head_ip = fetch_ip()
    if head_ip is None:
        raise RuntimeError("could not fetch head_ip")

    logging.info('Ready to run ray head')

    run_ray_head(head_ip)

    head_redis_address = f'{head_ip}:{REDIS_PORT}'

    logging.info(f'Head started at: {head_redis_address}')

    logging.info(f'Ready to broadcast head_redis_address: {head_redis_address}')

    head_redis_address = comm.bcast(head_redis_address, root=0)

    logging.info('Broadcast done...')

    logging.info('Waiting for workers to start...')

    comm.barrier() # waiting for ray_workers to start

    logging.info('Workers are all running!')

    logging.info('Ready to start driver!')


def driver(head_redis_address, exe):
    logging.info(f'Starting driver, wants to connect to head at: {head_redis_address}')

    with open('exe.out', 'wb') as fp:
        subprocess.run(
            exe.format(redis_address=head_redis_address),
            shell=True,
            stdout=fp,
            stderr=subprocess.STDOUT,
            check=True,
        )
        logging.info("ytopt subprocess is finished. exiting.")


def worker(run_driver=False, exe=None):
    head_redis_address = None

    logging.info('Waiting for broadcast...')
    head_redis_address = comm.bcast(head_redis_address, root=0)
    logging.info(f'Broadcast done... received head_redis_address= {head_redis_address}')

    logging.info(f"Worker on rank {rank} with ip {fetch_ip()} will connect to head-redis-address={head_redis_address}")
    run_ray_worker(head_redis_address)

    comm.barrier() # waiting for all workers to start

    if run_driver:
        driver(head_redis_address, exe)

if __name__ == "__main__":

    try:
        exe = sys.argv[1]
    except IndexError:
        from tuster.exceptions import TusterError
        raise TusterError('No executable was given...')

    logging.basicConfig(
        filename='tuster.log',
        format='%(asctime)s | %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p',
        level=logging.INFO)

    if rank == 0: master()
    else: worker(run_driver=rank==1, exe=exe)

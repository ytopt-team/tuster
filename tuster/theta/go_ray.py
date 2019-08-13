#!/usr/bin/env python
import os
import subprocess
import socket
import signal
import logging
logging.basicConfig(
        filename='app.log',
        format='%(asctime)s | %(message)s',
        datefmt='%m/%d/%Y %I:%M:%S %p',
        level=logging.INFO)
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
    # addrs_kind = "ipogif0"

    # addrs = [
    #     x.address for k, v in psutil.net_if_addrs().items() if k == addrs_kind
    #               for x in v if x.family == socket.AddressFamily.AF_INET
    #         ]
    # return addrs[0]

    ip = socket.gethostbyname(socket.gethostname())

    return ip


@ray.remote
def calc():
    res = fetch_ip()
    with open(f'res_{time.time()}', 'w') as f:
        f.write(str(res))
    return res

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

    # driver(head_redis_address)

    # comm.barrier() # waiting for driver to end
    # logging.info('Driver done...')

    # ray.shutdown()

def driver(head_redis_address):
    logging.info(f'Starting driver, wants to connect to head at: {head_redis_address}')
    sleep_time = 5
    infos = None
    while infos is None: # Raylets can take some time to register
        try:
            infos = ray.init(redis_address=head_redis_address)
            logging.info(infos)
        except ConnectionError:
            logging.info('Quitting driver start-up...', exc_info=True)
            return
        except Exception as e:
            logging.info('Failed to init driver... sleeping for 1sec...', exc_info=True)
            time.sleep(sleep_time)

    logging.info(f'Driver started on: {fetch_ip()}')
    nodes_infos = ray.nodes()
    logging.info(f'Cluster as {len(nodes_infos)} nodes:\n {pformat(nodes_infos)}')

    val_id = [calc.remote() for _ in range(10)]
    res = ray.get(val_id)
    logging.info(f'res: {str(res)}')

    # with open('ytopt.out', 'wb') as fp:
    #     logging.info("about to run ytopt subprocess...")
    #     # os.system(f'python -m ytopt.search.ambs --evaluator ray --redis-address {redis_address} --problem ytopt.benchmark.ackley.problem.Problem')
    #     subprocess.run(
    #        f'python -m ytopt.search.ambs --evaluator ray --redis-address {"localhost"} --problem ytopt.benchmark.ackley.problem.Problem',
    #        shell=True,
    #        stdout=fp,
    #        stderr=subprocess.STDOUT,
    #        check=True,
    #     )
    #     logging.info("ytopt subprocess is finished. exiting.")


def worker(run_driver=False):
    head_redis_address = None

    logging.info('Waiting for broadcast...')
    head_redis_address = comm.bcast(head_redis_address, root=0)
    logging.info(f'Broadcast done... received head_redis_address= {head_redis_address}')

    logging.info(f"Worker on rank {rank} with ip {fetch_ip()} will connect to head-redis-address={head_redis_address}")
    run_ray_worker(head_redis_address)

    comm.barrier() # waiting for all workers to start

    if run_driver:
       driver(head_redis_address)

    # comm.barrier() # waiting for driver to finish
    # ray_stop()

if __name__ == "__main__":
    if rank == 0:
        logging.info(f'CPU count: ({psutil.cpu_count()}, logical=True); ({psutil.cpu_count(logical=False)}, logical=False)')
        master()
    else: worker(rank==1)

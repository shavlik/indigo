#!/usr/bin/env python

# Copyright 2018 Francis Y. Yan, Jestin Ma
# Copyright 2018 Wei Wang, Yiyang Shao (Huawei Technologies)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#     Unless required by applicable law or agreed to in writing, software
#     distributed under the License is distributed on an "AS IS" BASIS,
#     WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#     See the License for the specific language governing permissions and
#     limitations under the License.


import os
import sys
import yaml
import argparse
import threading
import tensorflow as tf
from os import path
from subprocess import check_call

import context
from dagger_train import DaggerLeader, DaggerWorker
from env.environment_mininet import Environment_Mininet
from helpers.utils import Config


def create_mininet_env(worker_num, worker_index):
    # get total env and tp set
    total_env_set = Config.total_env_set_train
    total_tp_set = Config.total_tp_set_train
    total_env_len = len(total_env_set)
    tasks_per_work = total_env_len / worker_num

    # allocate the env and tp for this worker
    env_set = []
    tp_set = []
    if worker_index < worker_num - 1:
        for i in xrange(tasks_per_work * worker_index,
                        tasks_per_work * (worker_index + 1)):
            tp_set.append(total_tp_set[i])
            env_set.append(total_env_set[i])
            sys.stderr.write('worker {} is allocated tp & env: {} {}\n'.format(
                worker_index, total_tp_set[i], total_env_set[i]))
    else:  # last one
        for i in xrange(tasks_per_work * worker_index, total_env_len):
            tp_set.append(total_tp_set[i])
            env_set.append(total_env_set[i])

            sys.stderr.write('worker {} is allocated tp & env: {} {}\n'.format(
                worker_index, total_tp_set[i], total_env_set[i]))

    env = Environment_Mininet(tp_set, env_set, True)
    return env


def run(args):
    """ For each worker/parameter server, start the appropriate job
    associated with the cluster and server.
    """

    job_name = args.job_name
    task_index = args.task_index
    sys.stderr.write('Starting job %s task %d\n' % (job_name, task_index))

    ps_hosts = args.ps_hosts.split(',')
    worker_hosts = args.worker_hosts.split(',')
    num_workers = len(worker_hosts)

    cluster = tf.train.ClusterSpec({'ps': ps_hosts, 'worker': worker_hosts})
    server = tf.train.Server(cluster, job_name=job_name, task_index=task_index)

    if job_name == 'ps':
        worker_tasks = set([idx for idx in xrange(num_workers)])
        leader = DaggerLeader(cluster, server, worker_tasks)

        try:
            leader.run(debug=True)
        except KeyboardInterrupt:
            pass
        finally:
            leader.cleanup()

    elif job_name == 'worker':
        env = create_mininet_env(num_workers, task_index)
        worker = DaggerWorker(cluster, server, task_index, env)

        try:
            worker.run(debug=True)
        except KeyboardInterrupt:
            pass
        finally:
            worker.cleanup()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--ps-hosts', required=True, metavar='[HOSTNAME:PORT, ...]',
        help='comma-separated list of hostname:port of parameter servers')
    parser.add_argument(
        '--worker-hosts', required=True, metavar='[HOSTNAME:PORT, ...]',
        help='comma-separated list of hostname:port of workers')
    parser.add_argument('--job-name', choices=['ps', 'worker'],
                        required=True, help='ps or worker')
    parser.add_argument('--task-index', metavar='N', type=int, required=True,
                        help='index of task')
    args = parser.parse_args()

    # run parameter servers and workers
    run(args)


if __name__ == '__main__':
    main()

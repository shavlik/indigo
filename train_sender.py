#!/usr/bin/env python

import os
import sys
import argparse
from sender import Sender
from dagger import Dagger
from reinforce import Reinforce
from helpers import make_sure_path_exists


class Trainer(object):
    def __init__(self, args):
        self.sender = Sender(args.ip, args.port, training=True)
        self.algorithm = args.algorithm

        curr_file_path = os.path.dirname(os.path.abspath(__file__))
        saved_models_path = os.path.join(curr_file_path, 'saved_models')
        make_sure_path_exists(saved_models_path)

        if self.algorithm == 'dagger':
            model_path = os.path.join(saved_models_path, 'dagger')

            self.learner = Dagger(
                state_dim=self.sender.state_dim,
                action_cnt=self.sender.action_cnt,
                training=True,
                save_vars=model_path,
                restore_vars=None,
                debug=True)
        elif self.algorithm == 'reinforce':
            model_path = os.path.join(saved_models_path, 'reinforce')

            self.learner = Reinforce(
                state_dim=self.sender.state_dim,
                action_cnt=self.sender.action_cnt,
                training=True,
                save_vars=model_path,
                restore_vars=None,
                debug=True)

        self.sender.set_sample_action(self.learner.sample_action)

        self.max_batches = 1000
        self.episodes_per_batch = 1

    def run(self):
        for batch_i in xrange(1, self.max_batches + 1):
            sys.stderr.write('\nBatch %s/%s is running...\n\n' %
                             (batch_i, self.max_batches))

            for episode_i in xrange(1, self.episodes_per_batch + 1):
                sys.stderr.write('Episode %s/%s is running...\n' %
                                 (episode_i, self.episodes_per_batch))

                self.sender.run()
                state_buf, action_buf, reward = self.sender.get_experience()

                if self.algorithm == 'dagger':
                    self.learner.store_episode(state_buf)
                elif self.algorithm == 'reinforce':
                    self.learner.store_episode(state_buf, action_buf, reward)

                self.sender.reset_training()

            self.learner.update_model()

        self.learner.save_model()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('ip', metavar='IP')
    parser.add_argument('port', type=int)
    parser.add_argument('--algorithm', choices=['dagger', 'reinforce'],
                        required=True)
    args = parser.parse_args()

    trainer = Trainer(args)
    try:
        trainer.run()
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()

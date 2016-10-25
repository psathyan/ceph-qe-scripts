import os, sys
sys.path.append(os.path.abspath(os.path.join(__file__, "../../..")))
import utils.log as log
import sys
from utils.test_desc import AddTestInfo
from lib.s3.rgw import Config
from lib.s3.rgw import RGW
import lib.s3.rgw as rgw_lib
import argparse
import yaml


def test_exec_write(config):

    test_info = AddTestInfo('give the permission for all the users and then reset it')

    try:

        # test case starts

        test_info.started_info()

        all_user_details = rgw_lib.create_users(config.user_count)

        user1 = all_user_details[0]
        u1 = RGW(config, user1)
        log.info('user1: %s' % user1)

        all_user_details.pop(0)

        for each_user in all_user_details:

            print 'iter ------------------>'

            log.info('user2: %s' % each_user)

            u2 = RGW(config, each_user)

            u2_canonical_id = u2.canonical_id

            log.info('canonical id of u2: %s' % u2_canonical_id)

            log.info('setting only read permission')

            grants = {'permission': 'READ', 'user_id': None, 'recursive': True}

            log.info('write persmission are not set')
            grants['user_id'] = u2_canonical_id

            u1.grants = grants

            u1.initiate_buckets()
            u2.bucket_names = u1.bucket_names
            u2.buckets_created = u1.buckets_created

            u2.json_file_upload = u1.json_file_upload
            u2.json_file_download = u1.json_file_download

            u2.grants = None
            buckets = u2.initiate_buckets()
            key_created = u2.create_keys(buckets)
            if not key_created:
                log.info('no write permission set and hence failing to create object')

            elif key_created:
                raise AssertionError,  "object created even with no permission"

            log.info('setting permission to write also')

            grants = {'permission': 'WRITE', 'user_id': u2_canonical_id, 'recursive': True}
            u1.grants = grants
            u1.initiate_buckets()
            u2.bucket_names = u1.bucket_names
            u2.buckets_created = u1.buckets_created

            u2.grants = None
            buckets = u2.initiate_buckets()
            key_created = u2.create_keys(buckets, object_base_name=str(u2.canonical_id) + ".key")
            if key_created:
                log.info('object created after permission set')

        log.info('***************** removing grants and mking the bucket private *****************')
        u1.grants = None
        u1.acls = 'private'
        u1.initiate_buckets()

        for each_user in all_user_details:

            u2 = RGW(config, each_user)

            print 'iter ------------------>'

            u2.bucket_names = u1.bucket_names
            u2.buckets_created = u1.buckets_created

            u2.json_file_upload = u1.json_file_upload
            u2.json_file_download = u1.json_file_download

            u2.grants = None
            buckets = u2.initiate_buckets()

            if not buckets:
                log.info('bucket init failed: %s' % buckets)
            elif buckets:

                key_created = u2.create_keys(buckets)
                if not key_created:
                    log.info('no write permission set and hence failing to create object')

                elif key_created:
                    raise AssertionError, "object created even with no permission"

        test_info.success_status('test completed')

    except AssertionError, e:
        log.error(e)
        test_info.failed_status('test failed: %s' % e)
        sys.exit(1)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='RGW Automation')

    parser.add_argument('-c', dest="config", default='yamls/config.yaml',
                        help='RGW Test yaml configuration')

    parser.add_argument('-p', dest="port", default='8080',
                        help='port number where RGW is running')

    args = parser.parse_args()

    yaml_file = args.config

    with open(yaml_file, 'r') as f:
        doc = yaml.load(f)

    config = Config()

    config.user_count = doc['config']['user_count']
    config.bucket_count = doc['config']['bucket_count']
    config.objects_count = doc['config']['objects_count']
    config.objects_size_range = {'min': doc['config']['objects_size_range']['min'],
                                 'max': doc['config']['objects_size_range']['max']}

    config.port = args.port

    log.info('user_count:%s\n'
             'bucket_count: %s\n'
             'objects_count: %s\n'
             'objects_size_range: %s\n'
             'port: %s' % (
              config.user_count, config.bucket_count, config.objects_count, config.objects_size_range, config.port))

    test_exec_write(config)

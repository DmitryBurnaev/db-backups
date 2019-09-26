from run_old import logger


def upload_file(client, src_filename, dst_filename):
    logger.info(
        'Uploading file {} to {} server'.format(src_filename, dst_filename)
    )
    client.upload(src_filename, dst_filename)


def upload_backup(src_filename):
    ...
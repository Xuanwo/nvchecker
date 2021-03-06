# MIT licensed
# Copyright (c) 2013-2017 lilydjwg <lilydjwg@gmail.com>, et al.

import re
from importlib import import_module

import structlog

logger = structlog.get_logger(logger_name=__name__)

handler_precedence = (
  'github', 'aur', 'pypi', 'archpkg', 'debianpkg', 'ubuntupkg',
  'gems', 'pacman',
  'cmd', 'bitbucket', 'regex', 'manual', 'vcs',
  'cratesio', 'npm', 'hackage', 'cpan', 'gitlab', 'packagist',
  'anitya', 'android_sdk',
)

def substitute_version(version, name, conf):
  '''
  Substitute the version string via defined rules in the configuration file.
  See README.rst#global-options for details.
  '''
  prefix = conf.get('prefix')
  if prefix:
    if version.startswith(prefix):
      version = version[len(prefix):]
    return version

  from_pattern = conf.get('from_pattern')
  if from_pattern:
    to_pattern = conf.get('to_pattern')
    if not to_pattern:
      raise ValueError('%s: from_pattern exists but to_pattern doesn\'t', name)

    return re.sub(from_pattern, to_pattern, version)

  # No substitution rules found. Just return the original version string.
  return version

async def get_version(name, conf, **kwargs):
  for key in handler_precedence:
    if key in conf:
      func = import_module('.source.' + key, __package__).get_version
      version = await func(name, conf, **kwargs)
      if version:
        version = version.replace('\n', ' ')
        try:
          version = substitute_version(version, name, conf)
        except (ValueError, re.error):
          logger.exception('error occurred in version substitutions', name=name)
      return version
  else:
    logger.error('no idea to get version info.', name=name)

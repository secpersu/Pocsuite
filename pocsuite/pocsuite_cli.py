#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright (c) 2014-2015 pocsuite developers (http://seebug.org)
See the file 'docs/COPYING' for copying permission
"""

import os
import sys
import time
import traceback
from .lib.utils import versioncheck
from .lib.core.common import unhandledExceptionMessage
from .lib.core.enums import CUSTOM_LOGGING
from .lib.core.common import banner
from .lib.core.exception import PocsuiteUserQuitException
from .lib.core.common import dataToStdout
from .lib.core.common import setPaths
from .lib.core.settings import LEGAL_DISCLAIMER
from .lib.core.settings import PCS_OPTIONS
from .lib.core.data import kb
from .lib.core.data import conf
from .lib.core.data import paths
from .lib.core.data import logger
from .lib.core.data import cmdLineOptions
from .lib.parse.parser import parseCmdOptions
from .lib.core.option import initOptions
from .lib.controller.controller import start
from .lib.core.option import init
from .lib.core.common import delModule
from .lib.core.common import getUnicode


def main():
    """
    @function Main function of pocsuite when running from command line.
    """
    pcsInit()


def modulePath():
    """
    @function the function will get us the program's directory
    """
    return getUnicode(os.path.dirname(os.path.realpath(__file__)), sys.getfilesystemencoding())


def pcsInit(PCS_OPTIONS=None):
    try:
        paths.POCSUITE_ROOT_PATH = modulePath()
        setPaths()

        argsDict = PCS_OPTIONS or parseCmdOptions()

        cmdLineOptions.update(argsDict)
        initOptions(cmdLineOptions)

        if argsDict['dork']:
            from pocsuite.api.x import ZoomEye
            z = ZoomEye(paths.POCSUITE_ROOT_PATH + '/api/conf.ini')
            if z.token:
                logger.log(CUSTOM_LOGGING.SYSINFO, 'Use exsiting token from /api/conf.ini')


            else:
                logger.log(CUSTOM_LOGGING.ERROR, 'No token found in /api.conf.ini, generate new token')
                logger.log(CUSTOM_LOGGING.SYSINFO, 'Username')
                usr = raw_input()
                logger.log(CUSTOM_LOGGING.SYSINFO, 'Password')
                pwd = raw_input()
                z.newToken(usr, pwd)
                if z.token:
                    logger.log(CUSTOM_LOGGING.SUCCESS, 'New token generation success')
            info = z.resourceInfo()
            if not z.token or not z.resources:
                sys.exit(logger.log(CUSTOM_LOGGING.WARNING, 'Token invalid or out of date'))
            logger.log(CUSTOM_LOGGING.SUCCESS, 'Aavaliable search times,\
whois {}, web-search{}, host-search{}'.\
                    format(info['whois'], info['web-search'], \
                    info['host-search']))

            tmpIpFile = paths.POCSUITE_TMP_PATH + '/zoomeye/%s.txt' % time.ctime()
            with open(tmpIpFile, 'w') as fp:
                for ip in z.search(argsDict['dork']):
                    fp.write('%s\n' % ip[0])
            conf.urlFile = argsDict['urlFile'] = tmpIpFile

        if not any((argsDict['url'] or argsDict['urlFile'], conf.requires, conf.requiresFreeze)):
            errMsg = 'No "url" or "urlFile" assigned.'
            sys.exit(logger.log(CUSTOM_LOGGING.ERROR, errMsg))

        def doNothin(*args, **kw):
            return

        if conf.quiet:
            logger.log = doNothin

        banner()
        conf.showTime = True
        dataToStdout

        dataToStdout("[!] legal disclaimer: %s\n\n" % LEGAL_DISCLAIMER)
        dataToStdout("[*] starting at %s\n\n" % time.strftime("%X"))

        init()
        start()

    except PocsuiteUserQuitException:
        errMsg = "user quit"
        logger.log(CUSTOM_LOGGING.ERROR, errMsg)

    except KeyboardInterrupt:
        print
        errMsg = "user aborted"
        logger.log(CUSTOM_LOGGING.ERROR, errMsg)

    except EOFError:
        print
        errMsg = "exit"
        logger.log(CUSTOM_LOGGING.ERROR, errMsg)

    except SystemExit:
        pass

    except Exception, ex:
        print
        print ex
        #errMsg = unhandledExceptionMessage()
        #logger.log(CUSTOM_LOGGING.WARNING, errMsg)
        excMsg = traceback.format_exc()
        dataToStdout(excMsg)

    if 'pCollect' in kb:
        for p in kb.pCollect:
            delModule(p)

        if conf.get("showTime"):
            dataToStdout("\n[*] shutting down at %s\n\n" % time.strftime("%X"))

        kb.threadContinue = False
        kb.threadException = True

        if conf.get("threads", 0) > 1:
            os._exit(0)


if __name__ == "__main__":
    main()

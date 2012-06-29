#! /usr/bin/env python2.6

################################################################################
#
# check-mountpoint.py control mount point presence and mount options
#
# (C) 2012 Francois SCALA
#

################################################################################
#
# Imports
#
import getopt
import sys
import pprint

################################################################################
#
# Globals
#

RES_OK = 0
RES_WARNING = 1
RES_CRITICAL = 2
RES_UNKNOWN = 3

ProgOpts = dict()
ProcMount = "/proc/mounts"
ProgName = 'CHECK-MOUNTPOINT'
ReturnCode = RES_OK
ReturnString = ''
ReturnCodesStrings = ['OK','WARNING','CRITICAL','UNKNOWN']

################################################################################
#
# main function
#
def main():
	global MPByDev, MPByPath

	scan_args()

	parse_procmounts()

	display_result()


################################################################################
#
# display result and exit
#
def display_result():
	global ReturnString

	ReturnString = '%s %s : %s' %(ProgName, ReturnCodesStrings[ReturnCode], ReturnString)

	print ReturnString

	sys.exit(ReturnCode)

################################################################################
#
# parse /proc/mounts file
#
def parse_procmounts():
	global ProgOpts, ReturnCode, ReturnString

	try:
		fd = open(ProcMount, 'r')
	except:
		ReturnString = 'Error : cannot open file %s' %(ProcMount)
		ReturnCode = RES_UNKNOWN
		display_result()

	line = fd.readline()
	while line:

		try:
			mntline = line.split()
			mntdev    = mntline[0]
			mntpath   = mntline[1]
			mntfstype = mntline[2]
			mntoptstr = mntline[3]
		except:
			ReturnString = 'Error : fileformat error %s' %(ProcMount)
			ReturnCode = RES_UNKNOWN
			display_result()

		# check mntdev or mntpath matching
		if( ((ProgOpts['mode'] == 'dev')  and (mntdev  == ProgOpts['path'])) or
			((ProgOpts['mode'] == 'path') and (mntpath == ProgOpts['path'])) ):

			# check fstype
			if( (ProgOpts.has_key('fstype')) and (ProgOpts['fstype']) != mntfstype ):
				if( ProgOpts['report'] == 'critical'):
					ReturnCode = RES_CRITICAL
				else:
					ReturnCode = RES_WARNING
				ReturnString += '%s mounted on %s is not %s but %s' %(mntdev, mntpath, ProgOpts['fstype'], mntfstype)

			# check mount options
			if( ProgOpts.has_key('option')):
				mntopts = mntoptstr.split(',')
				checkopts = ProgOpts['option'].split(',')
				tmpstring = ''

				for i in checkopts:
					if( not i in mntopts):
						tmpstring += ' %s' % i

				if( not tmpstring == '' ):
					if( ProgOpts['report'] == 'critical'):
						ReturnCode = RES_CRITICAL
					else:
						ReturnCode = RES_WARNING
					ReturnString = '%s mounted on %s as %s does not have%s mount option(s)' %(mntdev, mntpath, mntfstype, tmpstring)

			# ok
			break

		line = fd.readline()
		# while line:

	if(ReturnCode == RES_OK):
		ReturnString += '%s mounted on %s as %s' %(mntdev, mntpath, mntfstype)

################################################################################
#
# scan command line parameters
#
def scan_args():
	global ProgOpts, ReturnString, ReturnCode

	try:
		opts, args = getopt.getopt( sys.argv[1:],"d:p:cwf:o:h?", [ "dev=", "path=", "critical", "warning", "fstype=", "option=", "help" ] )
	except:
		ReturnString = 'Error : invalid parameters'
		ReturnCode = RES_UNKNOWN
		display_result()

	opts = dict(opts)

	if( (opts.has_key('-?')) or (opts.has_key('-h')) or (opts.has_key('--help' )) ):
		print_help()
		sys.exit(0)

	# --dev AND --path
	if( ((opts.has_key('-d')) or (opts.has_key('--dev' ))) and 
		((opts.has_key('-p')) or (opts.has_key('--path'))) ):
		ReturnString = 'Error : you must choose between --dev and --path'
		ReturnCode = RES_UNKNOWN
		display_result()

	# operating mode
	if( opts.has_key('-d')):
		#print ">> DEV mode"
		ProgOpts['mode'] = 'dev'
		ProgOpts['path'] = opts['-d']
	elif( opts.has_key('--dev' ) ):
		#print ">> DEV mode"
		ProgOpts['mode'] = 'dev'
		ProgOpts['path'] = opts['--dev']
	elif( opts.has_key('-p')):
		#print ">> PATH mode"
		ProgOpts['mode'] = 'path'
		ProgOpts['path'] = opts['-p']
	elif( opts.has_key('--path' )):
		#print ">> PATH mode"
		ProgOpts['mode'] = 'path'
		ProgOpts['path'] = opts['--path']
	else:
		ReturnString = 'Error : you must specify --dev or --path'
		ReturnCode = RES_UNKNOWN
		display_result()

	# error AND warning
	if( ((opts.has_key('-c')) or (opts.has_key('--critical' ))) and 
		((opts.has_key('-w')) or (opts.has_key('--warning'))) ):
		ReturnString = 'Error : you must choose between --critical and --warning'
		ReturnCode = RES_UNKNOWN
		display_result()

	# reporting mode
	if( (opts.has_key('-c')) or (opts.has_key('--critical' )) ):
		#print ">> Report ERROR"
		ProgOpts['report'] = 'critical'
	elif( (opts.has_key('-w')) or (opts.has_key('--warning' )) ):
		#print ">> Report WARNING"
		ProgOpts['report'] = 'warning'
	else:
		#print ">> Report ERROR (by default)"
		ProgOpts['report'] = 'critical'

	# fstype
	if( (opts.has_key('-f')) or (opts.has_key('--fstype' )) ):
		if(opts.has_key('-f')):
			ProgOpts['fstype'] = opts['-f']
		else:
			ProgOpts['fstype'] = opts['--fstype']

	# mount options
	if( (opts.has_key('-o')) or (opts.has_key('--option' )) ):
		if(opts.has_key('-o')):
			ProgOpts['option'] = opts['-o']
		else:
			ProgOpts['option'] = opts['--option']

	# check trailing /
	if( ProgOpts['path'][-1] == '/'):
		ProgOpts['path'] = ProgOpts['path'][:-1]

################################################################################
#
# print help message (but does not exit)
#
def print_help():
	print "check-mountpoint.py : nagios plugin to control mount point presence and options"
	print ""
	print "Usage : check-mountpoint.py <--dev|-d|--mountpoint|-m path >  [--critical] [--warning] [--fstype] [--option]"
	print ""
	print "    -d|--dev : control mount point by device name"
	print "    -p|--path : control mount point by path name"
	print "    -c|--critical : report problem as error"
	print "    -w|--warning : report problem as warning"
	print "    -f|--fstype : check for filesystem type"
	print "    -o|--option : check for mount options, separated by comma (rw,noatime)"
	print "    -h|--help : display help"
	print ""

################################################################################
if __name__ == '__main__':
	main()



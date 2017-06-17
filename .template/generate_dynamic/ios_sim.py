import os
import logging
import subprocess
import re

from module_dynamic.utils import which

import ios_sim_parser

LOG = logging.getLogger(__name__)

def _run_command(cmd):
	"""given shell command, returns communication tuple of stdout and stderr"""
	return subprocess.Popen(cmd,
							stdout=subprocess.PIPE,
							stderr=subprocess.PIPE,
							stdin=subprocess.PIPE).communicate()


def check_xcrun():
	xcrun = which("xcrun")
	if not xcrun:
		raise Exception(__name__, "xcrun not found", "Please check your Xcode installation.")
	return xcrun

# Alphanumeric comparison because _someone_ at Apple used "12.9-inch" in devicetypes but "12.9 inch" in devices
def _matches(s1, s2):
	s1 = re.sub('\W', '', s1)
	s2 = re.sub('\W', '', s2)
	return s1 == s2

def device(devicetype_id=None, devicesdk=None):
	error = "Could not locate simulator for: %s %s" % (devicetype_id, devicesdk)
	resolution = "Please check your Xcode and iOS simulator setup"

	output = _run_command(["xcrun", "simctl", "list"])
	if output[1] != "":
		raise Exception(__name__, output[1], "")

	simulators = ios_sim_parser.parse(output[0])
	if not simulators["runtimes"] or not simulators["devices"] or not simulators["devicetypes"]:
		raise Exception(__name__, error, resolution)

	if not devicetype_id:
		return simulators

	# find devicetype
	try:
		devicetype = (item for item in simulators["devicetypes"] if item["id"] == devicetype_id).next()
	except:
		raise Exception(__name__, error, resolution)

	# find runtime
	if devicesdk:
		try:
			runtime = (item for item in simulators["runtimes"] if item["name"] == devicesdk).next()
		except:
			runtime = None
	else:
			runtime = simulators["runtimes"][0]
	if not runtime:
		raise Exception(__name__, error, resolution)

	# find device
	try:
		device = (item for item in simulators["devices"] if _matches(item["devicetype"], devicetype["name"]) and item["runtime"] == runtime["name"]).next()
	except:
		raise Exception(__name__, error, resolution)

	return device


def start(device=None):
	# We can start a specific device in the sim using instruments, but it does complain
	# that no template was specified
	silly_hack = "No template (-t) specified"
	if device:
		cmd = [ "xcrun", "instruments", "-w", device["id"] ]
		#output = _run_command(cmd)
		#if output[1] != "" and not silly_hack in output[1]:
		#	raise Exception(__name__, output[1], "")
		output = subprocess.call(cmd)
		LOG.debug("Started simulator with command: %s -> %s" % (cmd, output))
		return

	output = _run_command(["open", "-a", "Simulator"])
	if output[1] == "":
		return
	output = _run_command(["open", "-a", "iOS Simulator"])
	if output[1] == "":
		return
	raise Exception(__name__, output[1], "")


def install(device, bundle):
	output = _run_command(["xcrun", "simctl", "install", device["id"], bundle])
	if output[1] != "":
		raise Exception(__name__, output[1], "")


def launch(device, package):
	output = _run_command(["xcrun", "simctl", "launch", device["id"], package])
	if output[1] != "":
		raise Exception(__name__, output[1], "")


def log(device):
	return "{home}/Library/Logs/CoreSimulator/{device}/system.log".format(
		home=os.path.expanduser("~"),
		device=device["id"]
	)

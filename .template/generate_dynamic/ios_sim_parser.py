import re
import logging

LOG = logging.getLogger(__name__)


# - Parsing for "simctl list" output --------------------------------------

re_runtime_unavailable = re.compile("(.*)\(([^)]+)\)\s\(([^)]+)\)\s\(([^)]+)\)")
re_runtime_available = re.compile("(.*)\(([^)]+)\)\s\(([^)]+)\)")
re_devicetype = re.compile("(.*)\(([^)]+)\)")
re_device_unavailable = re.compile("(.*)\(([^)]+)\)\s\(([^)]+)\)\s\(unavailable([^)]+)\)")
re_device_available = re.compile("(.*)\(([^)]+)\)\s\(([^)]+)\)")

def _parse_runtime(line):
	# iOS 7.0 (7.0 - Unknown) (com.apple.CoreSimulator.SimRuntime.iOS-7-0) (unavailable, runtime path not found)
	available = False
	matches = re_runtime_unavailable.findall(line)
	if not matches:
		matches = re_runtime_available.findall(line)
		available = True
	if matches:
		return {
			"name": matches[0][0].strip(),
			"build": matches[0][1].strip(),
			"id": matches[0][2].strip(),
			"available": available
		}
	return None

def _parse_devicetype(line):
	# iPhone 4s (com.apple.CoreSimulator.SimDeviceType.iPhone-4s)
	matches = re_devicetype.findall(line)
	if matches:
		return {
			"name": matches[0][0].strip(),
			"id": matches[0][1].strip(),
		}
	return None


def _parse_device(line):
	# iPad 2 (B5556627-383D-4355-9DFD-082971C5C062) (Shutdown) (unavailable, runtime profile not found)
	global _currentRuntime
	if line.startswith("--"):
		re_runtime_name = re.compile("--\s(.*)\s--")
		matches = re_runtime_name.findall(line)
		if matches:
			_currentRuntime = matches[0].strip()
		else:
			_currentRuntime = "unknown"
		return

	available = False
	matches = re_device_unavailable.findall(line)
	if not matches:
		matches = re_device_available.findall(line)
		available = True
	if matches:
		return {
			"runtime": _currentRuntime,
			"devicetype": matches[0][0].strip(),
			"id": matches[0][1].strip(),
			"state": matches[0][2].strip(),
			"available": available
		}
	return None

def parse(lines):
	ret = { "runtimes": [], "devices": [], "devicetypes": [] }

	lines = re.compile("\r?\n").split(lines)
	for line in lines:
		if line.startswith("== "):
			mode = line
			continue
		elif line == "":
			continue

		if mode == "== Runtimes ==":
			runtime = _parse_runtime(line)
			if runtime:
				ret["runtimes"].append(runtime)
		elif mode == "== Device Types ==":
			devicetype = _parse_devicetype(line)
			if devicetype:
				ret["devicetypes"].append(devicetype)
		elif mode == "== Devices ==":
			device = _parse_device(line)
			if device and not device["runtime"].startswith("Unavailable"):
				ret["devices"].append(device)
		else:
			# unknown mode
			pass

	return ret

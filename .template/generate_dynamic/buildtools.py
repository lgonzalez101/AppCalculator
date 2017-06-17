'''Stuff that used to live in build-tools/ that really needs to be
part of the platform.
'''
import logging
LOG = logging.getLogger(__name__)
import os
from os import path
import shutil
import json
import time
from datetime import datetime

try:
	import forge
except:
	LOG.info("Running on command line")

# these are only used when imported by build-tools, not when server imports
try:
	from forge.generate import Generate
	from forge import defaults, build_config, ForgeError
	from forge.lib import try_a_few_times, AccidentHandler, FilterHandler, CurrentThreadHandler, classify_platform
	from forge import cli
	LOG.info("Running from build-tools")
except:
	LOG.info("Running on the server")

import customer_phases

ENTRY_POINT_NAME = 'forge'
FORGE_BUILD_NEEDS_TARGET = """Target required for 'forge build', e.g. 'forge build android'"""

def development_build_dynamic(unhandled_args, has_target, manager, remote, app_config, stable_platform, frepeat):
	
	# Peek at target
	try:
		target = unhandled_args[0]
	except IndexError:
		target = ""

	config_changed = manager.need_new_templates_for_config()
	if config_changed and target in ["ios-native", "android-native"]:
			moved_to = moved_to = os.path.join('development', '%s.%s' % (target, datetime.now().isoformat().replace(":", "-")))
			LOG.warn("")
			LOG.warn("========================================================================")
			LOG.warn("Your application's configuration has changed and the Xcode project needs")
			LOG.warn("to be regenerated.")
			LOG.warn("")
			LOG.warn("Proceeding will reset any changes you've made to the Xcode project and")
			LOG.warn("require you to repopulate your ForgeExtensions/ folder.")	
			LOG.warn("")
			LOG.warn("Your existing Xcode project will be backed up to:")
			LOG.warn("")
			LOG.warn("\t%s" % moved_to)
			LOG.warn("========================================================================")
			time.sleep(1) # cli.ask_yes_no isn't buffered
			proceed = cli.ask_yes_no("Backup Xcode project directory and continue build?", False)
			if not proceed:
				LOG.info("Aborting build and restoring app configuration.")
				shutil.copy(path.join(defaults.TEMPLATE_DIR, "config.json"), path.join(defaults.SRC_DIR, "config.json"))
				LOG.info("App configuration restored.")
				return
			else: # backup existing Xcode directory
				moved_from = path.join('development', target)
				if os.path.exists(moved_from):					
					shutil.move(moved_from, moved_to)
				pass

	if config_changed:
		# Need new builds due to local config change
		LOG.info("Your local config has been changed, downloading updated build instructions.")
		manager.fetch_instructions()

		# repeat the whole procedure, as we may have migrated the app in some way
		forge.settings['full'] = False
		return frepeat(unhandled_args, has_target) # TODO This is a really ugly approach

	reload_result = remote.create_buildevent(app_config)['data']
	if not has_target:
		# No need to go further if we aren't building a target
		return

	try:
		target = unhandled_args.pop(0)
		if target.startswith("-"):
			raise ForgeError(FORGE_BUILD_NEEDS_TARGET)
	except IndexError:
		raise ForgeError(FORGE_BUILD_NEEDS_TARGET)

	# Not all targets output into a folder by the same name.
	target_dirs = {
		'safari': 'forge.safariextension',
	}
	target_dir = target
	if target in target_dirs:
		target_dir = target_dirs[target]


	reload_config = json.loads(reload_result['config'])
	reload_config_hash = reload_result['config_hash']

	if target != "reload": # Don't do a server side build for reload
		if not path.exists(path.join(defaults.TEMPLATE_DIR, target_dir)):
			LOG.info("Your app configuration has changed since your last build of this platform, performing a remote build of your app. Once this is downloaded future builds will be faster.")
			build = remote.build(config=reload_config, target=target)
			remote.fetch_unpackaged(build, to_dir=defaults.TEMPLATE_DIR, target=target)
	else:
		LOG.info('Config matches previously downloaded build, performing local build.')

	current_platform = app_config['platform_version']

	# Advise user about state of their current platform
	platform_category = classify_platform(stable_platform, current_platform)
	if platform_category == 'nonstandard':
		LOG.warning("Platform version: %s is a non-standard platform version, it may not be receiving updates and it is recommended you update to the stable platform version: %s" % (current_platform, stable_platform))

	elif platform_category == 'minor':
		# do nothing: not an issue to be on a minor platform since v2.0.0
		pass

	elif platform_category == 'old':
		LOG.warning("Platform version: %s is no longer the current platform version, it is recommended you switch to a newer version." % current_platform)

	def move_files_across():
		shutil.rmtree(path.join('development', target_dir), ignore_errors=True)
		if target != "reload":
			# Delete reload as other targets may build it
			shutil.rmtree(path.join('development', 'reload'), ignore_errors=True)
			# No reload server template
			shutil.copytree(path.join(defaults.TEMPLATE_DIR, target_dir), path.join('development', target_dir), symlinks=True)

	if target in ["ios-native", "android-native"]:
			if not os.path.isdir(path.join('development', 'ios-native')):
				try_a_few_times(move_files_across)
			else:
				# Just delete the source files
				shutil.rmtree(customer_phases.locations_normal[target])
				# Delete reload as other targets may build it
				shutil.rmtree(path.join('development', 'reload'), ignore_errors=True)
	else:
		# Windows often gives a permission error without a small wait
		try_a_few_times(move_files_across)

	# Put config hash in config object for local generation
	# copy first as mutating dict makes assertions about previous uses tricky
	reload_config_for_local = reload_config.copy()
	reload_config_for_local['config_hash'] = reload_config_hash

	# have templates and instructions - inject code
	generator = Generate()
	generator.all('development', defaults.SRC_DIR, extra_args=unhandled_args, config=reload_config_for_local, target=target)

	if target in ["ios-native", "android-native"]:
		LOG.info("Development build created. You can access your native project files in the 'development/{target}' directory.".format(
			target=target
		))
	else:
		LOG.info("Development build created. Use {prog} run to run your app.".format(
			prog=ENTRY_POINT_NAME
		))


